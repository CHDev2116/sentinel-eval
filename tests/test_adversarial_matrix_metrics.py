import unittest

from sentinel_eval.metrics.adversarial_matrix import compute_adversarial_matrix_metrics
from sentinel_eval.metrics.aggregation import aggregate_metrics


def _row(expected, predicted, tags, mutation_kinds=None):
    return {
        "expected_is_safe": expected,
        "parsed_output": {"is_safe": predicted},
        "schema_validation": {"is_valid": True},
        "tags": tags,
        "mutation_meta": {"kinds_applied": mutation_kinds or []},
    }


class TestAdversarialMatrixMetrics(unittest.TestCase):
    def test_ingress_metrics(self):
        rows = [
            _row(False, False, ["injection"]),
            _row(False, True, ["injection", "indirect_injection"]),
            _row(True, True, ["benign"]),
            _row(True, False, ["benign"]),
        ]
        matrix = compute_adversarial_matrix_metrics(rows)
        self.assertEqual(matrix.ingress.attack_cases, 2)
        self.assertEqual(matrix.ingress.blocked_attacks, 1)
        self.assertEqual(matrix.ingress.false_positives, 1)
        self.assertEqual(matrix.ingress.true_positive_rate, 50.0)
        self.assertEqual(matrix.ingress.false_positive_rate, 50.0)
        self.assertEqual(matrix.ingress.indirect_injection_immunity_rate, 0.0)

    def test_egress_and_red_team_metrics(self):
        rows = [
            _row(False, False, ["privilege_escalation", "tool_call"]),
            _row(False, True, ["redteam_generated", "injection"], ["unicode_homoglyph"]),
            _row(False, True, ["redteam_generated", "injection"], ["markdown_nest"]),
            _row(False, False, ["pii", "pii_leak"]),
        ]
        matrix = compute_adversarial_matrix_metrics(rows)
        self.assertEqual(matrix.egress.privilege_escalation_attempts, 1)
        self.assertEqual(matrix.egress.privilege_escalation_blocked, 1)
        self.assertEqual(matrix.red_team.generated_attacks, 2)
        self.assertEqual(matrix.red_team.successful_attacks, 2)
        self.assertEqual(matrix.red_team.unique_attack_patterns, 2)

    def test_aggregate_metrics_contains_matrix(self):
        rows = [
            _row(False, False, ["injection"]),
            _row(True, True, ["benign"]),
        ]
        metrics = aggregate_metrics(rows)
        self.assertIsNotNone(metrics.adversarial_matrix)
        self.assertEqual(metrics.adversarial_matrix.ingress.true_positive_rate, 100.0)


if __name__ == "__main__":
    unittest.main()
