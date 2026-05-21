#!/usr/bin/env python3
"""
Regression gate: compare run metrics against benchmarks/thresholds.json.

Usage:
  python scripts/benchmark_gate.py
  python scripts/benchmark_gate.py --report reports/latest.json
  python scripts/benchmark_gate.py --write-baseline reports/latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sentinel_eval.benchmark.regression import (
    check_regression,
    load_thresholds,
    metrics_from_report,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THRESHOLDS = ROOT / "benchmarks" / "thresholds.json"
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "golden_regression_report.json"
DEFAULT_BASELINE = ROOT / "benchmarks" / "baseline_metrics.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden benchmark regression gate")
    parser.add_argument(
        "--report",
        default=str(DEFAULT_FIXTURE),
        help="Run report JSON (default: offline fixture)",
    )
    parser.add_argument(
        "--thresholds",
        default=str(DEFAULT_THRESHOLDS),
        help="Threshold floors JSON",
    )
    parser.add_argument(
        "--write-baseline",
        metavar="REPORT",
        help="Write aggregate metrics snapshot to benchmarks/baseline_metrics.json",
    )
    args = parser.parse_args()

    if args.write_baseline:
        metrics = metrics_from_report(Path(args.write_baseline))
        snapshot = {
            "schema_valid_pct": metrics.schema_valid_pct,
            "label_match_pct": metrics.label_match_pct,
            "injection_recall_pct": metrics.injection_recall_pct,
            "benign_specificity_pct": metrics.benign_specificity_pct,
            "security_pass_pct": metrics.security_pass_pct,
            "cases_run": metrics.cases_run,
            "prompt_version": metrics.prompt_version,
        }
        DEFAULT_BASELINE.parent.mkdir(parents=True, exist_ok=True)
        with DEFAULT_BASELINE.open("w", encoding="utf-8") as fp:
            json.dump(snapshot, fp, indent=2)
        print(f"Wrote baseline → {DEFAULT_BASELINE}")
        return 0

    thresholds = load_thresholds(Path(args.thresholds))
    metrics = metrics_from_report(Path(args.report))
    floors = thresholds.get("floors") or {}
    failures = check_regression(metrics, floors)

    print(f"Benchmark gate: {Path(args.report).name}")
    print(f"  cases_run={metrics.cases_run} prompt={metrics.prompt_version}")
    for key in sorted(floors):
        actual = getattr(metrics, key, None)
        status = "FAIL" if any(msg.startswith(f"{key}:") for msg in failures) else "OK"
        print(f"  [{status}] {key}: {actual}% (floor {floors[key]}%)")

    if failures:
        print("REGRESSION:", file=sys.stderr)
        for msg in failures:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    print("Benchmark gate: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
