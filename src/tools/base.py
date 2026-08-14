"""
Base class for all tools in the safety evaluation sandbox.

Each tool represents an action that an LLM agent can perform.
Tools have:
- name: unique identifier
- description: what the tool does (for the LLM)
- parameters: JSON schema of expected arguments
- risk_level: safety classification (safe, confirmation_required, forbidden)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class RiskLevel(str, Enum):
    """Safety risk classification for tools."""
    SAFE = "safe"                           # Always allowed
    CONFIRMATION_REQUIRED = "confirmation"  # Needs user confirmation
    FORBIDDEN = "forbidden"                 # Never allowed
    CRITICAL = "critical"                   # High-impact forbidden


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.parameters: Dict[str, Any] = {}
        self.risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters. Must be implemented by subclasses."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self) -> str:
        return f"<Tool: {self.name} (risk={self.risk_level.value})>"