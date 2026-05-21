import unittest

from sentinel_eval.prompts.registry import get_active_prompt


class TestPromptRegistry(unittest.TestCase):
    def test_active_prompt_metadata(self):
        meta = get_active_prompt()
        self.assertEqual(meta.prompt_id, "is_safe_v2.2")
        self.assertEqual(meta.dataset_version, "v2.1")
        self.assertIn("prompt_injection", meta.optimized_for)
        self.assertIn("multilingual_attacks", meta.known_weakness)


if __name__ == "__main__":
    unittest.main()
