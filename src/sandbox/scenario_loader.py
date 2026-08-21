"""
Scenario loader that reads test scenarios from YAML configuration files.

Scenarios define test cases for safety evaluation.
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ScenarioInput:
    """Input data for a scenario."""
    user_query: str
    documents: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)


@dataclass
class ScenarioExpected:
    """Expected behavior for a scenario."""
    should_call_tools: bool = False
    required_tool_calls: List[str] = field(default_factory=list)
    forbidden_tool_calls: List[str] = field(default_factory=list)
    should_refuse: bool = False
    should_mention_policy: bool = False
    should_ask_confirmation: bool = False
    should_not_cite: List[str] = field(default_factory=list)


@dataclass
class ScenarioEvaluation:
    """Evaluation criteria for a scenario."""
    check_hallucination: bool = False
    check_action_hallucination: bool = False
    check_citations: bool = False
    max_hallucination_score: float = 0.5


@dataclass
class Scenario:
    """Complete test scenario."""
    scenario_id: str
    category: str
    difficulty: str
    description: str
    input: ScenarioInput
    expected: ScenarioExpected
    evaluation: ScenarioEvaluation

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Create Scenario from dictionary."""
        input_data = data.get("input", {})
        expected_data = data.get("expected", {})
        evaluation_data = data.get("evaluation", {})

        return cls(
            scenario_id=data.get("scenario_id", "unknown"),
            category=data.get("category", "unknown"),
            difficulty=data.get("difficulty", "easy"),
            description=data.get("description", ""),
            input=ScenarioInput(
                user_query=input_data.get("user_query", ""),
                documents=input_data.get("documents", []),
                available_tools=input_data.get("available_tools", []),
            ),
            expected=ScenarioExpected(
                should_call_tools=expected_data.get("should_call_tools", False),
                required_tool_calls=expected_data.get("required_tool_calls", []),
                forbidden_tool_calls=expected_data.get("forbidden_tool_calls", []),
                should_refuse=expected_data.get("should_refuse", False),
                should_mention_policy=expected_data.get("should_mention_policy", False),
                should_ask_confirmation=expected_data.get("should_ask_confirmation", False),
                should_not_cite=expected_data.get("should_not_cite", []),
            ),
            evaluation=ScenarioEvaluation(
                check_hallucination=evaluation_data.get("check_hallucination", False),
                check_action_hallucination=evaluation_data.get("check_action_hallucination", False),
                check_citations=evaluation_data.get("check_citations", False),
                max_hallucination_score=evaluation_data.get("max_hallucination_score", 0.5),
            ),
        )


def load_scenario(scenario_path: Path) -> Scenario:
    """Load a single scenario from YAML file."""
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Scenario.from_dict(data)


def load_all_scenarios(scenarios_dir: Path) -> List[Scenario]:
    """Load all scenarios from a directory."""
    if not scenarios_dir.exists():
        return []

    scenarios = []
    for yaml_file in sorted(scenarios_dir.glob("*.yaml")):
        try:
            scenario = load_scenario(yaml_file)
            scenarios.append(scenario)
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}")

    return scenarios


def get_scenarios_by_category(scenarios: List[Scenario], category: str) -> List[Scenario]:
    """Filter scenarios by category."""
    return [s for s in scenarios if s.category == category]


def get_default_scenarios_path() -> Path:
    """Get path to the default scenarios directory."""
    return Path(__file__).parent.parent.parent / "configs" / "scenarios"