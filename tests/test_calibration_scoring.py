import unittest

from sentinel_eval.metrics.calibration_scoring import (
    brier_score,
    expected_calibration_error,
    reliability_diagram,
    summarize_calibration_scoring,
)


class TestCalibrationScoring(unittest.TestCase):
    def test_perfect_calibration_low_brier(self):
        pairs = [(0.9, 1), (0.1, 0), (0.85, 1), (0.15, 0)]
        self.assertLess(brier_score(pairs), 0.05)
        self.assertLess(expected_calibration_error(pairs), 0.15)
        self.assertGreaterEqual(len(reliability_diagram(pairs)), 2)

    def test_summarize_from_results(self):
        results = [
            {
                "expected_is_safe": False,
                "parsed_output": {"risk_score": 0.9, "is_safe": False},
            },
            {
                "expected_is_safe": True,
                "parsed_output": {"risk_score": 0.1, "is_safe": True},
            },
        ]
        summary = summarize_calibration_scoring(results)
        self.assertEqual(summary["scored_pairs"], 2)
        self.assertIsNotNone(summary["brier_score"])
        self.assertIsNotNone(summary["ece"])


if __name__ == "__main__":
    unittest.main()
