import unittest

from sentinel_eval.domain.models import AuditOutput, TestCase
from sentinel_eval.evaluators.calibration_evaluator import CalibrationEvaluator
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator
from sentinel_eval.evaluators.protocol import CaseEvalContext
from sentinel_eval.evaluators.schema_evaluator import SchemaEvaluator
from sentinel_eval.evaluators.semantic_evaluator import SemanticEvaluator


class TestEvaluatorProtocol(unittest.TestCase):
    def test_evaluators_expose_ids(self):
        ev = CaseEvaluator()
        ids = [e.evaluator_id for e in ev.evaluators]
        self.assertEqual(
            ids,
            ["semantic", "schema", "security", "release_gate", "calibration"],
        )

    def test_evaluate_context_schema(self):
        audit = AuditOutput(
            is_safe=True,
            reasoning="ok",
            security_status="Pass",
            risk_score=0.1,
            confidence=0.9,
            uncertainty=0.1,
        )
        ctx = CaseEvalContext(
            case=TestCase(case_id="T", email_thread="x"),
            audit=audit,
            raw_output="{}",
            structured="{}",
            reference="",
            rouge_l_threshold=0.25,
            semantic_threshold=0.55,
        )
        schema = SchemaEvaluator().evaluate_context(ctx)
        self.assertTrue(schema.is_valid)
        cal = CalibrationEvaluator().evaluate_context(ctx)
        self.assertTrue(cal.has_calibration)


if __name__ == "__main__":
    unittest.main()
