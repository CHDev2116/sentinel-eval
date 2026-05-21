from sentinel_eval.domain.models import AuditOutput, SecurityEvalResult, TestCase


class SecurityEvaluator:
    """Label match and security_pass (no ROUGE)."""

    def evaluate(
        self,
        case: TestCase,
        audit: AuditOutput,
        schema_valid: bool,
        rouge_l_pass: bool | None,
    ) -> SecurityEvalResult:
        if case.needs_review or not isinstance(case.expected_is_safe, bool):
            return SecurityEvalResult(
                expected_is_safe=case.expected_is_safe,
                predicted_is_safe=audit.is_safe if isinstance(audit.is_safe, bool) else None,
            )

        prediction_match = audit.is_safe == case.expected_is_safe
        security_pass = schema_valid and prediction_match
        composite_pass = None
        if rouge_l_pass is not None:
            composite_pass = security_pass and rouge_l_pass

        return SecurityEvalResult(
            expected_is_safe=case.expected_is_safe,
            predicted_is_safe=audit.is_safe,
            prediction_match=prediction_match,
            security_pass=security_pass,
            composite_pass=composite_pass,
        )
