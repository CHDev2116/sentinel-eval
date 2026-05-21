import json
import os

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import TestCase

_settings = get_settings()
GOLDEN_PAYLOAD = _settings.golden_payload
GENERATED_PAYLOAD = _settings.generated_payload
# Former path payloads/email_scenarios.json (removed); alias for backward-compatible CLI paths.
LEGACY_PAYLOAD = GOLDEN_PAYLOAD
LEGACY_SAFE_KEY = "is_inclusive"


def load_payload_cases(
    payload_path,
    include_generated: bool = False,
    tag_filter=None,
) -> list[TestCase]:
    """Load benchmark cases as typed TestCase models."""
    golden_paths = {GOLDEN_PAYLOAD, LEGACY_PAYLOAD}
    if payload_path in golden_paths:
        paths = [payload_path]
        if include_generated and os.path.exists(GENERATED_PAYLOAD):
            paths.append(GENERATED_PAYLOAD)
    elif os.path.basename(payload_path) == "scenarios_golden.json":
        paths = [payload_path]
        if include_generated and os.path.exists(GENERATED_PAYLOAD):
            paths.append(GENERATED_PAYLOAD)
    else:
        paths = [payload_path]

    merged: list[TestCase] = []
    seen: set[str] = set()
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            batch = json.load(f)
        if not isinstance(batch, list):
            continue
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
