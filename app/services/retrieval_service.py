"""Retrieval service for the Security Compliance Assistant."""
from typing import Dict, List, Optional, Tuple, Union

from app.config import settings
from app.services.vector_store import VectorStore, create_vector_store


class RetrievalService:
    """Service for retrieving relevant chunks from the vector store."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize the retrieval service.
        
        Args:
            vector_store: The vector store to retrieve from.
        """
        self.vector_store = vector_store or create_vector_store()
    
    def retrieve(
        self,
        query: str,
        num_results: int = settings.DEFAULT_NUM_RESULTS,
        min_score: float = settings.DEFAULT_MIN_SCORE,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Retrieve chunks relevant to the query.
        
        Args:
            query: The query text.
            num_results: Maximum number of results to return.
            min_score: Minimum similarity score (0-1) for results.
            filters: Optional filters for the search.
            
        Returns:
            List of dictionaries containing the search results.
        """
        # Try to load the vector store if it's empty
        if not self.vector_store.chunks:
            try:
                self.vector_store.load()
            except FileNotFoundError:
                # No index exists yet, return empty results
                return []
        
        # Search for relevant chunks
        results = self.vector_store.search(
            query=query,
            num_results=num_results,
            min_score=min_score,
            filters=filters
        )
        
        return results
    
    def generate_citations(self, results: List[Dict]) -> Dict[str, Dict]:
        """Generate citations for search results.
        
        Args:
            results: List of search results from retrieve().
            
        Returns:
            Dictionary mapping citation IDs to citation details.
        """
        citations = {}
        
        for i, result in enumerate(results):
            citation_id = f"[{i+1}]"
            
            metadata = result["metadata"]
            document_title = metadata.get("title") or metadata.get("filename", "Unknown document")
            
            citations[citation_id] = {
                "document": document_title,
                "text": result["text"][:150] + "..." if len(result["text"]) > 150 else result["text"],
                "metadata": {
                    "filename": metadata.get("filename"),
                    "author": metadata.get("author"),
                    "modified_date": metadata.get("modified_date")
                }
            }
        
        return citations


# Default retrieval service instance
default_retrieval_service = RetrievalService()
