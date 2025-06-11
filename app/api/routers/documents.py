"""Documents router for the Security Compliance Assistant API."""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.vector_store import create_vector_store


router = APIRouter()


class DocumentInfo(BaseModel):
    """Information about a document in the knowledge base."""
    doc_id: str
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    chunk_count: int
    modified_date: Optional[str] = None


@router.get("", response_model=List[DocumentInfo])
async def list_documents(
    index_name: str = Query("default", description="Index name"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """List all documents in the knowledge base.
    
    Args:
        index_name: Name of the index to query.
        tag: Optional tag to filter by.
        category: Optional category to filter by.
        
    Returns:
        List of document information.
    """
    try:
        # Create vector store
        vector_store = create_vector_store(index_name=index_name)
        
        try:
            # Load vector store
            vector_store.load()
        except FileNotFoundError:
            # No index exists yet, return empty results
            return []
        
        # Get all documents
        documents = {}
        document_chunks = {}
        
        # Process all chunks to gather document information
        for chunk in vector_store.chunks:
            metadata = chunk.metadata
            doc_id = metadata.doc_id
            
            if doc_id not in documents:
                documents[doc_id] = {
                    "doc_id": doc_id,
                    "filename": metadata.filename,
                    "title": metadata.title,
                    "author": metadata.author,
                    "category": metadata.category,
                    "tags": metadata.tags,
                    "modified_date": metadata.modified_date,
                    "chunk_count": 0
                }
            
            # Count chunks for each document
            documents[doc_id]["chunk_count"] += 1
        
        # Apply filters
        filtered_documents = []
        for doc_info in documents.values():
            # Apply tag filter
            if tag and tag not in doc_info["tags"]:
                continue
            
            # Apply category filter
            if category and doc_info["category"] != category:
                continue
            
            filtered_documents.append(DocumentInfo(**doc_info))
        
        return filtered_documents
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving documents: {str(e)}"
        )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(
    doc_id: str,
    index_name: str = Query("default", description="Index name"),
):
    """Get information about a specific document.
    
    Args:
        doc_id: Document ID.
        index_name: Name of the index.
        
    Returns:
        Document information.
    """
    try:
        # Create vector store
        vector_store = create_vector_store(index_name=index_name)
        
        try:
            # Load vector store
            vector_store.load()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Index {index_name} not found"
            )
        
        # Find chunks for the document
        doc_chunks = [chunk for chunk in vector_store.chunks if chunk.doc_id == doc_id]
        
        if not doc_chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document {doc_id} not found"
            )
        
        # Get metadata from the first chunk
        metadata = doc_chunks[0].metadata
        
        # Create document info
        doc_info = DocumentInfo(
            doc_id=doc_id,
            filename=metadata.filename,
            title=metadata.title,
            author=metadata.author,
            category=metadata.category,
            tags=metadata.tags,
            chunk_count=len(doc_chunks),
            modified_date=metadata.modified_date
        )
        
        return doc_info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    index_name: str = Query("default", description="Index name"),
):
    """Delete a document from the knowledge base.
    
    Args:
        doc_id: Document ID.
        index_name: Name of the index.
        
    Returns:
        Success message.
    """
    try:
        # Create vector store
        vector_store = create_vector_store(index_name=index_name)
        
        try:
            # Load vector store
            vector_store.load()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Index {index_name} not found"
            )
        
        # Find chunks for the document
        doc_chunks = [chunk for chunk in vector_store.chunks if chunk.doc_id == doc_id]
        
        if not doc_chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document {doc_id} not found"
            )
        
        # Remove chunks for the document
        vector_store.delete_chunks(doc_id)
        
        # Save vector store
        vector_store.save()
        
        return {"success": True, "message": f"Document {doc_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )
