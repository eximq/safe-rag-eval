"""
Sandbox executor for tools with policy enforcement.

The sandbox is the single entry point for tool execution.
It checks policies, logs attempts, and executes only allowed tools.
"""

from typing import Dict, Any, Optional, List
from ..tools.base import BaseTool, ToolResult, RiskLevel
from .logger import ToolCallLogger


class ToolPolicy:
    """Policy configuration for tool execution."""

    def __init__(self):
        # Risk levels that are always allowed
        self.allowed_levels = {RiskLevel.SAFE}
        # Risk levels that require explicit confirmation
        self.confirmation_levels = {RiskLevel.CONFIRMATION_REQUIRED}
        # Risk levels that are never allowed
        self.forbidden_levels = {RiskLevel.FORBIDDEN, RiskLevel.CRITICAL}

    def check(self, tool: BaseTool, confirmed: bool = False) -> tuple[str, Optional[str]]:
        """
        Check if tool execution is allowed.

        Returns:
            (decision, reason) where decision is one of:
            "allowed", "blocked", "needs_confirmation"
        """
        if tool.risk_level in self.allowed_levels:
            return "allowed", None

        if tool.risk_level in self.forbidden_levels:
            reason = f"Tool '{tool.name}' is forbidden (risk_level={tool.risk_level.value})"
            return "blocked", reason

        if tool.risk_level in self.confirmation_levels:
            if confirmed:
                return "allowed", None
            reason = f"Tool '{tool.name}' requires user confirmation"
            return "needs_confirmation", reason

        return "blocked", f"Unknown risk level: {tool.risk_level}"


class Sandbox:
    """
    Isolated environment for tool execution with policy enforcement.

    All tool calls must go through the sandbox. This is the only place
    where tools are actually executed.
    """

    def __init__(self, tools: List[BaseTool], logger: ToolCallLogger, policy: Optional[ToolPolicy] = None):
        self.tools = {tool.name: tool for tool in tools}
        self.logger = logger
        self.policy = policy or ToolPolicy()

    def call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        confirmed: bool = False,
        scenario_id: Optional[str] = None,
    ) -> Optional[ToolResult]:
        """
        Execute a tool if policy allows.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            confirmed: Whether user has confirmed the action
            scenario_id: ID of the test scenario (for logging)

        Returns:
            ToolResult if executed, None if blocked
        """
        # Check if tool exists
        if tool_name not in self.tools:
            self.logger.log(
                tool_name=tool_name,
                arguments=arguments,
                policy_decision="blocked",
                policy_reason=f"Unknown tool: {tool_name}",
                executed=False,
                scenario_id=scenario_id,
            )
            return None

        tool = self.tools[tool_name]

        # Check policy
        decision, reason = self.policy.check(tool, confirmed=confirmed)

        if decision == "blocked":
            self.logger.log(
                tool_name=tool_name,
                arguments=arguments,
                policy_decision="blocked",
                policy_reason=reason,
                executed=False,
                scenario_id=scenario_id,
            )
            return None

        if decision == "needs_confirmation":
            self.logger.log(
                tool_name=tool_name,
                arguments=arguments,
                policy_decision="needs_confirmation",
                policy_reason=reason,
                executed=False,
                scenario_id=scenario_id,
            )
            return None

        # Execute the tool
        try:
            result = tool.execute(**arguments)
            self.logger.log(
                tool_name=tool_name,
                arguments=arguments,
                policy_decision="allowed",
                policy_reason=None,
                executed=True,
                result_summary=str(result.output)[:200],
                scenario_id=scenario_id,
            )
            return result
        except Exception as e:
            self.logger.log(
                tool_name=tool_name,
                arguments=arguments,
                policy_decision="error",
                policy_reason=str(e),
                executed=False,
                scenario_id=scenario_id,
            )
            return None