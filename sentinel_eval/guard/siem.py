"""Threat-intelligence JSONL sink for production guard interceptions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from sentinel_eval.config import get_settings
from sentinel_eval.guard.models import SentinelJudgeVerdict

_INGRESS_VECTORS = (
    "Prompt Injection / Jailbreak",
    "Instruction Override",
    "Indirect Prompt Injection",
)
_EGRESS_VECTORS = (
    "PII / Secret Leak",
    "Credential Exfiltration",
    "System Prompt Leak",
)


class ThreatIncidentMeta(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    evaluator_model: str = "unknown"
    target_agent: str = "unknown"
    environment: str = "production"


class ThreatIncidentRecord(BaseModel):
    """One blocked request — append-only SIEM row."""

    type: str = "threat_incident"
    incident_id: str = Field(
        default_factory=lambda: f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
    )
    meta: ThreatIncidentMeta = Field(default_factory=ThreatIncidentMeta)
    phase: str = Field(description="ingress | egress")
    attack_vector: str = ""
    payload_preview: str = ""
    agent_response_preview: str = ""
    security_metrics: dict[str, str] = Field(default_factory=dict)
    adversarial_tier: str = "High"
    action: str = "blocked"
    rationale: str = ""
    block_type: str = Field(
        default="unknown_block",
        description="Funnel layer: heuristic_block | llm_block",
    )
    reason: str = Field(
        default="",
        description="Block reason: Static Heuristic Match | LLM-Judge Behavioral Match",
    )
    timestamp: str = Field(
        default="",
        description="ISO-8601 event time (duplicate of meta.timestamp for SIEM parsers).",
    )
    input: str = Field(
        default="",
        description="Truncated user payload (alias of payload_preview for dashboards).",
    )

    def to_jsonl_line(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)


def _infer_attack_vector(phase: str, user_input: str, verdict: SentinelJudgeVerdict) -> str:
    text = f"{user_input} {verdict.rationale}".lower()
    if phase == "egress":
        if "pii" in text or "ssn" in text:
            return _EGRESS_VECTORS[0]
        if "key" in text or "token" in text or "secret" in text:
            return _EGRESS_VECTORS[1]
        return _EGRESS_VECTORS[2]
    if "html" in text or "indirect" in text:
        return _INGRESS_VECTORS[2]
    if "ignore" in text or "override" in text or "jailbreak" in text:
        return _INGRESS_VECTORS[1]
    return _INGRESS_VECTORS[0]


def _adversarial_tier(phase: str, user_input: str) -> str:
    lower = user_input.lower()
    if phase == "egress":
        return "Critical"
    if any(k in lower for k in ("ignore all prior", "system prompt", "dan mode", "jailbreak")):
        return "Critical"
    return "High"


def build_threat_incident(
    *,
    phase: str,
    user_input: str,
    verdict: SentinelJudgeVerdict,
    target_agent: str,
    evaluator_model: str,
    agent_response: str | None = None,
    environment: str = "production",
    payload_max_len: int = 500,
    block_type: str = "unknown_block",
    reason: str = "",
) -> ThreatIncidentRecord:
    preview = user_input[:payload_max_len]
    agent_preview = (agent_response or "")[:payload_max_len]
    metrics = verdict.metrics
    recorded_at = datetime.now(timezone.utc).isoformat()
    block_reason = reason or verdict.rationale
    return ThreatIncidentRecord(
        meta=ThreatIncidentMeta(
            timestamp=recorded_at,
            evaluator_model=evaluator_model,
            target_agent=target_agent,
            environment=environment,
        ),
        phase=phase,
        attack_vector=_infer_attack_vector(phase, user_input, verdict),
        payload_preview=preview,
        agent_response_preview=agent_preview,
        security_metrics={
            "ingress_breach": metrics.ingress_breach,
            "egress_leak": metrics.egress_leak,
            "refusal_compliance": metrics.refusal_compliance,
            "is_safe": "false",
        },
        adversarial_tier=_adversarial_tier(phase, user_input),
        rationale=verdict.rationale,
        block_type=block_type,
        reason=block_reason,
        timestamp=recorded_at,
        input=preview,
    )


def _resolve_paths(
    events_path: Path | None,
    latest_path: Path | None,
) -> tuple[Path, Path]:
    settings = get_settings()
    events = events_path or Path(settings.threat_intel_events_path)
    latest = latest_path or Path(settings.threat_intel_latest_path)
    return events, latest


def _append_line(path: Path, line: str, *, meta: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if meta and (not path.exists() or path.stat().st_size == 0):
        header = {"type": "meta", **meta}
        with path.open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(header, ensure_ascii=False) + "\n")
    with path.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def append_threat_incident(
    incident: ThreatIncidentRecord | dict[str, Any],
    *,
    events_path: Path | None = None,
    latest_path: Path | None = None,
) -> Path:
    """
    Append one interception to the SIEM JSONL stream(s).

    Writes to ``reports/threat_intel/events.jsonl`` and mirrors to
    ``reports/threat_latest.jsonl`` (append-only).
    """
    record = (
        incident
        if isinstance(incident, ThreatIncidentRecord)
        else ThreatIncidentRecord.model_validate(incident)
    )
    events, latest = _resolve_paths(events_path, latest_path)
    line = record.to_jsonl_line()
    meta_header = {
        "stream": "sentinel-threat-intel",
        "schema_version": "1.0",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _append_line(events, line, meta=meta_header)
    _append_line(latest, line, meta=meta_header)
    return events
