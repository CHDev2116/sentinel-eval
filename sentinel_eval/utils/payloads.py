import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import TestCase

_settings = get_settings()
PAYLOADS_ROOT = Path(_settings.payloads_root)
DEFAULT_DATASET_VERSION = _settings.dataset_version
# Version aliases (resolved by resolve_payload_path)
GOLDEN_PAYLOAD = _settings.golden_payload
GENERATED_PAYLOAD = _settings.generated_payload
MUTATION_PAYLOAD = _settings.mutation_payload
GENERATED_MANIFEST = str(PAYLOADS_ROOT / "generated" / "manifest.json")
LEGACY_PAYLOAD = GOLDEN_PAYLOAD
LEGACY_SAFE_KEY = "is_inclusive"

_VERSION_ALIASES = {
    "v2": PAYLOADS_ROOT / "v2",
    "v2.1": PAYLOADS_ROOT / "v2",
    "golden": PAYLOADS_ROOT / "v2",
    "generated": PAYLOADS_ROOT / "generated",
    "gen": PAYLOADS_ROOT / "generated",
    "mutations": PAYLOADS_ROOT / "mutations",
    "mutation": PAYLOADS_ROOT / "mutations",
    "mut": PAYLOADS_ROOT / "mutations",
}


class DatasetManifest(BaseModel):
    dataset_version: str
    suite: str = ""
    description: str = ""
    cases_file: str = "scenarios_golden.json"
    case_count: int | None = None
    compatible_prompts: list[str] = Field(default_factory=list)


def resolve_payload_path(payload_path: str | Path) -> Path:
    """Resolve CLI path, version alias (v2), or manifest path to a cases JSON file."""
    raw = Path(payload_path)
    key = str(payload_path).strip().lower()
    if key in _VERSION_ALIASES:
        manifest_path = _VERSION_ALIASES[key] / "manifest.json"
        if manifest_path.is_file():
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = DatasetManifest.model_validate(raw)
            return manifest_path.parent / manifest.cases_file
        return _VERSION_ALIASES[key] / "scenarios_golden.json"

    if not raw.is_absolute():
        raw = Path.cwd() / raw

    if raw.name == "manifest.json" and raw.is_file():
        manifest = DatasetManifest.model_validate(json.loads(raw.read_text(encoding="utf-8")))
        return raw.parent / manifest.cases_file

    # Legacy flat path after v2 migration
    legacy = Path("payloads/scenarios_golden.json")
    if raw.resolve() == (Path.cwd() / legacy).resolve() and not raw.is_file():
        migrated = Path(GOLDEN_PAYLOAD)
        if migrated.is_file():
            return migrated

    return raw


def _load_cases_json(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    with path.open(encoding="utf-8") as fp:
        data = json.load(fp)
    if isinstance(data, list):
        return data, None
    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        return data["cases"], data.get("dataset_version")
    raise ValueError(f"Unrecognized payload format: {path}")


def load_dataset_manifest(path: str | Path) -> DatasetManifest | None:
    """Load manifest.json next to a dataset directory or cases file."""
    p = Path(path)
    if p.name != "manifest.json":
        candidate = p.parent / "manifest.json"
        if p.is_dir():
            candidate = p / "manifest.json"
    else:
        candidate = p
    if not candidate.is_file():
        return None
    return DatasetManifest.model_validate(json.loads(candidate.read_text(encoding="utf-8")))


def load_payload_cases(
    payload_path,
    include_generated: bool = False,
    tag_filter=None,
) -> list[TestCase]:
    """Load benchmark cases as typed TestCase models."""
    resolved = resolve_payload_path(payload_path)
    golden_resolved = resolve_payload_path(GOLDEN_PAYLOAD)

    paths: list[Path] = []
    if resolved.resolve() == golden_resolved.resolve() or str(payload_path) in {
        GOLDEN_PAYLOAD,
        LEGACY_PAYLOAD,
        "v2",
        "v2.1",
        "golden",
    }:
        paths.append(golden_resolved)
        if include_generated:
            paths.append(resolve_payload_path(GENERATED_PAYLOAD))
    else:
        paths.append(resolved)
        if include_generated and os.path.exists(GENERATED_PAYLOAD):
            paths.append(resolve_payload_path(GENERATED_PAYLOAD))

    merged: list[TestCase] = []
    seen: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        batch, _version = _load_cases_json(path)
        for case in batch:
            cid = case.get("case_id")
            if not cid or cid in seen:
                continue
            normalized = normalize_case(case)
            if tag_filter and not _case_has_tag(normalized, tag_filter):
                continue
            seen.add(cid)
            merged.append(TestCase.from_payload(normalized))
    return merged


def _case_has_tag(case: dict, tag_filter) -> bool:
    tags = case.get("tags") or []
    if isinstance(tag_filter, str):
        return tag_filter in tags
    return any(t in tags for t in tag_filter)


def normalize_case(case: dict) -> dict:
    """Accept legacy expected_is_inclusive / reference_answer keys."""
    out = dict(case)
    if "expected_is_safe" not in out and "expected_is_inclusive" in out:
        out["expected_is_safe"] = out["expected_is_inclusive"]
    ref = out.get("reference_answer", "")
    if isinstance(ref, str) and LEGACY_SAFE_KEY in ref and '"is_safe"' not in ref:
        out["reference_answer"] = ref.replace(LEGACY_SAFE_KEY, "is_safe")
    tags = out.get("tags") or []
    if "golden" in tags:
        tags = [t for t in tags if t != "golden"]
        if out.get("expected_is_safe") is False and "injection" not in tags:
            tags.append("injection")
        out["tags"] = tags or ["golden"]
    return out
