"""Immutable contracts for synthetic RAG freshness evaluation cases."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import SourceDocument


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationCase:
    """Labeled retrieval inputs for later stale-document evaluation.

    Ground truth is the one ``expected_current_document_id`` and the non-empty
    ``stale_document_ids`` set. This contract contains no observed retrieval
    output and does not infer document freshness from dates or version fields.
    """

    evaluation_id: str
    source_documents: tuple[SourceDocument, ...]
    retrieval_query: str
    top_k: int
    expected_current_document_id: str
    stale_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, str):
            raise TypeError("evaluation_id must be a string.")
        if not self.evaluation_id or self.evaluation_id.isspace():
            raise ValueError("evaluation_id must not be blank.")

        if not isinstance(self.retrieval_query, str):
            raise TypeError("retrieval_query must be a string.")
        if not self.retrieval_query or self.retrieval_query.isspace():
            raise ValueError("retrieval_query must not be blank.")

        if type(self.top_k) is not int:
            raise TypeError("top_k must be an integer.")
        if self.top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if not isinstance(self.source_documents, tuple):
            raise TypeError("source_documents must be a tuple.")

        seen_document_ids: set[str] = set()
        for document in self.source_documents:
            if not isinstance(document, SourceDocument):
                raise TypeError(
                    "source_documents must contain only SourceDocument objects."
                )
            if document.document_id in seen_document_ids:
                raise ValueError(
                    "source_documents must not contain duplicate document_id values."
                )
            seen_document_ids.add(document.document_id)

        if not isinstance(self.expected_current_document_id, str):
            raise TypeError("expected_current_document_id must be a string.")
        if (
            not self.expected_current_document_id
            or self.expected_current_document_id.isspace()
        ):
            raise ValueError("expected_current_document_id must not be blank.")
        if self.expected_current_document_id not in seen_document_ids:
            raise ValueError(
                "expected_current_document_id must reference a document_id value "
                "present in source_documents."
            )

        if not isinstance(self.stale_document_ids, tuple):
            raise TypeError("stale_document_ids must be a tuple.")
        if not self.stale_document_ids:
            raise ValueError("stale_document_ids must not be empty.")

        seen_stale_ids: set[str] = set()
        for document_id in self.stale_document_ids:
            if not isinstance(document_id, str):
                raise TypeError("stale_document_ids must contain only strings.")
            if not document_id or document_id.isspace():
                raise ValueError("stale_document_ids entries must not be blank.")
            if document_id in seen_stale_ids:
                raise ValueError(
                    "stale_document_ids must not contain duplicate values."
                )
            if document_id not in seen_document_ids:
                raise ValueError(
                    "stale_document_ids must reference document_id values "
                    "present in source_documents."
                )
            seen_stale_ids.add(document_id)

        if self.expected_current_document_id in seen_stale_ids:
            raise ValueError(
                "expected_current_document_id must not appear in stale_document_ids."
            )
