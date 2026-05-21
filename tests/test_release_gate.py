import unittest
from unittest.mock import MagicMock

from core.eval_runner import (
    RELEASE_GATE_THRESHOLDS,
    evaluate_case,
    evaluate_release_gate,
    load_payload_cases,
)


class TestReleaseGate(unittest.TestCase):
    def test_needs_review_skips_security_pass(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": false, "reasoning": "x", "security_status": "Fail"}'
        )
        case = {
            "case_id": "TC-GENERATED-SE-099",
            "email_thread": "test",
            "needs_review": True,
            "expected_is_safe": None,
        }
        result = evaluate_case(case, tester)
        self.assertIsNone(result["prediction_match"])
        self.assertIsNone(result["security_pass"])
        self.assertIsNone(result["composite_pass"])

    def test_release_gate_passes_strong_metrics(self):
        results = []
        for i, safe in enumerate([False, False, True, True]):
            results.append(
                {
                    "case_id": f"TC-{i}",
                    "tags": ["injection"] if not safe else ["benign"],
                    "needs_review": False,
                    "expected_is_safe": safe,
                    "schema_validation": {"is_valid": True},
                    "prediction_match": True,
                    "security_pass": True,
                    "parsed_output": {"is_safe": safe},
                }
            )
        metrics = {
            "schema_valid_pct": 100.0,
            "security_pass_pct": 100.0,
            "injection_recall_pct": 100.0,
            "benign_specificity_pct": 100.0,
        }
        passed, failures = evaluate_release_gate(metrics, results)
        self.assertTrue(passed)
        self.assertEqual(failures, [])

    def test_release_gate_fails_p0_case(self):
        results = [
            {
                "case_id": "TC-009-FORMAT-ATTACK",
                "tags": ["format_attack"],
                "needs_review": False,
                "schema_validation": {"is_valid": True},
                "prediction_match": False,
                "security_pass": False,
                "parsed_output": {"is_safe": True},
                "expected_is_safe": False,
            }
        ]
        metrics = {k: 100.0 for k in RELEASE_GATE_THRESHOLDS}
        passed, failures = evaluate_release_gate(metrics, results)
        self.assertFalse(passed)
        self.assertTrue(any("TC-009" in msg for msg in failures))

    def test_load_legacy_payload_path(self):
        cases = load_payload_cases("payloads/email_scenarios.json")
        self.assertEqual(len(cases), 12)
        self.assertIn("expected_is_safe", cases[0])


if __name__ == "__main__":
    unittest.main()
