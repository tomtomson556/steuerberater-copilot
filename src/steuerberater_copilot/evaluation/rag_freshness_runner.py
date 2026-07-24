"""Deterministic observation of one synthetic RAG freshness evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

from .rag_freshness_case import RAGFreshnessEvaluationCase


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationRunResult:
    """Observed retrieval output for one RAG freshness evaluation case.

    ``retrieved_documents`` is separate from current/stale ground truth and
    does not imply a pass/fail assessment.
    """

    evaluation_case: RAGFreshnessEvaluationCase
    retrieved_documents: tuple[SourceDocument, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RAGFreshnessEvaluationCase):
            raise TypeError("evaluation_case must be a RAGFreshnessEvaluationCase.")
        if not isinstance(self.retrieved_documents, tuple):
            raise TypeError("retrieved_documents must be a tuple.")
        for document in self.retrieved_documents:
            if not isinstance(document, SourceDocument):
                raise TypeError(
                    "retrieved_documents must contain only SourceDocument objects."
                )


def run_offline_rag_freshness_evaluation_case(
    evaluation_case: RAGFreshnessEvaluationCase,
) -> RAGFreshnessEvaluationRunResult:
    """Run one freshness case through existing retrieval without assessing labels."""
    retriever = LocalDocumentRetriever(documents=evaluation_case.source_documents)
    retrieved_documents = retriever.retrieve(
        evaluation_case.retrieval_query,
        top_k=evaluation_case.top_k,
    )
    return RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )
