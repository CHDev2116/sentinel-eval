#!/usr/bin/env python3
"""Materialize golden attack cases × robust surface forms → scenarios_robust_surfaces.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel_eval.mutations.expand import expand_payload_cases
from sentinel_eval.utils.payloads import load_payload_cases, normalize_case

OUT = ROOT / "payloads" / "mutations" / "scenarios_robust_surfaces.json"


def main() -> int:
    cases = load_payload_cases("v2")
    expanded = expand_payload_cases(cases, include_plain=True, expand_attacks_only=True)
    payload = {
        "dataset_version": "robust-1.0",
        "suite": "robust-surfaces-golden",
        "description": (
            "Golden attack cases expanded to isolated surface forms "
            "(same semantic attack, different adversarial packaging)."
        ),
        "cases": [normalize_case(c.model_dump()) for c in expanded],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(expanded)} cases to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
