"""Deterministic grounding checks for parsed grounded drafts.

Exact supporting_text presence in a source document is a structural check
only. It is not evidence of semantic entailment or fachliche correctness.
"""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .grounded_draft import GroundedDraft


class GroundedDraftValidationError(ValueError):
    """Raised when a grounded draft violates deterministic grounding rules."""

    rule: str
    citation_index: int | None
    summary_point_index: int | None

    def __init__(
        self,
        rule: str,
        *,
        citation_index: int | None = None,
        summary_point_index: int | None = None,
    ) -> None:
        self.rule = rule
        self.citation_index = citation_index
        self.summary_point_index = summary_point_index
        details = [f"rule={rule}"]
        if citation_index is not None:
            details.append(f"citation_index={citation_index}")
        if summary_point_index is not None:
            details.append(f"summary_point_index={summary_point_index}")
        super().__init__(
            "Grounded draft validation failed: " + ", ".join(details) + "."
        )


def validate_grounded_draft(
    grounded_draft: GroundedDraft,
    *,
    source_documents: tuple[SourceDocument, ...],
) -> None:
    """Validate grounded citations against the supplied source-document context.

    Validation order is stable and first-error-wins:

    1. each citation must reference a known ``document_id``
    2. each citation ``supporting_text`` must occur as an exact contiguous
       substring of that document's ``content``
    3. each ``summary_point`` must have at least one citation
    """
    if not isinstance(grounded_draft, GroundedDraft):
        raise TypeError("grounded_draft must be a GroundedDraft.")

    documents_by_id = _index_source_documents(source_documents)

    for citation_index, citation in enumerate(grounded_draft.citations):
        document = documents_by_id.get(citation.document_id)
        if document is None:
            raise GroundedDraftValidationError(
                "unknown_document",
                citation_index=citation_index,
                summary_point_index=citation.summary_point_index,
            )
        if citation.supporting_text not in document.content:
            raise GroundedDraftValidationError(
                "supporting_text_not_found",
                citation_index=citation_index,
                summary_point_index=citation.summary_point_index,
            )

    covered_indices = {
        citation.summary_point_index for citation in grounded_draft.citations
    }
    for summary_point_index in range(
        len(grounded_draft.structured_draft.summary_points)
    ):
        if summary_point_index not in covered_indices:
            raise GroundedDraftValidationError(
                "missing_citation_coverage",
                summary_point_index=summary_point_index,
            )


def _index_source_documents(
    source_documents: tuple[SourceDocument, ...],
) -> dict[str, SourceDocument]:
    if not isinstance(source_documents, tuple):
        raise TypeError("source_documents must be a tuple.")

    documents_by_id: dict[str, SourceDocument] = {}
    for document in source_documents:
        if not isinstance(document, SourceDocument):
            raise TypeError(
                "source_documents must contain only SourceDocument objects."
            )
        if document.document_id in documents_by_id:
            raise ValueError(
                "source_documents must not contain duplicate document_id values."
            )
        documents_by_id[document.document_id] = document
    return documents_by_id
