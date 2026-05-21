import logging
from typing import Any

from sentinel_eval.config import get_settings
from sentinel_eval.domain.models import CaseEvaluationResult, TestCase
from sentinel_eval.evaluators.audit_parser import AuditParser
from sentinel_eval.evaluators.calibration_evaluator import CalibrationEvaluator
from sentinel_eval.evaluators.release_gate_evaluator import ReleaseGateEvaluator
from sentinel_eval.evaluators.schema_evaluator import SchemaEvaluator
from sentinel_eval.evaluators.security_evaluator import SecurityEvaluator
from sentinel_eval.evaluators.semantic_evaluator import SemanticEvaluator

logger = logging.getLogger(__name__)


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

    def evaluate(
        self,
        case: TestCase | dict[str, Any],
        tester,
        rouge_l_threshold: float | None = None,
    ) -> CaseEvaluationResult:
        test_case = case if isinstance(case, TestCase) else TestCase.from_payload(case)
        threshold = (
            rouge_l_threshold
            if rouge_l_threshold is not None
            else self._settings.default_rouge_l_threshold
        )

        logger.info("Running case %s", test_case.case_id)
        raw_output = tester.run_test(test_case.email_thread)
        audit, clean_output = self.parser.parse(raw_output)

        schema_eval = self.schema.evaluate(audit)
        schema_result = schema_eval.validation
        reference = test_case.reference_answer or ""
        structured = self.parser.canonical_json(audit)

        semantic_eval = self.semantic.evaluate(
            reference,
            structured,
            clean_output,
            rouge_l_threshold=threshold,
        )
        rouge_l_pass = semantic_eval.rouge_l_pass

        security_eval = self.security.evaluate(
            test_case,
            audit,
            schema_valid=schema_result.is_valid,
            rouge_l_pass=rouge_l_pass if reference or not test_case.needs_review else None,
        )

        release_eval = self.release_gate.evaluate(
            schema_validation=schema_result,
            prediction_match=security_eval.prediction_match,
            rouge=semantic_eval.rouge,
            needs_review=test_case.needs_review,
        )

        calibration_eval = self.calibration.evaluate(audit)

        if security_eval.prediction_match is not None:
            logger.info(
                "Case %s label_match=%s security_pass=%s rougeL=%.2f",
                test_case.case_id,
                security_eval.prediction_match,
                security_eval.security_pass,
                semantic_eval.rouge_l_f1,
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
        )
