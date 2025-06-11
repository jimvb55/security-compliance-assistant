"""Query service for the Security Compliance Assistant."""
from typing import Dict, List, Optional, Tuple, Any

from app.config import settings
from app.models.chunk import Chunk
from app.services.embedding_service import default_embedding_service
from app.services.providers.factory import create_llm_provider
from app.services.vector_store import create_vector_store


class QueryService:
    """Service for querying the knowledge base."""
    
    def __init__(
        self,
        vector_store=None,
        embedding_service=None,
        llm_provider=None,
    ):
        """Initialize the query service.
        
        Args:
            vector_store: Vector store to use.
            embedding_service: Embedding service to use.
            llm_provider: LLM provider to use.
        """
        self.vector_store = vector_store or create_vector_store()
        self.embedding_service = embedding_service or default_embedding_service
        self.llm_provider = llm_provider or create_llm_provider()
        
        # Load vector store if it exists
        try:
            self.vector_store.load()
        except FileNotFoundError:
            # Vector store doesn't exist yet, initialize empty
            pass
    
    def query(
        self,
        query: str,
        num_results: int = settings.DEFAULT_NUM_RESULTS,
        min_score: float = settings.DEFAULT_MIN_SCORE,
        filters: Optional[Dict] = None,
    ) -> Tuple[str, List[Dict], Dict]:
        """Query the knowledge base.
        
        Args:
            query: Query string.
            num_results: Number of results to return.
            min_score: Minimum similarity score.
            filters: Metadata filters.
            
        Returns:
            Tuple of (answer, results, citations).
        """
        # Get query embedding
        query_embedding = self.embedding_service.get_embedding(query)
        
        # Search the vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            num_results=num_results,
            min_score=min_score,
            filters=filters
        )
        
        # Prepare context for LLM
        context = []
        for chunk, score in results:
            context.append({
                "text": chunk.text,
                "score": score,
                "metadata": {
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "filename": chunk.metadata.filename,
                    "title": chunk.metadata.title,
                }
            })
        
        # Generate system prompt
        system_prompt = self._generate_system_prompt(query)
        
        # Query the LLM
        response = self.llm_provider.generate_with_sources(
            prompt=query,
            context=context,
            system_prompt=system_prompt,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
        
        # Extract answer, sources, and citations
        answer = response.get("answer", "")
        sources = response.get("sources", [])
        citations = response.get("citations", {})
        
        return answer, sources, citations
    
    def _generate_system_prompt(self, query: str) -> str:
        """Generate a system prompt based on the query.
        
        Args:
            query: Query string.
            
        Returns:
            System prompt.
        """
        # Basic system prompt
        system_prompt = """
        You are a security compliance assistant that helps answer questions about security, compliance, and vendor security questionnaires.
        
        GUIDELINES:
        1. Base your answers only on the provided context. If the context doesn't contain the answer, say "I don't have enough information to answer this question."
        2. Cite your sources using the citation format [n] where n is the number of the source.
        3. Be concise and to the point.
        4. When answering security or compliance questions, provide specific, actionable information.
        5. Focus on accuracy rather than generalization.
        6. For vendor security questionnaires, provide specific responses that can be directly used in the questionnaire.
        
        Now, please answer the following question based on the provided context:
        """.strip()
        
        # Check if the query is related to vendor questionnaires
        questionnaire_keywords = ["vendor", "questionnaire", "assessment", "compliance", "audit"]
        if any(keyword in query.lower() for keyword in questionnaire_keywords):
            system_prompt += """
            
            ADDITIONAL GUIDELINES FOR VENDOR QUESTIONNAIRES:
            1. Provide a specific, direct answer that can be copied into a questionnaire.
            2. Include relevant details about security controls, policies, and procedures.
            3. Cite specific standards or frameworks where applicable (e.g., SOC 2, ISO 27001, GDPR).
            4. If multiple approaches are possible, list them in order of security best practices.
            """.strip()
        
        return system_prompt


# Default query service
default_query_service = QueryService()
