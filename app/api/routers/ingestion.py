"""Ingestion router for the Security Compliance Assistant API."""
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings
from app.services.ingestion_service import default_ingestion_service


router = APIRouter()


class IngestionResponse(BaseModel):
    """Response model for ingestion endpoints."""
    success: bool
    message: str
    doc_id: Optional[str] = None
    filename: Optional[str] = None
    num_chunks: Optional[int] = None


@router.post("/file", response_model=IngestionResponse)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    index_name: str = Form("default"),
    tags: Optional[str] = Form(None),
):
    """Ingest a document file.
    
    Args:
        file: The file to ingest.
        index_name: The name of the index to use.
        tags: Comma-separated list of tags to apply to the document.
        
    Returns:
        IngestionResponse with success status and document details.
    """
    # Validate file type
    valid_extensions = [".pdf", ".docx", ".txt", ".md"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(valid_extensions)}"
        )
    
    try:
        # Save file to disk temporarily
        temp_file_path = f"/tmp/{uuid.uuid4()}{file_extension}"
        with open(temp_file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Process tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Ingest file
        document = default_ingestion_service.ingest_file(temp_file_path)
        
        # Add tags to document metadata
        if tag_list:
            document.metadata.tags.extend(tag_list)
            # Re-ingest with updated metadata
            document = default_ingestion_service.ingest_file(
                temp_file_path, 
                metadata=document.metadata,
                doc_id=document.doc_id
            )
        
        # Save the vector store in the background
        background_tasks.add_task(default_ingestion_service.save_vector_store)
        
        # Delete temporary file in the background
        background_tasks.add_task(os.unlink, temp_file_path)
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested document: {file.filename}",
            doc_id=document.doc_id,
            filename=file.filename,
            num_chunks=document.num_chunks
        )
    
    except Exception as e:
        # Clean up temporary file if it exists
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        )


@router.post("/directory", response_model=IngestionResponse)
async def ingest_directory(
    directory_path: str,
    recursive: bool = False,
    file_extensions: Optional[List[str]] = None,
    index_name: str = "default",
):
    """Ingest all documents in a directory.
    
    Args:
        directory_path: Path to the directory to ingest.
        recursive: Whether to recursively search subdirectories.
        file_extensions: List of file extensions to include (e.g., pdf, docx, txt).
        index_name: The name of the index to use.
        
    Returns:
        IngestionResponse with success status and summary information.
    """
    try:
        # Normalize file extensions
        if file_extensions:
            normalized_extensions = [
                ext if ext.startswith(".") else f".{ext}" 
                for ext in file_extensions
            ]
        else:
            normalized_extensions = None
        
        # Ingest documents
        documents = default_ingestion_service.ingest_directory(
            directory_path=directory_path,
            recursive=recursive,
            file_extensions=normalized_extensions
        )
        
        # Save the vector store
        default_ingestion_service.save_vector_store()
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {len(documents)} documents from {directory_path}",
            num_chunks=sum(doc.num_chunks for doc in documents)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting directory: {str(e)}"
        )


@router.post("/clear", response_model=IngestionResponse)
async def clear_index(index_name: str = "default"):
    """Clear the vector store index.
    
    Args:
        index_name: The name of the index to clear.
        
    Returns:
        IngestionResponse with success status.
    """
    try:
        default_ingestion_service.clear_vector_store()
        default_ingestion_service.save_vector_store()
        
        return IngestionResponse(
            success=True,
            message=f"Successfully cleared index: {index_name}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing index: {str(e)}"
        )
