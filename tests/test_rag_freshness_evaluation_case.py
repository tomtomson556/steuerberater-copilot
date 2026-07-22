from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import RAGFreshnessEvaluationCase
from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument


def test_freshness_case_keeps_valid_values_and_object_identities() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_ORCHARD_V1"),
        _document("SYNTHETIC_SOURCE_ORCHARD_V2"),
    )
    records = (
        _record("SYNTHETIC_SOURCE_ORCHARD_V1", version=1),
        _record("SYNTHETIC_SOURCE_ORCHARD_V2", version=2),
    )
    expected = ("SYNTHETIC_SOURCE_ORCHARD_V1",)

    case = RAGFreshnessEvaluationCase(
        evaluation_id=" EVAL_RAG_FRESHNESS_001 ",
        source_documents=documents,
        version_records=records,
        reference_date="2026-07-01",
        expected_outdated_document_ids=expected,
    )

    assert case.evaluation_id == " EVAL_RAG_FRESHNESS_001 "
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.version_records is records
    assert case.version_records[0] is records[0]
    assert case.reference_date == "2026-07-01"
    assert case.expected_outdated_document_ids is expected


def test_rag_freshness_case_is_immutable_and_uses_slots() -> None:
    case = _valid_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert RAGFreshnessEvaluationCase.__slots__ == (
        "evaluation_id",
        "source_documents",
        "version_records",
        "reference_date",
        "expected_outdated_document_ids",
    )


def test_rag_freshness_case_uses_value_equality() -> None:
    assert _valid_case() == _valid_case()


def test_current_case_allows_empty_expected_outdated_document_ids() -> None:
    case = RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_CURRENT",
        source_documents=(_document("SYNTHETIC_SOURCE_CURRENT"),),
        version_records=(_record("SYNTHETIC_SOURCE_CURRENT"),),
        reference_date="2026-07-01",
        expected_outdated_document_ids=(),
    )

    assert case.expected_outdated_document_ids == ()


def test_case_contract_contains_no_observed_detection_result() -> None:
    case = _valid_case()

    assert not hasattr(case, "observed_outdated_document_ids")
    assert not hasattr(case, "detector_output")
    assert not hasattr(case, "workflow_output")
    assert not hasattr(case, "passed")


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_rejects_blank_evaluation_id(evaluation_id: str) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id=evaluation_id,
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        )


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL"]))
def test_rejects_non_string_evaluation_id(evaluation_id: object) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id=evaluation_id,
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        )


def test_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_DOCS",
            source_documents=[_document("SYNTHETIC_SOURCE_001")],
            version_records=(_record("SYNTHETIC_SOURCE_001"),),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_DOCS",
            source_documents=("not-a-document",),
            version_records=(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_duplicate_source_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_DUPLICATE_DOCS",
            source_documents=(
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
            ),
            version_records=(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_non_tuple_version_records() -> None:
    with pytest.raises(TypeError, match=r"^version_records must be a tuple\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_RECORDS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            version_records=[_record("SYNTHETIC_SOURCE_001")],
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_non_document_version_record_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^version_records must contain only DocumentVersionRecord objects\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_RECORDS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            version_records=("not-a-record",),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_version_record_for_unknown_document_id() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^version_records document_id values must reference "
            r"document_id values present in source_documents\.$"
        ),
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_UNKNOWN_RECORD",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            version_records=(_record("SYNTHETIC_SOURCE_MISSING"),),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_duplicate_version_record_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^version_records must not contain duplicate document_id values\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_DUPLICATE_RECORDS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            version_records=(
                _record("SYNTHETIC_SOURCE_001"),
                _record("SYNTHETIC_SOURCE_001"),
            ),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_version_records_that_do_not_cover_all_documents() -> None:
    with pytest.raises(
        ValueError,
        match=r"^version_records must cover exactly the source_documents set\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_INCOMPLETE_RECORDS",
            source_documents=(
                _document("SYNTHETIC_SOURCE_001"),
                _document("SYNTHETIC_SOURCE_002"),
            ),
            version_records=(_record("SYNTHETIC_SOURCE_001"),),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(),
        )


@pytest.mark.parametrize("reference_date", ("", " \t\n"))
def test_rejects_blank_reference_date(reference_date: str) -> None:
    with pytest.raises(ValueError, match=r"^reference_date must not be blank\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_REFERENCE",
            source_documents=_documents(),
            version_records=_records(),
            reference_date=reference_date,
            expected_outdated_document_ids=(),
        )


def test_rejects_non_string_reference_date() -> None:
    with pytest.raises(TypeError, match=r"^reference_date must be a string\.$"):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_REFERENCE",
            source_documents=_documents(),
            version_records=_records(),
            reference_date=20260701,
            expected_outdated_document_ids=(),
        )


