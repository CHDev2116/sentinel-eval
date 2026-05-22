"""Temporal benchmark history for prompt/model regression tracking."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_eval.domain.suite_metrics import SuiteMetrics

DEFAULT_HISTORY_DIR = Path("benchmarks/history")
INDEX_FILE = "index.jsonl"


def _metric_snapshot(metrics: SuiteMetrics) -> dict[str, Any]:
    keys = (
        "cases_run",
        "prompt_version",
        "schema_valid_pct",
        "label_match_pct",
        "security_pass_pct",
        "composite_pass_pct",
        "ensemble_pass_pct",
        "release_pass_pct",
        "avg_rouge_l_f1",
        "injection_recall_pct",
        "benign_specificity_pct",
        "precision_pct",
        "f1_pct",
    )
    snap = {k: getattr(metrics, k, None) for k in keys}
    cal = metrics.calibration
    if cal is not None:
        snap["brier_score"] = cal.brier_score
        snap["ece"] = cal.ece
    return snap


def append_run_history(
    *,
    metrics: SuiteMetrics,
    model: str,
    payload: str = "",
    report_path: str = "",
    extra: dict[str, Any] | None = None,
    history_dir: str | Path = DEFAULT_HISTORY_DIR,
) -> Path:
    """Append one run snapshot to benchmarks/history/index.jsonl."""
    root = Path(history_dir)
    root.mkdir(parents=True, exist_ok=True)
    entry = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "payload": payload,
        "report_path": report_path,
        "metrics": _metric_snapshot(metrics),
    }
    if extra:
        entry.update(extra)
    index_path = root / INDEX_FILE
    with index_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return index_path


def load_history(history_dir: str | Path = DEFAULT_HISTORY_DIR) -> list[dict[str, Any]]:
    index_path = Path(history_dir) / INDEX_FILE
    if not index_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
