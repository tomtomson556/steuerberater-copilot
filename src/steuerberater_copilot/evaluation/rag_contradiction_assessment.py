"""Deterministic expectation assessment for one RAG contradiction result."""

from __future__ import annotations

from dataclasses import dataclass

from .rag_contradiction_runner import RAGContradictionEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationCaseAssessment:
    """Contradiction presence and implicated-document match for one result.

    Pass requires:

    1. exact bool match for contradiction presence, and
    2. exact set equality of implicated ``document_id`` values.

    Exact supporting-text equality is reported as a diagnostic signal only. It
    is intentionally not required for ``passed``, so evaluation does not reward
    copying detector sentence strings into ground truth.
    """

    evaluation_run_result: RAGContradictionEvaluationRunResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation_run_result,
            RAGContradictionEvaluationRunResult,
        ):
            raise TypeError(
                "evaluation_run_result must be a RAGContradictionEvaluationRunResult."
            )

    @property
    def contradiction_present_matches(self) -> bool:
        evaluation_case = self.evaluation_run_result.evaluation_case
        return (
            evaluation_case.expected_contradiction_present
            == self.evaluation_run_result.observed_contradiction_present
        )

    @property
    def contradicting_document_ids_match(self) -> bool:
        expected = {
            label.document_id
            for label in self.evaluation_run_result.evaluation_case.contradicting_passages
        }
        observed = {
            label.document_id
            for label in self.evaluation_run_result.observed_contradicting_passages
        }
        return expected == observed

    @property
    def contradicting_passages_match(self) -> bool:
        """Diagnostic exact passage match; not required for ``passed``."""
        expected = {
            (label.document_id, label.supporting_text)
            for label in self.evaluation_run_result.evaluation_case.contradicting_passages
        }
        observed = {
            (label.document_id, label.supporting_text)
            for label in self.evaluation_run_result.observed_contradicting_passages
        }
        return expected == observed

    @property
    def passed(self) -> bool:
        return (
            self.contradiction_present_matches
            and self.contradicting_document_ids_match
        )


def assess_rag_contradiction_evaluation_run_result(
    evaluation_run_result: RAGContradictionEvaluationRunResult,
) -> RAGContradictionEvaluationCaseAssessment:
    """Assess one contradiction result using presence and document-id comparison."""
    return RAGContradictionEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
