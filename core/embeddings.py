"""
Z.M.ai - Embeddings Module

Handles vector embeddings using sentence-transformers (local, free).
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from config import get_rag_config, get_data_source_config
from .text_processor import TextChunk

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model."""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformers model
        """
        self.config = get_rag_config()
        self.model_name = model_name or self.config.embedding_model

        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        logger.info(f"Embedding model loaded: dimension={self.embedding_dim}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Embedding matrix as numpy array (shape: [n_texts, embedding_dim])
        """
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    def embed_chunks(self, chunks: List[TextChunk]) -> np.ndarray:
        """
        Generate embeddings for text chunks.

        Args:
            chunks: List of TextChunk objects

        Returns:
            Embedding matrix as numpy array
        """
        texts = [chunk.content for chunk in chunks]
        return self.embed_texts(texts)


class VectorStore:
    """FAISS-based vector store for similarity search."""

    def __init__(self, embedding_dim: int):
        """
        Initialize the vector store.

        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.index: Optional[faiss.Index] = None
        self.chunks: List[TextChunk] = []
        self.is_built = False

    def build_index(self, chunks: List[TextChunk], embeddings: Optional[np.ndarray] = None):
        """
        Build the FAISS index from chunks and embeddings.

        Args:
            chunks: List of TextChunk objects
            embeddings: Pre-computed embeddings (optional, will compute if None)
        """
        if not chunks:
            logger.warning("No chunks to build index from")
            return

        self.chunks = chunks

        if embeddings is None:
            # Compute embeddings
            embedding_model = EmbeddingModel()
            embeddings = embedding_model.embed_chunks(chunks)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Create FAISS index (using Inner Product for cosine similarity)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings.astype("float32"))

        self.is_built = True
        logger.info(f"Built FAISS index with {len(chunks)} chunks")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (chunk_index, score) tuples
        """
        if not self.is_built:
            logger.error("Cannot search: index not built")
            return []

        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(query_embedding.reshape(1, -1))

        # Search
        scores, indices = self.index.search(query_embedding.reshape(1, -1).astype("float32"), min(top_k, len(self.chunks)))

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx >= 0:  # FAISS returns -1 for empty results
                results.append((int(idx), float(score)))

        return results

    def get_chunk(self, index: int) -> Optional[TextChunk]:
        """Get chunk by index."""
        if 0 <= index < len(self.chunks):
            return self.chunks[index]
        return None

    def save(self, path: Path):
        """
        Save the index to disk.

        Args:
            path: Directory to save index files
        """
        if not self.is_built:
            logger.warning("Cannot save: index not built")
            return

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = path / "index.faiss"
        faiss.write_index(self.index, str(index_path))

        # Save chunks metadata (simplified - just save the text content)
        # In production, you might want to use a proper serialization format
        chunks_path = path / "chunks.txt"
        with open(chunks_path, "w", encoding="utf-8") as f:
            for chunk in self.chunks:
                f.write(f"--- CHUNK {chunk.chunk_index} ---\n")
                f.write(f"Source: {chunk.source}\n")
                f.write(f"Type: {chunk.source_type}\n")
                f.write(f"Content: {chunk.content}\n")
                f.write("\n")

        logger.info(f"Saved index to {path}")

    def load(self, path: Path):
        """
        Load the index from disk.

        Args:
            path: Directory containing index files
        """
        path = Path(path)

        index_path = path / "index.faiss"
        if not index_path.exists():
            logger.error(f"Index file not found: {index_path}")
            return

        self.index = faiss.read_index(str(index_path))
        self.is_built = True

        logger.info(f"Loaded index from {path}")


class EmbeddingManager:
    """High-level manager for embeddings and vector store."""

    def __init__(self):
        self.config = get_rag_config()
        self.data_config = get_data_source_config()
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(self.embedding_model.embedding_dim)

    def create_index(self, chunks: List[TextChunk]) -> VectorStore:
        """
        Create a searchable index from chunks.

        Args:
            chunks: List of TextChunk objects

        Returns:
            VectorStore with built index
        """
        if not chunks:
            logger.warning("No chunks to index")
            return self.vector_store

        logger.info(f"Creating index from {len(chunks)} chunks...")

        # Generate embeddings
        embeddings = self.embedding_model.embed_chunks(chunks)

        # Build vector store
        self.vector_store.build_index(chunks, embeddings)

        logger.info(f"Index created successfully")
        return self.vector_store

    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[TextChunk, float]]:
        """
        Search for relevant chunks given a query.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (TextChunk, score) tuples
        """
        if not self.vector_store.is_built:
            logger.error("Cannot search: index not built")
            return []

        top_k = top_k or self.config.top_k_results

        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)

        # Search
        results = self.vector_store.search(query_embedding, top_k)

        # Convert to (chunk, score) tuples
        chunk_results = []
        for idx, score in results:
            chunk = self.vector_store.get_chunk(idx)
            if chunk and score >= self.config.similarity_threshold:
                chunk_results.append((chunk, score))

        logger.info(f"Found {len(chunk_results)} relevant chunks (threshold={self.config.similarity_threshold})")
        return chunk_results

    def save_index(self):
        """Save the current index to disk."""
        cache_dir = self.data_config.project_root / self.data_config.cache_dir
        self.vector_store.save(cache_dir)

    def load_index(self) -> bool:
        """
        Load index from disk.

        Returns:
            True if successful, False otherwise
        """
        cache_dir = self.data_config.project_root / self.data_config.cache_dir
        index_path = cache_dir / "index.faiss"

        if not index_path.exists():
            logger.info("No cached index found")
            return False

        try:
            self.vector_store.load(cache_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to load cached index: {e}")
            return False
