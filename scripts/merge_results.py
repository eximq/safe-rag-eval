"""
Merge per-scenario result files into aggregated reports per provider.

Usage:
    python scripts/merge_results.py

Reads all JSON files from reports/runs/scenarios/ and produces:
- reports/final/results/{provider}_all_scenarios.json
- reports/final/results/{provider}_all_scenarios.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def aggregate_scenario(data):
    """Aggregate N-run results for a single scenario."""
    n_runs = data.get("n_runs", 1)
    runs = data.get("runs", [])
    
    if not runs:
        return None
    
    # Collect pass/fail across runs
    passed_count = sum(1 for run in runs for result in run if result.get("passed"))
    total_runs = len(runs)
    
    # Collect judge scores across runs
    judge_scores = defaultdict(list)
    for run in runs:
        for result in run:
            for jr in result.get("judge_results", []):
                judge_scores[jr["judge_name"]].append(jr["score"])
    
    # Compute mean/std for each judge
    judge_stats = {}
    for judge_name, scores in judge_scores.items():
        if len(scores) == 1:
            judge_stats[judge_name] = {"mean": scores[0], "std": 0.0, "min": scores[0], "max": scores[0]}
        else:
            import statistics
            judge_stats[judge_name] = {
                "mean": statistics.mean(scores),
                "std": statistics.stdev(scores),
                "min": min(scores),
                "max": max(scores),
            }
    
    return {
        "n_runs": n_runs,
        "passed_count": passed_count,
        "total_runs": total_runs,
        "pass_rate": passed_count / total_runs if total_runs > 0 else 0.0,
        "judge_stats": judge_stats,
    }


def main():
    scenarios_dir = Path("reports/runs/scenarios")
    final_dir = Path("reports/final/results")
    final_dir.mkdir(parents=True, exist_ok=True)

    if not scenarios_dir.exists():
        print(f"Directory not found: {scenarios_dir}")
        sys.exit(1)

    json_files = sorted(scenarios_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {scenarios_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} scenario files")

    # Group by provider
    providers = defaultdict(dict)
    for file_path in json_files:
        print(f"  Reading: {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Parse filename: {scenario_id}_{provider}.json
        filename = file_path.stem
        parts = filename.rsplit("_", 1)
        if len(parts) != 2:
            print(f"    Skipping (invalid filename format): {filename}")
            continue
        
        scenario_id, provider = parts
        aggregated = aggregate_scenario(data)
        if aggregated:
            providers[provider][scenario_id] = aggregated

    # Generate reports per provider
    for provider, scenarios in providers.items():
        print(f"\nAggregating {provider}: {len(scenarios)} scenarios")
        
        # Save JSON
        output_json = final_dir / f"{provider}_all_scenarios.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(scenarios, f, indent=2)
        print(f"  JSON: {output_json}")
        
        # Generate Markdown
        output_md = final_dir / f"{provider}_all_scenarios.md"
        generate_markdown_report(provider, scenarios, output_md)
        print(f"  Markdown: {output_md}")

    print("\nDone.")


def generate_markdown_report(provider, scenarios, output_path):
    """Generate Markdown report for a provider."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {provider.upper()} - All Scenarios Aggregated\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"Total scenarios: {len(scenarios)}\n\n")
        f.write("---\n\n")
        
        # Summary table
        f.write("## Summary\n\n")
        f.write("| Scenario | Pass Rate | N Runs | Judges (mean ± std) |\n")
        f.write("| --- | --- | --- | --- |\n")
        
        for scenario_id, data in sorted(scenarios.items()):
            pass_rate = data["pass_rate"] * 100
            n_runs = data["n_runs"]
            
            # Format judge stats
            judge_parts = []
            for judge_name, stats in data["judge_stats"].items():
                judge_parts.append(f"{judge_name}: {stats['mean']:.2f}±{stats['std']:.2f}")
            judges_str = ", ".join(judge_parts) if judge_parts else "N/A"
            
            f.write(f"| `{scenario_id}` | {pass_rate:.0f}% | {n_runs} | {judges_str} |\n")
        
        f.write("\n")
        
        # Detailed stats
        f.write("## Detailed Statistics\n\n")
        for scenario_id, data in sorted(scenarios.items()):
            f.write(f"### {scenario_id}\n\n")
            f.write(f"- Pass rate: {data['passed_count']}/{data['total_runs']} ({data['pass_rate']*100:.0f}%)\n")
            f.write(f"- N runs: {data['n_runs']}\n\n")
            
            if data["judge_stats"]:
                f.write("| Judge | Mean | Std | Min | Max |\n")
                f.write("| --- | --- | --- | --- | --- |\n")
                for judge_name, stats in data["judge_stats"].items():
                    f.write(f"| {judge_name} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |\n")
                f.write("\n")


if __name__ == "__main__":
    main()