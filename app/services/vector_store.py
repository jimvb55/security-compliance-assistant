"""Vector store service for the Security Compliance Assistant."""
import json
import os
import pickle
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple

import numpy as np

from app.config import settings
from app.models.chunk import Chunk, ChunkMetadata


class BaseVectorStore(ABC):
    """Base class for vector stores."""
    
    def __init__(self, index_name: str = "default"):
        """Initialize the vector store.
        
        Args:
            index_name: Name of the index.
        """
        self.index_name = index_name
        self.chunks: List[Chunk] = []
        self.index_path = os.path.join(settings.VECTOR_DB_PATH, index_name)
    
    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Add chunks to the vector store.
        
        Args:
            chunks: List of chunks to add.
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        num_results: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[Tuple[Chunk, float]]:
        """Search for similar chunks.
        
        Args:
            query_embedding: Query embedding.
            num_results: Number of results to return.
            min_score: Minimum similarity score.
            filters: Metadata filters.
            
        Returns:
            List of (chunk, score) tuples.
        """
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Save the vector store to disk."""
        pass
    
    @abstractmethod
    def load(self) -> None:
        """Load the vector store from disk."""
        pass
    
    def delete_chunks(self, doc_id: str) -> None:
        """Delete chunks for a document.
        
        Args:
            doc_id: Document ID.
        """
        # Filter out chunks for the specified document
        self.chunks = [chunk for chunk in self.chunks if chunk.doc_id != doc_id]
        
        # Re-index
        self._build_index()
    
    def clear(self) -> None:
        """Clear the vector store."""
        self.chunks = []
        self._build_index()
    
    @abstractmethod
    def _build_index(self) -> None:
        """Build the index from chunks."""
        pass


class FaissVectorStore(BaseVectorStore):
    """FAISS vector store implementation."""
    
    def __init__(self, index_name: str = "default"):
        """Initialize the FAISS vector store.
        
        Args:
            index_name: Name of the index.
        """
        super().__init__(index_name=index_name)
        
        # Import FAISS lazily to avoid dependency issues
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError(
                "FAISS not installed. Please install it with 'pip install faiss-cpu' or 'pip install faiss-gpu'."
            )
        
        # Initialize index
        self.index = None
        self.embeddings = None
    
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Add chunks to the vector store.
        
        Args:
            chunks: List of chunks to add.
        """
        # Add chunks to the list
        self.chunks.extend(chunks)
        
        # Rebuild the index
        self._build_index()
    
    def search(
        self,
        query_embedding: List[float],
        num_results: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[Tuple[Chunk, float]]:
        """Search for similar chunks.
        
        Args:
            query_embedding: Query embedding.
            num_results: Number of results to return.
            min_score: Minimum similarity score.
            filters: Metadata filters.
            
        Returns:
            List of (chunk, score) tuples.
        """
        if not self.index or not self.chunks:
            return []
        
        # Convert query embedding to numpy array
        query_embedding_np = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        # Search the index
        distances, indices = self.index.search(query_embedding_np, len(self.chunks))
        
        # Flatten results
        distances = distances[0]
        indices = indices[0]
        
        # Convert distances to scores (similarity)
        scores = 1.0 - distances / 2.0
        
        # Filter results
        results = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.chunks) or score < min_score:
                continue
            
            chunk = self.chunks[idx]
            
            # Apply filters
            if filters and not self._apply_filters(chunk, filters):
                continue
            
            results.append((chunk, float(score)))
            
            if len(results) >= num_results:
                break
        
        return results
    
    def _apply_filters(self, chunk: Chunk, filters: Dict) -> bool:
        """Apply filters to a chunk.
        
        Args:
            chunk: Chunk to filter.
            filters: Metadata filters.
            
        Returns:
            True if the chunk passes the filters, False otherwise.
        """
        for key, value in filters.items():
            if key == "tags" and isinstance(value, list):
                # Check if any of the specified tags is present
                if not any(tag in chunk.metadata.tags for tag in value):
                    return False
            elif key == "tags" and isinstance(value, str):
                # Check if the specified tag is present
                if value not in chunk.metadata.tags:
                    return False
            elif hasattr(chunk.metadata, key):
                # Check if the attribute matches
                if getattr(chunk.metadata, key) != value:
                    return False
        
        return True
    
    def save(self) -> None:
        """Save the vector store to disk."""
        # Create the directory if it doesn't exist
        os.makedirs(self.index_path, exist_ok=True)
        
        # Save chunks
        chunks_data = [chunk.to_dict() for chunk in self.chunks]
        with open(os.path.join(self.index_path, "chunks.json"), "w") as f:
            json.dump(chunks_data, f)
        
        # Save index if it exists
        if self.index is not None:
            self.faiss.write_index(
                self.index,
                os.path.join(self.index_path, "index.faiss")
            )
    
    def load(self) -> None:
        """Load the vector store from disk."""
        # Check if index exists
        index_file = os.path.join(self.index_path, "index.faiss")
        chunks_file = os.path.join(self.index_path, "chunks.json")
        
        if not os.path.exists(index_file) or not os.path.exists(chunks_file):
            raise FileNotFoundError(f"Index {self.index_name} not found")
        
        # Load chunks
        with open(chunks_file, "r") as f:
            chunks_data = json.load(f)
        
        self.chunks = [Chunk.from_dict(data) for data in chunks_data]
        
        # Load index
        self.index = self.faiss.read_index(index_file)
        
        # Extract embeddings
        self._extract_embeddings()
    
    def _build_index(self) -> None:
        """Build the index from chunks."""
        if not self.chunks:
            self.index = None
            self.embeddings = None
            return
        
        # Extract embeddings
        self._extract_embeddings()
        
        # Create index
        dimension = self.embeddings.shape[1]
        self.index = self.faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        self.index.add(self.embeddings)
    
    def _extract_embeddings(self) -> None:
        """Extract embeddings from chunks."""
        # Check if chunks have embeddings
        if not all(chunk.embedding is not None for chunk in self.chunks):
            raise ValueError("Some chunks do not have embeddings")
        
        # Convert embeddings to numpy array
        self.embeddings = np.array(
            [chunk.embedding for chunk in self.chunks],
            dtype=np.float32
        )


def create_vector_store(index_name: str = "default") -> BaseVectorStore:
    """Create a vector store based on configuration.
    
    Args:
        index_name: Name of the index.
        
    Returns:
        BaseVectorStore instance.
    """
    vector_db_type = settings.VECTOR_DB_TYPE.lower()
    
    if vector_db_type == "faiss":
        return FaissVectorStore(index_name=index_name)
    else:
        raise ValueError(f"Unsupported vector store type: {vector_db_type}")
