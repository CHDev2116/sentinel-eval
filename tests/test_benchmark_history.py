import json
import tempfile
import unittest
from pathlib import Path

from sentinel_eval.benchmark.history import append_run_history, load_history
from sentinel_eval.domain.suite_metrics import SuiteMetrics


class TestBenchmarkHistory(unittest.TestCase):
    def test_append_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp)
            append_run_history(
                metrics=SuiteMetrics(cases_run=3, label_match_pct=80.0),
                model="test-model",
                payload="v2",
                history_dir=hist,
            )
            rows = load_history(hist)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["model"], "test-model")
            self.assertEqual(rows[0]["metrics"]["cases_run"], 3)


if __name__ == "__main__":
    unittest.main()
