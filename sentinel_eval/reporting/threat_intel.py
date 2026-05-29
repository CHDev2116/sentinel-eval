"""Load and aggregate threat-intel JSONL for incident dashboards."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ThreatIntelSummary(BaseModel):
    """SIEM-style rollup — interceptions, not benchmark pass rates."""

    total_interceptions: int = 0
    ingress_blocks: int = 0
    egress_blocks: int = 0
    ingress_block_pct: float | None = None
    egress_block_pct: float | None = None
    block_rate_pct: float | None = Field(
        default=None,
        description="Share of logged events that were blocked (always 100% for pure block logs).",
    )
    by_tier: dict[str, int] = Field(default_factory=dict)
    by_attack_vector: dict[str, int] = Field(default_factory=dict)
    by_target_agent: dict[str, int] = Field(default_factory=dict)
    stream_meta: dict[str, Any] = Field(default_factory=dict)


def _pct(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return round(100.0 * num / den, 1)


def load_threat_incidents(path: str | Path) -> list[dict[str, Any]]:
    """Parse JSONL; skip ``type=meta`` header lines."""
    file_path = Path(path)
    if not file_path.is_file():
        return []
    incidents: list[dict[str, Any]] = []
    stream_meta: dict[str, Any] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        row_type = row.get("type")
        if row_type == "meta":
            stream_meta = row
            continue
        if row_type == "threat_incident":
            if stream_meta and "stream_meta" not in row:
                row["_stream_meta"] = stream_meta
            incidents.append(row)
    return incidents


def aggregate_threat_intel(incidents: list[dict[str, Any]]) -> ThreatIntelSummary:
    """Compute incident dashboard metrics from blocked-event rows."""
    n = len(incidents)
    if n == 0:
        return ThreatIntelSummary()

    ingress = sum(1 for i in incidents if i.get("phase") == "ingress")
    egress = sum(1 for i in incidents if i.get("phase") == "egress")
    by_tier: dict[str, int] = {}
    by_vector: dict[str, int] = {}
    by_agent: dict[str, int] = {}

    for item in incidents:
        tier = str(item.get("adversarial_tier") or "Unknown")
        by_tier[tier] = by_tier.get(tier, 0) + 1
        vector = str(item.get("attack_vector") or "unspecified")
        by_vector[vector] = by_vector.get(vector, 0) + 1
        meta = item.get("meta") or {}
        agent = str(meta.get("target_agent") or "unknown")
        by_agent[agent] = by_agent.get(agent, 0) + 1

    stream_meta = {}
    if incidents and "_stream_meta" in incidents[0]:
        stream_meta = incidents[0]["_stream_meta"]

    return ThreatIntelSummary(
        total_interceptions=n,
        ingress_blocks=ingress,
        egress_blocks=egress,
        ingress_block_pct=_pct(ingress, n),
        egress_block_pct=_pct(egress, n),
        block_rate_pct=100.0 if n > 0 else None,
        by_tier=dict(sorted(by_tier.items())),
        by_attack_vector=dict(sorted(by_vector.items(), key=lambda kv: -kv[1])),
        by_target_agent=dict(sorted(by_agent.items())),
        stream_meta=stream_meta,
    )


def log_threat_intel_dashboard(summary: ThreatIntelSummary, *, source: str) -> None:
    """Human-readable SIEM summary for ``sentinel-summarize --incidents``."""
    logger.info("=== Security Incident Dashboard ===")
    logger.info("Source: %s", source)
    if summary.stream_meta:
        logger.info("Stream: %s", summary.stream_meta.get("stream", "n/a"))
    logger.info(
        "Total interceptions: %s (Ingress %s | Egress %s)",
        summary.total_interceptions,
        summary.ingress_blocks,
        summary.egress_blocks,
    )
    if summary.total_interceptions:
        logger.info(
            "Ingress blocked: %s (%s%%) | Egress masked: %s (%s%%)",
            summary.ingress_blocks,
            summary.ingress_block_pct,
            summary.egress_blocks,
            summary.egress_block_pct,
        )
        logger.info("System block rate: %s%%", summary.block_rate_pct)
    if summary.by_attack_vector:
        logger.info("Top attack vectors:")
        for vector, count in list(summary.by_attack_vector.items())[:5]:
            logger.info("  - %s: %s", vector, count)
    if summary.by_tier:
        logger.info("By adversarial tier: %s", summary.by_tier)
    if summary.by_target_agent:
        logger.info("By target agent: %s", summary.by_target_agent)


def format_incident_markdown(summary: ThreatIntelSummary, source: str) -> str:
    """Markdown row for CI / dashboards."""
    ingress = summary.ingress_block_pct if summary.ingress_block_pct is not None else "—"
    egress = summary.egress_block_pct if summary.egress_block_pct is not None else "—"
    return (
        f"| `{source}` | **{summary.total_interceptions}** | "
        f"**{summary.ingress_blocks}** ({ingress}%) | "
        f"**{summary.egress_blocks}** ({egress}%) | "
        f"**{summary.block_rate_pct}%** |"
    )
