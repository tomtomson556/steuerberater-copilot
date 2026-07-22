from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.rag as rag
from steuerberater_copilot.rag import (
    DocumentVersionRecord,
    find_outdated_document_ids,
)


def test_document_version_record_keeps_valid_values() -> None:
    record = DocumentVersionRecord(
        document_id=" SYNTHETIC_SOURCE_001 ",
        document_family=" synthetic_orchard_policy ",
        version_number=3,
        effective_date="2026-07-01",
    )

    assert record.document_id == " SYNTHETIC_SOURCE_001 "
    assert record.document_family == " synthetic_orchard_policy "
    assert record.version_number == 3
    assert record.effective_date == "2026-07-01"


def test_document_version_record_is_immutable_and_uses_slots() -> None:
    record = _record("SYNTHETIC_SOURCE_001")

    with pytest.raises(FrozenInstanceError):
        record.version_number = 2

    assert not hasattr(record, "__dict__")
    assert DocumentVersionRecord.__slots__ == (
        "document_id",
        "document_family",
        "version_number",
        "effective_date",
    )


def test_document_version_record_uses_value_equality() -> None:
    assert _record("SYNTHETIC_SOURCE_001") == _record("SYNTHETIC_SOURCE_001")


@pytest.mark.parametrize("field_name", ("document_id", "document_family", "effective_date"))
@pytest.mark.parametrize("value", ("", " \t\n"))
def test_document_version_record_rejects_blank_string_fields(
    field_name: str,
    value: str,
) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments[field_name] = value

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("field_name", ("document_id", "document_family", "effective_date"))
@pytest.mark.parametrize("value", (1, None, ["synthetic"]))
def test_document_version_record_rejects_non_string_fields(
    field_name: str,
    value: object,
) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments[field_name] = value

    with pytest.raises(TypeError, match=rf"^{field_name} must be a string\.$"):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("value", (True, False, 1.5, "1"))
def test_document_version_record_rejects_non_int_version_number(value: object) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["version_number"] = value

    with pytest.raises(TypeError, match=r"^version_number must be an integer\.$"):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("value", (0, -1))
def test_document_version_record_rejects_non_positive_version_number(value: int) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["version_number"] = value

    with pytest.raises(
        ValueError,
        match=r"^version_number must be greater than zero\.$",
    ):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("effective_date", ("2026-13-01", "2026/07/01", "not-a-date"))
def test_document_version_record_rejects_invalid_iso_date(effective_date: str) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["effective_date"] = effective_date

    with pytest.raises(
        ValueError,
        match=r"^effective_date must be an ISO calendar date YYYY-MM-DD\.$",
    ):
        DocumentVersionRecord(**arguments)


def test_find_outdated_document_ids_detects_superseded_lower_family_version() -> None:
    records = (
        _record(
            "SYNTHETIC_ORCHARD_POLICY_V1",
            family="orchard_policy",
            version=1,
            effective_date="2026-07-01",
        ),
        _record(
            "SYNTHETIC_ORCHARD_POLICY_V2",
            family="orchard_policy",
            version=2,
            effective_date="2026-07-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_ORCHARD_POLICY_V1",
    )


def test_find_outdated_document_ids_detects_expired_effective_date() -> None:
    records = (
        _record(
            "SYNTHETIC_MEADOW_NOTICE",
            family="meadow_notice",
            version=1,
            effective_date="2026-06-30",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_MEADOW_NOTICE",
    )


def test_find_outdated_document_ids_returns_empty_for_current_documents() -> None:
    records = (
        _record(
            "SYNTHETIC_ORCHARD_GUIDE",
            family="orchard_guide",
            version=2,
            effective_date="2026-07-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == ()


def test_find_outdated_document_ids_handles_mixed_outdated_reasons() -> None:
    records = (
        _record(
            "SYNTHETIC_MIXED_CURRENT",
            family="mixed_policy",
            version=2,
            effective_date="2026-07-01",
        ),
        _record(
            "SYNTHETIC_MIXED_SUPERSEDED",
            family="mixed_policy",
            version=1,
            effective_date="2026-07-01",
        ),
        _record(
            "SYNTHETIC_MIXED_EXPIRED",
            family="expired_notice",
            version=1,
            effective_date="2026-01-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_MIXED_EXPIRED",
        "SYNTHETIC_MIXED_SUPERSEDED",
    )


def test_find_outdated_document_ids_rejects_invalid_records_input() -> None:
    with pytest.raises(TypeError, match=r"^records must be a tuple\.$"):
        find_outdated_document_ids([_record("SYNTHETIC_SOURCE_001")], reference_date="2026-07-01")

    with pytest.raises(
        TypeError,
        match=r"^records must contain only DocumentVersionRecord objects\.$",
    ):
        find_outdated_document_ids(("not-a-record",), reference_date="2026-07-01")


def test_find_outdated_document_ids_rejects_invalid_reference_date() -> None:
    with pytest.raises(TypeError, match=r"^reference_date must be a string\.$"):
        find_outdated_document_ids((), reference_date=20260701)

    with pytest.raises(ValueError, match=r"^reference_date must not be blank\.$"):
        find_outdated_document_ids((), reference_date=" \t\n")

    with pytest.raises(
        ValueError,
        match=r"^reference_date must be an ISO calendar date YYYY-MM-DD\.$",
    ):
        find_outdated_document_ids((), reference_date="2026-99-01")


def test_find_outdated_document_ids_rejects_duplicate_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^records must not contain duplicate document_id values\.$",
    ):
        find_outdated_document_ids(
            (
                _record("SYNTHETIC_SOURCE_DUPLICATE"),
                _record("SYNTHETIC_SOURCE_DUPLICATE"),
            ),
            reference_date="2026-07-01",
        )


def test_rag_package_exports_document_freshness_contract() -> None:
    assert rag.DocumentVersionRecord is DocumentVersionRecord
    assert rag.find_outdated_document_ids is find_outdated_document_ids


def _record(
    document_id: str,
    *,
    family: str = "synthetic_policy",
    version: int = 1,
    effective_date: str = "2026-07-01",
) -> DocumentVersionRecord:
    return DocumentVersionRecord(
        document_id=document_id,
        document_family=family,
        version_number=version,
        effective_date=effective_date,
    )


def _record_arguments(document_id: str) -> dict[str, object]:
    return {
        "document_id": document_id,
        "document_family": "synthetic_policy",
        "version_number": 1,
        "effective_date": "2026-07-01",
    }
