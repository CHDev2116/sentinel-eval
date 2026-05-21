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
    payloads_root: str = "payloads"
    dataset_version: str = "v2.1"
    golden_payload: str = "v2"
    generated_payload: str = "generated"
    mutation_payload: str = "mutations"
    log_level: str = "INFO"
    require_calibration_fields: bool = True
    prompt_version: str = "is_safe_v2.2"
    model_temperature: float | None = None
    model_seed: int | None = None
    eval_cache_enabled: bool = True
    eval_cache_path: str = ".cache/sentinel_eval_responses.sqlite3"
    judge_ensemble: bool = False
    judge_ensemble_mode: str = "heuristic"
    mutation_kinds: str = ""
    mutation_seed: int | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
