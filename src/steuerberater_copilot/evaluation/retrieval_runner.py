"""Deterministic observation of one synthetic retrieval evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

from .retrieval_case import RetrievalEvaluationCase


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationRunResult:
    """Observed retrieval output for one synthetic retrieval evaluation case."""

    evaluation_case: RetrievalEvaluationCase
    retrieved_documents: tuple[SourceDocument, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RetrievalEvaluationCase):
            raise TypeError("evaluation_case must be a RetrievalEvaluationCase.")
        if not isinstance(self.retrieved_documents, tuple):
            raise TypeError("retrieved_documents must be a tuple.")
        for document in self.retrieved_documents:
            if not isinstance(document, SourceDocument):
                raise TypeError(
                    "retrieved_documents must contain only SourceDocument objects."
                )


def run_offline_retrieval_evaluation_case(
    evaluation_case: RetrievalEvaluationCase,
) -> RetrievalEvaluationRunResult:
    """Run one retrieval case and return observations without assessing labels."""
    retriever = LocalDocumentRetriever(documents=evaluation_case.source_documents)
    retrieved_documents = retriever.retrieve(
        evaluation_case.retrieval_query,
        top_k=evaluation_case.top_k,
    )
    return RetrievalEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )
