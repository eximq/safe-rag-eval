"""
OpenAI-compatible LLM client.

Works with any provider that has an OpenAI-compatible API:
- OpenAI (api.openai.com/v1)
- Groq (api.groq.com/openai/v1)
- Mistral AI (api.mistral.ai/v1)
- Together AI (api.together.xyz/v1)
- Ollama (localhost:11434/v1)
- And many others
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .base import BaseLLMClient, LLMResponse

# Load environment variables from .env file
load_dotenv()


class OpenAIClient(BaseLLMClient):
    """
    LLM client that works with any OpenAI-compatible API.

    Configuration is done through environment variables:
    - OPENAI_API_KEY or GROQ_API_KEY: API key
    - OPENAI_BASE_URL or GROQ_BASE_URL: API endpoint
    - OPENAI_MODEL or GROQ_MODEL: Model name
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "groq",
    ):
        """
        Initialize the client.

        Args:
            api_key: API key (defaults to env var)
            base_url: API base URL (defaults to env var)
            model: Model name (defaults to env var)
            provider: Provider name for env var lookup ("groq", "openai", etc.)
        """
        self.provider = provider

        # Resolve configuration from args or environment
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.base_url = base_url or os.getenv(f"{provider.upper()}_BASE_URL")
        self.model = model or os.getenv(f"{provider.upper()}_MODEL")

        if not self.api_key:
            raise ValueError(
                f"API key not found. Set {provider.upper()}_API_KEY in .env or pass api_key parameter."
            )

        if not self.base_url:
            raise ValueError(
                f"Base URL not found. Set {provider.upper()}_BASE_URL in .env or pass base_url parameter."
            )

        if not self.model:
            raise ValueError(
                f"Model not found. Set {provider.upper()}_MODEL in .env or pass model parameter."
            )

        # Initialize OpenAI client with custom base_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: Conversation history
            tools: List of available tools (OpenAI format)
            temperature: Sampling temperature (0 = deterministic)
            max_tokens: Maximum response length

        Returns:
            LLMResponse with content and/or tool_calls
        """
        # Build request parameters
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add tools if provided
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"  # Let model decide

        # Make API call
        response = self.client.chat.completions.create(**request_params)

        # Parse response
        message = response.choices[0].message

        # Extract tool calls if present
        tool_calls = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                })

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    def get_model_name(self) -> str:
        return self.model