"""Deterministic expectation assessment for one RAG freshness result."""

from __future__ import annotations

from dataclasses import dataclass

from .rag_freshness_runner import RAGFreshnessEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationCaseAssessment:
    """Exact outdated-document ID set match for one freshness result."""

    evaluation_run_result: RAGFreshnessEvaluationRunResult

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_run_result, RAGFreshnessEvaluationRunResult):
            raise TypeError(
                "evaluation_run_result must be a RAGFreshnessEvaluationRunResult."
            )

    @property
    def outdated_document_ids_match(self) -> bool:
        expected = set(
            self.evaluation_run_result.evaluation_case.expected_outdated_document_ids
        )
        observed = set(self.evaluation_run_result.observed_outdated_document_ids)
        return expected == observed

    @property
    def passed(self) -> bool:
        return self.outdated_document_ids_match


def assess_rag_freshness_evaluation_run_result(
    evaluation_run_result: RAGFreshnessEvaluationRunResult,
) -> RAGFreshnessEvaluationCaseAssessment:
    """Assess one freshness result using exact expected/observed ID set comparison."""
    return RAGFreshnessEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
