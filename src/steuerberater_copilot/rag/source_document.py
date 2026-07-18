"""Provider- and workflow-neutral source document contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Immutable source text for later local retrieval work."""

    document_id: str
    title: str
    content: str

    def __post_init__(self) -> None:
        for field_name in ("document_id", "title", "content"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")
