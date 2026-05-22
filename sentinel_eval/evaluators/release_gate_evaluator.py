from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import (
    ReleaseGateEvalResult,
    RougeScores,
    SchemaValidationResult,
    SemanticEvalResult,
)
from sentinel_eval.evaluators.protocol import CaseEvalContext
from sentinel_eval.evaluators.release_gate_checker import ReleaseGate


class ReleaseGateEvaluator:
    """Per-case release gate (schema + label + semantic alignment)."""

    evaluator_id = "release_gate"

    def __init__(self, gate: ReleaseGate | None = None):
        self.gate = gate or ReleaseGate()

    def evaluate(
        self,
        *,
        schema_validation: SchemaValidationResult,
        prediction_match: bool | None,
        rouge: RougeScores,
        semantic_eval: SemanticEvalResult | None = None,
        needs_review: bool = False,
    ) -> ReleaseGateEvalResult:
        settings = get_settings()
        sem_dict = semantic_eval.model_dump() if semantic_eval else {}
        release_pass = self.gate.per_case_pass(
            schema_validation=schema_validation,
            prediction_match=prediction_match,
            rouge=rouge,
            semantic_eval=sem_dict,
            needs_review=needs_review,
        )
        return ReleaseGateEvalResult(
            release_pass=release_pass,
            release_rouge_l_threshold=settings.release_rouge_l_threshold,
        )

    def evaluate_context(self, ctx: CaseEvalContext) -> ReleaseGateEvalResult:
        sem = ctx.extra.get("semantic_eval")
        schema_validation = ctx.extra.get("schema_validation")
        if schema_validation is None:
            from sentinel_eval.domain.models import SchemaValidationResult

            schema_validation = SchemaValidationResult(is_valid=ctx.schema_valid)
        return self.evaluate(
            schema_validation=schema_validation,
            prediction_match=ctx.extra.get("prediction_match"),
            rouge=sem.rouge if sem else None,
            semantic_eval=sem,
            needs_review=ctx.case.needs_review,
        )
