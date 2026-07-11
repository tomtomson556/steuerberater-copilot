"""Deterministic expectation assessment for one offline evaluation result."""

from dataclasses import dataclass

from steuerberater_copilot.offline_mvp import GatewayDecision, ReviewGateStatus

from .runner import EvaluationRunResult


@dataclass(frozen=True, slots=True)
class EvaluationCaseAssessment:
    """Exact expectation matches derived from one immutable evaluation result."""

    evaluation_run_result: EvaluationRunResult

    @property
    def expected_provider_call_count(self) -> int:
        evaluation_case = self.evaluation_run_result.evaluation_case
        if evaluation_case.expected_gateway_decision is not GatewayDecision.ALLOW_DRAFT:
            return 0
        if (
            evaluation_case.expected_review_gate_status
            is not ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ):
            return 0
        return 1

    @property
    def gateway_decision_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_gateway_decision
            == evaluation_run_result.observed_gateway_decision
        )

    @property
    def review_gate_status_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_review_gate_status
            == evaluation_run_result.observed_review_gate_status
        )

    @property
    def outcome_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_outcome
            == evaluation_run_result.observed_outcome
        )

    @property
    def structured_draft_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_structured_draft
            == evaluation_run_result.observed_structured_draft
        )

    @property
    def provider_call_count_matches(self) -> bool:
        return (
            self.expected_provider_call_count
            == self.evaluation_run_result.provider_call_count
        )

    @property
    def passed(self) -> bool:
        return all(
            (
                self.gateway_decision_matches,
                self.review_gate_status_matches,
                self.outcome_matches,
                self.structured_draft_matches,
                self.provider_call_count_matches,
            )
        )


def assess_evaluation_run_result(
    evaluation_run_result: EvaluationRunResult,
) -> EvaluationCaseAssessment:
    """Assess one observed result against its case using exact comparisons."""
    return EvaluationCaseAssessment(evaluation_run_result=evaluation_run_result)
