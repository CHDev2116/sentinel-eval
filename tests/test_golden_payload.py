import json
import unittest

GOLDEN_PATH = "payloads/scenarios_golden.json"


class TestGoldenPayload(unittest.TestCase):
    def test_reference_security_status_matches_is_safe(self):
        with open(GOLDEN_PATH, encoding="utf-8") as f:
            cases = json.load(f)
        self.assertEqual(len(cases), 12)
        for case in cases:
            ref = json.loads(case["reference_answer"])
            expected_safe = case["expected_is_safe"]
            status = ref["security_status"]
            if expected_safe:
                self.assertEqual(status, "Pass", case["case_id"])
            else:
                self.assertEqual(status, "Fail", case["case_id"])


if __name__ == "__main__":
    unittest.main()
