"""Base LLM provider for the Security Compliance Assistant."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: User prompt or question.
            system_prompt: System prompt to guide the LLM.
            temperature: Temperature for sampling (higher = more random).
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            Generated text.
        """
        pass
    
    @abstractmethod
    def generate_with_sources(
        self,
        prompt: str,
        context: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Generate text with source citations.
        
        Args:
            prompt: User prompt or question.
            context: List of context items with text and metadata.
            system_prompt: System prompt to guide the LLM.
            temperature: Temperature for sampling (higher = more random).
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            Dictionary with 'answer', 'sources', and 'citations' fields.
        """
        pass
