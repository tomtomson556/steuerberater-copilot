"""Structured draft output contract for future parsed model responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredDraftOutput:
    """Structured internal draft material awaiting validation and human review."""

    summary_points: tuple[str, ...]
    uncertainties: tuple[str, ...]
    review_questions: tuple[str, ...]
