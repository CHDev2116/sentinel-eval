"""Typed aggregate metrics for a benchmark run."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from sentinel_eval.prompts.audit import PROMPT_VERSION


class ConfusionMatrix(BaseModel):
    columns: list[str] = Field(
        default_factory=lambda: ["predicted safe", "predicted unsafe"],
    )
    rows: list[str] = Field(default_factory=lambda: ["actual safe", "actual unsafe"])
    cell_labels: list[list[str]] = Field(
        default_factory=lambda: [["TP", "FN"], ["FP", "TN"]],
    )
    counts: list[list[int]] = Field(default_factory=lambda: [[0, 0], [0, 0]])


class ClassificationMetrics(BaseModel):
    confusion_matrix: ConfusionMatrix = Field(default_factory=ConfusionMatrix)
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    scored_cases: int = 0
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    false_positive_rate: float | None = None
    specificity: float | None = None
    precision_pct: float | None = None
    recall_pct: float | None = None
    f1_pct: float | None = None
    false_positive_rate_pct: float | None = None
    specificity_pct: float | None = None
    safe_precision: float | None = None
    safe_precision_pct: float | None = None
    benign_specificity: float | None = None
    benign_specificity_pct: float | None = None
    injection_recall: float | None = None
    injection_recall_pct: float | None = None


class CalibrationMetrics(BaseModel):
    """Suite-level calibration coverage (when models emit risk scores)."""

    cases_with_risk_score: int = 0
    cases_with_confidence: int = 0
    cases_with_uncertainty: int = 0
    mean_risk_score: float | None = None
    mean_confidence: float | None = None
    mean_uncertainty: float | None = None
    high_risk_on_attacks_pct: float | None = None
    low_risk_on_benign_pct: float | None = None


class TagMetrics(BaseModel):
    """Per-tag subset (subset of suite fields)."""

    cases: int = 0
    schema_valid_pct: float | None = None
    label_match_pct: float | None = None
    security_pass_pct: float | None = None
    composite_pass_pct: float | None = None
    ensemble_pass_pct: float | None = None
    release_pass_pct: float | None = None
    avg_rouge_l_f1: float = 0.0
    injection_recall_pct: float | None = None
    benign_specificity_pct: float | None = None
    precision_pct: float | None = None
    f1_pct: float | None = None
    false_positive_rate_pct: float | None = None
    classification: ClassificationMetrics | None = None


class SuiteMetrics(BaseModel):
    """Leaderboard-style metrics for one run."""

    cases_run: int = 0
    prompt_version: str = PROMPT_VERSION
    schema_valid_pct: float | None = None
    schema_valid: str = "0/0"
    label_match_pct: float | None = None
    label_match: str = "n/a"
    security_pass_pct: float | None = None
    security_pass: str = "0/0"
    composite_pass_pct: float | None = None
    composite_pass: str = "0/0"
    ensemble_pass_pct: float | None = None
    ensemble_pass: str = "n/a"
    release_pass_pct: float | None = None
    release_pass: str = "0/0"
    release_rouge_l_threshold: float = 0.70
    avg_rouge_l_f1: float = 0.0
    injection_recall_pct: float | None = None
    injection_recall: str = "n/a"
    benign_specificity_pct: float | None = None
    benign_specificity: str = "n/a"
    precision_pct: float | None = None
    precision: str = "n/a"
    f1_pct: float | None = None
    f1: float | None = None
    false_positive_rate_pct: float | None = None
    false_positive_rate: float | None = None
    classification: ClassificationMetrics | None = None
    calibration: CalibrationMetrics | None = None
    by_tag: dict[str, TagMetrics] = Field(default_factory=dict)

    @field_validator("by_tag", mode="before")
    @classmethod
    def coerce_by_tag(cls, value: Any) -> dict[str, TagMetrics]:
        if not value:
            return {}
        if not isinstance(value, dict):
            return {}
        out: dict[str, TagMetrics] = {}
        for tag, raw in value.items():
            if isinstance(raw, TagMetrics):
                out[tag] = raw
            elif isinstance(raw, dict):
                clf = raw.get("classification")
                payload = dict(raw)
                if isinstance(clf, dict):
                    payload["classification"] = ClassificationMetrics.model_validate(clf)
                out[tag] = TagMetrics.model_validate(payload)
        return out

    @field_validator("calibration", mode="before")
    @classmethod
    def coerce_calibration(cls, value: Any) -> CalibrationMetrics | None:
        if value is None:
            return None
        if isinstance(value, CalibrationMetrics):
            return value
        if isinstance(value, dict):
            return CalibrationMetrics.model_validate(value)
        return None

    @field_validator("classification", mode="before")
    @classmethod
    def coerce_classification(cls, value: Any) -> ClassificationMetrics | None:
        if value is None:
            return None
        if isinstance(value, ClassificationMetrics):
            return value
        if isinstance(value, dict):
            return ClassificationMetrics.model_validate(value)
        return None

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible dict (legacy report meta.metrics shape)."""
        return self.model_dump()
