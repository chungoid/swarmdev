"""
Utility module for LLM providers in the SwarmDev platform.
This module provides the interface and implementations for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class LLMProviderInterface(ABC):
    """
    Interface for LLM providers.
    
    This abstract class defines the standard interface that all LLM providers
    must implement to be compatible with the SwarmDev platform.
    """
    
    def __init__(self):
        """Initialize the LLM provider with usage tracking."""
        self.usage_metrics = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0
        }
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated text
        """
        pass
    
    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response based on a conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated response
        """
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of input texts
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of this LLM provider.
        
        Returns:
            Dict[str, bool]: Dictionary of capability names and availability
        """
        pass
    
    def get_usage_metrics(self) -> Dict:
        """
        Get usage metrics for this LLM provider.
        
        Returns:
            Dict: Usage metrics including token counts and costs
        """
        return self.usage_metrics.copy()
    
    def _update_usage_metrics(self, input_tokens: int, output_tokens: int, cost: float = 0.0):
        """
        Update usage metrics after an API call.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            cost: Cost of the API call
        """
        self.usage_metrics["total_calls"] += 1
        self.usage_metrics["total_input_tokens"] += input_tokens
        self.usage_metrics["total_output_tokens"] += output_tokens
        self.usage_metrics["total_cost"] += cost


class OpenAIProvider(LLMProviderInterface):
    """
    OpenAI LLM provider implementation.
    
    This class implements the LLMProviderInterface for OpenAI models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", **kwargs):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model name
            **kwargs: Additional configuration parameters
        """
        super().__init__()  # Initialize usage tracking
        
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with 'pip install openai'.")
        
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.config = kwargs
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI's completion API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated text
        """
        params = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        response = self.client.chat.completions.create(
            messages=messages,
            **params
        )
        
        # Track token usage
        if hasattr(response, 'usage'):
            self._update_usage_metrics(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )
        
        return response.choices[0].message.content
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response based on a conversation history using OpenAI's chat API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated response
        """
        params = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        }
        
        # Convert messages to OpenAI format if needed
        openai_messages = []
        for msg in messages:
            role = msg["role"]
            # Map roles to OpenAI's expected format
            if role == "agent":
                role = "assistant"
            openai_messages.append({"role": role, "content": msg["content"]})
        
        response = self.client.chat.completions.create(
            messages=openai_messages,
            **params
        )
        
        # Track token usage
        if hasattr(response, 'usage'):
            self._update_usage_metrics(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )
        
        return response.choices[0].message.content
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI's embedding API.
        
        Args:
            texts: List of input texts
            **kwargs: Additional parameters
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        model = kwargs.get("embedding_model", "text-embedding-3-small")
        
        # Process in batches if needed
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                input=text,
                model=model
            )
            embeddings.append(response.data[0].embedding)
        
        return embeddings
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of the OpenAI provider.
        
        Returns:
            Dict[str, bool]: Dictionary of capability names and availability
        """
        # Capabilities depend on the model
        if self.model.startswith("gpt-4"):
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": True,
                "function_calling": True,
                "vision": "vision" in self.model or self.model == "gpt-4o",
                "long_context": "32k" in self.model or self.model == "gpt-4o",
            }
        else:
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": True,
                "function_calling": True,
                "vision": False,
                "long_context": "16k" in self.model,
            }


class AnthropicProvider(LLMProviderInterface):
    """
    Anthropic LLM provider implementation.
    
    This class implements the LLMProviderInterface for Anthropic Claude models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229", **kwargs):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key (defaults to environment variable)
            model: Model name
            **kwargs: Additional configuration parameters
        """
        super().__init__()  # Initialize usage tracking
        
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with 'pip install anthropic'.")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.config = kwargs
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Anthropic's completion API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated text
        """
        params = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        response = self.client.messages.create(
            messages=[{"role": "user", "content": prompt}],
            **params
        )
        
        return response.content[0].text
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response based on a conversation history using Anthropic's chat API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated response
        """
        params = {
            "model": kwargs.get("model", self.model),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            role = msg["role"]
            # Map roles to Anthropic's expected format
            if role == "agent":
                role = "assistant"
            anthropic_messages.append({"role": role, "content": msg["content"]})
        
        response = self.client.messages.create(
            messages=anthropic_messages,
            **params
        )
        
        return response.content[0].text
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Note: Anthropic doesn't provide a native embedding API, so this implementation
        uses a third-party embedding model.
        
        Args:
            texts: List of input texts
            **kwargs: Additional parameters
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("SentenceTransformer package not installed. Install with 'pip install sentence-transformers'.")
        
        model_name = kwargs.get("embedding_model", "all-MiniLM-L6-v2")
        model = SentenceTransformer(model_name)
        
        embeddings = model.encode(texts).tolist()
        return embeddings
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of the Anthropic provider.
        
        Returns:
            Dict[str, bool]: Dictionary of capability names and availability
        """
        # Capabilities depend on the model
        if "opus" in self.model:
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": False,  # No native embedding API
                "function_calling": True,
                "vision": True,
                "long_context": True,
            }
        elif "sonnet" in self.model:
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": False,  # No native embedding API
                "function_calling": True,
                "vision": True,
                "long_context": True,
            }
        else:  # haiku
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": False,  # No native embedding API
                "function_calling": True,
                "vision": True,
                "long_context": False,
            }


