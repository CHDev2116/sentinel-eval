"""Central configuration (env: OLLAMA_MODEL, OLLAMA_HOST, SENTINEL_*)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_model: str = "llama3.1:latest"
    ollama_host: str | None = None
    default_rouge_l_threshold: float = 0.25
    release_rouge_l_threshold: float = 0.70
    golden_payload: str = "payloads/scenarios_golden.json"
    generated_payload: str = "payloads/scenarios_generated.json"
    log_level: str = "INFO"
    require_calibration_fields: bool = True
    prompt_version: str = "is_safe_v2.2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
