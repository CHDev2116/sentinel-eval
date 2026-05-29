"""SentinelEval — local LLM prompt-injection detection benchmark."""

from sentinel_eval.clients.ollama import DEFAULT_MODEL, SentinelTester
from sentinel_eval.clients.ollama_auditor import create_ollama_auditor
from sentinel_eval.clients.protocol import AuditorModel, ModelInferenceParams
from sentinel_eval.config import Settings, get_settings
from sentinel_eval.domain.models import AuditOutput, CaseEvaluationResult, TestCase
from sentinel_eval.domain.report import RunLineage, RunMeta, RunReport
from sentinel_eval.evaluators.case import evaluate_case
from sentinel_eval.evaluators.case_evaluator import CaseEvaluator
from sentinel_eval.guard import sentinel_guard
from sentinel_eval.guard.exceptions import SentinelGuardBlocked
from sentinel_eval.prompts.audit import PROMPT_VERSION, build_audit_prompt

__all__ = [
    "DEFAULT_MODEL",
    "SentinelTester",
    "AuditorModel",
    "ModelInferenceParams",
    "create_ollama_auditor",
    "Settings",
    "get_settings",
    "AuditOutput",
    "CaseEvaluationResult",
    "TestCase",
    "RunMeta",
    "RunLineage",
    "RunReport",
    "evaluate_case",
    "CaseEvaluator",
    "PROMPT_VERSION",
    "build_audit_prompt",
    "sentinel_guard",
    "SentinelGuardBlocked",
]
