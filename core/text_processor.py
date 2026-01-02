"""
Z.M.ai - Text Processor

Handles text chunking and cleaning for the RAG pipeline.
"""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass

from config import get_rag_config
from .document_loader import Document

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    source: str
    source_type: str
    chunk_index: int
    page_numbers: Optional[List[int]] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __len__(self) -> int:
        return len(self.content)

    def to_dict(self) -> dict:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "chunk_index": self.chunk_index,
            "page_numbers": self.page_numbers,
            "metadata": self.metadata,
        }


class TextCleaner:
    """Cleans and normalizes text content."""

    # Common patterns to clean
    PATTERNS_TO_REMOVE = [
        r"\s+",  # Multiple whitespace
        r"\n{3,}",  # Three or more newlines
        r"\r",  # Carriage returns
    ]

    @staticmethod
    def clean(text: str) -> str:
        """
        Clean text by normalizing whitespace and removing artifacts.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove carriage returns
        text = text.replace("\r", "")

        # Normalize multiple newlines to double newline
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Normalize multiple spaces to single space
        text = re.sub(r"[ \t]+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def normalize_quotes(text: str) -> str:
        """Normalize different quote characters to standard quotes."""
        # Curly quotes to straight quotes
        text = text.replace("\u201c", '"').replace("\u201d", '"')  # Double quotes
        text = text.replace("\u2018", "'").replace("\u2019", "'")  # Single quotes
        return text

    @staticmethod
    def remove_special_chars(text: str, keep: str = ".!?,;:") -> str:
        """
        Remove special characters except those specified.

        Args:
            text: Text to process
            keep: Characters to keep (punctuation, etc.)

        Returns:
            Text with special chars removed
        """
        # Build pattern to keep alphanumeric and specified chars
        pattern = f"[^a-zA-Z0-9\\s{re.escape(keep)}]"
        return re.sub(pattern, "", text)


class TextChunker:
    """Splits text into chunks for RAG processing."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.config = get_rag_config()
        self.chunk_size = chunk_size or self.config.chunk_size
        self.chunk_overlap = chunk_overlap or self.config.chunk_overlap
        self.cleaner = TextCleaner()

        logger.info(f"TextChunker initialized: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")

    def chunk_document(self, document: Document) -> List[TextChunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of TextChunk objects
        """
        cleaned_text = self.cleaner.clean(document.content)
        chunks = self._split_text(cleaned_text)

        text_chunks = []
        for i, chunk_content in enumerate(chunks):
            text_chunks.append(TextChunk(
                content=chunk_content,
                source=document.source,
                source_type=document.source_type,
                chunk_index=i,
                page_numbers=document.page_numbers,
                metadata={
                    **document.metadata,
                    "chunk_size": len(chunk_content),
                }
            ))

        logger.debug(f"Created {len(text_chunks)} chunks from {document.source}")
        return text_chunks

    def chunk_documents(self, documents: List[Document]) -> List[TextChunk]:
        """
        Split multiple documents into chunks.

        Args:
            documents: List of Documents to chunk

        Returns:
            List of TextChunk objects from all documents
        """
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} total chunks from {len(documents)} documents")
        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using a sliding window approach.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                boundary = self._find_sentence_boundary(text, start, end)

                if boundary > start:
                    end = boundary
                else:
                    # No good boundary found, try to break at a word boundary
                    boundary = self._find_word_boundary(text, end)
                    if boundary > start:
                        end = boundary

            # Extract the chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap
            chunk_index += 1

            # Avoid infinite loop
            if start <= 0:
                start = end

        return chunks

    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find a good sentence boundary near the end position.

        Args:
            text: Full text
            start: Current start position
            end: Current end position

        Returns:
            Position of sentence boundary, or start if none found
        """
        # Look for sentence endings within a reasonable range before end
        search_start = max(start, end - 200)

        # Sentence endings (period, question mark, exclamation)
        for pos in range(end - 1, search_start, -1):
            char = text[pos]
            if char in ".!?":
                # Check if it's followed by space and capital letter or end of text
                next_pos = pos + 1
                if next_pos >= len(text):
                    return pos + 1
                if text[next_pos] == " ":
                    next_next = next_pos + 1
                    if next_next < len(text) and text[next_next].isupper():
                        return pos + 1
                # Also accept abbreviations with periods
                if char == "." and pos > 0:
                    prev_char = text[pos - 1]
                    if prev_char.isupper():  # Likely an abbreviation
                        continue

        return start  # No good boundary found

    def _find_word_boundary(self, text: str, end: int) -> int:
        """
        Find a word boundary near the end position.

        Args:
            text: Full text
            end: Current end position

        Returns:
            Position of word boundary, or end if none found
        """
        # Look backwards for a space
        for pos in range(end - 1, max(0, end - 100), -1):
            if text[pos] == " ":
                return pos + 1

        return end


class TextProcessor:
    """Main text processor that combines cleaning and chunking."""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.chunker = TextChunker()

    def process_documents(self, documents: List[Document]) -> List[TextChunk]:
        """
        Process documents into clean chunks ready for embedding.

        Args:
            documents: List of Documents to process

        Returns:
            List of TextChunk objects
        """
        if not documents:
            logger.warning("No documents to process")
            return []

        return self.chunker.chunk_documents(documents)

    def process_query(self, query: str) -> str:
        """
        Clean and normalize a user query.

        Args:
            query: Raw user query

        Returns:
            Cleaned query
        """
        if not query:
            return ""

        cleaned = self.cleaner.clean(query)
        cleaned = self.cleaner.normalize_quotes(cleaned)

        return cleaned

    def get_chunk_summary(self, chunks: List[TextChunk]) -> dict:
        """
        Get summary statistics about chunks.

        Args:
            chunks: List of TextChunk objects

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {"count": 0, "total_chars": 0, "avg_chars": 0}

        total_chars = sum(len(c) for c in chunks)
        source_types = {}

        for chunk in chunks:
            source_types[chunk.source_type] = source_types.get(chunk.source_type, 0) + 1

        return {
            "count": len(chunks),
            "total_chars": total_chars,
            "avg_chars": total_chars // len(chunks),
            "min_chars": min(len(c) for c in chunks),
            "max_chars": max(len(c) for c in chunks),
            "source_types": source_types,
        }
