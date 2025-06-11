"""Document model for the Security Compliance Assistant."""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    
    filename: str = ""
    file_path: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    modified_date: Optional[datetime] = None
    
    @classmethod
    def from_file(cls, file_path: str) -> "DocumentMetadata":
        """Create metadata from a file path.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            DocumentMetadata instance.
        """
        import os
        from pathlib import Path
        
        path = Path(file_path)
        stat = path.stat()
        
        return cls(
            filename=path.name,
            file_path=str(path),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            # Extract title from filename (remove extension)
            title=path.stem
        )


class Document(BaseModel):
    """Document model representing a document in the knowledge base."""
    
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    metadata: DocumentMetadata
    chunks: List[Dict] = Field(default_factory=list)
    
    @property
    def num_chunks(self) -> int:
        """Get the number of chunks in the document."""
        return len(self.chunks)
    
    @classmethod
    def from_text(
        cls,
        text: str,
        metadata: Optional[DocumentMetadata] = None,
        doc_id: Optional[str] = None
    ) -> "Document":
        """Create a document from text.
        
        Args:
            text: The document text.
            metadata: Document metadata. If None, create empty metadata.
            doc_id: Document ID. If None, generate a random UUID.
            
        Returns:
            Document instance.
        """
        if metadata is None:
            metadata = DocumentMetadata()
        
        return cls(
            doc_id=doc_id or str(uuid.uuid4()),
            text=text,
            metadata=metadata
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self.dict()
