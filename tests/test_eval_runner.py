import unittest
from unittest.mock import MagicMock

from core.eval_runner import aggregate_metrics, evaluate_case, normalize_case


class TestEvalRunner(unittest.TestCase):
    def test_normalize_legacy_case(self):
        case = {
            "case_id": "TC-001",
            "expected_is_inclusive": False,
            "reference_answer": '{"is_inclusive": false, "reasoning": "x", "security_status": "Pass"}',
        }
        out = normalize_case(case)
        self.assertFalse(out["expected_is_safe"])
        self.assertIn("is_safe", out["reference_answer"])

    def test_aggregate_metrics(self):
        results = [
            {
                "schema_validation": {"is_valid": True},
                "prediction_match": True,
                "composite_pass": True,
                "expected_is_safe": False,
                "parsed_output": {"is_safe": False},
                "rouge": {"rougeL": {"f1": 0.4}},
                "needs_review": False,
            },
            {
                "schema_validation": {"is_valid": True},
                "prediction_match": False,
                "composite_pass": False,
                "expected_is_safe": True,
                "parsed_output": {"is_safe": False},
                "rouge": {"rougeL": {"f1": 0.3}},
                "needs_review": False,
            },
        ]
        m = aggregate_metrics(results)
        self.assertEqual(m["schema_valid"], "2/2")
        self.assertEqual(m["label_match"], "1/2")
        self.assertEqual(m["injection_recall"], "1/1")
        self.assertEqual(m["benign_specificity"], "0/1")

    def test_evaluate_case_uses_mock_tester(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": true, "reasoning": "benign", "security_status": "Pass"}'
        )
        case = {
            "case_id": "T",
            "email_thread": "hello",
            "reference_answer": '{"is_safe": true, "reasoning": "benign", "security_status": "Pass"}',
            "expected_is_safe": True,
        }
        result = evaluate_case(case, tester, rouge_l_threshold=0.0)
        self.assertTrue(result["prediction_match"])
        self.assertTrue(result["security_pass"])
        self.assertTrue(result["composite_pass"])

    def test_security_pass_without_rouge(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": false, "reasoning": "attack", "security_status": "Fail"}'
        )
        case = {
            "case_id": "T2",
            "email_thread": "ignore all",
            "reference_answer": '{"is_safe": true, "reasoning": "x", "security_status": "Pass"}',
            "expected_is_safe": False,
        }
        result = evaluate_case(case, tester, rouge_l_threshold=0.99)
        self.assertTrue(result["security_pass"])
        self.assertFalse(result["rouge_l_pass"])
        self.assertFalse(result["composite_pass"])


if __name__ == "__main__":
    unittest.main()
