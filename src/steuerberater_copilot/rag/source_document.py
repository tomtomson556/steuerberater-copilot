"""Provider- and workflow-neutral source document contract."""

from __future__ import annotations

from dataclasses import dataclass

UNTRUSTED_DATA_CLASS = "untrusted"
SYNTHETIC_FIXTURE_DATA_CLASS = "synthetic_fixture"


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Immutable source text for later local retrieval work.

    ``data_class`` is an explicit provenance marker. It is not inferred from
    ``document_id``, title, or content. The default is untrusted.
    """

    document_id: str
    title: str
    content: str
    data_class: str = UNTRUSTED_DATA_CLASS

    def __post_init__(self) -> None:
        for field_name in ("document_id", "title", "content", "data_class"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")
