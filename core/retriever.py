"""
Z.M.ai - Retriever Module

Handles context retrieval and formatting for the RAG pipeline.
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from .embeddings import EmbeddingManager
from .text_processor import TextChunk, TextProcessor
from .document_loader import Document

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from a retrieval operation."""
    chunks: List[TextChunk] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    query: str = ""
    total_chunks_found: int = 0

    @property
    def has_context(self) -> bool:
        """Check if any relevant context was found."""
        return len(self.chunks) > 0

    @property
    def context_text(self) -> str:
        """Get combined context text from all chunks."""
        if not self.chunks:
            return ""

        parts = []
        for chunk, score in zip(self.chunks, self.scores):
            source_label = self._format_source_label(chunk)
            parts.append(f"[{source_label}] (relevance: {score:.2f})")
            parts.append(chunk.content)
            parts.append("")  # Empty line between chunks

        return "\n".join(parts)

    def _format_source_label(self, chunk: TextChunk) -> str:
        """Format a source label for a chunk."""
        if chunk.source_type == "pdf":
            from pathlib import Path
            name = Path(chunk.source).name
            if chunk.page_numbers:
                return f"PDF: {name}, Page {chunk.page_numbers[0]}"
            return f"PDF: {name}"
        else:
            return f"Website: {chunk.source}"

    def get_unique_sources(self) -> List[str]:
        """Get list of unique sources."""
        sources = set()
        for chunk in self.chunks:
            if chunk.source_type == "pdf":
                from pathlib import Path
                sources.add(f"📄 {Path(chunk.source).name}")
            else:
                sources.add(f"🌐 Website")
        return list(sources)

    def get_sources_with_pages(self) -> List[str]:
        """Get detailed source list with page numbers."""
        sources = []
        for chunk in self.chunks:
            if chunk.source_type == "pdf":
                from pathlib import Path
                name = Path(chunk.source).name
                if chunk.page_numbers:
                    sources.append(f"📄 {name} (Page {chunk.page_numbers[0]})")
                else:
                    sources.append(f"📄 {name}")
            else:
                sources.append(f"🌐 Website")
        return sources


class Retriever:
    """
    High-level retriever that combines embeddings and text processing.
    """

    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        """
        Initialize the retriever.

        Args:
            embedding_manager: Optional pre-configured embedding manager
        """
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.text_processor = TextProcessor()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant context for a query.

        Args:
            query: User query
            top_k: Maximum number of chunks to retrieve
            min_score: Minimum similarity score threshold

        Returns:
            RetrievalResult with relevant chunks
        """
        # Clean query
        clean_query = self.text_processor.process_query(query)

        if not clean_query:
            logger.warning("Empty query after processing")
            return RetrievalResult(query=query)

        # Search for relevant chunks
        chunk_results = self.embedding_manager.search(clean_query, top_k=top_k)

        if not chunk_results:
            logger.info(f"No relevant chunks found for query: {query[:50]}...")
            return RetrievalResult(query=query)

        # Extract chunks and scores
        chunks = [chunk for chunk, _ in chunk_results]
        scores = [score for _, score in chunk_results]

        # Filter by minimum score if specified
        if min_score is not None:
            filtered_chunks = []
            filtered_scores = []
            for chunk, score in zip(chunks, scores):
                if score >= min_score:
                    filtered_chunks.append(chunk)
                    filtered_scores.append(score)

            chunks = filtered_chunks
            scores = filtered_scores

        logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:50]}...")

        return RetrievalResult(
            chunks=chunks,
            scores=scores,
            query=query,
            total_chunks_found=len(chunk_results),
        )

    def format_context_for_llm(self, result: RetrievalResult, max_chars: int = 4000) -> str:
        """
        Format retrieved context for LLM consumption.

        Args:
            result: RetrievalResult from retrieve()
            max_chars: Maximum characters to include

        Returns:
            Formatted context string
        """
        if not result.has_context:
            return "No relevant information found in the documents."

        context = result.context_text

        # Truncate if necessary
        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Context truncated...]"

        return context

    def build_prompt(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Build a complete prompt for the LLM.

        Args:
            query: User query
            retrieval_result: Result from retrieve()
            system_prompt: Optional custom system prompt

        Returns:
            Complete prompt string
        """
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        context = self.format_context_for_llm(retrieval_result)

        prompt = f"""{system_prompt}

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION:
{query}

ANSWER:"""

        return prompt

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return """You are Z.M.ai, an academic policy assistant. Your role is to help students understand university policies accurately.

IMPORTANT RULES:
1. ONLY answer based on the context provided above
2. If the answer is not in the context, say "I don't have enough information about this in the policy documents."
3. Do NOT make up or guess any information
4. Do NOT add information from outside the provided context
5. Keep answers clear, concise, and helpful
6. If you're uncertain, say so rather than guessing

Format your response in a clear, readable way with bullet points or numbered lists where appropriate."""

    def retrieve_and_format(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> Tuple[str, List[str]]:
        """
        Convenience method to retrieve and format in one call.

        Args:
            query: User query
            top_k: Maximum number of chunks to retrieve

        Returns:
            Tuple of (formatted_context, list_of_sources)
        """
        result = self.retrieve(query, top_k=top_k)
        context = self.format_context_for_llm(result)
        sources = result.get_sources_with_pages()

        return context, sources


class RAGPipeline:
    """
    Complete RAG pipeline combining all components.
    """

    def __init__(self):
        """Initialize the RAG pipeline."""
        self.retriever = Retriever()
        self.documents: List[Document] = []
        self.is_initialized = False

    def initialize(self, documents: List[Document]) -> bool:
        """
        Initialize the pipeline with documents.

        Args:
            documents: List of Documents to index

        Returns:
            True if successful
        """
        if not documents:
            logger.warning("No documents provided for initialization")
            return False

        logger.info(f"Initializing RAG pipeline with {len(documents)} documents...")

        self.documents = documents

        # Process documents into chunks
        text_processor = TextProcessor()
        chunks = text_processor.process_documents(documents)

        if not chunks:
            logger.error("No chunks generated from documents")
            return False

        # Create embedding index
        self.retriever.embedding_manager.create_index(chunks)

        self.is_initialized = True
        logger.info(f"RAG pipeline initialized successfully")
        return True

    def query(self, user_query: str) -> RetrievalResult:
        """
        Query the RAG pipeline.

        Args:
            user_query: User's question

        Returns:
            RetrievalResult with relevant context
        """
        if not self.is_initialized:
            logger.error("Pipeline not initialized")
            return RetrievalResult(query=user_query)

        return self.retriever.retrieve(user_query)

    def get_stats(self) -> dict:
        """Get statistics about the pipeline."""
        return {
            "is_initialized": self.is_initialized,
            "num_documents": len(self.documents),
            "document_types": self._count_document_types(),
        }

    def _count_document_types(self) -> dict:
        """Count documents by type."""
        types = {"pdf": 0, "web": 0}
        for doc in self.documents:
            if doc.source_type in types:
                types[doc.source_type] += 1
        return types
