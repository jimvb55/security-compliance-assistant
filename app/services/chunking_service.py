"""Chunking service for the Security Compliance Assistant."""
import re
from typing import Dict, List, Optional, Union, Any

from app.config import settings
from app.models.chunk import Chunk, ChunkMetadata
from app.models.document import Document, DocumentMetadata


class ChunkingService:
    """Service for chunking documents into smaller pieces."""
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """Initialize the chunking service.
        
        Args:
            chunk_size: Size of each chunk in words.
                If None, use the chunk size specified in settings.
            chunk_overlap: Overlap between chunks in words.
                If None, use the chunk overlap specified in settings.
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a document into smaller pieces.
        
        Args:
            document: Document to chunk.
            
        Returns:
            List of chunks.
        """
        # Split text into words
        words = re.findall(r'\S+|\n', document.text)
        
        # Calculate chunk parameters
        chunk_size_words = self.chunk_size
        chunk_overlap_words = self.chunk_overlap
        
        # Handle small documents
        if len(words) <= chunk_size_words:
            return [self._create_chunk(document, words, 0, len(words))]
        
        # Chunk the document
        chunks = []
        start = 0
        
        while start < len(words):
            # Calculate end of chunk
            end = min(start + chunk_size_words, len(words))
            
            # Create chunk
            chunk = self._create_chunk(document, words, start, end)
            chunks.append(chunk)
            
            # Move to next chunk
            start += chunk_size_words - chunk_overlap_words
            
            # Break if we've reached the end
            if start >= len(words):
                break
        
        # Store chunk information in the document
        document.chunks = [
            {
                "chunk_id": chunk.chunk_id,
                "start_idx": chunk.metadata.start_idx,
                "end_idx": chunk.metadata.end_idx,
            }
            for chunk in chunks
        ]
        
        return chunks
    
    def _create_chunk(
        self,
        document: Document,
        words: List[str],
        start_idx: int,
        end_idx: int
    ) -> Chunk:
        """Create a chunk from a document.
        
        Args:
            document: Source document.
            words: List of words from the document.
            start_idx: Start index in the words list.
            end_idx: End index in the words list.
            
        Returns:
            Chunk instance.
        """
        # Join words to create chunk text
        chunk_text = ' '.join(words[start_idx:end_idx])
        
        # Replace multiple spaces with a single space
        chunk_text = re.sub(r'\s+', ' ', chunk_text)
        
        # Create chunk ID
        chunk_id = f"{document.doc_id}_chunk_{start_idx}_{end_idx}"
        
        # Create chunk metadata
        metadata = ChunkMetadata(
            doc_id=document.doc_id,
            chunk_id=chunk_id,
            filename=document.metadata.filename,
            title=document.metadata.title,
            author=document.metadata.author,
            file_path=document.metadata.file_path,
            start_idx=start_idx,
            end_idx=end_idx,
            tags=document.metadata.tags,
            category=document.metadata.category,
            version=document.metadata.version,
            modified_date=document.metadata.modified_date.isoformat() if document.metadata.modified_date else None
        )
        
        # Create chunk
        return Chunk(
            doc_id=document.doc_id,
            chunk_id=chunk_id,
            text=chunk_text,
            metadata=metadata
        )


# Default chunking service
default_chunking_service = ChunkingService()
