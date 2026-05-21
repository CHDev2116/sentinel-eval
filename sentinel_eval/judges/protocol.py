"""Judge ensemble protocol (post-audit, hidden rubric)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from sentinel_eval.domain.models import AuditOutput


class JudgeVerdict(BaseModel):
    judge_id: str
    dimension: str
    weight: float = 1.0
    score: float = Field(ge=0.0, le=1.0, description="1 = pass rubric dimension")
    is_safe_vote: bool | None = None
    reasoning: str = ""
    mode: str = "heuristic"


class EnsembleEvalResult(BaseModel):
    verdicts: list[JudgeVerdict] = Field(default_factory=list)
    weighted_score: float = 0.0
    weighted_is_safe: bool | None = None
    agreement_rate: float = 0.0
    ensemble_pass: bool | None = None
    prediction_match: bool | None = None
    mode: str = "heuristic"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


@runtime_checkable
class Judge(Protocol):
    judge_id: str
    dimension: str
    weight: float

    def evaluate(self, thread: str, audit: AuditOutput) -> JudgeVerdict: ...
