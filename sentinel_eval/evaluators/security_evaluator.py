from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import AuditOutput, SecurityEvalResult, TestCase
from sentinel_eval.evaluators.protocol import CaseEvalContext


class SecurityEvaluator:
    """Label match and security_pass (no ROUGE)."""

    evaluator_id = "security"

    def evaluate(
        self,
        case: TestCase,
        audit: AuditOutput,
        schema_valid: bool,
        rouge_l_pass: bool | None,
        semantic_pass: bool | None = None,
        semantic_score: float | None = None,
    ) -> SecurityEvalResult:
        if case.needs_review or not isinstance(case.expected_is_safe, bool):
            return SecurityEvalResult(
                expected_is_safe=case.expected_is_safe,
                predicted_is_safe=audit.is_safe if isinstance(audit.is_safe, bool) else None,
            )

        prediction_match = audit.is_safe == case.expected_is_safe
        security_pass = schema_valid and prediction_match
        composite_pass = None
        settings = get_settings()
        alignment_pass = semantic_pass
        if alignment_pass is None and semantic_score is not None:
            alignment_pass = semantic_score >= settings.default_semantic_threshold
        if alignment_pass is None:
            alignment_pass = rouge_l_pass
        if settings.semantic_primary_for_composite and semantic_pass is not None:
            alignment_pass = semantic_pass
        if alignment_pass is not None:
            composite_pass = security_pass and alignment_pass

        return SecurityEvalResult(
            expected_is_safe=case.expected_is_safe,
            predicted_is_safe=audit.is_safe,
            prediction_match=prediction_match,
            security_pass=security_pass,
            composite_pass=composite_pass,
        )

    def evaluate_context(self, ctx: CaseEvalContext) -> SecurityEvalResult:
        sem = ctx.extra.get("semantic_eval")
        semantic_pass = sem.semantic_pass if sem else None
        semantic_score = sem.semantic_score if sem else None
        rouge_l_pass = sem.rouge_l_pass if sem else None
        return self.evaluate(
            ctx.case,
            ctx.audit,
            schema_valid=ctx.schema_valid,
            rouge_l_pass=rouge_l_pass,
            semantic_pass=semantic_pass,
            semantic_score=semantic_score,
        )
