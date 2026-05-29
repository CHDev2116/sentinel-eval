"""Runtime guardrails — async decorator around target-agent calls."""

from sentinel_eval.guard.decorator import sentinel_guard
from sentinel_eval.guard.exceptions import SentinelGuardBlocked
from sentinel_eval.guard.funnel import (
    GuardDecision,
    evaluate_egress_funnel,
    evaluate_ingress_funnel,
    sentinel_guard_logic,
)
from sentinel_eval.guard.judge import HeuristicSentinelJudge, OllamaSentinelJudge
from sentinel_eval.guard.models import SentinelJudgeMetrics, SentinelJudgeVerdict
from sentinel_eval.guard.siem import (
    ThreatIncidentRecord,
    append_threat_incident,
    build_threat_incident,
)

__all__ = [
    "sentinel_guard",
    "sentinel_guard_logic",
    "GuardDecision",
    "evaluate_ingress_funnel",
    "evaluate_egress_funnel",
    "SentinelGuardBlocked",
    "HeuristicSentinelJudge",
    "OllamaSentinelJudge",
    "SentinelJudgeMetrics",
    "SentinelJudgeVerdict",
    "ThreatIncidentRecord",
    "append_threat_incident",
    "build_threat_incident",
]
