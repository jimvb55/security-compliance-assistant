"""LLM provider factory for the Security Compliance Assistant."""
from typing import Dict, Optional

from app.config import settings
from app.services.providers.base import BaseLLMProvider
from app.services.providers.mock_provider import MockLLMProvider


def create_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """Create an LLM provider based on configuration.
    
    Args:
        provider_type: Type of LLM provider. If None, use the provider specified in settings.
            
    Returns:
        BaseLLMProvider instance.
    """
    provider_type = provider_type or settings.LLM_PROVIDER
    provider_type = provider_type.lower()
    
    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type == "azure_openai":
        # Import lazily to avoid dependency issues
        try:
            from app.services.providers.azure_openai_provider import AzureOpenAIProvider
            return AzureOpenAIProvider()
        except ImportError:
            raise ImportError(
                "Azure OpenAI provider dependencies not installed. "
                "Please install with 'pip install openai azure-identity'."
            )
    elif provider_type == "anthropic":
        # Import lazily to avoid dependency issues
        try:
            from app.services.providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider()
        except ImportError:
            raise ImportError(
                "Anthropic provider dependencies not installed. "
                "Please install with 'pip install anthropic'."
            )
    else:
        raise ValueError(f"Unsupported LLM provider type: {provider_type}")
