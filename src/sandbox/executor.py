"""
Sandbox executor for tools with policy enforcement.

The sandbox is the single entry point for tool execution.
It checks policies, logs attempts, and executes only allowed tools.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from ..tools.base import BaseTool, ToolResult, RiskLevel
from .logger import ToolCallLogger
from .policy_loader import PolicyConfig, load_policy, get_default_policy_path


class ConfigurablePolicy:
    """Policy that reads rules from configuration."""

    def __init__(self, config: PolicyConfig):
        self.config = config

    def check(self, tool: BaseTool, confirmed: bool = False) -> tuple[str, Optional[str]]:
        """
        Check if tool execution is allowed based on policy configuration.

        Returns:
            (decision, reason) where decision is one of:
            "allowed", "blocked", "needs_confirmation"
        """
        # Check tool-specific override first
        override = self.config.get_tool_override(tool.name)
        if override:
            action = override.get("action", "block")
            reason = override.get("reason", "Tool-specific override")

            if action == "allow":
                return "allowed", None
            elif action == "require_confirmation":
                if confirmed:
                    return "allowed", None
                return "needs_confirmation", reason
            else:  # block
                return "blocked", reason

        # Check risk level action
        action = self.config.get_action_for_risk_level(tool.risk_level)

        if action == "allow":
            return "allowed", None

        elif action == "require_confirmation":
            if confirmed:
                return "allowed", None
            reason = f"Tool '{tool.name}' requires user confirmation"
            return "needs_confirmation", reason

        else:  # block
            reason = f"Tool '{tool.name}' is forbidden (risk_level={tool.risk_level.value})"
            return "blocked", reason


class Sandbox:
    """
    Isolated environment for tool execution with policy enforcement.

    All tool calls must go through the sandbox. This is the only place
    where tools are actually executed.
    """

    def __init__(
        self,
        tools: List[BaseTool],
        logger: ToolCallLogger,
        policy_config: Optional[PolicyConfig] = None,
    ):
        self.tools = {tool.name: tool for tool in tools}
        self.logger = logger

        # Load policy from config or use default
        if policy_config is None:
            policy_path = get_default_policy_path()
            policy_config = load_policy(policy_path)

        self.policy = ConfigurablePolicy(policy_config)
        self.policy_config = policy_config

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