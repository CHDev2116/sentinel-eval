import unittest

from sentinel_eval.clients.lineage import dataset_sha256, prompt_sha256
from sentinel_eval.utils.payloads import GOLDEN_PAYLOAD


class TestLineage(unittest.TestCase):
    def test_prompt_sha256_stable(self):
        a = prompt_sha256()
        b = prompt_sha256()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_dataset_sha256_golden(self):
        digest = dataset_sha256(GOLDEN_PAYLOAD, include_generated=False)
        self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
