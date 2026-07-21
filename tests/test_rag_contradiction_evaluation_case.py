from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
)
from steuerberater_copilot.rag import SourceDocument


def test_contradiction_evidence_label_keeps_valid_values_and_identities() -> None:
    document_id = " SYNTHETIC_SOURCE_001 "
    supporting_text = "\nSynthetic orchard passage remains unchanged.\n"

    label = ContradictionEvidenceLabel(
        document_id=document_id,
        supporting_text=supporting_text,
    )

    assert label.document_id is document_id
    assert label.supporting_text is supporting_text


def test_contradiction_evidence_label_is_immutable_and_uses_slots() -> None:
    label = ContradictionEvidenceLabel(
        document_id="SYNTHETIC_SOURCE_001",
        supporting_text="Synthetic orchard passage.",
    )

    with pytest.raises(FrozenInstanceError):
        label.document_id = "SYNTHETIC_SOURCE_CHANGED"

    assert not hasattr(label, "__dict__")
    assert ContradictionEvidenceLabel.__slots__ == (
        "document_id",
        "supporting_text",
    )


def test_contradiction_evidence_label_uses_value_equality() -> None:
    assert _label() == _label()


@pytest.mark.parametrize("field_name", ("document_id", "supporting_text"))
@pytest.mark.parametrize("value", ("", " \t\n"))
def test_contradiction_evidence_label_rejects_blank_fields(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "document_id": "SYNTHETIC_SOURCE_001",
        "supporting_text": "Synthetic orchard passage.",
        field_name: value,
    }
    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        ContradictionEvidenceLabel(**kwargs)


@pytest.mark.parametrize("field_name", ("document_id", "supporting_text"))
@pytest.mark.parametrize("value", (1, None, ["text"]))
def test_contradiction_evidence_label_rejects_non_string_fields(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "document_id": "SYNTHETIC_SOURCE_001",
        "supporting_text": "Synthetic orchard passage.",
        field_name: value,
    }
    with pytest.raises(TypeError, match=rf"^{field_name} must be a string\.$"):
        ContradictionEvidenceLabel(**kwargs)  # type: ignore[arg-type]


def test_positive_contradiction_case_keeps_valid_values_and_object_identities() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic meadow content. Synthetic beta orchard passage.",
        ),
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic alpha orchard passage. Synthetic meadow content.",
        ),
    )
    contradicting_passages = (
        _label(
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic alpha orchard passage.",
        ),
        _label(
            document_id="SYNTHETIC_SOURCE_002",
            supporting_text="Synthetic beta orchard passage.",
        ),
    )

    case = RAGContradictionEvaluationCase(
        evaluation_id=" EVAL_RAG_CONTRADICTION_001 ",
        source_documents=documents,
        expected_contradiction_present=True,
        contradicting_passages=contradicting_passages,
    )

    assert case.evaluation_id == " EVAL_RAG_CONTRADICTION_001 "
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.expected_contradiction_present is True
    assert case.contradicting_passages is contradicting_passages
    assert case.contradicting_passages[0] is contradicting_passages[0]
    assert case.contradicting_passages[1] is contradicting_passages[1]


def test_rag_contradiction_case_is_immutable_and_uses_slots() -> None:
    case = _positive_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert RAGContradictionEvaluationCase.__slots__ == (
        "evaluation_id",
        "source_documents",
        "expected_contradiction_present",
        "contradicting_passages",
    )


def test_rag_contradiction_case_uses_value_equality() -> None:
    assert _positive_case() == _positive_case()
    assert _negative_case() == _negative_case()


def test_negative_control_case_allows_empty_contradicting_passages() -> None:
    case = _negative_case()

    assert case.expected_contradiction_present is False
    assert case.contradicting_passages == ()


def test_positive_case_allows_two_passages_from_same_document() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content=(
                "Synthetic orchard is open today. "
                "Synthetic orchard is closed today."
            ),
        ),
    )
    case = RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_SAME_DOC",
        source_documents=documents,
        expected_contradiction_present=True,
        contradicting_passages=(
            _label(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic orchard is open today.",
            ),
            _label(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic orchard is closed today.",
            ),
        ),
    )

    assert case.expected_contradiction_present is True
    assert len(case.contradicting_passages) == 2
    assert (
        case.contradicting_passages[0].document_id
        == case.contradicting_passages[1].document_id
    )


def test_case_contract_contains_no_observed_detector_result() -> None:
    case = _positive_case()

    assert not hasattr(case, "observed_contradiction_present")
    assert not hasattr(case, "detected_contradiction")
    assert not hasattr(case, "detector_output")
    assert not hasattr(case, "workflow_output")
    assert not hasattr(case, "passed")


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_rejects_blank_evaluation_id(evaluation_id: str) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        RAGContradictionEvaluationCase(
            evaluation_id=evaluation_id,
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=_two_labels(),
        )


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL"]))
def test_rejects_non_string_evaluation_id(evaluation_id: object) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        RAGContradictionEvaluationCase(
            evaluation_id=evaluation_id,  # type: ignore[arg-type]
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=_two_labels(),
        )


