"""
Mock LLM client for testing without API keys.

This simulates LLM behavior based on scenario expectations.
Useful for testing the pipeline without incurring API costs.
"""

from typing import List, Dict, Any, Optional
from .base import BaseLLMClient, LLMResponse


class MockLLM(BaseLLMClient):
    """
    Mock LLM that simulates tool-calling behavior.

    This is useful for:
    - Testing the pipeline without API costs
    - Verifying sandbox behavior
    - Development and debugging
    """

    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Simulate LLM response.

        For now, this uses simple heuristics:
        - If tools are available and query mentions search, call search_documents
        - If query mentions email, call send_email
        - Otherwise, return text response
        """
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        user_message_lower = user_message.lower()

        # Simple heuristics for tool calling
        tool_calls = []

        if tools:
            available_tool_names = [
                t.get("function", {}).get("name", "") for t in tools
            ]

            # If query mentions search, documents, or policy
            if any(
                keyword in user_message_lower
                for keyword in ["search", "document", "policy", "summarize", "find"]
            ):
                if "search_documents" in available_tool_names:
                    tool_calls.append({
                        "id": "call_001",
                        "type": "function",
                        "function": {
                            "name": "search_documents",
                            "arguments": {"query": user_message},
                        },
                    })

            # If query mentions email
            if "email" in user_message_lower or "send" in user_message_lower:
                if "send_email" in available_tool_names:
                    tool_calls.append({
                        "id": "call_002",
                        "type": "function",
                        "function": {
                            "name": "send_email",
                            "arguments": {
                                "to": "user@example.com",
                                "subject": "Test",
                                "body": "Test email",
                            },
                        },
                    })

            # If query mentions delete
            if "delete" in user_message_lower:
                if "delete_file" in available_tool_names:
                    tool_calls.append({
                        "id": "call_003",
                        "type": "function",
                        "function": {
                            "name": "delete_file",
                            "arguments": {"path": "/tmp/test.txt"},
                        },
                    })

        if tool_calls:
            return LLMResponse(
                content=None,
                tool_calls=tool_calls,
                finish_reason="tool_calls",
            )
        else:
            return LLMResponse(
                content=f"I understand your request: {user_message}",
                tool_calls=[],
                finish_reason="stop",
            )

    def get_model_name(self) -> str:
        return self.model_name