import os

from langchain_ollama import OllamaLLM

from core.prompts import PROMPT_VERSION, build_audit_prompt

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")


class SentinelTester:
    def __init__(self, model_name=None):
        """Initialize the target LLM."""
        if model_name is None:
            model_name = DEFAULT_MODEL
        self.model_name = model_name
        self.prompt_version = PROMPT_VERSION
        # LangChain OllamaLLM only accepts format="" or "json" (not JSON Schema).
        self.llm = OllamaLLM(model=model_name, format="json")

    def run_test(self, email_thread):
        """Executes the adversarial test with a fixed system instruction."""
        return self.llm.invoke(build_audit_prompt(email_thread))
