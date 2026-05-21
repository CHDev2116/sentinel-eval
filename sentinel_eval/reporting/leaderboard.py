"""Aggregate multi-model SentinelEval runs into a benchmark leaderboard."""

import json
import os
from datetime import datetime, timezone

from sentinel_eval.domain.report import RunMeta, RunReport, case_result_from_dict
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.utils.payloads import GOLDEN_PAYLOAD
from sentinel_eval.utils.reports import load_run_report

DEFAULT_LEADERBOARD_PATH = os.path.join("reports", "leaderboard.json")
GOLDEN_SUITE = "golden-12"


def _metric_snapshot(metrics: SuiteMetrics) -> dict:
    keys = (
        "schema_valid_pct",
        "label_match_pct",
        "security_pass_pct",
        "release_pass_pct",
        "avg_rouge_l_f1",
        "injection_recall_pct",
        "benign_specificity_pct",
        "precision_pct",
        "f1_pct",
        "false_positive_rate_pct",
        "composite_pass_pct",
    )
    return {k: getattr(metrics, k) for k in keys if getattr(metrics, k, None) is not None}


def entry_from_run_report(run_report: RunReport, report_path: str = "") -> dict:
    """Build a leaderboard entry from a typed RunReport."""
    metrics = run_report.metrics
    if metrics.cases_run == 0 and run_report.results:
        metrics = aggregate_metrics(run_report.results)

    meta = run_report.meta
    return {
        "model": meta.model,
        "prompt_version": metrics.prompt_version or meta.prompt_version,
        "timestamp": meta.timestamp or datetime.now(timezone.utc).isoformat(),
        "suite": GOLDEN_SUITE if meta.full_suite else "partial",
        "payload": meta.payload or GOLDEN_PAYLOAD,
        "cases_run": metrics.cases_run or len(run_report.results),
        "report_path": report_path,
        "metrics": _metric_snapshot(metrics),
    }


def entry_from_report(report_path, meta=None, results=None, metrics=None):
    """Legacy helper: path or pre-loaded parts → leaderboard entry dict."""
    if meta is not None and results is not None:
        if metrics is None:
            metrics = aggregate_metrics(results)
        if not isinstance(metrics, SuiteMetrics):
            metrics = SuiteMetrics.model_validate(metrics)
        normalized = [
            case_result_from_dict(r) if isinstance(r, dict) else r for r in results
        ]
        run_report = RunReport(
            meta=RunMeta.model_validate({**meta, "metrics": metrics}),
            results=normalized,
        )
        return entry_from_run_report(run_report, report_path)

    run_report = load_run_report(report_path)
    return entry_from_run_report(run_report, report_path)


