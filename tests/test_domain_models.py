import unittest

from sentinel_eval.domain.models import (
    AuditOutput,
    CaseEvaluationResult,
    SchemaValidationResult,
    TestCase,
)
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator
from sentinel_eval.evaluators.schema_validator import SchemaValidator


class TestDomainModels(unittest.TestCase):
    def test_audit_output_from_dict(self):
        audit = AuditOutput.from_parsed_dict(
            {
                "is_safe": False,
                "reasoning": "attack detected",
                "security_status": "Fail",
                "risk_score": 0.9,
                "confidence": 0.85,
                "uncertainty": 0.15,
            }
        )
        self.assertFalse(audit.is_safe)
        result = SchemaValidator().validate(audit)
        self.assertTrue(result.is_valid)

    def test_case_evaluation_roundtrip_dict(self):
        result = CaseEvaluationResult(
            case_id="TC-X",
            parsed_output=AuditOutput(is_safe=True, reasoning="ok", security_status="Pass"),
            schema_validation=SchemaValidationResult(is_valid=True),
        )
        data = result.to_report_dict()
        self.assertEqual(data["case_id"], "TC-X")
        self.assertTrue(data["parsed_output"]["is_safe"])

    def test_test_case_from_payload(self):
        case = TestCase.from_payload(
            {
                "case_id": "TC-1",
                "email_thread": "hello",
                "expected_is_safe": True,
            }
        )
        self.assertEqual(case.case_id, "TC-1")
        self.assertTrue(case.expected_is_safe)

    def test_case_evaluator_class_exists(self):
        self.assertIsNotNone(CaseEvaluator())


if __name__ == "__main__":
    unittest.main()
