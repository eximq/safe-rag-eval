"""
Test script to verify scenario loading works correctly.

Loads all scenarios from configs/scenarios/ and displays them.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox.scenario_loader import load_all_scenarios, get_default_scenarios_path


def main():
    print("=" * 60)
    print("SafeRAG Eval - Scenario Loading Test")
    print("=" * 60)

    # Load scenarios
    scenarios_path = get_default_scenarios_path()
    print(f"\nLoading scenarios from: {scenarios_path}")

    scenarios = load_all_scenarios(scenarios_path)
    print(f"\nLoaded {len(scenarios)} scenarios:")

    for scenario in scenarios:
        print(f"\n{'-' * 40}")
        print(f"ID: {scenario.scenario_id}")
        print(f"Category: {scenario.category}")
        print(f"Difficulty: {scenario.difficulty}")
        print(f"Description: {scenario.description}")
        print(f"User query: {scenario.input.user_query}")
        print(f"Documents: {len(scenario.input.documents)}")
        print(f"Available tools: {scenario.input.available_tools}")
        print(f"Expected:")
        print(f"  - Should call tools: {scenario.expected.should_call_tools}")
        print(f"  - Required tools: {scenario.expected.required_tool_calls}")
        print(f"  - Forbidden tools: {scenario.expected.forbidden_tool_calls}")
        print(f"  - Should refuse: {scenario.expected.should_refuse}")
        print(f"Evaluation:")
        print(f"  - Check hallucination: {scenario.evaluation.check_hallucination}")
        print(f"  - Check citations: {scenario.evaluation.check_citations}")


if __name__ == "__main__":
    main()