"""Immutable contracts for synthetic RAG abstention evaluation cases."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.offline_mvp import IntakeCase
from steuerberater_copilot.rag import SourceDocument


@dataclass(frozen=True, slots=True)
class RAGAbstentionEvaluationCase:
    """Labeled inputs for later offline RAG missing-evidence abstention checks.

    Ground truth is ``expected_abstained_for_missing_evidence`` only. It must
    later be compared against the observed
    ``SyntheticRAGWorkflowOutput.abstained_for_missing_evidence`` flag. This
    contract does not execute the RAG workflow, store observed results, or
    evaluate pass/fail thresholds.

    Abstention for missing evidence is distinct from gateway or review-gate
    stops: those paths leave ``abstained_for_missing_evidence`` false in the
    existing workflow even when no draft is produced.
    """

    evaluation_id: str
    intake: IntakeCase
    source_documents: tuple[SourceDocument, ...]
    retrieval_query: str
    top_k: int
    expected_abstained_for_missing_evidence: bool

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, str):
            raise TypeError("evaluation_id must be a string.")
        if not self.evaluation_id or self.evaluation_id.isspace():
            raise ValueError("evaluation_id must not be blank.")

        if not isinstance(self.intake, IntakeCase):
            raise TypeError("intake must be an IntakeCase.")

        if not isinstance(self.retrieval_query, str):
            raise TypeError("retrieval_query must be a string.")
        if not self.retrieval_query or self.retrieval_query.isspace():
            raise ValueError("retrieval_query must not be blank.")

        if type(self.top_k) is not int:
            raise TypeError("top_k must be an integer.")
        if self.top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if type(self.expected_abstained_for_missing_evidence) is not bool:
            raise TypeError(
                "expected_abstained_for_missing_evidence must be a boolean."
            )

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
