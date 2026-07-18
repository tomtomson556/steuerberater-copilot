"""Immutable contracts linking draft summary points to source evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .structured_output import StructuredDraftOutput


@dataclass(frozen=True, slots=True)
class GroundedDraftCitation:
    """One source-text reference for a positioned draft summary point."""

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
class GroundedDraft:
    """A structured draft with optional position-based source citations."""

    structured_draft: StructuredDraftOutput
    citations: tuple[GroundedDraftCitation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.structured_draft, StructuredDraftOutput):
            raise TypeError("structured_draft must be a StructuredDraftOutput.")
        if not isinstance(self.citations, tuple):
            raise TypeError("citations must be a tuple.")

        summary_point_count = len(self.structured_draft.summary_points)
        for citation in self.citations:
            if not isinstance(citation, GroundedDraftCitation):
                raise TypeError("citations must contain only GroundedDraftCitation objects.")
            if not 0 <= citation.summary_point_index < summary_point_count:
                raise ValueError(
                    "citation summary_point_index must reference an existing summary point."
                )
