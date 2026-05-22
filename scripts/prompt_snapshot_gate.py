#!/usr/bin/env python3
"""Offline label snapshot gate (prompt regression without live LLM)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sentinel_eval.utils.reports import load_run_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "benchmarks" / "snapshots" / "golden-12" / "expected_labels.json"
DEFAULT_REPORT = ROOT / "tests" / "fixtures" / "golden_regression_report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare run labels to golden snapshot")
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT))
    args = parser.parse_args()

    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    expected = snapshot["cases"]
    report = load_run_report(Path(args.report))

    failures: list[str] = []
    for item in report.results:
        case_id = item.case_id or ""
        if case_id not in expected:
            continue
        exp = expected[case_id]
        pred = item.parsed_output
        if pred.is_safe != exp["is_safe"]:
            failures.append(f"{case_id}: is_safe {pred.is_safe} != {exp['is_safe']}")
        if (pred.security_status or "").strip() != exp["security_status"]:
            failures.append(
                f"{case_id}: security_status {pred.security_status!r} != {exp['security_status']!r}"
            )
        if not item.schema_validation.is_valid:
            failures.append(f"{case_id}: schema invalid")

    print(f"Snapshot gate: {Path(args.report).name} vs {Path(args.snapshot).name}")
    if failures:
        print("FAILURES:", file=sys.stderr)
        for msg in failures:
            print(f"  - {msg}", file=sys.stderr)
        return 1
    print(f"Snapshot gate: PASSED ({len(expected)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
