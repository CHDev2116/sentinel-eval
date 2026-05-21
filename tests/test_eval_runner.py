import unittest
from unittest.mock import MagicMock

from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.evaluators.case import evaluate_case
from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.utils.payloads import load_payload_cases, normalize_case


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

    def test_load_payload_returns_test_cases(self):
        cases = load_payload_cases("v2")
        self.assertEqual(len(cases), 12)
        self.assertEqual(cases[0].case_id, "TC-001-INJECTION")
        self.assertIsInstance(cases[0].email_thread, str)

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
        self.assertEqual(m.schema_valid, "2/2")
        self.assertEqual(m.label_match, "1/2")

    def test_evaluate_case_returns_typed_result(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": true, "reasoning": "benign", "security_status": "Pass", '
            '"risk_score": 0.1, "confidence": 0.9, "uncertainty": 0.1}'
        )
        case = {
            "case_id": "T",
            "email_thread": "hello",
            "reference_answer": '{"is_safe": true, "reasoning": "benign", "security_status": "Pass"}',
            "expected_is_safe": True,
        }
        result = evaluate_case(case, tester, rouge_l_threshold=0.0)
        self.assertIsInstance(result, CaseEvaluationResult)
        self.assertTrue(result.prediction_match)
        self.assertTrue(result.security_pass)
        self.assertTrue(result.composite_pass)
        self.assertIn("is_safe", result.to_report_dict()["parsed_output"])

    def test_security_pass_without_rouge(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": false, "reasoning": "attack", "security_status": "Fail", '
            '"risk_score": 0.9, "confidence": 0.88, "uncertainty": 0.12}'
        )
        case = {
            "case_id": "T2",
            "email_thread": "ignore all",
            "reference_answer": '{"is_safe": true, "reasoning": "x", "security_status": "Pass"}',
            "expected_is_safe": False,
        }
        result = evaluate_case(case, tester, rouge_l_threshold=0.99)
        self.assertTrue(result.security_pass)
        self.assertFalse(result.rouge_l_pass)
        self.assertFalse(result.composite_pass)


if __name__ == "__main__":
    unittest.main()
