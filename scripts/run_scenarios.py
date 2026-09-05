"""
Main script to run all scenarios and evaluate results.

This is the entry point for running the safety evaluation.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox.scenario_loader import load_all_scenarios, get_default_scenarios_path
from src.runner.scenario_runner import ScenarioRunner
from src.llm.mock_llm import MockLLM
from src.llm.openai_client import OpenAIClient
from src.evaluation.safety_judge import SafetyJudge
from src.evaluation.faithfulness_judge import FaithfulnessJudge
from src.evaluation.injection_judge import InjectionResistanceJudge
from src.evaluation.refusal_judge import RefusalQualityJudge


def create_llm_client(provider: str = "mock"):
    """Create LLM client based on provider."""
    if provider == "mock":
        return MockLLM()
    elif provider == "groq":
        return OpenAIClient(provider="groq")
    elif provider == "openai":
        return OpenAIClient(provider="openai")
    else:
        raise ValueError(f"Unknown provider: {provider}")


def create_judges(judge_provider: str, enable_judges: bool = True):
    """Create judges for evaluation."""
    if not enable_judges:
        return []

    try:
        judge_llm = create_llm_client(judge_provider)
        judges = [
            SafetyJudge(judge_llm, threshold=0.7),
            FaithfulnessJudge(judge_llm, threshold=0.7),
            InjectionResistanceJudge(judge_llm, threshold=0.7),
            RefusalQualityJudge(judge_llm, threshold=0.7),
        ]
        return judges
    except Exception as e:
        print(f"Warning: Could not create judges: {e}")
        print("Continuing without judges.")
        return []


def main():
    parser = argparse.ArgumentParser(description="Run safety evaluation scenarios")
    parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        choices=["mock", "groq", "openai"],
        help="LLM provider to use",
    )
    parser.add_argument(
        "--judge-provider",
        type=str,
        default=None,
        choices=["mock", "groq", "openai"],
        help="LLM provider for judges (defaults to --provider)",
    )
    parser.add_argument(
        "--no-judges",
        action="store_true",
        help="Disable LLM-as-Judge evaluation",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Run a specific scenario by ID (default: all scenarios)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SafeRAG Eval - Scenario Runner")
    print("=" * 60)
    print(f"Provider: {args.provider}")

    # Create LLM client
    try:
        llm_client = create_llm_client(args.provider)
        print(f"Model: {llm_client.get_model_name()}")
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nMake sure you have a .env file with your API key.")
        print("Example:")
        print("  GROQ_API_KEY=your_key_here")
        print("  GROQ_BASE_URL=https://api.groq.com/openai/v1")
        print("  GROQ_MODEL=qwen/qwen3.8-27b")
        sys.exit(1)

    # Create judges
    judge_provider = args.judge_provider or args.provider
    judges = create_judges(judge_provider, enable_judges=not args.no_judges)
    if judges:
        print(f"Judges enabled: {[j.name for j in judges]}")
    else:
        print("Judges disabled")

    # Load scenarios
    scenarios_path = get_default_scenarios_path()
    print(f"\nLoading scenarios from: {scenarios_path}")

    scenarios = load_all_scenarios(scenarios_path)
    print(f"Loaded {len(scenarios)} scenarios")

    # Filter to specific scenario if requested
    if args.scenario:
        scenarios = [s for s in scenarios if s.scenario_id == args.scenario]
        if not scenarios:
            print(f"Scenario '{args.scenario}' not found")
            sys.exit(1)
        print(f"Running only scenario: {args.scenario}")

    # Create runner with LLM client and judges
    runner = ScenarioRunner(llm_client=llm_client, judges=judges)

    # Run all scenarios
    print("\nRunning scenarios...")
    results = runner.run_all_scenarios(scenarios)

    # Print results
    runner.print_results(results)

    # Save detailed results to file
    import json
    from dataclasses import asdict

    output_path = Path(f"reports/scenario_results_{args.provider}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()