"""Immutable contracts for synthetic RAG freshness evaluation cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationCase:
    """Labeled inputs for offline outdated-document freshness checks.

    Ground truth is the ordered ``expected_outdated_document_ids`` set. Version
    metadata lives in ``version_records`` and must reference the case source
    documents. This contract does not run detection or pass/fail thresholds.
    """

    evaluation_id: str
    source_documents: tuple[SourceDocument, ...]
    version_records: tuple[DocumentVersionRecord, ...]
    reference_date: str
    expected_outdated_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, str):
            raise TypeError("evaluation_id must be a string.")
        if not self.evaluation_id or self.evaluation_id.isspace():
            raise ValueError("evaluation_id must not be blank.")

        if not isinstance(self.source_documents, tuple):
            raise TypeError("source_documents must be a tuple.")
        documents_by_id: dict[str, SourceDocument] = {}
        for document in self.source_documents:
            if not isinstance(document, SourceDocument):
                raise TypeError(
                    "source_documents must contain only SourceDocument objects."
                )
            if document.document_id in documents_by_id:
                raise ValueError(
                    "source_documents must not contain duplicate document_id values."
                )
            documents_by_id[document.document_id] = document

        if not isinstance(self.version_records, tuple):
            raise TypeError("version_records must be a tuple.")
        record_ids: set[str] = set()
        for record in self.version_records:
            if not isinstance(record, DocumentVersionRecord):
                raise TypeError(
                    "version_records must contain only DocumentVersionRecord objects."
                )
            if record.document_id not in documents_by_id:
                raise ValueError(
                    "version_records document_id values must reference "
                    "document_id values present in source_documents."
                )
            if record.document_id in record_ids:
                raise ValueError(
                    "version_records must not contain duplicate document_id values."
                )
            record_ids.add(record.document_id)
        if record_ids != set(documents_by_id):
            raise ValueError(
                "version_records must cover exactly the source_documents set."
            )

        if not isinstance(self.reference_date, str):
            raise TypeError("reference_date must be a string.")
        if not self.reference_date or self.reference_date.isspace():
            raise ValueError("reference_date must not be blank.")
        try:
            date.fromisoformat(self.reference_date)
        except ValueError as error:
            raise ValueError(
                "reference_date must be an ISO calendar date YYYY-MM-DD."
            ) from error

        if not isinstance(self.expected_outdated_document_ids, tuple):
            raise TypeError("expected_outdated_document_ids must be a tuple.")
        seen_expected: set[str] = set()
        for document_id in self.expected_outdated_document_ids:
            if not isinstance(document_id, str):
                raise TypeError(
                    "expected_outdated_document_ids must contain only strings."
                )
            if not document_id or document_id.isspace():
                raise ValueError(
                    "expected_outdated_document_ids must not contain blank values."
                )
            if document_id not in documents_by_id:
                raise ValueError(
                    "expected_outdated_document_ids must reference "
                    "document_id values present in source_documents."
                )
            if document_id in seen_expected:
                raise ValueError(
                    "expected_outdated_document_ids must not contain duplicates."
                )
            seen_expected.add(document_id)
