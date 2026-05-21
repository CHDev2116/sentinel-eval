import json
import logging
import os
from datetime import datetime, timezone

from ollama import AsyncClient

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import TriAgentTaskResult
from sentinel_eval.pipelines.agents import TriAgentOrchestrator
from sentinel_eval.prompts.audit import PROMPT_VERSION
from sentinel_eval.utils.parsing import parse_loose_json

logger = logging.getLogger(__name__)


async def run_async_pipeline(
    test_count,
    max_concurrent_tasks,
    generator_model,
    auditor_model,
    judge_model,
    startup_stagger_seconds,
):
    settings = get_settings()
    host = settings.ollama_host
    client = AsyncClient(host=host) if host else AsyncClient()
    orchestrator = TriAgentOrchestrator(
        client=client,
        generator_model=generator_model,
        auditor_model=auditor_model,
        judge_model=judge_model,
        startup_stagger_seconds=startup_stagger_seconds,
    )
    return await orchestrator.run_batch(test_count, max_concurrent_tasks)


def _result_to_dict(item) -> dict:
    if isinstance(item, TriAgentTaskResult):
        return item.to_dict()
    return item


def write_reports(results, models):
    valid_results = []
    for item in results:
        data = _result_to_dict(item)
        if data.get("error"):
            continue
        valid_results.append(data)

    os.makedirs("reports", exist_ok=True)
    os.makedirs(os.path.join("reports", "async_runs"), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = os.path.join("reports", "async_runs", f"{timestamp}.jsonl")
    latest_path = os.path.join("reports", "async_latest.jsonl")

    header = {
        "type": "meta",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "models": models,
    }
    for path in (jsonl_path, latest_path):
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(header, ensure_ascii=False) + "\n")
            for item in valid_results:
                fp.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("Async run report: %s", jsonl_path)
    logger.info("Async latest report: %s", latest_path)

    if valid_results:
        scores = [(item.get("g_eval") or {}).get("score", 0) for item in valid_results]
        logger.info("Average judge score: %.2f/5.0", sum(scores) / len(scores))
    logger.info("Success: %s/%s", len(valid_results), len(results))


def safe_parse_json(text):
    """Backwards-compatible alias for tests."""
    return parse_loose_json(text)
