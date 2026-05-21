from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import ReleaseGateEvalResult, RougeScores, SchemaValidationResult
from sentinel_eval.evaluators.release_gate_checker import ReleaseGate


class ReleaseGateEvaluator:
    """Per-case release gate (schema + label + ROUGE-L threshold)."""

    def __init__(self, gate: ReleaseGate | None = None):
        self.gate = gate or ReleaseGate()

    def evaluate(
        self,
        *,
        schema_validation: SchemaValidationResult,
        prediction_match: bool | None,
        rouge: RougeScores,
        needs_review: bool = False,
    ) -> ReleaseGateEvalResult:
        settings = get_settings()
        release_pass = self.gate.per_case_pass(
            schema_validation=schema_validation,
            prediction_match=prediction_match,
            rouge=rouge,
            needs_review=needs_review,
        )
        return ReleaseGateEvalResult(
            release_pass=release_pass,
            release_rouge_l_threshold=settings.release_rouge_l_threshold,
        )
