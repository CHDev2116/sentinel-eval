"""Attack taxonomy for research-grade benchmark tagging."""

from __future__ import annotations

ATTACK_TAXONOMY: tuple[str, ...] = (
    "instruction_override",
    "format_attack",
    "authority_escalation",
    "tool_confusion",
    "long_context_burial",
    "markdown_injection",
    "unicode_obfuscation",
    "roleplay_escape",
)

BENIGN_TAXONOMY: tuple[str, ...] = ("benign",)

ALL_TAXONOMY_TAGS: frozenset[str] = frozenset([*ATTACK_TAXONOMY, *BENIGN_TAXONOMY])

# Legacy coarse tags mapped to fine-grained defaults (migration helper)
LEGACY_TAG_MAP: dict[str, list[str]] = {
    "injection": ["instruction_override"],
    "long_context": ["long_context_burial"],
    "format_attack": ["format_attack"],
}


def expand_legacy_tags(tags: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if tag in ALL_TAXONOMY_TAGS:
            if tag not in seen:
                out.append(tag)
                seen.add(tag)
            continue
        for mapped in LEGACY_TAG_MAP.get(tag, [tag]):
            if mapped not in seen:
                out.append(mapped)
                seen.add(mapped)
    return out


def is_attack_tag(tag: str) -> bool:
    return tag in ATTACK_TAXONOMY
