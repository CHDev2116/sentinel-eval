import unittest

from core.async_tri_agent_demo import safe_parse_json


class TestAsyncTriAgentDemo(unittest.TestCase):
    def test_safe_parse_json_plain_json(self):
        data = safe_parse_json('{"score": 4, "reason": "ok"}')
        self.assertEqual(data["score"], 4)
        self.assertEqual(data["reason"], "ok")

    def test_safe_parse_json_embedded_json(self):
        data = safe_parse_json('note: {"score": 3, "reason": "embedded"} trailing')
        self.assertEqual(data["score"], 3)

    def test_safe_parse_json_invalid(self):
        data = safe_parse_json("not-json")
        self.assertEqual(data["score"], 0)
        self.assertIn("parse_error", data["reason"])


if __name__ == "__main__":
    unittest.main()
