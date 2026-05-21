import unittest
from unittest.mock import MagicMock

from sentinel_eval.domain.models import CaseEvaluationResult
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator


class TestEvaluatorSeparation(unittest.TestCase):
    def test_case_result_has_separated_eval_blocks(self):
        tester = MagicMock()
        tester.run_test.return_value = (
            '{"is_safe": true, "reasoning": "ok", "security_status": "Pass", '
            '"risk_score": 0.15, "confidence": 0.9, "uncertainty": 0.1}'
        )
        case = {
            "case_id": "T",
            "email_thread": "hello",
            "reference_answer": '{"is_safe": true, "reasoning": "ok", "security_status": "Pass"}',
            "expected_is_safe": True,
        }
        result = CaseEvaluator().evaluate(case, tester, rouge_l_threshold=0.0)
        self.assertIsInstance(result, CaseEvaluationResult)
        self.assertIsNotNone(result.semantic_eval)
        self.assertIsNotNone(result.schema_eval)
        self.assertIsNotNone(result.security_eval)
        self.assertIsNotNone(result.release_eval)
        self.assertTrue(result.calibration_eval.has_calibration)


if __name__ == "__main__":
    unittest.main()
