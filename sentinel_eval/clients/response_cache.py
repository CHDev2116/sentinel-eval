"""SQLite-backed LLM response cache for stable, cheap re-runs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from sentinel_eval.clients.protocol import ModelInferenceParams


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def audit_cache_key(
    *,
    backend: str,
    model: str,
    prompt_sha256: str,
    thread: str,
    inference: ModelInferenceParams,
    format_schema: str = "",
) -> str:
    """Stable cache key for one auditor invocation."""
    payload = {
        "backend": backend,
        "model": model,
        "prompt_sha256": prompt_sha256,
        "thread": thread,
        "inference": inference.for_lineage(),
        "format_schema": format_schema,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return sha256_hex(canonical)


class ResponseCache:
    """Persist raw model outputs keyed by audit_cache_key."""

    def __init__(self, path: str | Path, enabled: bool = True):
        self.path = Path(path)
        self.enabled = enabled
        self.hits = 0
        self.misses = 0
        self._conn: sqlite3.Connection | None = None
        if self.enabled:
            self._ensure_db()

    def _ensure_db(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                cache_key TEXT PRIMARY KEY,
                raw_output TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, cache_key: str) -> str | None:
        if not self.enabled or self._conn is None:
            self.misses += 1
            return None
        row = self._conn.execute(
            "SELECT raw_output FROM responses WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        return row[0]

    def set(self, cache_key: str, raw_output: str) -> None:
        if not self.enabled or self._conn is None:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO responses (cache_key, raw_output, created_at) VALUES (?, ?, ?)",
            (cache_key, raw_output, time.time()),
        )
        self._conn.commit()

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "path": str(self.path),
            "hits": self.hits,
            "misses": self.misses,
        }

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
