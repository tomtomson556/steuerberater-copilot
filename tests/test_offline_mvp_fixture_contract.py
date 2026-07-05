import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "offline_mvp" / "cases.json"
SYSTEM_OVERVIEW_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "03-architecture" / "system-overview.md"
)

EXPECTED_CASE_FIELDS = {
    "case_id",
    "client_ref",
    "scenario",
    "period",
    "documents",
    "notes",
    "missing_items",
    "mock_risk_signals",
}
EXPECTED_DOCUMENT_FIELDS = {"document_id", "label", "period", "source_note"}
CASE_ID_RE = re.compile(r"^CASE_[0-9]{3}$")
CLIENT_REF_RE = re.compile(r"^CLIENT_[0-9]{3}$")
DOCUMENT_ID_RE = re.compile(r"^DOCUMENT_[0-9]{3}$")
SYNTHETIC_MARKERS = (
    "synthetisch",
    "synthetischer",
    "synthetische",
    "fixture",
    "abstrakt",
    "abstraktes",
    "beispiel",
)
SOURCE_BOUNDARY_MARKERS = (
    "ohne",
    "fixture",
    "abstrakt",
    "generisch",
)
RISKY_REAL_DATA_PATTERNS = {
    "email_address": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "iban": re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b"),
    "german_tax_id_like_number": re.compile(r"\b[0-9]{11}\b"),
    "datev_reference": re.compile(r"\bdatev\b", re.IGNORECASE),
    "elster_reference": re.compile(r"\belster\b", re.IGNORECASE),
    "agenda_reference": re.compile(r"\bagenda\b", re.IGNORECASE),
    "productive_receipt_reference": re.compile(
        r"\b(originalbeleg|echter beleg|produktiver beleg)\b",
        re.IGNORECASE,
    ),
}


def test_fixture_cases_have_unique_case_ids() -> None:
    cases = _load_raw_cases()
    case_ids = [case["case_id"] for case in cases]

    assert len(case_ids) == len(set(case_ids))


def test_fixture_documents_have_unique_document_ids() -> None:
    document_ids = [
        document["document_id"]
        for case in _load_raw_cases()
        for document in case["documents"]
    ]

    assert len(document_ids) == len(set(document_ids))


def test_fixture_cases_and_documents_keep_expected_fields() -> None:
    for case in _load_raw_cases():
        assert set(case) == EXPECTED_CASE_FIELDS
        assert isinstance(case["documents"], list)
        assert case["documents"]
        assert isinstance(case["notes"], list)
        assert isinstance(case["missing_items"], list)
        assert isinstance(case["mock_risk_signals"], list)

        for document in case["documents"]:
            assert set(document) == EXPECTED_DOCUMENT_FIELDS


def test_fixture_references_remain_synthetic_or_abstract() -> None:
    for case in _load_raw_cases():
        assert CASE_ID_RE.fullmatch(case["case_id"])
        assert CLIENT_REF_RE.fullmatch(case["client_ref"])
        assert _contains_marker(case["scenario"], SYNTHETIC_MARKERS)

        for document in case["documents"]:
            assert DOCUMENT_ID_RE.fullmatch(document["document_id"])
            assert _contains_marker(document["label"], SYNTHETIC_MARKERS)
            assert _contains_marker(document["source_note"], SYNTHETIC_MARKERS)
            assert _contains_marker(document["source_note"], SOURCE_BOUNDARY_MARKERS)


def test_fixture_text_avoids_obvious_real_pii_and_productive_system_references() -> None:
    combined_text = "\n".join(_walk_strings(_load_raw_cases()))

    for pattern_name, pattern in RISKY_REAL_DATA_PATTERNS.items():
        assert not pattern.search(combined_text), pattern_name


def test_fixture_text_does_not_contain_real_data_claims() -> None:
    combined_text = "\n".join(_walk_strings(_load_raw_cases())).lower()

    risky_claims = (
        "echte mandantendaten",
        "echte kanzleidaten",
        "echte steuerberaterdaten",
        "echte belegdaten",
        "produktive beleg",
        "original-pii",
        "original pii",
    )

    for claim in risky_claims:
        assert claim not in combined_text


def test_system_overview_documents_all_fixture_cases_without_semantic_coupling() -> None:
    fixture_case_ids = {case["case_id"] for case in _load_raw_cases()}
    documented_case_ids = set(
        re.findall(
            r"\|\s*`(CASE_[0-9]{3})`\s*\|",
            SYSTEM_OVERVIEW_PATH.read_text(encoding="utf-8"),
        )
    )

    assert fixture_case_ids <= documented_case_ids


def _load_raw_cases() -> list[dict[str, Any]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _contains_marker(value: str, markers: Iterable[str]) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in markers)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
