import unittest

from sentinel_eval.prompts.adversarial import build_operational_triage_prompt
from sentinel_eval.prompts.audit import build_audit_prompt
from sentinel_eval.prompts.builder import resolve_prompt_builder
from sentinel_eval.prompts.rubric import HIDDEN_RUBRIC_FULL


class TestAdversarialPrompt(unittest.TestCase):
    def test_v3_prompt_avoids_benchmark_framing(self):
        prompt = build_operational_triage_prompt("test thread")
        self.assertNotIn("DATASET TO AUDIT", prompt)
        self.assertNotIn("CALIBRATION —", prompt)
        self.assertIn("overnight", prompt.lower())

    def test_v22_still_has_few_shot(self):
        prompt = build_audit_prompt("x")
        self.assertIn("EXAMPLES", prompt)

    def test_hidden_rubric_not_in_auditor_prompts(self):
        for builder in (
            build_audit_prompt,
            build_operational_triage_prompt,
        ):
            prompt = builder("thread")
            self.assertNotIn(HIDDEN_RUBRIC_FULL[:40], prompt)

    def test_prompt_hashes_differ_by_version(self):
        from sentinel_eval.clients.lineage import prompt_sha256

        h22 = prompt_sha256(resolve_prompt_builder("is_safe_v2.2"))
        h30 = prompt_sha256(resolve_prompt_builder("is_safe_v3.0"))
        self.assertNotEqual(h22, h30)


if __name__ == "__main__":
    unittest.main()
