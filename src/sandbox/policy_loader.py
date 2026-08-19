"""
Policy loader that reads security policies from YAML configuration files.

This allows policies to be changed without modifying code.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from ..tools.base import RiskLevel


class PolicyConfig:
    """Parsed policy configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.policy_name: str = config.get("policy_name", "unnamed")
        self.version: str = config.get("version", "0.0")
        self.description: str = config.get("description", "")
        self.risk_levels: Dict[str, Dict[str, str]] = config.get("risk_levels", {})
        self.tool_overrides: Dict[str, Dict[str, str]] = config.get("tool_overrides", {})
        self.settings: Dict[str, Any] = config.get("settings", {})

    def get_action_for_risk_level(self, risk_level: RiskLevel) -> str:
        """
        Get the action to take for a given risk level.

        Returns one of: "allow", "require_confirmation", "block"
        """
        level_config = self.risk_levels.get(risk_level.value, {})
        return level_config.get("action", "block")  # Default to block for safety

    def get_tool_override(self, tool_name: str) -> Optional[Dict[str, str]]:
        """Get override configuration for a specific tool."""
        return self.tool_overrides.get(tool_name)

    def __repr__(self) -> str:
        return f"<PolicyConfig: {self.policy_name} v{self.version}>"


def load_policy(policy_path: Path) -> PolicyConfig:
    """
    Load policy from YAML file.

    Args:
        policy_path: Path to the YAML policy file

    Returns:
        PolicyConfig object

    Raises:
        FileNotFoundError: If policy file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")

    with open(policy_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return PolicyConfig(config)


def get_default_policy_path() -> Path:
    """Get path to the default policy file."""
    return Path(__file__).parent.parent.parent / "configs" / "policies" / "default_policy.yaml"