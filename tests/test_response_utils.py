import unittest

from sentinel_eval.schemas.audit import validate_audit_schema
from sentinel_eval.utils.parsing import (
    audit_json_canonical,
    extract_json_text,
    parse_audit_response,
)


class TestResponseUtils(unittest.TestCase):
    def test_parse_fenced_json(self):
        raw = '```json\n{"is_safe": false, "reasoning": "x", "security_status": "Fail"}\n```'
        parsed, _ = parse_audit_response(raw)
        self.assertFalse(parsed["is_safe"])
        self.assertTrue(validate_audit_schema(parsed)["is_valid"])

    def test_parse_legacy_is_inclusive(self):
        raw = '{"is_inclusive": true, "reasoning": "ok", "security_status": "Pass"}'
        parsed, canonical = parse_audit_response(raw)
        self.assertTrue(parsed["is_safe"])
        self.assertNotIn("is_inclusive", canonical)
        self.assertIn('"is_safe": true', canonical)

    def test_parse_prefers_is_safe_over_legacy(self):
        raw = (
            '{"is_inclusive": true, "is_safe": false, "reasoning": "x", "security_status": "Fail"}'
        )
        parsed, canonical = parse_audit_response(raw)
        self.assertFalse(parsed["is_safe"])
        self.assertNotIn("is_inclusive", canonical)

    def test_parse_invalid_json(self):
        parsed, _ = parse_audit_response("not json at all")
        self.assertIsNone(parsed["is_safe"])
        self.assertFalse(validate_audit_schema(parsed)["is_valid"])

    def test_extract_last_json_when_preamble(self):
        text = (
            'Here is the audit:\n```json\n{"is_safe": true, "reasoning": "a", '
            '"security_status": "Pass"}\n```\nExtra {"is_safe": false} noise'
        )
        extracted = extract_json_text(text)
        self.assertIn("is_safe", extracted)

    def test_audit_json_canonical_stable(self):
        parsed = {"is_safe": True, "reasoning": "r", "security_status": "Pass"}
        self.assertIn('"is_safe": true', audit_json_canonical(parsed))


if __name__ == "__main__":
    unittest.main()
