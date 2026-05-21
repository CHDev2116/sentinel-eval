"""Run lineage fingerprints for reproducible eval reports."""

from __future__ import annotations

from pathlib import Path

from sentinel_eval.clients.protocol import ModelInferenceParams
from sentinel_eval.clients.response_cache import sha256_hex
from sentinel_eval.prompts.builder import PromptBuilder, build_prompt_for_version
from sentinel_eval.prompts.registry import get_active_prompt
from sentinel_eval.utils.payloads import resolve_payload_path


def prompt_sha256(
    prompt_builder: PromptBuilder | None = None,
    probe_thread: str = "",
) -> str:
    """Hash of the active auditor prompt template (empty thread = canonical probe)."""
    if prompt_builder is not None:
        return sha256_hex(prompt_builder(probe_thread))
    from sentinel_eval.config import get_settings

    return sha256_hex(build_prompt_for_version(probe_thread, get_settings().prompt_version))


def dataset_sha256(payload_path: str | Path, include_generated: bool = False) -> str:
    """Hash dataset bytes used for a run (golden path + optional generated)."""
    from sentinel_eval.utils.payloads import GENERATED_PAYLOAD, GOLDEN_PAYLOAD

    paths: list[Path] = []
    resolved = resolve_payload_path(payload_path)
    paths.append(resolved)
    manifest = resolved.parent / "manifest.json"
    if manifest.is_file():
        paths.append(manifest)

    golden = resolve_payload_path(GOLDEN_PAYLOAD)
    if resolved.resolve() != golden.resolve():
        paths.append(golden)
        gm = golden.parent / "manifest.json"
        if gm.is_file():
            paths.append(gm)

    if include_generated:
        gen = resolve_payload_path(GENERATED_PAYLOAD)
        if gen.is_file():
            paths.append(gen)
            gm = gen.parent / "manifest.json"
            if gm.is_file():
                paths.append(gm)

    seen: set[str] = set()
    digest = __import__("hashlib").sha256()
    for path in sorted({str(p.resolve()) for p in paths}):
        if path in seen or not Path(path).is_file():
            continue
        seen.add(path)
        digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def build_lineage_fields(
    *,
    payload_path: str,
    include_generated: bool,
    inference: ModelInferenceParams,
    auditor_backend: str,
    cache_enabled: bool,
    cache_hits: int = 0,
    cache_misses: int = 0,
) -> dict:
    from sentinel_eval.prompts.rubric import HIDDEN_RUBRIC_VERSION

    prompt_meta = get_active_prompt()
    return {
        "prompt_sha256": prompt_sha256(),
        "rubric_version": HIDDEN_RUBRIC_VERSION,
        "dataset_sha256": dataset_sha256(payload_path, include_generated=include_generated),
        "dataset_version": prompt_meta.dataset_version,
        "auditor_backend": auditor_backend,
        "model_temperature": inference.temperature,
        "model_seed": inference.seed,
        "model_params": inference.for_lineage(),
        "cache_enabled": cache_enabled,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
    }
