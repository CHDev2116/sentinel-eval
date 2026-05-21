import unittest

from sentinel_eval.metrics.aggregation import aggregate_metrics
from sentinel_eval.metrics.classification import (
    compute_classification_metrics,
    format_confusion_matrix_table,
)


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
    def test_confusion_matrix_layout(self):
        results = [
            _case(True, True),  # TP
            _case(True, False),  # FN
            _case(False, True),  # FP
            _case(False, False),  # TN
            _case(False, False),  # TN
        ]
        clf = compute_classification_metrics(results)
        self.assertEqual(clf.tp, 1)
        self.assertEqual(clf.fn, 1)
        self.assertEqual(clf.fp, 1)
        self.assertEqual(clf.tn, 2)
        self.assertEqual(clf.confusion_matrix.counts, [[1, 1], [1, 2]])
        self.assertEqual(clf.confusion_matrix.cell_labels[0], ["TP", "FN"])
        table = format_confusion_matrix_table(clf)
        self.assertIn("actual safe", table)
        self.assertIn("predicted unsafe", table)
        self.assertIn("TP=1", table)

    def test_injection_recall_and_specificity(self):
        results = [
            _case(True, True),
            _case(True, True),
            _case(False, False),
            _case(False, False),
        ]
        clf = compute_classification_metrics(results)
        self.assertEqual(clf.injection_recall_pct, 100.0)
        self.assertEqual(clf.benign_specificity_pct, 100.0)
        self.assertEqual(clf.false_positive_rate_pct, 0.0)

    def test_aggregate_metrics_includes_classification(self):
        results = [
            _case(False, False),
            _case(True, True),
        ]
        m = aggregate_metrics(results)
        self.assertIsNotNone(m.classification)
        self.assertEqual(m.precision_pct, 100.0)
        self.assertEqual(m.f1_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
