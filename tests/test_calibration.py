import unittest

from sentinel_eval.domain.models import AuditOutput
from sentinel_eval.evaluators.calibration_evaluator import CalibrationEvaluator
from sentinel_eval.metrics.calibration import aggregate_calibration_metrics


class TestCalibration(unittest.TestCase):
    def test_extract_optional_scores(self):
        audit = AuditOutput(
            is_safe=False,
            reasoning="x",
            security_status="Fail",
            risk_score=0.92,
            confidence=0.88,
        )
        cal = CalibrationEvaluator().evaluate(audit)
        self.assertTrue(cal.has_calibration)
        self.assertEqual(cal.risk_score, 0.92)

    def test_aggregate_calibration_suite(self):
        results = [
            {
                "expected_is_safe": False,
                "calibration_eval": {"risk_score": 0.9, "has_calibration": True},
            },
            {
                "expected_is_safe": True,
                "calibration_eval": {"risk_score": 0.1, "has_calibration": True},
            },
        ]
        suite = aggregate_calibration_metrics(results)
        self.assertEqual(suite.cases_with_risk_score, 2)
        self.assertEqual(suite.high_risk_on_attacks_pct, 100.0)
        self.assertEqual(suite.low_risk_on_benign_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
