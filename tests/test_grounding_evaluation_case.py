from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    GroundingEvaluationCase,
    GroundingEvidenceLabel,
)
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    StructuredDraftOutput,
)
from steuerberater_copilot.rag import SourceDocument


def test_grounding_evidence_label_keeps_valid_values_and_identities() -> None:
    document_id = " SYNTHETIC_SOURCE_001 "
    supporting_text = "\nSynthetic orchard passage remains unchanged.\n"

    label = GroundingEvidenceLabel(
        summary_point_index=1,
        document_id=document_id,
        supporting_text=supporting_text,
    )

    assert label.summary_point_index == 1
    assert label.document_id is document_id
    assert label.supporting_text is supporting_text


def test_grounding_evidence_label_is_immutable_and_uses_slots() -> None:
    label = GroundingEvidenceLabel(
        summary_point_index=0,
        document_id="SYNTHETIC_SOURCE_001",
        supporting_text="Synthetic orchard passage.",
    )

    with pytest.raises(FrozenInstanceError):
        label.document_id = "SYNTHETIC_SOURCE_CHANGED"

    assert not hasattr(label, "__dict__")
    assert GroundingEvidenceLabel.__slots__ == (
        "summary_point_index",
        "document_id",
        "supporting_text",
    )


def test_grounding_evidence_label_uses_value_equality() -> None:
    assert _label() == _label()


def test_grounding_evaluation_case_keeps_valid_values_and_object_identities() -> None:
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
    grounded_draft = _grounded_draft(
        summary_points=(
            "Synthetic first summary point.",
            "Synthetic second summary point.",
        ),
        citations=(
            _candidate_citation(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_WRONG",
                supporting_text="Synthetic wrong supporting text.",
            ),
        ),
    )
    acceptable_evidence = (
        _label(
            summary_point_index=0,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic alpha orchard passage.",
        ),
        _label(
            summary_point_index=1,
            document_id="SYNTHETIC_SOURCE_002",
            supporting_text="Synthetic beta orchard passage.",
        ),
    )

    case = GroundingEvaluationCase(
        evaluation_id=" EVAL_GROUNDING_001 ",
        source_documents=documents,
        candidate_grounded_draft=grounded_draft,
        acceptable_evidence=acceptable_evidence,
    )

    assert case.evaluation_id == " EVAL_GROUNDING_001 "
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.candidate_grounded_draft is grounded_draft
    assert case.acceptable_evidence is acceptable_evidence
    assert case.acceptable_evidence[0] is acceptable_evidence[0]
    assert case.acceptable_evidence[1] is acceptable_evidence[1]


def test_grounding_evaluation_case_is_immutable_and_uses_slots() -> None:
    case = _valid_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert GroundingEvaluationCase.__slots__ == (
        "evaluation_id",
        "source_documents",
        "candidate_grounded_draft",
        "acceptable_evidence",
    )


def test_grounding_evaluation_case_uses_value_equality() -> None:
    assert _valid_case() == _valid_case()


def test_empty_acceptable_evidence_is_allowed_for_unsupported_claim_cases() -> None:
    documents = (_document("SYNTHETIC_SOURCE_001"),)
    grounded_draft = _grounded_draft(
        summary_points=("Synthetic unsupported summary point.",),
        citations=(),
    )

    case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_UNSUPPORTED",
        source_documents=documents,
        candidate_grounded_draft=grounded_draft,
        acceptable_evidence=(),
    )

    assert case.acceptable_evidence == ()
    assert case.candidate_grounded_draft.citations == ()


def test_multiple_acceptable_labels_for_one_summary_point_are_allowed() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage alpha.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic orchard passage beta.",
        ),
    )
    grounded_draft = _grounded_draft(
        summary_points=("Synthetic summary about orchard.",),
        citations=(
            _candidate_citation(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic orchard passage alpha.",
            ),
        ),
    )
    acceptable_evidence = (
        _label(
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic orchard passage alpha.",
        ),
        _label(
            document_id="SYNTHETIC_SOURCE_002",
            supporting_text="Synthetic orchard passage beta.",
        ),
    )

    case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_ALTERNATIVES",
        source_documents=documents,
        candidate_grounded_draft=grounded_draft,
        acceptable_evidence=acceptable_evidence,
    )

    assert case.acceptable_evidence is acceptable_evidence
    assert tuple(label.summary_point_index for label in case.acceptable_evidence) == (
        0,
        0,
    )


def test_faulty_candidate_citations_are_representable() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic correct orchard passage.",
        ),
    )
    grounded_draft = _grounded_draft(
        summary_points=(
            "Synthetic covered summary point.",
            "Synthetic uncovered summary point.",
        ),
        citations=(
            _candidate_citation(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_MISSING",
                supporting_text="Synthetic invented supporting text.",
            ),
            _candidate_citation(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic wrong contiguous text.",
            ),
        ),
    )

    case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_FAULTY_CANDIDATE",
        source_documents=documents,
        candidate_grounded_draft=grounded_draft,
        acceptable_evidence=(
            _label(supporting_text="Synthetic correct orchard passage."),
        ),
    )

    assert len(case.candidate_grounded_draft.citations) == 2
    assert case.candidate_grounded_draft.citations[0].document_id == (
        "SYNTHETIC_SOURCE_MISSING"
    )
    assert case.candidate_grounded_draft.citations[1].supporting_text == (
        "Synthetic wrong contiguous text."
    )
    assert case.acceptable_evidence[0].supporting_text == (
        "Synthetic correct orchard passage."
    )


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_grounding_evaluation_case_rejects_blank_evaluation_id(
    evaluation_id: str,
) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        GroundingEvaluationCase(
            evaluation_id=evaluation_id,
            source_documents=(),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(),
        )


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL_GROUNDING"]))
def test_grounding_evaluation_case_rejects_non_string_evaluation_id(
    evaluation_id: object,
) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        GroundingEvaluationCase(
            evaluation_id=evaluation_id,  # type: ignore[arg-type]
            source_documents=(),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(),
        )


def test_grounding_evaluation_case_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_DOCS",
            source_documents=[_document("SYNTHETIC_SOURCE_001")],  # type: ignore[arg-type]
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(),
        )


def test_grounding_evaluation_case_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_DOCS",
            source_documents=("not-a-document",),  # type: ignore[arg-type]
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(),
        )


def test_grounding_evaluation_case_rejects_duplicate_document_ids() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_DUPLICATE", content="Synthetic first content."),
        _document("SYNTHETIC_SOURCE_DUPLICATE", content="Synthetic second content."),
    )

    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_DOCS",
            source_documents=documents,
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(),
        )


def test_grounding_evaluation_case_rejects_non_grounded_draft_candidate() -> None:
    with pytest.raises(
        TypeError,
        match=r"^candidate_grounded_draft must be a GroundedDraft\.$",
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_CANDIDATE",
            source_documents=(),
            candidate_grounded_draft="not-a-draft",  # type: ignore[arg-type]
            acceptable_evidence=(),
        )


def test_grounding_evaluation_case_rejects_non_tuple_acceptable_evidence() -> None:
    with pytest.raises(TypeError, match=r"^acceptable_evidence must be a tuple\.$"):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=[_label()],  # type: ignore[arg-type]
        )


def test_grounding_evaluation_case_rejects_non_label_entry() -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^acceptable_evidence must contain only GroundingEvidenceLabel "
            r"objects\.$"
        ),
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=("not-a-label",),  # type: ignore[arg-type]
        )


def test_grounding_evaluation_case_rejects_label_index_outside_summary_points() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^acceptable_evidence summary_point_index must reference an "
            r"existing summary point\.$"
        ),
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=(
                _document(
                    "SYNTHETIC_SOURCE_001",
                    content="Synthetic orchard passage.",
                ),
            ),
            candidate_grounded_draft=_grounded_draft(
                summary_points=("Synthetic only summary point.",)
            ),
            acceptable_evidence=(_label(summary_point_index=1),),
        )


