import unittest

from sentinel_eval.prompts.audit import PROMPT_VERSION, build_audit_prompt
from sentinel_eval.schemas.audit import validate_audit_schema


class TestPromptV22(unittest.TestCase):
    def test_prompt_version(self):
        self.assertEqual(PROMPT_VERSION, "is_safe_v2.2")

    def test_prompt_requires_calibration_keys(self):
        prompt = build_audit_prompt("Subject: hello")
        self.assertIn("risk_score", prompt)
        self.assertIn("confidence", prompt)
        self.assertIn("uncertainty", prompt)
        self.assertIn("CALIBRATION POLICY", prompt)

    def test_schema_requires_calibration_when_enabled(self):
        ok = {
            "is_safe": True,
            "reasoning": "benign",
            "security_status": "Pass",
            "risk_score": 0.1,
            "confidence": 0.9,
            "uncertainty": 0.1,
        }
        missing = validate_audit_schema(
            {"is_safe": True, "reasoning": "x", "security_status": "Pass"},
            require_calibration=True,
        )
        self.assertFalse(missing["is_valid"])
        complete = validate_audit_schema(ok, require_calibration=True)
        self.assertTrue(complete["is_valid"])


if __name__ == "__main__":
    unittest.main()
