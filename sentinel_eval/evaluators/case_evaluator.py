import logging
from typing import Any

from sentinel_eval.clients.protocol import AuditorModel
from sentinel_eval.config import get_settings
from sentinel_eval.domain.audit_result import AuditResult
from sentinel_eval.domain.models import (
    CaseEvaluationResult,
    EnsembleEvalResult,
    MutationMeta,
    TestCase,
)
from sentinel_eval.evaluators.audit_parser import AuditParser
from sentinel_eval.evaluators.calibration_evaluator import CalibrationEvaluator
from sentinel_eval.evaluators.release_gate_evaluator import ReleaseGateEvaluator
from sentinel_eval.evaluators.schema_evaluator import SchemaEvaluator
from sentinel_eval.evaluators.security_evaluator import SecurityEvaluator
from sentinel_eval.evaluators.protocol import CaseEvalContext, Evaluator
from sentinel_eval.evaluators.semantic_evaluator import SemanticEvaluator
from sentinel_eval.judges.ensemble import JudgeEnsemble
from sentinel_eval.mutations.engine import apply_mutations, parse_mutation_kinds

logger = logging.getLogger(__name__)


def _audit_raw_output(auditor: AuditorModel | Any, thread: str) -> str:
    """Invoke AuditorModel.audit or legacy ``run_test``."""
    from unittest.mock import MagicMock, Mock

    if isinstance(auditor, (MagicMock, Mock)) and hasattr(auditor, "run_test"):
        return auditor.run_test(thread)
    if hasattr(auditor, "audit") and callable(auditor.audit):
        out = auditor.audit(thread)
        if isinstance(out, AuditResult):
            return out.raw_output
        return str(out)
    if hasattr(auditor, "run_test") and callable(auditor.run_test):
        return auditor.run_test(thread)
    raise TypeError("auditor must implement audit() or run_test()")


