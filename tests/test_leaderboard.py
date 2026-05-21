import json
import os
import tempfile
import unittest

from sentinel_eval.reporting.leaderboard import (
    entry_from_report,
    format_markdown_table,
    load_leaderboard,
    register_report,
    sort_entries,
    upsert_entry,
)


class TestLeaderboard(unittest.TestCase):
    def test_entry_from_report(self):
        meta = {
            "model": "llama3.1:latest",
            "prompt_version": "is_safe_v2.1",
            "full_suite": True,
            "timestamp": "2026-05-21T00:00:00+00:00",
        }
        results = [
            {
                "schema_validation": {"is_valid": True},
                "prediction_match": True,
                "parsed_output": {"is_safe": False},
                "expected_is_safe": False,
                "rouge": {"rougeL": {"f1": 0.8}},
            }
        ]
        entry = entry_from_report("fake.json", meta=meta, results=results)
        self.assertEqual(entry["model"], "llama3.1:latest")
        self.assertEqual(entry["metrics"]["schema_valid_pct"], 100.0)

    def test_upsert_keeps_latest(self):
        board = {"entries": []}
        upsert_entry(
            board,
            {
                "model": "gemma:7b",
                "prompt_version": "v1",
                "timestamp": "2026-01-01T00:00:00+00:00",
                "metrics": {"label_match_pct": 80},
            },
        )
        upsert_entry(
            board,
            {
                "model": "gemma:7b",
                "prompt_version": "v1",
                "timestamp": "2026-06-01T00:00:00+00:00",
                "metrics": {"label_match_pct": 90},
            },
        )
        self.assertEqual(len(board["entries"]), 1)
        self.assertEqual(board["entries"][0]["metrics"]["label_match_pct"], 90)

    def test_sort_entries_by_label_then_rouge(self):
        entries = [
            {"model": "a", "metrics": {"label_match_pct": 85, "avg_rouge_l_f1": 0.9}},
            {"model": "b", "metrics": {"label_match_pct": 88, "avg_rouge_l_f1": 0.7}},
        ]
        ordered = sort_entries(entries)
        self.assertEqual(ordered[0]["model"], "b")

    def test_format_markdown_table(self):
        md = format_markdown_table(
            [
                {
                    "model": "llama3.1:latest",
                    "prompt_version": "is_safe_v2.1",
                    "metrics": {
                        "schema_valid_pct": 100,
                        "label_match_pct": 92,
                        "avg_rouge_l_f1": 0.42,
                    },
                }
            ]
        )
        self.assertIn("Schema Valid", md)
        self.assertIn("llama3.1:latest", md)
        self.assertIn("92%", md)

    def test_register_report_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "run.json")
            board_path = os.path.join(tmp, "leaderboard.json")
            payload = {
                "meta": {
                    "model": "test-model",
                    "prompt_version": "is_safe_v2.1",
                    "full_suite": True,
                    "timestamp": "2026-05-21T12:00:00+00:00",
                },
                "results": [
                    {
                        "schema_validation": {"is_valid": True},
                        "prediction_match": True,
                        "expected_is_safe": True,
                        "parsed_output": {"is_safe": True},
                        "rouge": {"rougeL": {"f1": 0.75}},
                    }
                ],
            }
            with open(report, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            register_report(report, leaderboard_path=board_path)
            board = load_leaderboard(board_path)
            self.assertEqual(len(board["entries"]), 1)
            self.assertEqual(board["entries"][0]["model"], "test-model")


if __name__ == "__main__":
    unittest.main()
