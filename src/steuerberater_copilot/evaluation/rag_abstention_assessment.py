"""Deterministic expectation assessment for one RAG abstention result."""

from __future__ import annotations

from dataclasses import dataclass

from .rag_abstention_runner import RAGAbstentionEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RAGAbstentionEvaluationCaseAssessment:
    """Exact missing-evidence abstention match for one RAG abstention result.

    Match and pass use only the exact comparison of
    ``expected_abstained_for_missing_evidence`` and
    ``observed_abstained_for_missing_evidence``. Gateway or review-gate stops
    are never reinterpreted as missing-evidence abstention.
    """

    evaluation_run_result: RAGAbstentionEvaluationRunResult

    @property
    def abstained_for_missing_evidence_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_abstained_for_missing_evidence
            == evaluation_run_result.observed_abstained_for_missing_evidence
        )

    @property
    def passed(self) -> bool:
        return self.abstained_for_missing_evidence_matches


def assess_rag_abstention_evaluation_run_result(
    evaluation_run_result: RAGAbstentionEvaluationRunResult,
) -> RAGAbstentionEvaluationCaseAssessment:
    """Assess one abstention result using exact expected/observed bool comparison."""
    return RAGAbstentionEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