class CaseEvaluator:
    """
    Orchestrates one benchmark case via separated evaluators:
    Semantic → Schema → Security → Release gate → Calibration.
    """

    def __init__(
        self,
        parser: AuditParser | None = None,
        semantic: SemanticEvaluator | None = None,
        schema: SchemaEvaluator | None = None,
        security: SecurityEvaluator | None = None,
        release_gate: ReleaseGateEvaluator | None = None,
        calibration: CalibrationEvaluator | None = None,
    ):
        self.parser = parser or AuditParser()
        self.semantic = semantic or SemanticEvaluator()
        self.schema = schema or SchemaEvaluator()
        self.security = security or SecurityEvaluator()
        self.release_gate = release_gate or ReleaseGateEvaluator()
        self.calibration = calibration or CalibrationEvaluator()
        self._settings = get_settings()

    @property
    def evaluators(self) -> list[Evaluator]:
        """Ordered evaluator chain (Protocol-compliant)."""
        return [
            self.semantic,
            self.schema,
            self.security,
            self.release_gate,
            self.calibration,
        ]

    def evaluate(
        self,
        case: TestCase | dict[str, Any],
        auditor: AuditorModel | Any,
        rouge_l_threshold: float | None = None,
        *,
        mutation_kinds: list[str] | None = None,
        mutation_seed: int | None = None,
        judge_ensemble: bool | None = None,
        judge_ensemble_mode: str | None = None,
    ) -> CaseEvaluationResult:
        test_case = case if isinstance(case, TestCase) else TestCase.from_payload(case)
        threshold = (
            rouge_l_threshold
            if rouge_l_threshold is not None
            else self._settings.default_rouge_l_threshold
        )

        kinds = mutation_kinds
        if kinds is None and self._settings.mutation_kinds:
            kinds = parse_mutation_kinds(self._settings.mutation_kinds)
        if not kinds and test_case.mutation_kinds:
            kinds = list(test_case.mutation_kinds)
        kinds = kinds or []
        seed = mutation_seed if mutation_seed is not None else self._settings.mutation_seed
        surface = test_case.surface_form or ""
        if surface and not kinds:
            from sentinel_eval.mutations.engine import apply_surface_form

            mutation = apply_surface_form(test_case.email_thread, surface)
        else:
            mutation = apply_mutations(
                test_case.email_thread,
                kinds,
                seed=seed,
                surface_form=surface,
            )
        audit_thread = mutation.mutated_thread

        use_ensemble = (
            judge_ensemble
            if judge_ensemble is not None
            else self._settings.judge_ensemble
        )
        ensemble_mode = judge_ensemble_mode or self._settings.judge_ensemble_mode

        logger.info("Running case %s", test_case.case_id)
        if kinds:
            logger.info("Mutations applied: %s", kinds)
        raw_output = _audit_raw_output(auditor, audit_thread)
        audit, clean_output = self.parser.parse(raw_output)

        reference = test_case.reference_answer or ""
        structured = self.parser.canonical_json(audit)

        ctx = CaseEvalContext(
            case=test_case,
            audit=audit,
            raw_output=clean_output,
            structured=structured,
            reference=reference,
            rouge_l_threshold=threshold,
            semantic_threshold=self._settings.default_semantic_threshold,
        )

        semantic_eval = self.semantic.evaluate_context(ctx)
        ctx.extra["semantic_eval"] = semantic_eval
        rouge_l_pass = semantic_eval.rouge_l_pass

        schema_eval = self.schema.evaluate_context(ctx)
        schema_result = schema_eval.validation
        ctx.schema_valid = schema_result.is_valid
        ctx.extra["schema_validation"] = schema_result

        security_eval = self.security.evaluate_context(ctx)
        ctx.extra["security_eval"] = security_eval
        ctx.extra["prediction_match"] = security_eval.prediction_match

        release_eval = self.release_gate.evaluate_context(ctx)

        calibration_eval = self.calibration.evaluate_context(ctx)

        ensemble_eval = None
        if use_ensemble:
            ensemble = JudgeEnsemble(mode=ensemble_mode).evaluate(
                audit_thread,
                audit,
                expected_is_safe=test_case.expected_is_safe
                if not test_case.needs_review
                else None,
            )
            ensemble_eval = EnsembleEvalResult(
                verdicts=[v.model_dump() for v in ensemble.verdicts],
                weighted_score=ensemble.weighted_score,
                weighted_is_safe=ensemble.weighted_is_safe,
                agreement_rate=ensemble.agreement_rate,
                ensemble_pass=ensemble.ensemble_pass,
                prediction_match=ensemble.prediction_match,
                mode=ensemble.mode,
            )

        mutation_meta = None
        if kinds or mutation.surface_form or test_case.surface_form:
            mutation_meta = MutationMeta(
                kinds_applied=mutation.kinds_applied,
                seed=mutation.seed,
                surface_form=mutation.surface_form or test_case.surface_form,
                base_case_id=test_case.base_case_id or test_case.case_id,
            )

        if security_eval.prediction_match is not None:
            logger.info(
                "Case %s label_match=%s security_pass=%s rougeL=%.2f",
                test_case.case_id,
                security_eval.prediction_match,
                security_eval.security_pass,
                semantic_eval.rouge_l_f1,
                semantic_eval.semantic_score,
                semantic_eval.semantic_backend,
            )

        return CaseEvaluationResult(
            case_id=test_case.case_id,
            description=test_case.description,
            tags=test_case.tags,
            needs_review=test_case.needs_review,
            parsed_output=audit,
            audit_output=clean_output,
            schema_validation=schema_result,
            expected_is_safe=test_case.expected_is_safe,
            prediction_match=security_eval.prediction_match,
            security_pass=security_eval.security_pass,
            release_pass=release_eval.release_pass,
            release_rouge_l_threshold=release_eval.release_rouge_l_threshold,
            rouge_l_threshold=threshold,
            rouge_l_pass=rouge_l_pass,
            composite_pass=security_eval.composite_pass,
            rouge=semantic_eval.rouge,
            rouge_raw=semantic_eval.rouge_raw,
            semantic_eval=semantic_eval,
            schema_eval=schema_eval,
            security_eval=security_eval,
            release_eval=release_eval,
            calibration_eval=calibration_eval,
            mutation_meta=mutation_meta,
            ensemble_eval=ensemble_eval,
        )
