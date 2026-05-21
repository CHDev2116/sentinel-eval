import unittest

from sentinel_eval.domain.models import (
    AuditOutput,
    CaseEvaluationResult,
    EnsembleEvalResult,
    SchemaValidationResult,
)
from sentinel_eval.metrics.aggregation import aggregate_metrics


class TestEnsembleMetrics(unittest.TestCase):
    def _case(
        self,
        case_id: str,
        *,
        ensemble_pass: bool | None,
        prediction_match: bool = True,
    ) -> CaseEvaluationResult:
        ensemble = None
        if ensemble_pass is not None:
            ensemble = EnsembleEvalResult(
                ensemble_pass=ensemble_pass,
                prediction_match=ensemble_pass,
                mode="heuristic",
            )
        return CaseEvaluationResult(
            case_id=case_id,
            parsed_output=AuditOutput(is_safe=True, reasoning="ok", security_status="Pass"),
            schema_validation=SchemaValidationResult(is_valid=True),
            prediction_match=prediction_match,
            security_pass=prediction_match,
            ensemble_eval=ensemble,
        )

    def test_ensemble_pass_pct_when_present(self):
        metrics = aggregate_metrics(
            [
                self._case("a", ensemble_pass=True),
                self._case("b", ensemble_pass=True),
                self._case("c", ensemble_pass=False),
            ]
        )
        self.assertEqual(metrics.ensemble_pass, "2/3")
        self.assertEqual(metrics.ensemble_pass_pct, 66.7)

    def test_ensemble_pass_na_without_ensemble(self):
        metrics = aggregate_metrics([self._case("a", ensemble_pass=None)])
        self.assertEqual(metrics.ensemble_pass, "n/a")
        self.assertIsNone(metrics.ensemble_pass_pct)


if __name__ == "__main__":
    unittest.main()
