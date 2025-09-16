"""
LLM Client for Groq
Simple client using OpenAI-compatible API
"""

import os
from openai import OpenAI


def _make_client():
    """Create OpenAI client instance using Groq"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is required")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    ), os.getenv("LLM_MODEL", "llama-3.1-8b-instruct")


def chat(messages, temperature=0.2):
    """
    Simple chat completion using configured provider

    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        Generated response text
    """
    client, model = _make_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages
    )
    return resp.choices[0].message.content


def ask(question, system_prompt=None, temperature=0.2):
    """
    Convenience function for simple Q&A

    Args:
        question: User question
        system_prompt: Optional system prompt
        temperature: Sampling temperature

    Returns:
        Generated response text
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    return chat(messages, temperature)


# Legacy compatibility - keep existing class structure for backward compatibility
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7

class LLMClient:
    """Groq LLM client (legacy compatibility)"""

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = self._load_config_from_env()
        self.config = config
        self.client = self._initialize_client()

    def _load_config_from_env(self) -> LLMConfig:
        """Load configuration from environment variables"""
        # Use the same logic as _make_client for consistency
        client, model = _make_client()

        return LLMConfig(
            provider='groq',
            model=model,
            api_key=client.api_key,
            base_url=client.base_url
        )

    def _initialize_client(self) -> OpenAI:
        """Initialize the OpenAI client with provider-specific configuration"""
        client, _ = _make_client()
        return client

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response using the configured LLM provider

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Generated response text
        """
        try:
            # Use the simplified chat function
            return chat(messages, temperature or self.config.temperature)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embeddings (if supported by provider)
        Note: Not all providers support embeddings
        """
        if self.config.provider == 'openai':
            try:
                response = self.client.embeddings.create(
                    model=model or "text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                raise
        else:
            # For other providers, we'll use sentence-transformers
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            return embedding_model.encode(text).tolist()

    def chat_completion(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Simple chat completion with optional system message and context

        Args:
            user_message: User's input message
            system_message: Optional system prompt
            context: Optional context information

        Returns:
            LLM response
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        if context:
            user_message = f"Context: {context}\n\nQuestion: {user_message}"

        messages.append({"role": "user", "content": user_message})

        return self.generate_response(messages)

# Convenience function to get a configured client
def get_llm_client() -> LLMClient:
    """Get a configured LLM client instance"""
    return LLMClient()

# Example usage and testing
if __name__ == "__main__":
    print("Groq LLM Client Test")
    print("=" * 40)

    # Show current configuration
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instruct")
    print(f"Provider: Groq (groq.com)")
    print(f"Model: {model}")

    try:
        # Test 1: Simplified chat function
        print("\n1. Testing simplified chat() function...")
        messages = [
            {"role": "system", "content": "You are a helpful nutrition expert."},
            {"role": "user", "content": "What are the health benefits of eating organic vegetables?"}
        ]
        response = chat(messages, temperature=0.2)
        print("✓ Chat Response:", response[:100] + "..." if len(response) > 100 else response)

        # Test 2: Convenience ask function
        print("\n2. Testing convenience ask() function...")
        response2 = ask(
            "Tell me about organic food benefits.",
            system_prompt="You are a helpful nutrition expert.",
            temperature=0.2
        )
        print("✓ Ask Response:", response2[:100] + "..." if len(response2) > 100 else response2)

        # Test 3: Legacy class for backward compatibility
        print("\n3. Testing legacy LLMClient class...")
        client = get_llm_client()
        response3 = client.chat_completion(
            user_message="What makes food organic?",
            system_message="You are a helpful nutrition expert."
        )
        print("✓ Legacy Response:", response3[:100] + "..." if len(response3) > 100 else response3)

        print("\n✅ All tests passed! Groq LLM client is working correctly.")

    except RuntimeError as e:
        if "GROQ_API_KEY" in str(e):
            print(f"\n❌ Configuration Error: {e}")
            print("\nTo fix this, set your Groq API key:")
            print("export GROQ_API_KEY='your-groq-api-key'")
        else:
            print(f"\n❌ Error: {e}")

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("This might be a network issue or API problem.")