import unittest

from core.eval_runner import aggregate_metrics, compute_classification_metrics


def _case(expected_safe, predicted_safe, match=None):
    if match is None:
        match = expected_safe == predicted_safe
    return {
        "needs_review": False,
        "expected_is_safe": expected_safe,
        "prediction_match": match,
        "schema_validation": {"is_valid": True},
        "parsed_output": {"is_safe": predicted_safe},
        "security_pass": match,
    }


class TestClassificationMetrics(unittest.TestCase):
    def test_confusion_matrix_counts(self):
        results = [
            _case(True, True),   # TN
            _case(True, False),  # FP
            _case(False, True),  # FN
            _case(False, False),  # TP
            _case(False, False),  # TP
        ]
        clf = compute_classification_metrics(results)
        self.assertEqual(clf["tn"], 1)
        self.assertEqual(clf["fp"], 1)
        self.assertEqual(clf["fn"], 1)
        self.assertEqual(clf["tp"], 2)
        self.assertEqual(clf["confusion_matrix"]["counts"], [[1, 1], [1, 2]])

    def test_precision_recall_f1_fpr(self):
        results = [
            _case(True, True),
            _case(True, True),
            _case(False, False),
            _case(False, False),
        ]
        clf = compute_classification_metrics(results)
        self.assertEqual(clf["precision_pct"], 100.0)
        self.assertEqual(clf["recall_pct"], 100.0)
        self.assertEqual(clf["f1_pct"], 100.0)
        self.assertEqual(clf["false_positive_rate_pct"], 0.0)
        self.assertEqual(clf["specificity_pct"], 100.0)

    def test_aggregate_metrics_includes_classification(self):
        results = [
            _case(False, False),
            _case(True, True),
        ]
        m = aggregate_metrics(results)
        self.assertIn("classification", m)
        self.assertEqual(m["precision_pct"], 100.0)
        self.assertEqual(m["f1_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