def load_leaderboard(path=DEFAULT_LEADERBOARD_PATH):
    if not os.path.exists(path):
        return {"suite": GOLDEN_SUITE, "updated_at": None, "entries": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("entries", [])
    return data


def save_leaderboard(data, path=DEFAULT_LEADERBOARD_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _entry_key(entry):
    return (entry.get("model"), entry.get("prompt_version") or "")


def _parse_ts(entry):
    raw = entry.get("timestamp") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def upsert_entry(leaderboard, entry, prefer="latest"):
    """Merge one run; keep latest timestamp per (model, prompt_version)."""
    entries = leaderboard.setdefault("entries", [])
    key = _entry_key(entry)
    replaced = False
    for idx, existing in enumerate(entries):
        if _entry_key(existing) != key:
            continue
        if prefer == "latest" and _parse_ts(entry) >= _parse_ts(existing):
            entries[idx] = entry
        replaced = True
        break
    if not replaced:
        entries.append(entry)
    return leaderboard


def register_run_report(
    report_path: str | os.PathLike,
    leaderboard_path=DEFAULT_LEADERBOARD_PATH,
    prefer="latest",
) -> dict:
    """Register a run JSON file using typed RunReport.load."""
    run_report = load_run_report(report_path)
    entry = entry_from_run_report(run_report, str(report_path))
    board = load_leaderboard(leaderboard_path)
    upsert_entry(board, entry, prefer=prefer)
    save_leaderboard(board, leaderboard_path)
    return entry


def register_report(report_path, leaderboard_path=DEFAULT_LEADERBOARD_PATH, prefer="latest"):
    """Alias for register_run_report."""
    return register_run_report(report_path, leaderboard_path, prefer=prefer)


def discover_report_paths(extra_dirs=None):
    """Collect run JSON paths from common report locations."""
    candidates = []
    roots = [
        os.path.join("reports", "runs"),
        os.path.join("reports", "generated_runs"),
        "reports",
    ]
    if extra_dirs:
        roots = list(extra_dirs) + roots

    singles = [
        os.path.join("reports", "latest.json"),
        os.path.join("reports", "evaluation_results.json"),
    ]
    for path in singles:
        if os.path.isfile(path):
            candidates.append(path)

    for root in roots:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if not name.endswith(".json"):
                continue
            candidates.append(os.path.join(root, name))

    seen = set()
    unique = []
    for path in candidates:
        abspath = os.path.abspath(path)
        if abspath in seen:
            continue
        seen.add(abspath)
        unique.append(path)
    return unique


def scan_and_register(leaderboard_path=DEFAULT_LEADERBOARD_PATH, report_paths=None):
    board = load_leaderboard(leaderboard_path)
    paths = report_paths or discover_report_paths()
    registered = 0
    for path in paths:
        try:
            run_report = load_run_report(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not run_report.meta.full_suite and run_report.metrics.cases_run < 12:
            continue
        entry = entry_from_run_report(run_report, path)
        upsert_entry(board, entry)
        registered += 1
    save_leaderboard(board, leaderboard_path)
    return registered, board


def sort_entries(entries):
    def sort_key(e):
        m = e.get("metrics") or {}
        return (
            -(m.get("label_match_pct") or 0),
            -(m.get("avg_rouge_l_f1") or 0),
            -(m.get("schema_valid_pct") or 0),
        )

    return sorted(entries, key=sort_key)


def _fmt_pct(value):
    if value is None:
        return "—"
    return f"{value:.0f}%" if isinstance(value, (int, float)) else str(value)


def _fmt_rouge(value):
    if value is None:
        return "—"
    return f"{value:.2f}"


def format_markdown_table(entries, title=None):
    rows = sort_entries(entries)
    lines = []
    if title:
        lines.append(f"### {title}")
        lines.append("")
    lines.append("| Model | Schema Valid | Label Match | ROUGE-L | Release | Prompt |")
    lines.append("|-------|--------------|-------------|---------|---------|--------|")
    for e in rows:
        m = e.get("metrics") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{e.get('model', '?')}`",
                    f"**{_fmt_pct(m.get('schema_valid_pct'))}**",
                    f"**{_fmt_pct(m.get('label_match_pct'))}**",
                    f"**{_fmt_rouge(m.get('avg_rouge_l_f1'))}**",
                    _fmt_pct(m.get("release_pass_pct")),
                    f"`{e.get('prompt_version', '?')}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def format_ascii_table(entries):
    rows = sort_entries(entries)
    headers = ("Model", "Schema", "Label", "ROUGE-L", "Release", "Prompt")
    data = []
    for e in rows:
        m = e.get("metrics") or {}
        data.append(
            (
                e.get("model", "?"),
                _fmt_pct(m.get("schema_valid_pct")),
                _fmt_pct(m.get("label_match_pct")),
                _fmt_rouge(m.get("avg_rouge_l_f1")),
                _fmt_pct(m.get("release_pass_pct")),
                e.get("prompt_version", "?"),
            )
        )
    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def line(cells):
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells))

    out = [line(headers), line(["-" * w for w in widths])]
    out.extend(line(row) for row in data)
    return "\n".join(out)
