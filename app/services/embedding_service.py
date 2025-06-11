"""Embedding service for the Security Compliance Assistant."""
import os
from typing import Dict, List, Optional, Union, Any

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    """Service for generating embeddings for text."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use.
                If None, use the model specified in settings.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the embedding model."""
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model {self.model_name}: {str(e)}")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of embeddings, one for each input text.
        """
        if not self.model:
            self._load_model()
        
        # Handle empty input
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Convert to list of lists
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        else:
            return embeddings
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector.
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0]


# Default embedding service
default_embedding_service = EmbeddingService()
