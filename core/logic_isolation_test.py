import os

from ollama import Client

from core.prompts import PROMPT_VERSION, build_audit_prompt
from core.response_utils import AUDIT_OUTPUT_SCHEMA

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")


class SentinelTester:
    def __init__(self, model_name=None):
        """Initialize the target LLM (Ollama native client + JSON schema)."""
        if model_name is None:
            model_name = DEFAULT_MODEL
        self.model_name = model_name
        self.prompt_version = PROMPT_VERSION
        host = os.environ.get("OLLAMA_HOST")
        self.client = Client(host=host) if host else Client()

    def run_test(self, email_thread):
        """Executes the adversarial test with a fixed system instruction."""
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": build_audit_prompt(email_thread)}],
            format=AUDIT_OUTPUT_SCHEMA,
        )
        return response["message"]["content"]
