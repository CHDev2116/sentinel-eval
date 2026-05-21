import unittest
from pathlib import Path

from sentinel_eval.benchmark.regression import (
    check_regression,
    load_thresholds,
    metrics_from_report,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "golden_regression_report.json"


class TestBenchmarkGate(unittest.TestCase):
    def test_fixture_passes_thresholds(self):
        thresholds = load_thresholds(ROOT / "benchmarks" / "thresholds.json")
        metrics = metrics_from_report(FIXTURE)
        failures = check_regression(metrics, thresholds["floors"])
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
