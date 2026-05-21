"""Ollama client (backward-compatible facade over OllamaAuditor)."""

from sentinel_eval.clients.ollama_auditor import create_ollama_auditor
from sentinel_eval.config import get_settings

_settings = get_settings()
DEFAULT_MODEL = _settings.ollama_model


class SentinelTester:
    """
    Legacy name for the Ollama auditor.

    Prefer ``create_ollama_auditor()`` or any ``AuditorModel`` implementation.
    """

    def __init__(
        self,
        model_name=None,
        *,
        use_cache: bool | None = None,
        inference_params=None,
    ):
        self._auditor = create_ollama_auditor(
            model_name,
            use_cache=use_cache,
            inference_params=inference_params,
        )

    @property
    def model_name(self) -> str:
        return self._auditor.model_name

    @property
    def prompt_version(self) -> str:
        return self._auditor.prompt_version

    @property
    def auditor(self):
        return self._auditor

    def audit(self, thread: str):
        return self._auditor.audit(thread)

    def run_test(self, email_thread: str) -> str:
        """Deprecated: use ``audit(thread).raw_output``."""
        return self._auditor.audit(email_thread).raw_output