def test_rejects_invalid_iso_reference_date() -> None:
    with pytest.raises(
        ValueError,
        match=r"^reference_date must be an ISO calendar date YYYY-MM-DD\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_REFERENCE",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-99-01",
            expected_outdated_document_ids=(),
        )


def test_rejects_non_tuple_expected_outdated_document_ids() -> None:
    with pytest.raises(
        TypeError,
        match=r"^expected_outdated_document_ids must be a tuple\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_EXPECTED",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=["SYNTHETIC_SOURCE_ORCHARD_V1"],
        )


def test_rejects_non_string_expected_outdated_document_id() -> None:
    with pytest.raises(
        TypeError,
        match=r"^expected_outdated_document_ids must contain only strings\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_EXPECTED",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(1,),
        )


def test_rejects_blank_expected_outdated_document_id() -> None:
    with pytest.raises(
        ValueError,
        match=r"^expected_outdated_document_ids must not contain blank values\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_EXPECTED",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(" \t\n",),
        )


def test_rejects_unknown_expected_outdated_document_id() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^expected_outdated_document_ids must reference "
            r"document_id values present in source_documents\.$"
        ),
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_EXPECTED",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=("SYNTHETIC_SOURCE_MISSING",),
        )


def test_rejects_duplicate_expected_outdated_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^expected_outdated_document_ids must not contain duplicates\.$",
    ):
        RAGFreshnessEvaluationCase(
            evaluation_id="EVAL_RAG_FRESHNESS_EXPECTED",
            source_documents=_documents(),
            version_records=_records(),
            reference_date="2026-07-01",
            expected_outdated_document_ids=(
                "SYNTHETIC_SOURCE_ORCHARD_V1",
                "SYNTHETIC_SOURCE_ORCHARD_V1",
            ),
        )


def test_evaluation_package_exports_rag_freshness_case_contract() -> None:
    assert evaluation.RAGFreshnessEvaluationCase is RAGFreshnessEvaluationCase
    assert "RAGFreshnessEvaluationCase" in evaluation.__all__


def _valid_case() -> RAGFreshnessEvaluationCase:
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_VALID",
        source_documents=_documents(),
        version_records=_records(),
        reference_date="2026-07-01",
        expected_outdated_document_ids=("SYNTHETIC_SOURCE_ORCHARD_V1",),
    )


def _documents() -> tuple[SourceDocument, ...]:
    return (
        _document("SYNTHETIC_SOURCE_ORCHARD_V1"),
        _document("SYNTHETIC_SOURCE_ORCHARD_V2"),
    )


def _records() -> tuple[DocumentVersionRecord, ...]:
    return (
        _record("SYNTHETIC_SOURCE_ORCHARD_V1", version=1),
        _record("SYNTHETIC_SOURCE_ORCHARD_V2", version=2),
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic orchard content for {document_id}.",
    )


def _record(
    document_id: str,
    *,
    family: str = "orchard_policy",
    version: int = 1,
    effective_date: str = "2026-07-01",
) -> DocumentVersionRecord:
    return DocumentVersionRecord(
        document_id=document_id,
        document_family=family,
        version_number=version,
        effective_date=effective_date,
    )
