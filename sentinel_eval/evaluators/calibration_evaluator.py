from sentinel_eval.domain.models import AuditOutput, CalibrationEvalResult
from sentinel_eval.evaluators.protocol import CaseEvalContext


def _clamp01(value) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v < 0.0 or v > 1.0:
        return None
    return round(v, 4)


class CalibrationEvaluator:
    """
    Extract optional calibration fields from auditor output.

    Models may emit e.g. {"risk_score": 0.92, "confidence": 0.88, "uncertainty": 0.1}.
    """

    evaluator_id = "calibration"

    def evaluate(self, audit: AuditOutput) -> CalibrationEvalResult:
        risk = _clamp01(audit.risk_score)
        confidence = _clamp01(audit.confidence)
        uncertainty = _clamp01(audit.uncertainty)
        has = any(v is not None for v in (risk, confidence, uncertainty))
        return CalibrationEvalResult(
            risk_score=risk,
            confidence=confidence,
            uncertainty=uncertainty,
            has_calibration=has,
        )

    def evaluate_context(self, ctx: CaseEvalContext) -> CalibrationEvalResult:
        return self.evaluate(ctx.audit)
