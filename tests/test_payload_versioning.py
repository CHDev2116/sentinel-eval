import json
import unittest
from pathlib import Path

from sentinel_eval.utils.payloads import (
    GOLDEN_PAYLOAD,
    load_dataset_manifest,
    load_payload_cases,
    resolve_payload_path,
)

ROOT = Path(__file__).resolve().parents[1]


class TestPayloadVersioning(unittest.TestCase):
    def test_v2_manifest(self):
        manifest = load_dataset_manifest(ROOT / "payloads/v2/manifest.json")
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertEqual(manifest.dataset_version, "v2.2")
        self.assertEqual(manifest.case_count, 12)

    def test_envelope_loads_twelve_cases(self):
        cases = load_payload_cases("v2")
        self.assertEqual(len(cases), 12)

    def test_resolve_alias_v2(self):
        path = resolve_payload_path("v2")
        self.assertTrue(path.name.endswith("scenarios_golden.json"))
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["dataset_version"], "v2.2")
        self.assertEqual(len(data["cases"]), 12)

    def test_default_golden_alias(self):
        cases = load_payload_cases(GOLDEN_PAYLOAD)
        self.assertGreaterEqual(len(cases), 12)


if __name__ == "__main__":
    unittest.main()
