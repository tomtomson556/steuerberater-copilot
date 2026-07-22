"""Deterministic outdated-document detection from version records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DocumentVersionRecord:
    """Version metadata for one synthetic source document.

    Records are evaluation and retrieval-side metadata only. They do not change
    ``SourceDocument`` content and do not assert fachliche document validity.
    """

    document_id: str
    document_family: str
    version_number: int
    effective_date: str

    def __post_init__(self) -> None:
        for field_name in ("document_id", "document_family", "effective_date"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")
        if type(self.version_number) is not int:
            raise TypeError("version_number must be an integer.")
        if self.version_number <= 0:
            raise ValueError("version_number must be greater than zero.")
        try:
            date.fromisoformat(self.effective_date)
        except ValueError as error:
            raise ValueError(
                "effective_date must be an ISO calendar date YYYY-MM-DD."
            ) from error


def find_outdated_document_ids(
    records: tuple[DocumentVersionRecord, ...],
    *,
    reference_date: str,
) -> tuple[str, ...]:
    """Return outdated document IDs in stable document_id order.

    A document is outdated when either:

    1. its ``effective_date`` is strictly before ``reference_date``, or
    2. another record in the same ``document_family`` has a higher
       ``version_number``.
    """
    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple.")
    if not isinstance(reference_date, str):
        raise TypeError("reference_date must be a string.")
    if not reference_date or reference_date.isspace():
        raise ValueError("reference_date must not be blank.")
    try:
        parsed_reference = date.fromisoformat(reference_date)
    except ValueError as error:
        raise ValueError(
            "reference_date must be an ISO calendar date YYYY-MM-DD."
        ) from error

    seen_document_ids: set[str] = set()
    for record in records:
        if not isinstance(record, DocumentVersionRecord):
            raise TypeError("records must contain only DocumentVersionRecord objects.")
        if record.document_id in seen_document_ids:
            raise ValueError("records must not contain duplicate document_id values.")
        seen_document_ids.add(record.document_id)

    max_version_by_family: dict[str, int] = {}
    for record in records:
        current_max = max_version_by_family.get(record.document_family)
        if current_max is None or record.version_number > current_max:
            max_version_by_family[record.document_family] = record.version_number

    outdated_ids: list[str] = []
    for record in records:
        effective = date.fromisoformat(record.effective_date)
        superseded = (
            record.version_number < max_version_by_family[record.document_family]
        )
        expired = effective < parsed_reference
        if superseded or expired:
            outdated_ids.append(record.document_id)

    return tuple(sorted(outdated_ids))
