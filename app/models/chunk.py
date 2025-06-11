"""Chunk model for the Security Compliance Assistant."""
from typing import Dict, List, Optional, Union, Any

import numpy as np
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    
    doc_id: str
    chunk_id: str
    filename: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    file_path: Optional[str] = None
    start_idx: int = 0
    end_idx: int = 0
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    version: Optional[str] = None
    modified_date: Optional[str] = None


class Chunk(BaseModel):
    """Chunk model representing a chunk of text in the knowledge base."""
    
    doc_id: str
    chunk_id: Optional[str] = None
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
    
    def __init__(self, **data):
        """Initialize a chunk.
        
        If chunk_id is not provided, it's generated from doc_id.
        If metadata.chunk_id is not set, it's set to chunk_id.
        """
        super().__init__(**data)
        
        # Set chunk_id if not provided
        if self.chunk_id is None and self.metadata.chunk_id:
            self.chunk_id = self.metadata.chunk_id
        elif self.chunk_id is None:
            self.chunk_id = f"{self.doc_id}_chunk"
        
        # Ensure metadata.chunk_id is set
        if not self.metadata.chunk_id:
            self.metadata.chunk_id = self.chunk_id
    
    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of the chunk.
        """
        result = self.dict(exclude={"embedding"})
        
        # Convert embedding to list if it's a numpy array
        if self.embedding is not None:
            if isinstance(self.embedding, np.ndarray):
                result["embedding"] = self.embedding.tolist()
            else:
                result["embedding"] = self.embedding
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Chunk":
        """Create a chunk from a dictionary.
        
        Args:
            data: Dictionary representation of a chunk.
            
        Returns:
            Chunk instance.
        """
        # Create a copy to avoid modifying the input
        chunk_data = data.copy()
        
        # Extract metadata if it's nested
        if "metadata" in chunk_data and isinstance(chunk_data["metadata"], dict):
            metadata = ChunkMetadata(**chunk_data["metadata"])
        else:
            # Try to extract metadata fields from the chunk data
            metadata_fields = {
                field: chunk_data.pop(field)
                for field in ChunkMetadata.__annotations__.keys()
                if field in chunk_data
            }
            metadata = ChunkMetadata(**metadata_fields)
        
        # Create the chunk
        return cls(
            doc_id=chunk_data.get("doc_id", ""),
            chunk_id=chunk_data.get("chunk_id"),
            text=chunk_data.get("text", ""),
            metadata=metadata,
            embedding=chunk_data.get("embedding")
        )
