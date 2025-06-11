"""LLM service for the Security Compliance Assistant."""
import os
from typing import Dict, List, Optional, Tuple, Union

from app.config import settings
from app.services.query_service import LLMProvider


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the Azure OpenAI provider.
        
        Args:
            api_key: The API key for Azure OpenAI. If None, use the one from settings.
            endpoint: The endpoint URL for Azure OpenAI. If None, use the one from settings.
            deployment: The deployment name for Azure OpenAI. If None, use the one from settings.
            model: The model name for Azure OpenAI. If None, use the one from settings.
        """
        self.api_key = api_key or settings.LLM_API_KEY
        self.endpoint = endpoint or settings.LLM_ENDPOINT
        self.deployment = deployment or settings.LLM_DEPLOYMENT
        self.model = model or settings.LLM_MODEL
        
        if not all([self.api_key, self.endpoint, self.deployment]):
            raise ValueError(
                "Azure OpenAI provider requires API key, endpoint, and deployment name. "
                "Set them in the environment variables or pass them to the constructor."
            )
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Azure OpenAI.
        
        Args:
            prompt: The prompt to generate text from.
            **kwargs: Additional arguments for the OpenAI API.
            
        Returns:
            The generated text.
            
        Raises:
            Exception: If there's an error calling the API.
        """
        try:
            import openai
            
            # Configure the client
            openai.api_key = self.api_key
            openai.api_base = self.endpoint
            openai.api_type = "azure"
            openai.api_version = "2023-05-15"  # Update to the latest API version
            
            # Set up parameters
            params = {
                "engine": self.deployment,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 800),
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0),
                "stop": kwargs.get("stop", None)
            }
            
            # Call the API
            response = openai.Completion.create(**params)
            
            # Extract and return the text
            return response.choices[0].text.strip()
        
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use the Azure OpenAI provider. "
                "Install it with 'pip install openai'."
            )
        except Exception as e:
            raise Exception(f"Error calling Azure OpenAI API: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the Anthropic provider.
        
        Args:
            api_key: The API key for Anthropic. If None, use the one from settings.
            model: The model name for Anthropic. If None, use the one from settings.
        """
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or "claude-2"
        
        if not self.api_key:
            raise ValueError(
                "Anthropic provider requires API key. "
                "Set it in the environment variables or pass it to the constructor."
            )
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Anthropic Claude.
        
        Args:
            prompt: The prompt to generate text from.
            **kwargs: Additional arguments for the Anthropic API.
            
        Returns:
            The generated text.
            
        Raises:
            Exception: If there's an error calling the API.
        """
        try:
            import anthropic
            
            # Initialize the client
            client = anthropic.Client(api_key=self.api_key)
            
            # Call the API
            response = client.completion(
                prompt=f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
                model=self.model,
                max_tokens_to_sample=kwargs.get("max_tokens", 800),
                temperature=kwargs.get("temperature", 0.1),
                stop_sequences=kwargs.get("stop", [])
            )
            
            # Extract and return the text
            return response.completion.strip()
        
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required to use the Anthropic provider. "
                "Install it with 'pip install anthropic'."
            )
        except Exception as e:
            raise Exception(f"Error calling Anthropic API: {str(e)}")


def create_llm_provider() -> LLMProvider:
    """Create an LLM provider based on configuration.
    
    Returns:
        An LLM provider instance.
    """
    provider_type = settings.LLM_PROVIDER.lower()
    
    try:
        if provider_type == "azure_openai":
            return AzureOpenAIProvider()
        elif provider_type == "anthropic":
            return AnthropicProvider()
        else:
            # Default to mock provider for testing
            from app.services.query_service import MockLLMProvider
            return MockLLMProvider()
    except Exception as e:
        print(f"Error creating LLM provider: {str(e)}")
        print("Falling back to mock provider")
        from app.services.query_service import MockLLMProvider
        return MockLLMProvider()
