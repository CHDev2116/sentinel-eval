import unittest

from sentinel_eval.domain.taxonomy import ATTACK_TAXONOMY, expand_legacy_tags, is_attack_tag
from sentinel_eval.utils.payloads import load_payload_cases


class TestTaxonomy(unittest.TestCase):
    def test_golden_uses_fine_grained_tags(self):
        cases = load_payload_cases("v2")
        attack_cases = [c for c in cases if c.expected_is_safe is False]
        for case in attack_cases:
            tags = set(case.tags)
            self.assertTrue(tags & set(ATTACK_TAXONOMY), f"{case.case_id} missing taxonomy tag")
            self.assertNotIn("injection", tags)

    def test_legacy_expansion(self):
        self.assertEqual(expand_legacy_tags(["injection"]), ["instruction_override"])


if __name__ == "__main__":
    unittest.main()
