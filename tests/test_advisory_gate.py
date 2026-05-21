import unittest

from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.metrics.release_gate import evaluate_advisory_gate


def _result(case_id, *, schema_valid=True, match=True, expected_safe=False, rouge_f1=0.8):
    predicted_safe = expected_safe if match else (not expected_safe)
    tags = ["benign"] if expected_safe else ["injection"]
    return {
        "case_id": case_id,
        "tags": tags,
        "needs_review": False,
        "expected_is_safe": expected_safe,
        "schema_validation": {"is_valid": schema_valid},
        "prediction_match": match,
        "security_pass": schema_valid and match,
        "parsed_output": {"is_safe": predicted_safe},
        "rouge": {"rougeL": {"f1": rouge_f1}},
    }


class TestAdvisoryGate(unittest.TestCase):
    def test_advisory_passes_strong_suite(self):
        results = [
            _result("TC-0", expected_safe=False),
            _result("TC-1", expected_safe=True),
        ]
        metrics = aggregate_metrics(results)
        passed, failures = evaluate_advisory_gate(metrics)
        self.assertTrue(passed)
        self.assertEqual(failures, [])

    def test_advisory_fails_low_security_pass(self):
        results = [
            _result("TC-0", match=False),
            _result("TC-1", expected_safe=True),
        ]
        metrics = aggregate_metrics(results)
        passed, failures = evaluate_advisory_gate(metrics)
        self.assertFalse(passed)
        self.assertTrue(any("security_pass_pct" in msg for msg in failures))


if __name__ == "__main__":
    unittest.main()
