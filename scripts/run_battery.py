"""
Battery runner: executes all models x all scenarios from a YAML config.

Usage:
    python scripts/run_battery.py --config configs/battery.yaml
    python scripts/run_battery.py --config configs/battery.yaml --models gpt_oss_120b,qwen_groq
    python scripts/run_battery.py --config configs/battery.yaml --scenarios tool_result_injection_001
"""

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from run_scenarios import create_llm_client, create_judges, compute_aggregated_stats
from src.sandbox.scenario_loader import load_all_scenarios, get_default_scenarios_path
from src.runner.scenario_runner import ScenarioRunner


def select_judge(judge_pool, provider, model):
    """Pick first judge from pool that differs from candidate."""
    for entry in judge_pool:
        if entry["provider"] != provider or entry["model"] != model:
            return entry
    return judge_pool[0]


def save_scenario_results(scenario_id, provider, model, judge, n_runs, all_runs):
    """Save per-scenario results with full metadata."""
    output_data = {
        "metadata": {
            "provider": provider,
            "model": model,
            "judge_provider": judge["provider"],
            "judge_model": judge["model"],
            "timestamp": datetime.now().isoformat(),
            "n_runs": n_runs,
            "source": "battery",
        },
        "runs": [[asdict(r) for r in run_results] for run_results in all_runs],
        "aggregated_stats": compute_aggregated_stats(all_runs),
    }

    out_dir = Path("reports/runs/scenarios")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{scenario_id}_{provider}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved: {out_path}")


def print_scenario_stats(scenario_id, all_runs):
    """Print aggregated stats for one scenario."""
    stats = compute_aggregated_stats(all_runs)
    data = stats.get(scenario_id, {})
    print(f"\n  {scenario_id}: pass_rate={data.get('pass_rate', 0):.0%} "
          f"({data.get('passed', 0)}/{data.get('total', 0)})")
    for judge_name, js in sorted(data.get("judges", {}).items()):
        print(f"    {judge_name}: mean={js['mean']:.2f} ±{js['std']:.2f} "
              f"(min={js['min']:.2f}, max={js['max']:.2f})")


def main():
    parser = argparse.ArgumentParser(description="Run test battery from YAML config")
    parser.add_argument("--config", type=str, default="configs/battery.yaml")
    parser.add_argument("--models", type=str, default=None,
                        help="Comma-separated model IDs (default: all from config)")
    parser.add_argument("--scenarios", type=str, default=None,
                        help="Comma-separated scenario IDs (default: from config)")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    judge_pool = config.get("judge_pool", [{"provider": "groq", "model": "qwen/qwen3.8-27b"}])
    models = config.get("models", [])
    settings = config.get("settings", {})
    n_runs = settings.get("n_runs", 3)
    delay = settings.get("delay_between_runs", 15)

    if args.models:
        wanted = set(args.models.split(","))
        models = [m for m in models if m["id"] in wanted]

    scenarios = load_all_scenarios(get_default_scenarios_path())
    if args.scenarios:
        wanted_s = set(args.scenarios.split(","))
        scenarios = [s for s in scenarios if s.scenario_id in wanted_s]
    elif config.get("scenarios", "all") != "all":
        wanted_s = set(config["scenarios"])
        scenarios = [s for s in scenarios if s.scenario_id in wanted_s]

    print("=" * 60)
    print("SafeRAG Eval - Battery Runner")
    print("=" * 60)
    print(f"Models: {len(models)}")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Runs per scenario: {n_runs}")
    print(f"Total evaluations: {len(models) * len(scenarios) * n_runs}")

    summary = {}

    for model_cfg in models:
        provider = model_cfg["provider"]
        model = model_cfg["model"]
        display = model_cfg.get("display_name", model)
        judge = select_judge(judge_pool, provider, model)

        print(f"\n{'=' * 60}")
        print(f"Candidate: {display} ({provider}/{model})")
        print(f"Judge:     {judge['provider']}/{judge['model']}")
        print(f"{'=' * 60}")

        try:
            llm_client = create_llm_client(provider, model=model)
            judges = create_judges(True, judge["provider"], judge["model"])
        except Exception as e:
            print(f"⚠️ Skipping {display}: {e}")
            summary[display] = {"error": str(e)}
            continue

        model_stats = {}
        for scenario in scenarios:
            print(f"\n--- Scenario: {scenario.scenario_id} ---")
            all_runs = []
            for run_idx in range(n_runs):
                if run_idx > 0:
                    print(f"Waiting {delay}s before next run...")
                    time.sleep(delay)
                runner = ScenarioRunner(llm_client=llm_client, judges=judges)
                results = runner.run_all_scenarios([scenario])
                all_runs.append(results)

            save_scenario_results(scenario.scenario_id, provider, model, judge, n_runs, all_runs)
            print_scenario_stats(scenario.scenario_id, all_runs)

            stats = compute_aggregated_stats(all_runs).get(scenario.scenario_id, {})
            model_stats[scenario.scenario_id] = stats

        summary[display] = model_stats

    # Final summary table
    print("\n" + "=" * 60)
    print("BATTERY SUMMARY")
    print("=" * 60)
    for display, stats in summary.items():
        if "error" in stats:
            print(f"{display}: ERROR - {stats['error'][:60]}")
            continue
        rates = [s.get("pass_rate", 0) for s in stats.values()]
        overall = sum(rates) / len(rates) if rates else 0
        print(f"{display}: overall pass_rate={overall:.0%} across {len(rates)} scenarios")


if __name__ == "__main__":
    main()