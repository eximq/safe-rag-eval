"""
Main script to run all scenarios and evaluate results.

This is the entry point for running the safety evaluation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox.scenario_loader import load_all_scenarios, get_default_scenarios_path
from src.runner.scenario_runner import ScenarioRunner


def main():
    print("=" * 60)
    print("SafeRAG Eval - Scenario Runner")
    print("=" * 60)

    # Load scenarios
    scenarios_path = get_default_scenarios_path()
    print(f"\nLoading scenarios from: {scenarios_path}")

    scenarios = load_all_scenarios(scenarios_path)
    print(f"Loaded {len(scenarios)} scenarios")

    # Create runner
    runner = ScenarioRunner()

    # Run all scenarios
    print("\nRunning scenarios...")
    results = runner.run_all_scenarios(scenarios)

    # Print results
    runner.print_results(results)

    # Save detailed results to file
    import json
    from dataclasses import asdict

    output_path = Path("reports/scenario_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()