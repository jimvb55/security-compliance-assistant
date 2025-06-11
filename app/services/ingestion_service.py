"""Ingestion service for the Security Compliance Assistant."""
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from app.config import settings
from app.models.document import Document, DocumentMetadata
from app.models.chunk import Chunk
from app.services.chunking_service import default_chunking_service
from app.services.embedding_service import default_embedding_service
from app.services.vector_store import create_vector_store


class IngestionService:
    """Service for ingesting documents into the knowledge base."""
    
    def __init__(
        self,
        vector_store=None,
        chunking_service=None,
        embedding_service=None,
    ):
        """Initialize the ingestion service.
        
        Args:
            vector_store: Vector store to use.
            chunking_service: Chunking service to use.
            embedding_service: Embedding service to use.
        """
        self.vector_store = vector_store or create_vector_store()
        self.chunking_service = chunking_service or default_chunking_service
        self.embedding_service = embedding_service or default_embedding_service
        
        # Load vector store if it exists
        try:
            self.vector_store.load()
        except FileNotFoundError:
            # Vector store doesn't exist yet, initialize empty
            pass
    
    def ingest_text(
        self,
        text: str,
        metadata: Optional[DocumentMetadata] = None,
        doc_id: Optional[str] = None
    ) -> Document:
        """Ingest text into the knowledge base.
        
        Args:
            text: Text to ingest.
            metadata: Metadata for the document. If None, create empty metadata.
            doc_id: Document ID. If None, generate a random UUID.
            
        Returns:
            Ingested document.
        """
        # Create document
        document = Document.from_text(
            text=text,
            metadata=metadata or DocumentMetadata(),
            doc_id=doc_id
        )
        
        # Process document
        self._process_document(document)
        
        return document
    
    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[DocumentMetadata] = None,
        doc_id: Optional[str] = None
    ) -> Document:
        """Ingest a file into the knowledge base.
        
        Args:
            file_path: Path to the file to ingest.
            metadata: Metadata for the document. If None, create from file.
            doc_id: Document ID. If None, generate a random UUID.
            
        Returns:
            Ingested document.
        """
        # Read file
        text = self._read_file(file_path)
        
        # Create metadata from file if not provided
        if metadata is None:
            metadata = DocumentMetadata.from_file(file_path)
        
        # Ingest text
        return self.ingest_text(
            text=text,
            metadata=metadata,
            doc_id=doc_id
        )
    
    def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = False,
        file_extensions: Optional[List[str]] = None,
    ) -> List[Document]:
        """Ingest all files in a directory.
        
        Args:
            directory_path: Path to the directory.
            recursive: Whether to recursively traverse subdirectories.
            file_extensions: List of file extensions to include.
                If None, include all files.
            
        Returns:
            List of ingested documents.
        """
        # Get files in directory
        files = self._get_files(directory_path, recursive, file_extensions)
        
        # Ingest files
        documents = []
        for file_path in files:
            try:
                document = self.ingest_file(file_path)
                documents.append(document)
            except Exception as e:
                print(f"Error ingesting file {file_path}: {str(e)}")
        
        return documents
    
    def clear_vector_store(self) -> None:
        """Clear the vector store."""
        self.vector_store.clear()
    
    def save_vector_store(self) -> None:
        """Save the vector store."""
        self.vector_store.save()
    
    def _process_document(self, document: Document) -> None:
        """Process a document and add it to the vector store.
        
        Args:
            document: Document to process.
        """
        # Chunk document
        chunks = self.chunking_service.chunk_document(document)
        
        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_service.get_embeddings(chunk_texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Add chunks to vector store
        self.vector_store.add_chunks(chunks)
    
    def _read_file(self, file_path: str) -> str:
        """Read a file and extract its text.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Extracted text.
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Plain text
        if file_extension in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # PDF
        elif file_extension == ".pdf":
            try:
                from pypdf import PdfReader
                
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                raise ImportError(
                    "PDF support requires pypdf. Install with 'pip install pypdf'."
                )
        
        # DOCX
        elif file_extension == ".docx":
            try:
                import docx
                
                doc = docx.Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            except ImportError:
                raise ImportError(
                    "DOCX support requires python-docx. Install with 'pip install python-docx'."
                )
        
        # Unsupported
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _get_files(
        self,
        directory_path: str,
        recursive: bool = False,
        file_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """Get all files in a directory.
        
        Args:
            directory_path: Path to the directory.
            recursive: Whether to recursively traverse subdirectories.
            file_extensions: List of file extensions to include.
                If None, include all files.
                
        Returns:
            List of file paths.
        """
        files = []
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")
        
        # Walk through directory
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            
            # If directory and recursive, process subdirectory
            if os.path.isdir(entry_path) and recursive:
                sub_files = self._get_files(entry_path, recursive, file_extensions)
                files.extend(sub_files)
            
            # If file, check extension
            elif os.path.isfile(entry_path):
                if file_extensions is None:
                    files.append(entry_path)
                else:
                    ext = os.path.splitext(entry_path)[1].lower()
                    if ext in file_extensions:
                        files.append(entry_path)
        
        return files


# Default ingestion service
default_ingestion_service = IngestionService()
