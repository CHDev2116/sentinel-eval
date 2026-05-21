import json
import tempfile
import unittest

from sentinel_eval.domain.models import (
    AuditOutput,
    CaseEvaluationResult,
    RougeMetric,
    RougeScores,
    SchemaValidationResult,
)
from sentinel_eval.domain.report import case_result_from_dict
from sentinel_eval.domain.suite_metrics import SuiteMetrics
from sentinel_eval.utils.reports import build_run_report, load_run_report


class TestRunReport(unittest.TestCase):
    def _sample_result(self) -> CaseEvaluationResult:
        return CaseEvaluationResult(
            case_id="TC-1",
            parsed_output=AuditOutput(is_safe=False, reasoning="x", security_status="Fail"),
            schema_validation=SchemaValidationResult(is_valid=True),
            prediction_match=True,
            rouge=RougeScores(rougeL=RougeMetric(precision=0.1, recall=0.2, f1=0.75)),
        )

    def test_roundtrip_write_load(self):
        result = self._sample_result()
        report = build_run_report(
            [result],
            model_name="test-model",
            payload_path="payloads/scenarios_golden.json",
            full_suite=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/run.json"
            report.write_json(path)
            loaded = load_run_report(path)
        self.assertEqual(loaded.meta.model, "test-model")
        self.assertIsInstance(loaded.meta.metrics, SuiteMetrics)
        self.assertEqual(loaded.results[0].case_id, "TC-1")
        self.assertEqual(loaded.results[0].parsed_output.is_safe, False)

    def test_case_result_from_legacy_dict(self):
        raw = {
            "case_id": "TC-2",
            "parsed_output": {"is_safe": True, "reasoning": "ok", "security_status": "Pass"},
            "schema_validation": {"is_valid": True, "errors": []},
            "rouge": {"rougeL": {"precision": 0.5, "recall": 0.5, "f1": 0.5}},
        }
        item = case_result_from_dict(raw)
        self.assertTrue(item.parsed_output.is_safe)

    def test_json_on_disk_matches_envelope(self):
        report = build_run_report(
            [self._sample_result()],
            model_name="m",
            payload_path="p",
            full_suite=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/run.json"
            report.write_json(path)
            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
        self.assertIn("meta", data)
        self.assertIn("results", data)
        self.assertEqual(data["results"][0]["case_id"], "TC-1")


if __name__ == "__main__":
    unittest.main()
