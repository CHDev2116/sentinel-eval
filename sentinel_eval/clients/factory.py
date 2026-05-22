"""Auditor factory — select backend at runtime."""

from __future__ import annotations

from sentinel_eval.clients.ollama_auditor import OllamaAuditor, create_ollama_auditor
from sentinel_eval.clients.openai_compatible import OpenAICompatibleAuditor
from sentinel_eval.clients.protocol import AuditorModel, ModelInferenceParams
from sentinel_eval.clients.response_cache import ResponseCache
from sentinel_eval.config import get_settings

BACKENDS = ("ollama", "openai", "openai_compatible", "vllm", "lmstudio")


def create_auditor(
    model_name: str | None = None,
    *,
    backend: str | None = None,
    use_cache: bool | None = None,
    inference_params: ModelInferenceParams | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
) -> AuditorModel:
    """
    Create an :class:`AuditorModel` for the requested backend.

    Aliases: ``openai``, ``vllm``, ``lmstudio`` → OpenAI-compatible HTTP API.
    """
    settings = get_settings()
    resolved = (backend or settings.auditor_backend).strip().lower()
    if resolved in ("openai", "openai_compatible", "vllm", "lmstudio", "llama_cpp"):
        return _create_openai_compatible(
            model_name,
            use_cache=use_cache,
            inference_params=inference_params,
            api_base=api_base,
            api_key=api_key,
        )
    if resolved == "ollama":
        return create_ollama_auditor(
            model_name,
            use_cache=use_cache,
            inference_params=inference_params,
        )
    raise ValueError(f"Unknown auditor backend={resolved!r}; choose from {BACKENDS}")


def _create_openai_compatible(
    model_name: str | None,
    *,
    use_cache: bool | None,
    inference_params: ModelInferenceParams | None,
    api_base: str | None,
    api_key: str | None,
) -> AuditorModel:
    settings = get_settings()
    cache = None
    enabled = settings.eval_cache_enabled if use_cache is None else use_cache
    if enabled:
        cache = ResponseCache(settings.eval_cache_path, enabled=True)
    return OpenAICompatibleAuditor(
        model_name=model_name,
        api_base=api_base,
        api_key=api_key,
        inference_params=inference_params,
        cache=cache,
    )


def create_ollama_auditor_from_factory(
    model_name: str | None = None,
    **kwargs,
) -> AuditorModel:
    """Backward-compatible alias."""
    return create_auditor(model_name, backend="ollama", **kwargs)
