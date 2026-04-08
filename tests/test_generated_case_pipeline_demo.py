import json
import unittest

from core.generated_case_pipeline_demo import (
    build_case_id,
    get_next_generated_index,
    to_payload_case,
)


class TestGeneratedCasePipelineDemo(unittest.TestCase):
    def test_build_case_id_format(self):
        self.assertEqual(build_case_id(1), "TC-GENERATED-SE-001")
        self.assertEqual(build_case_id(12), "TC-GENERATED-SE-012")

    def test_to_payload_case_with_valid_bool(self):
        evaluated_case = {
            "case_id": "TC-GENERATED-SE-001",
            "description": "Generated social-engineering simulation for pipeline validation",
            "email_thread": "test email",
            "parsed_output": {
                "is_inclusive": True,
                "reasoning": "benign",
                "security_status": "Pass",
            },
        }
        payload_case = to_payload_case(evaluated_case)

        self.assertEqual(payload_case["case_id"], evaluated_case["case_id"])
        self.assertEqual(payload_case["expected_is_inclusive"], True)
        loaded_ref = json.loads(payload_case["reference_answer"])
        self.assertIn("is_inclusive", loaded_ref)
        self.assertIn("reasoning", loaded_ref)
        self.assertIn("security_status", loaded_ref)

    def test_to_payload_case_with_invalid_bool_defaults_false(self):
        evaluated_case = {
            "case_id": "TC-GENERATED-SE-002",
            "description": "Generated social-engineering simulation for pipeline validation",
            "email_thread": "test email",
            "parsed_output": {
                "is_inclusive": None,
                "reasoning": "parse error",
                "security_status": "ParseError",
            },
        }
        payload_case = to_payload_case(evaluated_case)
        self.assertEqual(payload_case["expected_is_inclusive"], False)

    def test_get_next_generated_index(self):
        cases = [
            {"case_id": "TC-001-INJECTION"},
            {"case_id": "TC-GENERATED-SE-001"},
            {"case_id": "TC-GENERATED-SE-015"},
            {"case_id": "TC-GENERATED-SE-003"},
        ]
        self.assertEqual(get_next_generated_index(cases), 16)


if __name__ == "__main__":
    unittest.main()
