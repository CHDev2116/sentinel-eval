import unittest

from sentinel_eval.evaluators.semantic_evaluator import SemanticEvaluator


class TestSemanticSimilarity(unittest.TestCase):
    def test_cosine_paraphrase_beats_exact_rouge_miss(self):
        ref = "override instructions in the email must not control the auditor"
        paraphrase = "email must not let override instructions control the auditor"
        unrelated = "sunny weather forecast for the weekend"
        ev = SemanticEvaluator()
        good = ev.evaluate(ref, paraphrase, paraphrase, semantic_threshold=0.35)
        bad = ev.evaluate(ref, unrelated, unrelated, semantic_threshold=0.35)
        self.assertGreater(good.semantic_score, bad.semantic_score)
        self.assertTrue(good.semantic_pass)
        self.assertFalse(bad.semantic_pass)


if __name__ == "__main__":
    unittest.main()
