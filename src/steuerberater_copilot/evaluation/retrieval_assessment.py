"""Deterministic Recall@k assessment for one retrieval evaluation result."""

from __future__ import annotations

from dataclasses import dataclass

from .retrieval_runner import RetrievalEvaluationRunResult


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationCaseAssessment:
    """Recall@k derived from one immutable retrieval evaluation result.

    Empty relevance labels make Recall inapplicable (``recall_at_k`` is
    ``None``). This contract does not evaluate abstention or pass/fail
    thresholds.
    """

    evaluation_run_result: RetrievalEvaluationRunResult

    @property
    def recalled_document_ids_at_k(self) -> tuple[str, ...]:
        evaluation_case = self.evaluation_run_result.evaluation_case
        relevant_document_ids = frozenset(evaluation_case.relevant_document_ids)
        if not relevant_document_ids:
            return ()

        recalled_document_ids: list[str] = []
        seen_document_ids: set[str] = set()
        for document in self.evaluation_run_result.retrieved_documents[
            : evaluation_case.top_k
        ]:
            document_id = document.document_id
            if (
                document_id in relevant_document_ids
                and document_id not in seen_document_ids
            ):
                recalled_document_ids.append(document_id)
                seen_document_ids.add(document_id)

        return tuple(recalled_document_ids)

    @property
    def recall_at_k(self) -> float | None:
        relevant_document_count = len(
            self.evaluation_run_result.evaluation_case.relevant_document_ids
        )
        if relevant_document_count == 0:
            return None
        return len(self.recalled_document_ids_at_k) / relevant_document_count


def assess_retrieval_evaluation_run_result(
    evaluation_run_result: RetrievalEvaluationRunResult,
) -> RetrievalEvaluationCaseAssessment:
    """Assess one retrieval result for Recall@k without pass/fail thresholds."""
    return RetrievalEvaluationCaseAssessment(
        evaluation_run_result=evaluation_run_result,
    )
