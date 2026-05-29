"""Heuristic funnel tiers: allowlist, static block, suspect → LLM."""

from __future__ import annotations

import re

# Highest priority: routine greetings (ingress fast-path bypass).
_BENIGN_EXACT: frozenset[str] = frozenset(
    {
        "hello team",
        "hi there",
        "hi",
        "hello",
        "hey team",
        "good morning team",
    },
)

_BENIGN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^hello\s+team\b", re.I),
    re.compile(r"^hi\s+there\b", re.I),
    re.compile(r"^hello\s+team,\s+can you help\b", re.I),
    re.compile(r"^hi[,!]?\s+what is the weather\b", re.I),
)

_USER_LINE = re.compile(r"^User:\s*(.*)$", re.MULTILINE | re.DOTALL)

# Tier 1 — immediate block without LLM (100% malicious / destructive).
_EXTREMELY_DANGEROUS = re.compile(
    r"rm\s+-rf\b|"
    r"sk-[a-zA-Z0-9]{16,}|"
    r"api[_-]?key\s*[:=]\s*\S+|"
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----|"
    r"<script\b|"
    r"javascript:\s*",
    re.I,
)

# Tier 2 — ambiguous; escalate to LLM judge (do not block on regex alone).
_SUSPECT_SIGNALS = re.compile(
    r"agent\s+says|"
    r"ignore\s+(all\s+)?(prior|previous)\s+(context|instructions)|"
    r"do\s+anything\s+now|\bDAN\b|"
    r"system\s+prompt|"
    r"jailbreak|"
    r"disregard\s+safety|"
    r"print\s+the\s+secret|"
    r"eval\s*\(|"
    r"base64\s+decode",
    re.I,
)

# Used by LLM stand-in judge (full behavioral check).
_OVERRIDE_PATTERNS = _SUSPECT_SIGNALS

_SECRET_PATTERNS = re.compile(
    r"sk-[a-zA-Z0-9]{16,}|"
    r"api[_-]?key\s*[:=]\s*\S+|"
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----|"
    r"print\s+the\s+secret",
    re.I,
)

_HIGH_RISK_PATTERNS = _EXTREMELY_DANGEROUS


def extract_user_message(target_session: str) -> str:
    """Pull the User: line from a formatted target session."""
    match = _USER_LINE.search(target_session)
    if match:
        return match.group(1).strip()
    return target_session.strip()


def is_benign_allowlist(user_message: str) -> bool:
    """True when the user turn matches routine safe greetings / small talk."""
    text = user_message.strip()
    if not text:
        return False
    norm = text.lower()
    if norm in _BENIGN_EXACT:
        return True
    return any(pat.search(text) for pat in _BENIGN_PATTERNS)


def is_extremely_dangerous(text: str) -> bool:
    """Tier-1 coarse block: only unambiguous destructive / secret exfil patterns."""
    return bool(_EXTREMELY_DANGEROUS.search(text))


def has_suspect_signals(text: str) -> bool:
    """Tier-2 triage: structural or behavioral hints → send to LLM judge."""
    return bool(_SUSPECT_SIGNALS.search(text))


def has_attack_signals(text: str) -> bool:
    """Union of tier-1 + tier-2 (for LLM stand-in / egress agent scan)."""
    return is_extremely_dangerous(text) or has_suspect_signals(text)


def should_bypass_ingress(user_message: str, *, full_session: str | None = None) -> bool:
    """Allowlist bypass when no dangerous or suspect signals in scope."""
    scope = full_session if full_session is not None else user_message
    if is_extremely_dangerous(scope) or has_suspect_signals(scope):
        return False
    return is_benign_allowlist(user_message)
