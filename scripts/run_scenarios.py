"""
Main script to run all scenarios and evaluate results.

This is the entry point for running the safety evaluation.
Uses UnifiedLLMClient (LiteLLM) for multi-provider support.
"""

import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox.scenario_loader import load_all_scenarios, get_default_scenarios_path
from src.runner.scenario_runner import ScenarioRunner
from src.llm.mock_llm import MockLLM
from src.llm.unified_client import UnifiedLLMClient
from src.evaluation.safety_judge import SafetyJudge
from src.evaluation.faithfulness_judge import FaithfulnessJudge
from src.evaluation.injection_judge import InjectionResistanceJudge
from src.evaluation.refusal_judge import RefusalQualityJudge

# Supported providers (unified_client compatible)
PROVIDERS = ["mock", "openai", "anthropic", "gemini", "groq", "qwen", "together", "ollama"]

# Model configuration for comparison testing
MODEL_CONFIG = {
    "gpt_oss": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS 120B (Groq)",
    },
    "gemini_flash": {
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "display_name": "Gemini 3.5 Flash Lite",
    },
    "qwen_groq": {
        "provider": "groq",
        "model": "qwen/qwen3.8-27b",
        "display_name": "Qwen 3.8 27B (Groq)",
    },
}


def create_llm_client(provider: str, model: Optional[str] = None):
    """Create LLM client using UnifiedLLMClient (LiteLLM)."""
    if provider == "mock":
        return MockLLM()
    try:
        # UnifiedLLMClient resolves API key from env via its own ENV_KEYS mapping
        return UnifiedLLMClient(provider=provider, model=model)
    except Exception as e:
        raise ValueError(f"Failed to create client for {provider}/{model}: {e}")


def create_judges(enable_judges: bool = True, judge_provider: str = "groq", judge_model: str = "qwen/qwen3.8-27b"):
    """Create judges for evaluation."""
    if not enable_judges:
        return []

    try:
        judge_llm = UnifiedLLMClient(provider=judge_provider, model=judge_model)
        
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


def compute_aggregated_stats(all_runs_results):
    """Compute aggregated statistics across all runs."""
    from collections import defaultdict
    import statistics
    
    scenario_scores = defaultdict(lambda: defaultdict(list))
    scenario_pass_counts = defaultdict(lambda: {"passed": 0, "total": 0})
    
    for run_results in all_runs_results:
        for result in run_results:
            scenario_pass_counts[result.scenario_id]["total"] += 1
            if result.passed:
                scenario_pass_counts[result.scenario_id]["passed"] += 1
            
            for jr in result.judge_results:
                scenario_scores[result.scenario_id][jr.judge_name].append(jr.score)
    
    stats = {}
    for scenario_id in scenario_scores:
        stats[scenario_id] = {
            "pass_rate": scenario_pass_counts[scenario_id]["passed"] / scenario_pass_counts[scenario_id]["total"],
            "passed": scenario_pass_counts[scenario_id]["passed"],
            "total": scenario_pass_counts[scenario_id]["total"],
            "judges": {},
        }
        for judge_name, scores in scenario_scores[scenario_id].items():
            if len(scores) == 1:
                stats[scenario_id]["judges"][judge_name] = {
                    "mean": scores[0], "std": 0.0, "min": scores[0], "max": scores[0]
                }
            else:
                stats[scenario_id]["judges"][judge_name] = {
                    "mean": statistics.mean(scores),
                    "std": statistics.stdev(scores),
                    "min": min(scores),
                    "max": max(scores),
                }
    
    return stats


def print_aggregated_stats(all_runs_results):
    """Print mean/std/min/max scores across runs per scenario."""
    stats = compute_aggregated_stats(all_runs_results)
    
    print("\n" + "=" * 80)
    print("AGGREGATED STATISTICS (across all runs)")
    print("=" * 80)
    
    for scenario_id in sorted(stats.keys()):
        print(f"\n{scenario_id}:")
        data = stats[scenario_id]
        print(f"  Pass rate: {data['passed']}/{data['total']} ({data['pass_rate']*100:.0f}%)")
        for judge_name, judge_stats in sorted(data["judges"].items()):
            print(f"  {judge_name}: mean={judge_stats['mean']:.2f} ±{judge_stats['std']:.2f} (min={judge_stats['min']:.2f}, max={judge_stats['max']:.2f})")


def run_comparison(args):
    """Run scenarios on all models and generate comparison table."""
    print("=" * 60)
    print("SafeRAG Eval - Multi-Model Comparison")
    print("=" * 60)

    scenarios_path = get_default_scenarios_path()
    scenarios = load_all_scenarios(scenarios_path)
    
    if args.scenario:
        scenarios = [s for s in scenarios if s.scenario_id == args.scenario]
    
    print(f"Scenarios: {len(scenarios)}")
    print(f"Models: {len(MODEL_CONFIG)}")

    all_results = {}

    for _, config in MODEL_CONFIG.items():
        provider = config["provider"]
        display_name = config["display_name"]
        print(f"\n{'='*60}")
        print(f"Testing: {display_name}")
        print(f"{'='*60}")

        try:
            llm_client = create_llm_client(provider, model=config["model"])
            judges = create_judges(enable_judges=not args.no_judges)
            runner = ScenarioRunner(llm_client=llm_client, judges=judges)
            
            results = runner.run_all_scenarios(scenarios)
            
            all_results[display_name] = {
                "provider": provider,
                "model": config["model"],
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
                "total": len(results),
                "scenarios": {
                    r.scenario_id: {
                        "passed": r.passed,
                        "violations": r.violations,
                        "judge_scores": {jr.judge_name: jr.score for jr in r.judge_results},
                    }
                    for r in results
                },
            }
            
            print(f"Result: {all_results[display_name]['passed']}/{all_results[display_name]['total']} passed")
            
        except Exception as e:
            print(f"⚠️ Error with {display_name}: {e}")
            all_results[display_name] = {"error": str(e)}

    generate_comparison_report(all_results)