@pytest.mark.parametrize("value", (0, 1, "true", None))
def test_rejects_non_bool_expected_contradiction(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=r"^expected_contradiction_present must be a boolean\.$",
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_FLAG",
            source_documents=_two_documents(),
            expected_contradiction_present=value,  # type: ignore[arg-type]
            contradicting_passages=_two_labels(),
        )


def test_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_DOCS",
            source_documents=[_document("SYNTHETIC_SOURCE_001")],  # type: ignore[arg-type]
            expected_contradiction_present=False,
            contradicting_passages=(),
        )


def test_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_DOCS",
            source_documents=("not-a-document",),  # type: ignore[arg-type]
            expected_contradiction_present=False,
            contradicting_passages=(),
        )


def test_rejects_duplicate_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_DOCS",
            source_documents=(
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
            ),
            expected_contradiction_present=False,
            contradicting_passages=(),
        )


def test_rejects_non_tuple_contradicting_passages() -> None:
    with pytest.raises(
        TypeError,
        match=r"^contradicting_passages must be a tuple\.$",
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_LABELS",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=list(_two_labels()),  # type: ignore[arg-type]
        )


def test_rejects_non_label_entry_in_contradicting_passages() -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^contradicting_passages must contain only "
            r"ContradictionEvidenceLabel objects\.$"
        ),
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_LABELS",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=(
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
                "not-a-label",  # type: ignore[list-item]
            ),
        )


def test_positive_case_rejects_wrong_passage_count() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^positive contradiction cases must reference exactly two "
            r"contradicting passages\.$"
        ),
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_COUNT",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=(
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
            ),
        )


def test_negative_case_rejects_non_empty_contradicting_passages() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^negative contradiction cases must not include "
            r"contradicting_passages\.$"
        ),
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_NEGATIVE",
            source_documents=_two_documents(),
            expected_contradiction_present=False,
            contradicting_passages=_two_labels(),
        )


def test_rejects_unknown_document_id_in_contradicting_passages() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^contradicting_passages document_id values must reference "
            r"document_id values present in source_documents\.$"
        ),
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_UNKNOWN_DOC",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=(
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
                _label(
                    document_id="SYNTHETIC_SOURCE_MISSING",
                    supporting_text="Synthetic beta orchard passage.",
                ),
            ),
        )


def test_rejects_supporting_text_missing_from_document_content() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^contradicting_passages supporting_text must occur as an exact "
            r"contiguous substring of the referenced source document content\.$"
        ),
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_MISSING_PASSAGE",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=(
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
                _label(
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic missing orchard passage.",
                ),
            ),
        )


def test_rejects_duplicate_contradicting_passage_labels() -> None:
    with pytest.raises(
        ValueError,
        match=r"^contradicting_passages must not contain duplicate labels\.$",
    ):
        RAGContradictionEvaluationCase(
            evaluation_id="EVAL_RAG_CONTRADICTION_DUPLICATE",
            source_documents=_two_documents(),
            expected_contradiction_present=True,
            contradicting_passages=(
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
                _label(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
            ),
        )


def test_evaluation_package_exports_rag_contradiction_case_contract() -> None:
    assert evaluation.ContradictionEvidenceLabel is ContradictionEvidenceLabel
    assert evaluation.RAGContradictionEvaluationCase is RAGContradictionEvaluationCase
    assert "ContradictionEvidenceLabel" in evaluation.__all__
    assert "RAGContradictionEvaluationCase" in evaluation.__all__


def _positive_case() -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_POSITIVE",
        source_documents=_two_documents(),
        expected_contradiction_present=True,
        contradicting_passages=_two_labels(),
    )


def _negative_case() -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_NEGATIVE",
        source_documents=_two_documents(),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _two_documents() -> tuple[SourceDocument, ...]:
    return (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic alpha orchard passage. Synthetic meadow content.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic meadow content. Synthetic beta orchard passage.",
        ),
    )


def _two_labels() -> tuple[ContradictionEvidenceLabel, ...]:
    return (
        _label(
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic alpha orchard passage.",
        ),
        _label(
            document_id="SYNTHETIC_SOURCE_002",
            supporting_text="Synthetic beta orchard passage.",
        ),
    )


def _label(
    *,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic alpha orchard passage.",
) -> ContradictionEvidenceLabel:
    return ContradictionEvidenceLabel(
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _document(
    document_id: str,
    *,
    content: str | None = None,
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content or f"Synthetic content for {document_id}.",
    )
