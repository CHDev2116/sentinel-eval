#!/usr/bin/env python3
"""Print aggregate metrics from a SentinelEval run report."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.eval_runner import aggregate_metrics


def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "results" in data:
        return data.get("meta", {}), data["results"]
    if isinstance(data, list):
        return {}, data
    raise ValueError(f"Unrecognized report format: {path}")


def main():
    parser = argparse.ArgumentParser(description="Summarize SentinelEval run JSON.")
    parser.add_argument(
        "report",
        nargs="?",
        default=os.path.join("reports", "evaluation_results.json"),
    )
    parser.add_argument("--markdown", action="store_true", help="Print markdown table row.")
    args = parser.parse_args()

    meta, results = load_report(args.report)
    metrics = aggregate_metrics(results)
    model = meta.get("model", "unknown")

    if args.markdown:
        print(
            f"| `{model}` | **{metrics.get('schema_valid_pct')}%** | "
            f"**{metrics.get('label_match_pct')}%** | "
            f"**{metrics.get('avg_rouge_l_f1')}** | "
            f"recall {metrics.get('injection_recall_pct')}% · spec {metrics.get('benign_specificity_pct')}% |"
        )
        return

    print(f"Model: {model}")
    print(f"Report: {args.report}")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
