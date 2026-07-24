"""Deterministic expectation assessment for one RAG freshness result."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import SourceDocument

from .rag_freshness_runner import RAGFreshnessEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationCaseAssessment:
    """Assess current and stale retrieval observations within the case top_k."""

    evaluation_run_result: RAGFreshnessEvaluationRunResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.evaluation_run_result,
            RAGFreshnessEvaluationRunResult,
        ):
            raise TypeError(
                "evaluation_run_result must be a RAGFreshnessEvaluationRunResult."
            )

    @property
    def current_document_retrieved(self) -> bool:
        evaluation_run_result = self.evaluation_run_result
        expected_current_document_id = (
            evaluation_run_result.evaluation_case.expected_current_document_id
        )
        return any(
            document.document_id == expected_current_document_id
            for document in self._retrieved_documents_at_k
        )

    @property
    def retrieved_stale_document_ids(self) -> tuple[str, ...]:
        stale_document_ids = frozenset(
            self.evaluation_run_result.evaluation_case.stale_document_ids
        )
        return tuple(
            document.document_id
            for document in self._retrieved_documents_at_k
            if document.document_id in stale_document_ids
        )

    @property
    def stale_document_retrieved(self) -> bool:
        return bool(self.retrieved_stale_document_ids)

    @property
    def passed(self) -> bool:
        return self.current_document_retrieved and not self.stale_document_retrieved

    @property
    def _retrieved_documents_at_k(self) -> tuple[SourceDocument, ...]:
        evaluation_run_result = self.evaluation_run_result
        return evaluation_run_result.retrieved_documents[
            : evaluation_run_result.evaluation_case.top_k
        ]


def assess_rag_freshness_evaluation_run_result(
    evaluation_run_result: RAGFreshnessEvaluationRunResult,
) -> RAGFreshnessEvaluationCaseAssessment:
    """Assess one freshness result using only observed documents within top_k."""
    return RAGFreshnessEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
