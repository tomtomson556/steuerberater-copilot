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
        valid_from="2026-07-01",
        valid_to="2026-12-31",
    )

    assert record.document_id == " SYNTHETIC_SOURCE_001 "
    assert record.document_family == " synthetic_orchard_policy "
    assert record.version_number == 3
    assert record.valid_from == "2026-07-01"
    assert record.valid_to == "2026-12-31"


def test_document_version_record_is_immutable_and_uses_slots() -> None:
    record = _record("SYNTHETIC_SOURCE_001")

    with pytest.raises(FrozenInstanceError):
        record.version_number = 2

    assert not hasattr(record, "__dict__")
    assert DocumentVersionRecord.__slots__ == (
        "document_id",
        "document_family",
        "version_number",
        "valid_from",
        "valid_to",
    )


def test_document_version_record_uses_value_equality() -> None:
    assert _record("SYNTHETIC_SOURCE_001") == _record("SYNTHETIC_SOURCE_001")


@pytest.mark.parametrize("field_name", ("document_id", "document_family", "valid_from"))
@pytest.mark.parametrize("value", ("", " \t\n"))
def test_document_version_record_rejects_blank_string_fields(
    field_name: str,
    value: str,
) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments[field_name] = value

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("field_name", ("document_id", "document_family", "valid_from"))
@pytest.mark.parametrize("value", (1, None, ["synthetic"]))
def test_document_version_record_rejects_non_string_fields(
    field_name: str,
    value: object,
) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments[field_name] = value

    with pytest.raises(TypeError, match=rf"^{field_name} must be a string\.$"):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("value", ("", " \t\n"))
def test_document_version_record_rejects_blank_valid_to(value: str) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["valid_to"] = value

    with pytest.raises(
        ValueError,
        match=r"^valid_to must not be blank when provided\.$",
    ):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("value", (1, ["synthetic"]))
def test_document_version_record_rejects_non_string_valid_to(value: object) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["valid_to"] = value

    with pytest.raises(TypeError, match=r"^valid_to must be a string or None\.$"):
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


@pytest.mark.parametrize("valid_from", ("2026-13-01", "2026/07/01", "not-a-date"))
def test_document_version_record_rejects_invalid_valid_from_date(valid_from: str) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["valid_from"] = valid_from

    with pytest.raises(
        ValueError,
        match=r"^valid_from must be an ISO calendar date YYYY-MM-DD\.$",
    ):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("valid_to", ("2026-13-01", "2026/07/01", "not-a-date"))
def test_document_version_record_rejects_invalid_valid_to_date(valid_to: str) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["valid_to"] = valid_to

    with pytest.raises(
        ValueError,
        match=r"^valid_to must be an ISO calendar date YYYY-MM-DD\.$",
    ):
        DocumentVersionRecord(**arguments)


@pytest.mark.parametrize("valid_to", ("2025-12-31", "2026-01-01"))
def test_document_version_record_rejects_non_later_valid_to(valid_to: str) -> None:
    arguments = _record_arguments("SYNTHETIC_SOURCE_001")
    arguments["valid_from"] = "2026-01-01"
    arguments["valid_to"] = valid_to

    with pytest.raises(
        ValueError,
        match=r"^valid_to must be strictly after valid_from\.$",
    ):
        DocumentVersionRecord(**arguments)


def test_find_outdated_document_ids_detects_superseded_lower_in_force_family_version() -> None:
    records = (
        _record(
            "SYNTHETIC_ORCHARD_POLICY_V1",
            family="orchard_policy",
            version=1,
            valid_from="2025-01-01",
        ),
        _record(
            "SYNTHETIC_ORCHARD_POLICY_V2",
            family="orchard_policy",
            version=2,
            valid_from="2026-01-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_ORCHARD_POLICY_V1",
    )


def test_find_outdated_document_ids_detects_closed_validity_window() -> None:
    records = (
        _record(
            "SYNTHETIC_MEADOW_NOTICE",
            family="meadow_notice",
            version=1,
            valid_from="2025-01-01",
            valid_to="2026-07-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_MEADOW_NOTICE",
    )


def test_find_outdated_document_ids_keeps_past_valid_from_current() -> None:
    records = (
        _record(
            "SYNTHETIC_ORCHARD_GUIDE",
            family="orchard_guide",
            version=2,
            valid_from="2024-01-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == ()


def test_find_outdated_document_ids_future_draft_is_not_outdated_and_does_not_supersede() -> None:
    records = (
        _record(
            "SYNTHETIC_ORCHARD_POLICY_CURRENT",
            family="orchard_policy",
            version=1,
            valid_from="2025-01-01",
        ),
        _record(
            "SYNTHETIC_ORCHARD_POLICY_FUTURE",
            family="orchard_policy",
            version=2,
            valid_from="2026-12-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == ()


def test_find_outdated_document_ids_handles_mixed_outdated_reasons() -> None:
    records = (
        _record(
            "SYNTHETIC_MIXED_CURRENT",
            family="mixed_policy",
            version=2,
            valid_from="2026-01-01",
        ),
        _record(
            "SYNTHETIC_MIXED_SUPERSEDED",
            family="mixed_policy",
            version=1,
            valid_from="2025-01-01",
        ),
        _record(
            "SYNTHETIC_MIXED_VALIDITY_ENDED",
            family="validity_ended_notice",
            version=1,
            valid_from="2024-01-01",
            valid_to="2025-12-31",
        ),
        _record(
            "SYNTHETIC_MIXED_FUTURE_DRAFT",
            family="mixed_policy",
            version=3,
            valid_from="2027-01-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == (
        "SYNTHETIC_MIXED_SUPERSEDED",
        "SYNTHETIC_MIXED_VALIDITY_ENDED",
    )


def test_find_outdated_document_ids_same_family_higher_version_not_yet_in_force() -> None:
    records = (
        _record(
            "SYNTHETIC_MEADOW_POLICY_CURRENT",
            family="meadow_policy",
            version=4,
            valid_from="2025-06-01",
        ),
        _record(
            "SYNTHETIC_MEADOW_POLICY_PENDING",
            family="meadow_policy",
            version=5,
            valid_from="2027-01-01",
        ),
    )

    assert find_outdated_document_ids(records, reference_date="2026-07-01") == ()


def test_find_outdated_document_ids_rejects_invalid_records_input() -> None:
    with pytest.raises(TypeError, match=r"^records must be a tuple\.$"):
        find_outdated_document_ids(
            [_record("SYNTHETIC_SOURCE_001")],
            reference_date="2026-07-01",
        )

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
    valid_from: str = "2026-07-01",
    valid_to: str | None = None,
) -> DocumentVersionRecord:
    return DocumentVersionRecord(
        document_id=document_id,
        document_family=family,
        version_number=version,
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _record_arguments(document_id: str) -> dict[str, object]:
    return {
        "document_id": document_id,
        "document_family": "synthetic_policy",
        "version_number": 1,
        "valid_from": "2026-07-01",
        "valid_to": None,
    }
