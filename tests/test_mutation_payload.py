import json
import unittest
from pathlib import Path

from sentinel_eval.mutations.engine import apply_mutations
from sentinel_eval.utils.payloads import (
    MUTATION_PAYLOAD,
    load_dataset_manifest,
    load_payload_cases,
    resolve_payload_path,
)

ROOT = Path(__file__).resolve().parents[1]


class TestMutationPayload(unittest.TestCase):
    def test_manifest_and_alias(self):
        manifest = load_dataset_manifest(ROOT / "payloads/mutations/manifest.json")
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertEqual(manifest.dataset_version, "mut-1.0")
        self.assertEqual(manifest.case_count, 10)
        path = resolve_payload_path("mutations")
        self.assertTrue(path.name.endswith("scenarios_mutation.json"))

    def test_load_ten_cases_with_mutation_kinds(self):
        cases = load_payload_cases(MUTATION_PAYLOAD)
        self.assertEqual(len(cases), 10)
        with_kinds = [c for c in cases if c.mutation_kinds]
        self.assertGreaterEqual(len(with_kinds), 8)
        case = next(c for c in cases if c.case_id == "MUT-010-COMPOSED-STRESS")
        self.assertEqual(
            case.mutation_kinds,
            ["unicode_homoglyph", "multilingual_override"],
        )

    def test_per_case_mutation_applies(self):
        cases = load_payload_cases("mutations")
        case = next(c for c in cases if c.case_id == "MUT-001-UNICODE-OVERRIDE")
        result = apply_mutations(case.email_thread, case.mutation_kinds)
        self.assertNotEqual(result.mutated_thread, case.email_thread)

    def test_envelope_on_disk(self):
        data = json.loads(
            (ROOT / "payloads/mutations/scenarios_mutation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(data["dataset_version"], "mut-1.0")
        self.assertEqual(len(data["cases"]), 10)


if __name__ == "__main__":
    unittest.main()