def test_grounding_evaluation_case_rejects_label_document_outside_corpus() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^acceptable_evidence document_id values must reference "
            r"document_id values present in source_documents\.$"
        ),
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(_label(document_id="SYNTHETIC_SOURCE_MISSING"),),
        )


def test_grounding_evaluation_case_rejects_label_supporting_text_not_in_document() -> (
    None
):
    with pytest.raises(
        ValueError,
        match=(
            r"^acceptable_evidence supporting_text must occur as an exact "
            r"contiguous substring of the referenced source document content\.$"
        ),
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=(
                _document(
                    "SYNTHETIC_SOURCE_001",
                    content="Synthetic orchard passage.",
                ),
            ),
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(
                _label(supporting_text="Synthetic missing contiguous passage."),
            ),
        )


def test_grounding_evaluation_case_rejects_duplicate_labels() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage.",
        ),
    )
    duplicate_label = _label(supporting_text="Synthetic orchard passage.")

    with pytest.raises(
        ValueError,
        match=r"^acceptable_evidence must not contain duplicate labels\.$",
    ):
        GroundingEvaluationCase(
            evaluation_id="EVAL_GROUNDING_LABELS",
            source_documents=documents,
            candidate_grounded_draft=_grounded_draft(),
            acceptable_evidence=(duplicate_label, duplicate_label),
        )


@pytest.mark.parametrize("summary_point_index", (-1,))
def test_grounding_evidence_label_rejects_negative_summary_point_index(
    summary_point_index: int,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^summary_point_index must not be negative\.$",
    ):
        GroundingEvidenceLabel(
            summary_point_index=summary_point_index,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic orchard passage.",
        )


@pytest.mark.parametrize("summary_point_index", (True, False, 1.5, "0"))
def test_grounding_evidence_label_rejects_non_int_summary_point_index(
    summary_point_index: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^summary_point_index must be an integer\.$",
    ):
        GroundingEvidenceLabel(
            summary_point_index=summary_point_index,  # type: ignore[arg-type]
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic orchard passage.",
        )


@pytest.mark.parametrize("field_name", ("document_id", "supporting_text"))
@pytest.mark.parametrize("value", ("", " \t\n"))
def test_grounding_evidence_label_rejects_blank_string_fields(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "summary_point_index": 0,
        "document_id": "SYNTHETIC_SOURCE_001",
        "supporting_text": "Synthetic orchard passage.",
        field_name: value,
    }

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        GroundingEvidenceLabel(**kwargs)


def test_evaluation_package_exports_grounding_evaluation_case_contract() -> None:
    assert evaluation.GroundingEvaluationCase is GroundingEvaluationCase
    assert evaluation.GroundingEvidenceLabel is GroundingEvidenceLabel
    assert "GroundingEvaluationCase" in evaluation.__all__
    assert "GroundingEvidenceLabel" in evaluation.__all__


def _valid_case() -> GroundingEvaluationCase:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage for contract testing.",
        ),
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_VALID",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            citations=(
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic orchard passage for contract testing.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(supporting_text="Synthetic orchard passage for contract testing."),
        ),
    )


def _grounded_draft(
    *,
    summary_points: tuple[str, ...] = ("Synthetic summary point.",),
    citations: tuple[GroundedDraftCitation, ...] = (),
) -> GroundedDraft:
    return GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=summary_points,
            uncertainties=("Synthetic uncertainty.",),
            review_questions=("Synthetic review question?",),
        ),
        citations=citations,
    )


def _candidate_citation(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic supporting text.",
) -> GroundedDraftCitation:
    return GroundedDraftCitation(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _label(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic orchard passage.",
) -> GroundingEvidenceLabel:
    return GroundingEvidenceLabel(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _document(
    document_id: str,
    *,
    title: str = "Synthetic source title",
    content: str = "Synthetic orchard passage.",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
