"""Guard interception errors."""

from __future__ import annotations

from sentinel_eval.guard.models import SentinelJudgeVerdict


class SentinelGuardBlocked(Exception):
    """Raised when ``raise_on_block=True`` and a guard phase fails."""

    def __init__(
        self,
        phase: str,
        verdict: SentinelJudgeVerdict,
        *,
        message: str | None = None,
    ) -> None:
        self.phase = phase
        self.verdict = verdict
        super().__init__(message or f"Sentinel guard blocked at {phase}: {verdict.rationale}")
