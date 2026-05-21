"""Golden benchmark regression checks."""

from __future__ import annotations

import json
from pathlib import Path

from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.utils.reports import load_run_report


def load_thresholds(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as fp:
        data: dict[str, object] = json.load(fp)
        return data


def metrics_from_report(report_path: Path) -> SuiteMetrics:
    run_report = load_run_report(report_path)
    metrics = run_report.metrics
    if metrics.cases_run == 0 and run_report.results:
        metrics = aggregate_metrics(run_report.results)
    return metrics


def check_regression(metrics: SuiteMetrics, floors: dict[str, float]) -> list[str]:
    failures: list[str] = []
    for key, minimum in floors.items():
        actual = getattr(metrics, key, None)
        if actual is None:
            failures.append(f"{key}: n/a (metric missing)")
            continue
        if actual < minimum:
            failures.append(f"{key}: {actual}% < floor {minimum}%")
    return failures
