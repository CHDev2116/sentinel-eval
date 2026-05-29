"""Typed Sentinel-Judge verdict models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

YesNo = Literal["Yes", "No"]


def _coerce_yes_no(value: Any) -> YesNo:
    text = str(value).strip().lower()
    if text in {"yes", "true", "1", "y"}:
        return "Yes"
    return "No"


class SentinelJudgeMetrics(BaseModel):
    ingress_breach: YesNo = "No"
    egress_leak: YesNo = "No"
    refusal_compliance: YesNo = "No"

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None) -> SentinelJudgeMetrics:
        if not raw:
            return cls()
        return cls(
            ingress_breach=_coerce_yes_no(raw.get("ingress_breach", "No")),
            egress_leak=_coerce_yes_no(raw.get("egress_leak", "No")),
            refusal_compliance=_coerce_yes_no(raw.get("refusal_compliance", "No")),
        )


class SentinelJudgeVerdict(BaseModel):
    metrics: SentinelJudgeMetrics = Field(default_factory=SentinelJudgeMetrics)
    rationale: str = ""

    @property
    def ingress_breach(self) -> bool:
        return self.metrics.ingress_breach == "Yes"

    @property
    def egress_leak(self) -> bool:
        return self.metrics.egress_leak == "Yes"
