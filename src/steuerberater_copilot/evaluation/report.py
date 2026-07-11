"""Deterministic aggregate metrics for synthetic offline evaluation."""

from collections.abc import Sequence
from dataclasses import dataclass

from .assessment import EvaluationCaseAssessment, assess_evaluation_run_result
from .case import ExpectedAIWorkflowOutcome
from .library import SyntheticEvaluationFixture
from .runner import run_offline_evaluation_case


@dataclass(frozen=True, slots=True)
class EvaluationMetricsReport:
    """Traceable aggregate metrics derived from ordered case assessments."""

    assessments: tuple[EvaluationCaseAssessment, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessments", tuple(self.assessments))
        if not self.assessments:
            raise ValueError("assessments must not be empty.")

    @property
    def total_case_count(self) -> int:
        return len(self.assessments)

    @property
    def passed_case_count(self) -> int:
        return sum(assessment.passed for assessment in self.assessments)

    @property
    def failed_case_count(self) -> int:
        return self.total_case_count - self.passed_case_count

    @property
    def pass_rate(self) -> float:
        return self.passed_case_count / self.total_case_count

    @property
    def gateway_decision_match_rate(self) -> float:
        """Match rate for the gateway decision observed by the synthetic contract.

        This does not evaluate response-content controls or end-to-end safety.
        """
        return (
            sum(assessment.gateway_decision_matches for assessment in self.assessments)
            / self.total_case_count
        )

    @property
    def review_gate_status_match_rate(self) -> float:
        return (
            sum(assessment.review_gate_status_matches for assessment in self.assessments)
            / self.total_case_count
        )

    @property
    def outcome_match_rate(self) -> float:
        return (
            sum(assessment.outcome_matches for assessment in self.assessments)
            / self.total_case_count
        )

    @property
    def provider_call_count_match_rate(self) -> float:
        return (
            sum(assessment.provider_call_count_matches for assessment in self.assessments)
            / self.total_case_count
        )

    @property
    def structured_draft_case_count(self) -> int:
        return len(self._structured_draft_assessments)

    @property
    def structured_draft_match_rate(self) -> float | None:
        assessments = self._structured_draft_assessments
        if not assessments:
            return None
        return sum(assessment.structured_draft_matches for assessment in assessments) / len(
            assessments
        )

    @property
    def total_provider_call_count(self) -> int:
        return sum(
            assessment.evaluation_run_result.provider_call_count for assessment in self.assessments
        )

    @property
    def unexpected_provider_call_count(self) -> int:
        return sum(
            max(
                0,
                assessment.evaluation_run_result.provider_call_count
                - assessment.expected_provider_call_count,
            )
            for assessment in self.assessments
        )

    @property
    def failed_evaluation_ids(self) -> tuple[str, ...]:
        return tuple(
            assessment.evaluation_run_result.evaluation_case.evaluation_id
            for assessment in self.assessments
            if not assessment.passed
        )

    @property
    def _structured_draft_assessments(
        self,
    ) -> tuple[EvaluationCaseAssessment, ...]:
        return tuple(
            assessment
            for assessment in self.assessments
            if assessment.evaluation_run_result.evaluation_case.expected_outcome
            is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
        )


def run_offline_evaluation_suite(
    fixtures: Sequence[SyntheticEvaluationFixture],
) -> EvaluationMetricsReport:
    """Run and assess every fixture in input order with a fresh provider."""
    assessments = []
    for fixture in fixtures:
        provider = fixture.create_provider()
        result = run_offline_evaluation_case(
            fixture.evaluation_case,
            provider=provider,
        )
        assessments.append(assess_evaluation_run_result(result))

    return EvaluationMetricsReport(assessments=tuple(assessments))
