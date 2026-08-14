"""
Logger for tool invocations in the safety sandbox.

Records every tool call attempt for later analysis.
This is critical for calculating safety metrics.
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class ToolCallLog:
    """Record of a single tool call attempt."""
    timestamp: float
    tool_name: str
    arguments: Dict[str, Any]
    policy_decision: str        # "allowed", "blocked", "needs_confirmation"
    policy_reason: Optional[str]
    executed: bool              # Did the tool actually run?
    result_summary: Optional[str]
    scenario_id: Optional[str]  # Which test scenario this belongs to


class ToolCallLogger:
    """Logger that records tool invocations to memory and file."""

    def __init__(self, output_path: Optional[Path] = None):
        self.logs: List[ToolCallLog] = []
        self.output_path = output_path

    def log(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        policy_decision: str,
        policy_reason: Optional[str] = None,
        executed: bool = False,
        result_summary: Optional[str] = None,
        scenario_id: Optional[str] = None,
    ) -> None:
        """Record a tool call attempt."""
        log_entry = ToolCallLog(
            timestamp=time.time(),
            tool_name=tool_name,
            arguments=arguments,
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            executed=executed,
            result_summary=result_summary,
            scenario_id=scenario_id,
        )
        self.logs.append(log_entry)

    def save_to_file(self) -> None:
        """Save all logs to JSON file."""
        if not self.output_path:
            return

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(log) for log in self.logs], f, indent=2)

    def get_logs_by_decision(self, decision: str) -> List[ToolCallLog]:
        """Filter logs by policy decision."""
        return [log for log in self.logs if log.policy_decision == decision]

    def get_unauthorized_attempts(self) -> List[ToolCallLog]:
        """Get all attempts to call forbidden tools."""
        return [
            log for log in self.logs
            if log.policy_decision == "blocked"
        ]

    def summary(self) -> Dict[str, int]:
        """Return summary statistics."""
        summary = {"total": len(self.logs)}
        for log in self.logs:
            summary[log.policy_decision] = summary.get(log.policy_decision, 0) + 1
        return summary