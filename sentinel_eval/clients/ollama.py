from ollama import Client

from sentinel_eval.config import get_settings
from sentinel_eval.prompts.audit import PROMPT_VERSION, build_audit_prompt
from sentinel_eval.schemas.audit import AUDIT_OUTPUT_SCHEMA

_settings = get_settings()
DEFAULT_MODEL = _settings.ollama_model


class SentinelTester:
    def __init__(self, model_name=None):
        """Initialize the target LLM (Ollama native client + JSON schema)."""
        settings = get_settings()
        if model_name is None:
            model_name = settings.ollama_model
        self.model_name = model_name
        self.prompt_version = PROMPT_VERSION
        host = settings.ollama_host
        self.client = Client(host=host) if host else Client()

    def run_test(self, email_thread):
        """Executes the adversarial test with a fixed system instruction."""
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": build_audit_prompt(email_thread)}],
            format=AUDIT_OUTPUT_SCHEMA,
        )
        return response["message"]["content"]
