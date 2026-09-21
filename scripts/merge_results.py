"""
Merge per-scenario result files into a single comparison report.

Usage:
    python scripts/merge_results.py

Reads all JSON files from reports/results/ and produces a unified
report in reports/final/.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    results_dir = Path("reports/results")
    final_dir = Path("reports/final")
    final_dir.mkdir(parents=True, exist_ok=True)

    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        sys.exit(1)

    json_files = sorted(results_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {results_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} result files")

    # Merge structure: {model_name: {provider, model, scenarios: {scenario_id: {...}}}}
    merged = {}

    for file_path in json_files:
        print(f"  Reading: {file_path.name}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for model_name, model_data in data.items():
            if "error" in model_data:
                continue
            if model_name not in merged:
                merged[model_name] = {
                    "provider": model_data["provider"],
                    "model": model_data["model"],
                    "scenarios": {},
                }
            # Merge scenarios
            for sid, sdata in model_data.get("scenarios", {}).items():
                merged[model_name]["scenarios"][sid] = sdata

    # Recompute totals
    for model_name, mdata in merged.items():
        total = len(mdata["scenarios"])
        passed = sum(1 for s in mdata["scenarios"].values() if s["passed"])
        mdata["total"] = total
        mdata["passed"] = passed
        mdata["failed"] = total - passed

    # Save merged JSON
    timestamp = datetime.now().strftime("%Y-%m-%d")
    merged_json = final_dir / f"comparison_{timestamp}.json"
    with open(merged_json, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    print(f"\nMerged JSON: {merged_json}")

    # Generate Markdown using the same report function
    from scripts.run_scenarios import generate_comparison_report
    generate_comparison_report(merged, output_dir=final_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()