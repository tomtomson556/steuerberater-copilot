"""Deterministic outdated-document detection from version metadata.

Outdatedness is derived only from explicit versioning semantics:

1. A newer in-force version in the same ``document_family`` supersedes older
   started versions.
2. An explicit ``valid_to`` end date closes validity when
   ``valid_to <= reference_date`` (exact boundary inclusive for closure).

Additional deterministic rules:

- A past ``valid_from`` alone never marks a document outdated.
- Future-dated versions (``valid_from > reference_date``) are not outdated and
  do not supersede yet.
- Overlapping in-force windows are allowed; the highest in-force
  ``version_number`` is current and lower started versions are superseded.
- If the highest version has already closed, a lower still-open version may
  remain current.
- Version gaps are allowed (for example 1 and 3).
- Duplicate ``version_number`` values inside one family are rejected.

This helper is evaluation/retrieval metadata only. It makes no steuerliche
correctness claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DocumentVersionRecord:
    """Version metadata for one synthetic source document."""

    document_id: str
    document_family: str
    version_number: int
    valid_from: str
    valid_to: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("document_id", "document_family", "valid_from"):
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
            parsed_from = date.fromisoformat(self.valid_from)
        except ValueError as error:
            raise ValueError(
                "valid_from must be an ISO calendar date YYYY-MM-DD."
            ) from error
        if self.valid_to is not None:
            if not isinstance(self.valid_to, str):
                raise TypeError("valid_to must be a string or None.")
            if not self.valid_to or self.valid_to.isspace():
                raise ValueError("valid_to must not be blank when provided.")
            try:
                parsed_to = date.fromisoformat(self.valid_to)
            except ValueError as error:
                raise ValueError(
                    "valid_to must be an ISO calendar date YYYY-MM-DD."
                ) from error
            if parsed_to <= parsed_from:
                raise ValueError("valid_to must be strictly after valid_from.")


def find_outdated_document_ids(
    records: tuple[DocumentVersionRecord, ...],
    *,
    reference_date: str,
) -> tuple[str, ...]:
    """Return outdated document IDs in stable document_id order."""
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
    seen_family_versions: set[tuple[str, int]] = set()
    for record in records:
        if not isinstance(record, DocumentVersionRecord):
            raise TypeError("records must contain only DocumentVersionRecord objects.")
        if record.document_id in seen_document_ids:
            raise ValueError("records must not contain duplicate document_id values.")
        seen_document_ids.add(record.document_id)
        family_version = (record.document_family, record.version_number)
        if family_version in seen_family_versions:
            raise ValueError(
                "records must not contain duplicate version_number values "
                "inside the same document_family."
            )
        seen_family_versions.add(family_version)

    in_force_by_family: dict[str, list[DocumentVersionRecord]] = {}
    for record in records:
        if _is_in_force(record, parsed_reference):
            in_force_by_family.setdefault(record.document_family, []).append(record)

    current_version_by_family = {
        family: max(family_records, key=lambda item: item.version_number).version_number
        for family, family_records in in_force_by_family.items()
    }

    outdated_ids: list[str] = []
    for record in records:
        validity_closed = _validity_closed(record, parsed_reference)
        superseded = False
        current_version = current_version_by_family.get(record.document_family)
        if current_version is not None and record.version_number < current_version:
            if date.fromisoformat(record.valid_from) <= parsed_reference:
                superseded = True
        if validity_closed or superseded:
            outdated_ids.append(record.document_id)

    return tuple(sorted(outdated_ids))


def _is_in_force(record: DocumentVersionRecord, reference: date) -> bool:
    started = date.fromisoformat(record.valid_from) <= reference
    if not started:
        return False
    if record.valid_to is None:
        return True
    return date.fromisoformat(record.valid_to) > reference


def _validity_closed(record: DocumentVersionRecord, reference: date) -> bool:
    if record.valid_to is None:
        return False
    return date.fromisoformat(record.valid_to) <= reference
