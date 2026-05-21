from typing import Any

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import RougeScores, SchemaValidationResult
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.metrics.release_gate import (
    ADVISORY_GATE_THRESHOLDS,
    case_release_pass,
    evaluate_advisory_gate,
    evaluate_release_gate,
)


class ReleaseGate:
    """Per-case and suite-level release / advisory gates."""

    def __init__(self, rouge_threshold: float | None = None):
        settings = get_settings()
        self.rouge_threshold = (
            rouge_threshold if rouge_threshold is not None else settings.release_rouge_l_threshold
        )

    def per_case_pass(
        self,
        *,
        schema_validation: SchemaValidationResult,
        prediction_match: bool | None,
        rouge: RougeScores,
        needs_review: bool = False,
    ) -> bool | None:
        if needs_review or prediction_match is None:
            return None
        return case_release_pass(
            {
                "needs_review": False,
                "prediction_match": prediction_match,
                "schema_validation": schema_validation.to_dict(),
                "rouge": rouge.to_dict(),
            },
            rouge_threshold=self.rouge_threshold,
        )

    def evaluate_suite(
        self,
        metrics: SuiteMetrics | dict[str, Any],
        results: list[Any],
    ) -> tuple[bool, list[str]]:
        return evaluate_release_gate(metrics, results)

    def evaluate_advisory(self, metrics: SuiteMetrics) -> tuple[bool, list[str]]:
        return evaluate_advisory_gate(metrics)

    @property
    def advisory_thresholds(self) -> dict[str, float]:
        return dict(ADVISORY_GATE_THRESHOLDS)
