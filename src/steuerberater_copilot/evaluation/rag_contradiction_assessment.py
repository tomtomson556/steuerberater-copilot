"""Deterministic expectation assessment for one RAG contradiction result."""

from __future__ import annotations

from dataclasses import dataclass

from .rag_contradiction_runner import RAGContradictionEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationCaseAssessment:
    """Exact contradiction flag and evidence match for one observed result.

    Evidence matching compares every expected and observed passage by exact
    ``(document_id, supporting_text)`` value. Passage order is ignored while
    additional or duplicate observed passages remain mismatches.
    """

    evaluation_run_result: RAGContradictionEvaluationRunResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation_run_result,
            RAGContradictionEvaluationRunResult,
        ):
            raise TypeError(
                "evaluation_run_result must be a "
                "RAGContradictionEvaluationRunResult."
            )

    @property
    def contradiction_present_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        return (
            evaluation_run_result.evaluation_case.expected_contradiction_present
            == evaluation_run_result.observed_detection_result.contradiction_present
        )

    @property
    def contradiction_evidence_matches(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        expected_evidence = sorted(
            (label.document_id, label.supporting_text)
            for label in evaluation_run_result.evaluation_case.contradicting_passages
        )
        observed_evidence = sorted(
            (passage.document_id, passage.supporting_text)
            for contradiction in (
                evaluation_run_result.observed_detection_result.contradictions
            )
            for passage in (contradiction.first, contradiction.second)
        )
        return expected_evidence == observed_evidence

    @property
    def passed(self) -> bool:
        return all(
            (
                self.contradiction_present_matches,
                self.contradiction_evidence_matches,
            )
        )


def assess_rag_contradiction_evaluation_run_result(
    evaluation_run_result: RAGContradictionEvaluationRunResult,
) -> RAGContradictionEvaluationCaseAssessment:
    """Assess one contradiction result using exact flag and evidence comparisons."""
    return RAGContradictionEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
