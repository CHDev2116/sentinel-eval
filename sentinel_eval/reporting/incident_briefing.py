"""Stream-parse threat_intel JSONL and render ASCII security briefings."""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

_WIDTH = 65

_TIER_LABELS = {
    "heuristic_block": "[T1] Critical (Tier-1 Static Heuristic)",
    "llm_block": "[T2] Medium   (Tier-2 LLM Behavioral)",
    "unknown_block": "[??] Unknown block layer",
}


@dataclass
class IncidentBriefingStats:
    total_count: int = 0
    block_types: Counter = field(default_factory=Counter)
    rules_triggered: Counter = field(default_factory=Counter)
    by_phase: Counter = field(default_factory=Counter)
    recent_events: list[dict[str, str]] = field(default_factory=list)
    parse_errors: int = 0


def _infer_block_type(row: dict[str, Any]) -> str:
    explicit = row.get("block_type")
    if explicit:
        return str(explicit)
    rationale = str(row.get("rationale", ""))
    reason = str(row.get("reason", ""))
    blob = f"{rationale} {reason}".lower()
    if "static heuristic" in blob:
        return "heuristic_block"
    if "llm-judge" in blob or "llm judge" in blob:
        return "llm_block"
    return "unknown_block"


def _normalize_incident_row(row: dict[str, Any]) -> dict[str, str]:
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    ts = str(row.get("timestamp") or meta.get("timestamp") or "N/A")
    user_input = str(
        row.get("input")
        or row.get("payload_preview")
        or "",
    )
    reason = str(row.get("reason") or row.get("rationale") or "No reason provided")
    block_type = _infer_block_type(row)
    return {
        "timestamp": ts,
        "input": user_input,
        "reason": reason,
        "block_type": block_type,
        "phase": str(row.get("phase") or "ingress"),
        "incident_id": str(row.get("incident_id") or ""),
    }


def iter_threat_incidents(path: str | Path) -> Iterator[dict[str, Any]]:
    """Stream JSONL rows; yield only ``threat_incident`` events."""
    file_path = Path(path)
    if not file_path.is_file():
        return
    with file_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "threat_incident":
                yield row


def aggregate_incident_briefing(path: str | Path) -> IncidentBriefingStats:
    """Single-pass stream aggregation (memory-safe for large JSONL)."""
    stats = IncidentBriefingStats()
    for row in iter_threat_incidents(path):
        stats.total_count += 1
        normalized = _normalize_incident_row(row)
        stats.block_types[normalized["block_type"]] += 1
        stats.rules_triggered[normalized["reason"]] += 1
        stats.by_phase[normalized["phase"]] += 1
        stats.recent_events.append(normalized)
    return stats


def _stream_parse_with_errors(path: Path) -> IncidentBriefingStats:
    """Like aggregate but counts malformed lines."""
    stats = IncidentBriefingStats()
    if not path.is_file():
        return stats
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                stats.parse_errors += 1
                continue
            if row.get("type") != "threat_incident":
                continue
            stats.total_count += 1
            normalized = _normalize_incident_row(row)
            stats.block_types[normalized["block_type"]] += 1
            stats.rules_triggered[normalized["reason"]] += 1
            stats.by_phase[normalized["phase"]] += 1
            stats.recent_events.append(normalized)
    return stats


def render_threat_briefing(
    stats: IncidentBriefingStats,
    *,
    file_path: str,
    out: TextIO | None = None,
    recent_limit: int = 3,
) -> None:
    """ASCII terminal briefing for SIEM JSONL."""
    sink = out or sys.stdout
    bar = "=" * _WIDTH
    dash = "-" * _WIDTH

    if stats.total_count == 0:
        sink.write(f"\n[Error] No threat_incident rows in: {file_path}\n")
        if stats.parse_errors:
            sink.write(f"  (skipped {stats.parse_errors} malformed JSONL lines)\n")
        return

    sink.write(f"\n{bar[:21]} SENTINEL THREAT INTEL {bar[:21]}\n")
    sink.write(f"Log Source: {file_path}\n")
    sink.write(f"Total Blocked Incidents: {stats.total_count}\n")
    if stats.parse_errors:
        sink.write(f"Malformed lines skipped: {stats.parse_errors}\n")
    sink.write(f"{dash}\n")

    sink.write("[ Incident Severity Breakdown ]\n")
    for block_type, count in stats.block_types.most_common():
        label = _TIER_LABELS.get(block_type, block_type)
        sink.write(f"  {label:<44}: {count}\n")
    sink.write(f"{dash}\n")

    sink.write("[ Interception Phase ]\n")
    for phase, count in stats.by_phase.most_common():
        sink.write(f"  {phase:<44}: {count}\n")
    sink.write(f"{dash}\n")

    sink.write("[ Top Triggered Defense Rules ]\n")
    for rule, count in stats.rules_triggered.most_common(5):
        rule_short = rule if len(rule) <= 45 else rule[:42] + "..."
        sink.write(f"  - {rule_short:<45}: {count} times\n")
    sink.write(f"{dash}\n")

    sink.write(f"[ Recent Intercepted Streams (Latest {recent_limit}) ]\n")
    for ev in stats.recent_events[-recent_limit:]:
        prefix = "[T1]" if ev["block_type"] == "heuristic_block" else "[T2]"
        if ev["block_type"] == "unknown_block":
            prefix = "[??]"
        truncated = ev["input"] if len(ev["input"]) <= 40 else ev["input"][:37] + "..."
        sink.write(f"  {prefix} [{ev['timestamp']}] Input: '{truncated}'\n")
        sink.write(f"     Reason: {ev['reason']}\n")
    sink.write(f"{bar}\n\n")


def summarize_incidents(file_path: str, *, out: TextIO | None = None) -> IncidentBriefingStats:
    """
    Stream-parse JSONL, aggregate block tiers, print ASCII briefing.

    Returns stats for programmatic use / tests.
    """
    path = Path(file_path)
    if not path.exists():
        sink = out or sys.stdout
        sink.write(f"[Error] Threat intel log not found at: {file_path}\n")
        return IncidentBriefingStats()

    stats = _stream_parse_with_errors(path)
    render_threat_briefing(stats, file_path=file_path, out=out)
    return stats


def print_threat_briefing(file_path: str) -> IncidentBriefingStats:
    """CLI entry: print briefing to stdout."""
    return summarize_incidents(file_path)
