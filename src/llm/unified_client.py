"""
Unified LLM client using LiteLLM for multi-provider support.
Supports: OpenAI, Anthropic, Google Gemini, Groq, Qwen (DashScope), 
          Together AI, local models (Ollama)
"""

import os
os.environ["NO_COLOR"] = "1"  # of ANSI color in LiteLLM
os.environ["LITELLM_LOG"] = "ERROR"  # show only error, no INFO
from typing import List, Dict, Any, Optional
from litellm import completion
from litellm.exceptions import AuthenticationError, RateLimitError, APIError
import logging

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """
    Provider-agnostic LLM client using LiteLLM.
    
    Usage:
        client = UnifiedLLMClient(
            provider="anthropic",
            model="claude-sonnet-4-5",
            api_key="your-key"
        )
        response = client.chat(messages=[{"role": "user", "content": "Hello"}])
    """
    
    # Provider name mapping for LiteLLM
    PROVIDER_MAPPING = {
        "openai": "openai",
        "anthropic": "anthropic",
        "gemini": "gemini",
        "groq": "groq",
        "qwen": "qwen",           # Alibaba DashScope
        "together": "together_ai",
        "ollama": "ollama",
        "local": "ollama",  # alias for ollama
    }
    
    # Environment variable names for API keys
    ENV_KEYS = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",  # Alibaba Cloud
        "together": "TOGETHER_API_KEY",
        "ollama": None,  # Ollama doesn't need API key
    }
    
    def __init__(
        self,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout: int = 60
    ):
        """
        Initialize unified LLM client.
        
        Args:
            provider: Provider name (openai, anthropic, gemini, groq, qwen,
                together, ollama, or "local" as alias for ollama)
            model: Exact model name as listed by the provider. Check with
                `python scripts/list_models.py <provider>` and copy verbatim
                (e.g., "gpt-4o", "claude-sonnet-4-5", "qwen/qwen3.8-27b")
            api_key: API key (optional, reads from env if not provided)
            base_url: Custom base URL (for local models or custom endpoints)
            temperature: Sampling temperature (default 0.0 for deterministic)
            max_tokens: Max tokens in response
            timeout: Request timeout in seconds
        """

        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Validate provider
        if self.provider not in self.PROVIDER_MAPPING:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: {list(self.PROVIDER_MAPPING.keys())}"
            )
        
        # Build model identifier for LiteLLM
        self.model_id = self._build_model_id()
        
        logger.info(f"Initialized {self.provider} client with model {self.model}")
    
    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        env_var = self.ENV_KEYS.get(self.provider)
        
        if env_var:
            api_key = os.getenv(env_var)
            if not api_key:
                raise ValueError(
                    f"API key not provided and {env_var} not set in environment. "
                    f"Set {env_var} or pass api_key directly."
                )
            return api_key
        return "ollama"  # Dummy key for Ollama
    
    def _build_model_id(self) -> str:
        """Build LiteLLM model identifier.
        
        LiteLLM routes by prefix: provider/exact-model-name.
        OpenAI is the default (no prefix). DashScope (Qwen) has no native
        prefix, so we use OpenAI-compatible mode with custom api_base.
        """
        if self.provider == "openai":
            return self.model  # gpt-4o
        elif self.provider == "anthropic":
            return f"anthropic/{self.model}"  # anthropic/claude-sonnet-4-5
        elif self.provider in ("ollama", "local"):
            return f"ollama/{self.model}"  # ollama/qwen2.5:7b
        elif self.provider == "gemini":
            return f"gemini/{self.model}"  # gemini/gemini-2.0-pro
        elif self.provider == "groq":
            return f"groq/{self.model}"  # groq/qwen/qwen3.8-27b
        elif self.provider == "qwen":
            # No native LiteLLM prefix; use OpenAI-compatible endpoint
            return f"openai/{self.model}"  # + api_base set in chat()
        elif self.provider == "together":
            return f"together_ai/{self.model}"  # together_ai/Qwen/Qwen2.5-72B-Instruct
        else:
            return self.model
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with "role" and "content"
            tools: List of tool definitions (OpenAI function calling format)
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            **kwargs: Additional parameters passed to LiteLLM
        
        Returns:
            Dict with keys:
                - content: str (text response)
                - tool_calls: list of tool calls (if any)
                - usage: dict with token counts
                - raw_response: full LiteLLM response object
        """
        try:
            # Build request parameters
            request_params = {
                "model": self.model_id,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": self.timeout,
                **kwargs
            }
            
            # Add API key if provided
            if self.api_key:
                request_params["api_key"] = self.api_key
            
            # Add base URL if provided (for custom endpoints)
            if self.base_url:
                request_params["api_base"] = self.base_url
            elif self.provider == "qwen":
                # DashScope is OpenAI-compatible but lives at its own endpoint
                request_params["api_base"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                if tool_choice:
                    request_params["tool_choice"] = tool_choice
            
            # Make request
            logger.debug(f"Sending request to {self.provider}/{self.model}")
            response = completion(**request_params)
            
            # Parse response
            return self._parse_response(response)
            
        except AuthenticationError as e:
            logger.error(f"Authentication failed for {self.provider}: {e}")
            raise
        except RateLimitError as e:
            logger.warning(f"Rate limit hit for {self.provider}: {e}")
            raise
        except APIError as e:
            logger.error(f"API error from {self.provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error from {self.provider}: {e}")
            raise
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse LiteLLM response into unified format."""
        choice = response.choices[0]
        message = choice.message
        
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "raw_response": response
        }
        
        # Parse tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                })
        
        return result
    
    def test_connection(self) -> bool:
        """
        Test connection to provider with minimal request.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            self.chat(test_messages, max_tokens=5)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Convenience functions
def create_client_from_config(config: Dict[str, Any]) -> UnifiedLLMClient:
    """
    Create client from configuration dict.
    
    Expected config format:
    {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "api_key": "...",  # optional
        "base_url": "...",  # optional
        "temperature": 0.0,  # optional
        "max_tokens": 2048  # optional
    }
    """
    return UnifiedLLMClient(
        provider=config["provider"],
        model=config["model"],
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
        temperature=config.get("temperature", 0.0),
        max_tokens=config.get("max_tokens", 2048)
    )


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Unified LLM Client - Provider Examples")
    print("=" * 60)
    
    # Example 1: OpenAI
    print("\n1. OpenAI (GPT-4o)")
    print("-" * 60)
    try:
        client_openai = UnifiedLLMClient(
            provider="openai",
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        response = client_openai.chat(
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 2: Anthropic
    print("\n2. Anthropic (Claude Sonnet)")
    print("-" * 60)
    try:
        client_anthropic = UnifiedLLMClient(
            provider="anthropic",
            model="claude-sonnet-4-5",
            api_key=os.getenv("ANTHROPIC_API_KEY", "placeholder-key")
        )
        response = client_anthropic.chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except AuthenticationError:
        print("✓ Client structure works (auth failed as expected with placeholder)")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 3: Groq (Qwen via Groq)
    print("\n3. Groq (Qwen 3.8 27B via Groq)")
    print("-" * 60)
    try:
        client_groq = UnifiedLLMClient(
            provider="groq",
            model="qwen/qwen3.8-27b",
            api_key=os.getenv("GROQ_API_KEY")
        )
        response = client_groq.chat(
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 4: Qwen via DashScope (Alibaba Cloud)
    print("\n4. Qwen via DashScope (Alibaba Cloud)")
    print("-" * 60)
    try:
        client_qwen = UnifiedLLMClient(
            provider="qwen",
            model="qwen-max",  # or qwen-plus, qwen-turbo
            api_key=os.getenv("DASHSCOPE_API_KEY", "placeholder-key")
        )
        response = client_qwen.chat(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except AuthenticationError:
        print("✓ Client structure works (auth failed as expected with placeholder)")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 5: Qwen via Together AI
    print("\n5. Qwen via Together AI")
    print("-" * 60)
    try:
        client_together = UnifiedLLMClient(
            provider="together",
            model="Qwen/Qwen2.5-72B-Instruct",
            api_key=os.getenv("TOGETHER_API_KEY", "placeholder-key")
        )
        response = client_together.chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except AuthenticationError:
        print("✓ Client structure works (auth failed as expected with placeholder)")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 6: Local Qwen via Ollama
    print("\n6. Local Qwen via Ollama")
    print("-" * 60)
    print("Requires: ollama pull qwen2.5:7b")
    try:
        client_ollama = UnifiedLLMClient(
            provider="ollama",
            model="qwen2.5:7b"
        )
        response = client_ollama.chat(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"✓ Response: {response['content']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Supported providers:")
    for provider in UnifiedLLMClient.PROVIDER_MAPPING.keys():
        env_key = UnifiedLLMClient.ENV_KEYS.get(provider)
        env_info = f" (env: {env_key})" if env_key else " (no key needed)"
        print(f"  - {provider}{env_info}")
    print("=" * 60)