class GoogleProvider(LLMProviderInterface):
    """
    Google Gemini LLM provider implementation.
    
    This class implements the LLMProviderInterface for Google Gemini models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-001", **kwargs):
        """
        Initialize the Google provider.
        
        Args:
            api_key: Google API key (defaults to environment variable)
            model: Model name
            **kwargs: Additional configuration parameters
        """
        super().__init__()  # Initialize usage tracking
        
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google GenerativeAI package not installed. Install with 'pip install google-generativeai'.")
        
        self.model = model
        if api_key:
            genai.configure(api_key=api_key)
        
        # Initialize the model
        self.client = genai.GenerativeModel(self.model)
        self.config = kwargs
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Google's Gemini API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated text
        """
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
            "top_k": kwargs.get("top_k", 32),
        }
        
        response = self.client.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response based on a conversation history using Google's chat API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated response
        """
        generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0),
            "top_k": kwargs.get("top_k", 32),
        }
        
        # Convert messages to Google format
        google_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Map roles to Google's expected format
            if role == "agent":
                role = "model"
            elif role == "user":
                role = "user"
            
            google_messages.append({"role": role, "parts": [content]})
        
        # If we have chat history, use chat session
        if len(google_messages) > 1:
            chat = self.client.start_chat(history=google_messages[:-1])
            response = chat.send_message(
                google_messages[-1]["parts"][0],
                generation_config=generation_config
            )
        else:
            # Single message, use direct generation
            response = self.client.generate_content(
                google_messages[0]["parts"][0],
                generation_config=generation_config
            )
        
        return response.text
    
    def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Google's embedding API.
        
        Args:
            texts: List of input texts
            **kwargs: Additional parameters
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            import google.generativeai as genai
            
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model="models/text-embedding-004",  # Google's latest embedding model
                    content=text
                )
                embeddings.append(result['embedding'])
            
            return embeddings
        except Exception as e:
            # Fallback to sentence transformers if native embeddings fail
            try:
                from sentence_transformers import SentenceTransformer
                model_name = kwargs.get("embedding_model", "all-MiniLM-L6-v2")
                model = SentenceTransformer(model_name)
                embeddings = model.encode(texts).tolist()
                return embeddings
            except ImportError:
                raise ImportError("Neither Google embeddings nor SentenceTransformer available. Install with 'pip install sentence-transformers'.")
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of the Google provider.
        
        Returns:
            Dict[str, bool]: Dictionary of capability names and availability
        """
        # Capabilities depend on the model
        if "gemini-2" in self.model or "gemini-1.5" in self.model:
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": True,
                "function_calling": True,
                "vision": True,  # Gemini supports multimodal
                "long_context": True,  # Up to 2M tokens for some models
                "code_execution": "gemini-2" in self.model,  # Code execution available in Gemini 2.0
            }
        else:
            return {
                "text_generation": True,
                "chat": True,
                "embeddings": True,
                "function_calling": False,
                "vision": False,
                "long_context": False,
            }


class ProviderRegistry:
    """
    Registry for LLM providers.
    
    This class manages the registration and discovery of LLM providers.
    """
    
    def __init__(self):
        """Initialize the provider registry."""
        self.providers = {}
        self.default_provider = None
    
    def register_provider(self, provider_id: str, provider: LLMProviderInterface, is_default: bool = False):
        """
        Register an LLM provider.
        
        Args:
            provider_id: Unique identifier for the provider
            provider: Provider instance
            is_default: Whether this provider should be the default
        """
        self.providers[provider_id] = provider
        if is_default or self.default_provider is None:
            self.default_provider = provider_id
    
    def get_provider(self, provider_id: Optional[str] = None) -> LLMProviderInterface:
        """
        Get a provider by ID or the default provider.
        
        Args:
            provider_id: Provider ID (or None for default)
            
        Returns:
            LLMProviderInterface: Provider instance
            
        Raises:
            ValueError: If the provider is not found
        """
        if provider_id is None:
            provider_id = self.default_provider
        
        if provider_id not in self.providers:
            raise ValueError(f"Provider '{provider_id}' not found")
        
        return self.providers[provider_id]
    
    def get_provider_by_capability(self, capability: str) -> Optional[LLMProviderInterface]:
        """
        Get the first provider that supports a specific capability.
        
        Args:
            capability: Capability name
            
        Returns:
            Optional[LLMProviderInterface]: Provider instance or None if not found
        """
        for provider in self.providers.values():
            capabilities = provider.get_capabilities()
            if capability in capabilities and capabilities[capability]:
                return provider
        
        return None
    
    def discover_providers(self, plugins_dir: Optional[str] = None):
        """
        Discover and register providers from plugins directory.
        
        Args:
            plugins_dir: Directory containing provider plugins
        """
        # This is a placeholder implementation
        # In a real implementation, this would scan the plugins directory
        # and dynamically load provider implementations
        
        # Register built-in providers
        try:
            import os
            
            # Register OpenAI provider if API key is available
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                self.register_provider("openai", OpenAIProvider(api_key=openai_api_key), is_default=True)
            
            # Register Anthropic provider if API key is available
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                self.register_provider("anthropic", AnthropicProvider(api_key=anthropic_api_key))
            
            # Register Google provider if API key is available
            google_api_key = os.environ.get("GOOGLE_API_KEY")
            if google_api_key:
                self.register_provider("google", GoogleProvider(api_key=google_api_key))
        except Exception as e:
            print(f"Error discovering providers: {e}")
