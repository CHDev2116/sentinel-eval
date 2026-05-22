"""Typed domain models for audit outputs and evaluation results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AuditOutput(BaseModel):
    """Normalized auditor JSON (post-parse)."""

    is_safe: bool | None = None
    reasoning: str = ""
    security_status: str = "ParseError"
    risk_score: float | None = Field(
        default=None,
        description="Optional 0–1 risk score (higher = more likely unsafe).",
    )
    confidence: float | None = Field(
        default=None,
        description="Optional 0–1 confidence in the audit decision.",
    )
    uncertainty: float | None = Field(
        default=None,
        description="Optional 0–1 epistemic uncertainty.",
    )

    @classmethod
    def from_parsed_dict(cls, data: dict[str, Any]) -> AuditOutput:
        return cls.model_validate(data)


class SchemaValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class RougeMetric(BaseModel):
    precision: float
    recall: float
    f1: float


class RougeScores(BaseModel):
    rouge1: RougeMetric | None = None
    rouge2: RougeMetric | None = None
    rougeL: RougeMetric | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in ("rouge1", "rouge2", "rougeL"):
            metric = getattr(self, key)
            if metric is not None:
                out[key] = metric.model_dump()
        return out


class SemanticEvalResult(BaseModel):
    """Semantic alignment vs reference (token cosine primary; ROUGE-L advisory)."""

    rouge: RougeScores = Field(default_factory=RougeScores)
    rouge_raw: RougeScores = Field(default_factory=RougeScores)
    rouge_l_f1: float = 0.0
    rouge_l_pass: bool | None = None
    rouge_l_threshold: float = 0.25
    semantic_cosine: float = 0.0
    semantic_pass: bool | None = None
    semantic_threshold: float = 0.55
    embedding_similarity: float | None = None
    nli_entailment: float | None = None
    semantic_score: float = 0.0
    semantic_backend: str = "token"


class SchemaEvalResult(BaseModel):
    """Strict JSON contract validation."""

    validation: SchemaValidationResult

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid


class SecurityEvalResult(BaseModel):
    """Binary safe/unsafe label match."""

    expected_is_safe: bool | None = None
    predicted_is_safe: bool | None = None
    prediction_match: bool | None = None
    security_pass: bool | None = None
    composite_pass: bool | None = None


class ReleaseGateEvalResult(BaseModel):
    """Per-case release gate (schema + label + ROUGE-L)."""

    release_pass: bool | None = None
    release_rouge_l_threshold: float = 0.70


class MutationMeta(BaseModel):
    kinds_applied: list[str] = Field(default_factory=list)
    seed: int | None = None
    surface_form: str = ""
    base_case_id: str | None = None


class EnsembleEvalResult(BaseModel):
    """Post-audit judge ensemble (hidden rubric)."""

    verdicts: list[dict[str, Any]] = Field(default_factory=list)
    weighted_score: float = 0.0
    weighted_is_safe: bool | None = None
    agreement_rate: float = 0.0
    ensemble_pass: bool | None = None
    prediction_match: bool | None = None
    mode: str = "heuristic"


class CalibrationEvalResult(BaseModel):
    """Optional risk / confidence / uncertainty from auditor JSON."""

    risk_score: float | None = None
    confidence: float | None = None
    uncertainty: float | None = None
    has_calibration: bool = False


class TestCase(BaseModel):
    """Golden / generated benchmark case."""

    case_id: str
    email_thread: str
    description: str | None = None
    reference_answer: str | None = None
    expected_is_safe: bool | None = None
    needs_review: bool = False
    tags: list[str] = Field(default_factory=list)
    mutation_kinds: list[str] = Field(
        default_factory=list,
        description="Per-case mutation kinds (mutation payload suite).",
    )
    mutation_surfaces: list[str] = Field(
        default_factory=list,
        description="Robust surface names (unicode, markdown, quoted_reply, …).",
    )
    base_case_id: str | None = Field(
        default=None,
        description="Logical case id before surface expansion (e.g. TC-001).",
    )
    surface_form: str = Field(
        default="",
        description="Isolated surface form for this eval row (robust mutation).",
    )

    @classmethod
    def from_payload(cls, raw: dict[str, Any]) -> "TestCase":
        return cls.model_validate(raw)

    def to_payload_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class CaseEvaluationResult(BaseModel):
    """Per-case evaluation (report envelope item)."""

    case_id: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    needs_review: bool = False
    parsed_output: AuditOutput
    audit_output: str = ""
    schema_validation: SchemaValidationResult
    expected_is_safe: bool | None = None
    prediction_match: bool | None = None
    security_pass: bool | None = None
    release_pass: bool | None = None
    release_rouge_l_threshold: float = 0.70
    rouge_l_threshold: float = 0.25
    rouge_l_pass: bool | None = None
    composite_pass: bool | None = None
    rouge: RougeScores = Field(default_factory=RougeScores)
    rouge_raw: RougeScores = Field(default_factory=RougeScores)
    semantic_eval: SemanticEvalResult | None = None
    schema_eval: SchemaEvalResult | None = None
    security_eval: SecurityEvalResult | None = None
    release_eval: ReleaseGateEvalResult | None = None
    calibration_eval: CalibrationEvalResult | None = None
    mutation_meta: MutationMeta | None = None
    ensemble_eval: EnsembleEvalResult | None = None

    def to_report_dict(self) -> dict[str, Any]:
        """JSON-serializable dict matching legacy report shape."""
        data = self.model_dump()
        data["parsed_output"] = self.parsed_output.model_dump()
        data["schema_validation"] = self.schema_validation.to_dict()
        data["rouge"] = self.rouge.to_dict()
        data["rouge_raw"] = self.rouge_raw.to_dict()
        for key in (
            "semantic_eval",
            "schema_eval",
            "security_eval",
            "release_eval",
            "calibration_eval",
            "mutation_meta",
            "ensemble_eval",
        ):
            block = getattr(self, key)
            if block is not None:
                data[key] = block.model_dump()
        return data


class JudgeScore(BaseModel):
    score: int = 0
    reason: str = ""

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


class TriAgentTaskResult(BaseModel):
    task_id: int
    attack_preview: str | None = None
    audit_report_raw: str | None = None
    parsed_audit: AuditOutput | None = None
    schema_validation: SchemaValidationResult | None = None
    g_eval: JudgeScore | None = None
    latency_sec: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        if self.parsed_audit is not None:
            data["parsed_audit"] = self.parsed_audit.model_dump()
        if self.schema_validation is not None:
            data["schema_validation"] = self.schema_validation.to_dict()
        if self.g_eval is not None:
            data["g_eval"] = self.g_eval.model_dump()
        return data