def generate_comparison_report(all_results, output_dir=None):
    """Generate Markdown and JSON comparison reports."""
    import json

    if output_dir is None:
        output_dir = Path("reports/final/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    scenario_ids = set()
    for data in all_results.values():
        if "scenarios" in data:
            scenario_ids.update(data["scenarios"].keys())

    if len(scenario_ids) == 1:
        scenario_id = next(iter(scenario_ids))
        json_path = output_dir / f"{scenario_id}.json"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"multi_scenario_{timestamp}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nJSON saved: {json_path}")

    md_path = json_path.with_suffix(".md")

    scenarios_by_category = {}
    for scenario_id in sorted(scenario_ids):
        parts = scenario_id.rsplit("_", 1)
        category = parts[0] if len(parts) > 1 else "other"
        scenarios_by_category.setdefault(category, []).append(scenario_id)

    models = [name for name in all_results.keys() if "error" not in all_results[name]]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# LLM Safety Evaluation - Model Comparison\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("---\n\n")

        f.write("## Summary\n\n")
        f.write("| Model | Provider | Passed | Failed | Pass Rate |\n")
        f.write("| --- | --- | --- | --- | --- |\n")

        for model_name, data in all_results.items():
            if "error" in data:
                f.write(f"| {model_name} | - | ERROR | - | - |\n")
                continue

            total = data["total"]
            passed = data["passed"]
            failed = data["failed"]
            rate = (passed / total * 100) if total > 0 else 0
            f.write(f"| {model_name} | {data['provider']} | {passed} | {failed} | {rate:.1f}% |\n")

        f.write("\n")

    print(f"Markdown saved: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Run safety evaluation scenarios")
    parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        choices=PROVIDERS,
        help="LLM provider to use",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (e.g., 'gpt-4o', 'claude-sonnet-4-5', 'qwen/qwen3.8-27b')",
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
    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Run tests on all configured models and generate comparison table",
    )
    parser.add_argument(
        "--n-runs",
        type=int,
        default=1,
        help="Number of runs per scenario (default: 1 for backward compatibility)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=15,
        help="Delay in seconds between runs (default: 15)",
    )
    args = parser.parse_args()

    # Comparison mode
    if args.all_models:
        run_comparison(args)
        return

    # Single provider mode
    print("=" * 60)
    print("SafeRAG Eval - Scenario Runner")
    print("=" * 60)
    print(f"Provider: {args.provider}")

    # Create LLM client
    try:
        llm_client = create_llm_client(args.provider, model=args.model)
        print(f"Model: {args.model or 'default'}")
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nMake sure you have a .env file with your API key.")
        sys.exit(1)

    # Create judges
    judges = create_judges(enable_judges=not args.no_judges)
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

    # Run all scenarios (N times if requested)
    print(f"\nRunning scenarios ({args.n_runs} run(s) per scenario)...")
    all_runs_results = []
    
    for run_idx in range(args.n_runs):
        if args.n_runs > 1:
            print(f"\n--- Run {run_idx + 1}/{args.n_runs} ---")
            if run_idx > 0:
                print(f"Waiting {args.delay}s before next run...")
                time.sleep(args.delay)
        
        runner = ScenarioRunner(llm_client=llm_client, judges=judges)
        results = runner.run_all_scenarios(scenarios)
        all_runs_results.append(results)
        
        if args.n_runs > 1:
            runner.print_results(results)

    # Print results (use last run if single run mode)
    if args.n_runs == 1:
        runner.print_results(all_runs_results[0])

    # Build output data
    import json
    from dataclasses import asdict

    output_data = {
        "n_runs": args.n_runs,
        "runs": [[asdict(r) for r in run_results] for run_results in all_runs_results],
    }

    # Add aggregated statistics if multiple runs
    if args.n_runs > 1:
        output_data["aggregated_stats"] = compute_aggregated_stats(all_runs_results)

    # Save detailed results to file
    output_path = Path(f"reports/runs/scenario_results_{args.provider}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")

    # Also save per-scenario file (for merge_results.py aggregation)
    if args.scenario:
        scenarios_dir = Path("reports/runs/scenarios")
        scenarios_dir.mkdir(parents=True, exist_ok=True)
        scenario_output_path = scenarios_dir / f"{args.scenario}_{args.provider}.json"
        with open(scenario_output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"Per-scenario results saved to: {scenario_output_path}")
    
    # Print aggregated statistics if multiple runs
    if args.n_runs > 1:
        print_aggregated_stats(all_runs_results)


if __name__ == "__main__":
    main()