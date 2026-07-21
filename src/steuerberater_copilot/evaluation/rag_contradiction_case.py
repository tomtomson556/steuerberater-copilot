"""Immutable contracts for synthetic RAG contradiction evaluation cases."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import SourceDocument


@dataclass(frozen=True, slots=True)
class ContradictionEvidenceLabel:
    """One synthetic source-and-passage reference in a contradiction pair.

    Labels are ground truth only. They do not store observed detector output and
    do not assert semantic contradiction detection or fachliche correctness.
    """

    document_id: str
    supporting_text: str

    def __post_init__(self) -> None:
        for field_name in ("document_id", "supporting_text"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationCase:
    """Labeled synthetic inputs for later offline RAG contradiction checks.

    Ground truth is ``expected_contradiction_present`` plus the ordered
    ``contradicting_passages`` that justify a positive case. Positive cases
    must reference exactly two distinct source passages. Negative control
    cases must leave ``contradicting_passages`` empty.

    This contract validates structural consistency only. It does not detect
    semantic contradictions, store observed results, or evaluate pass/fail
    thresholds.
    """

    evaluation_id: str
    source_documents: tuple[SourceDocument, ...]
    expected_contradiction_present: bool
    contradicting_passages: tuple[ContradictionEvidenceLabel, ...]

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

        if type(self.expected_contradiction_present) is not bool:
            raise TypeError("expected_contradiction_present must be a boolean.")

        if not isinstance(self.contradicting_passages, tuple):
            raise TypeError("contradicting_passages must be a tuple.")

        if self.expected_contradiction_present:
            if len(self.contradicting_passages) != 2:
                raise ValueError(
                    "positive contradiction cases must reference exactly two "
                    "contradicting passages."
                )
        elif self.contradicting_passages:
            raise ValueError(
                "negative contradiction cases must not include "
                "contradicting_passages."
            )

        seen_labels: set[tuple[str, str]] = set()
        for label in self.contradicting_passages:
            if not isinstance(label, ContradictionEvidenceLabel):
                raise TypeError(
                    "contradicting_passages must contain only "
                    "ContradictionEvidenceLabel objects."
                )
            document = documents_by_id.get(label.document_id)
            if document is None:
                raise ValueError(
                    "contradicting_passages document_id values must reference "
                    "document_id values present in source_documents."
                )
            if label.supporting_text not in document.content:
                raise ValueError(
                    "contradicting_passages supporting_text must occur as an "
                    "exact contiguous substring of the referenced source "
                    "document content."
                )
            label_key = (label.document_id, label.supporting_text)
            if label_key in seen_labels:
                raise ValueError(
                    "contradicting_passages must not contain duplicate labels."
                )
            seen_labels.add(label_key)
