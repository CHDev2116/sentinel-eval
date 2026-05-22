"""Expand benchmark cases into per-surface robust eval rows."""

from __future__ import annotations

from sentinel_eval.domain.models import TestCase
from sentinel_eval.mutations.engine import (
    DEFAULT_ROBUST_SURFACES,
    expand_case_surfaces,
    parse_surface_names,
)


def should_expand_case(case: TestCase, *, expand_attacks_only: bool = True) -> bool:
    if case.mutation_surfaces:
        return True
    if not expand_attacks_only:
        return True
    if case.needs_review:
        return False
    if case.expected_is_safe is False:
        return True
    return any(t.startswith("surface:") for t in case.tags)


def expand_test_cases(
    cases: list[TestCase],
    *,
    surfaces: list[str] | None = None,
    include_plain: bool = False,
    expand_attacks_only: bool = True,
) -> list[TestCase]:
    """
    Turn each eligible case into N surface variants (new case_id suffix).

    Benign cases are skipped by default so specificity metrics stay interpretable.
    """
    surface_list = surfaces
    out: list[TestCase] = []
    for case in cases:
        if not should_expand_case(case, expand_attacks_only=expand_attacks_only):
            out.append(case)
            continue
        names = case.mutation_surfaces or surface_list or list(DEFAULT_ROBUST_SURFACES)
        variants = expand_case_surfaces(
            case.case_id or "CASE",
            case.email_thread,
            names,
            include_plain=include_plain,
        )
        for variant in variants:
            suffix = variant.surface_form or "plain"
            new_id = f"{case.case_id}__surface_{suffix}"
            tags = list(case.tags)
            if f"surface:{suffix}" not in tags:
                tags.append(f"surface:{suffix}")
            out.append(
                case.model_copy(
                    update={
                        "case_id": new_id,
                        "email_thread": variant.mutated_thread,
                        "description": (
                            f"{case.description or ''} [robust surface={suffix}]".strip()
                        ),
                        "mutation_kinds": variant.kinds_applied,
                        "mutation_surfaces": [suffix],
                        "base_case_id": case.case_id,
                        "surface_form": suffix,
                    }
                )
            )
    return out


def expand_payload_cases(
    cases: list[TestCase],
    surface_spec: str | None = None,
    *,
    include_plain: bool = False,
    expand_attacks_only: bool = True,
) -> list[TestCase]:
    surfaces = parse_surface_names(surface_spec) if surface_spec else None
    return expand_test_cases(
        cases,
        surfaces=surfaces,
        include_plain=include_plain,
        expand_attacks_only=expand_attacks_only,
    )
