"""Immutable contracts for synthetic grounding and citation evaluation cases."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.offline_mvp import GroundedDraft
from steuerberater_copilot.rag import SourceDocument


@dataclass(frozen=True, slots=True)
class GroundingEvidenceLabel:
    """One acceptable synthetic evidence reference for a summary point.

    Labels are ground truth only. They are not observed candidate citations and
    do not assert semantic entailment or fachliche correctness. Multiple labels
    with the same ``summary_point_index`` express alternative acceptable
    evidence for later assessment.
    """

    summary_point_index: int
    document_id: str
    supporting_text: str

    def __post_init__(self) -> None:
        if type(self.summary_point_index) is not int:
            raise TypeError("summary_point_index must be an integer.")
        if self.summary_point_index < 0:
            raise ValueError("summary_point_index must not be negative.")

        for field_name in ("document_id", "supporting_text"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")


@dataclass(frozen=True, slots=True)
class GroundingEvaluationCase:
    """Labeled synthetic grounding inputs for later offline grounding metrics.

    ``candidate_grounded_draft`` is the observed draft under evaluation. It may
    contain wrong, missing, incomplete, or structurally invalid citations for
    later assessment. ``acceptable_evidence`` is ordered ground truth: each
    entry is one acceptable source-and-passage pair for a summary point.

    Empty ``acceptable_evidence`` remains valid and supports later unsupported-
    claim cases. This contract does not assess correct source, correct passage,
    citation coverage, abstention, or pass/fail thresholds.
    """

    evaluation_id: str
    source_documents: tuple[SourceDocument, ...]
    candidate_grounded_draft: GroundedDraft
    acceptable_evidence: tuple[GroundingEvidenceLabel, ...]

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

        if not isinstance(self.candidate_grounded_draft, GroundedDraft):
            raise TypeError("candidate_grounded_draft must be a GroundedDraft.")

        if not isinstance(self.acceptable_evidence, tuple):
            raise TypeError("acceptable_evidence must be a tuple.")

        summary_point_count = len(
            self.candidate_grounded_draft.structured_draft.summary_points
        )
        seen_labels: set[tuple[int, str, str]] = set()
        for label in self.acceptable_evidence:
            if not isinstance(label, GroundingEvidenceLabel):
                raise TypeError(
                    "acceptable_evidence must contain only GroundingEvidenceLabel "
                    "objects."
                )
            if not 0 <= label.summary_point_index < summary_point_count:
                raise ValueError(
                    "acceptable_evidence summary_point_index must reference an "
                    "existing summary point."
                )
            document = documents_by_id.get(label.document_id)
            if document is None:
                raise ValueError(
                    "acceptable_evidence document_id values must reference "
                    "document_id values present in source_documents."
                )
            if label.supporting_text not in document.content:
                raise ValueError(
                    "acceptable_evidence supporting_text must occur as an exact "
                    "contiguous substring of the referenced source document "
                    "content."
                )
            label_key = (
                label.summary_point_index,
                label.document_id,
                label.supporting_text,
            )
            if label_key in seen_labels:
                raise ValueError(
                    "acceptable_evidence must not contain duplicate labels."
                )
            seen_labels.add(label_key)
