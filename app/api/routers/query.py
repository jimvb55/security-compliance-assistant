"""Query router for the Security Compliance Assistant API."""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.query_service import default_query_service


router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str
    num_results: int = Field(default=settings.DEFAULT_NUM_RESULTS, ge=1, le=20)
    min_score: float = Field(default=settings.DEFAULT_MIN_SCORE, ge=0.0, le=1.0)
    filters: Optional[Dict] = None


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: List[Dict] = []
    citations: Dict[str, Dict] = {}


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the knowledge base.
    
    Args:
        request: The query request containing the query string, number of results, etc.
        
    Returns:
        QueryResponse containing the answer, sources, and citations.
    """
    try:
        # Query the knowledge base
        answer, results, citations = default_query_service.query(
            query=request.query,
            num_results=request.num_results,
            min_score=request.min_score,
            filters=request.filters
        )
        
        return QueryResponse(
            answer=answer,
            sources=results,
            citations=citations
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
