from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    StructuredDraftOutput,
)


def test_grounded_draft_contracts_are_publicly_exported() -> None:
    assert offline_mvp.GroundedDraft is GroundedDraft
    assert offline_mvp.GroundedDraftCitation is GroundedDraftCitation
    assert "GroundedDraft" in offline_mvp.__all__
    assert "GroundedDraftCitation" in offline_mvp.__all__


def test_grounded_draft_citation_uses_value_equality() -> None:
    assert _citation() == _citation()


def test_grounded_draft_uses_value_equality() -> None:
    assert GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(_citation(),),
    ) == GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(_citation(),),
    )


def test_grounded_draft_citation_is_immutable_and_uses_slots() -> None:
    citation = _citation()

    for field_name in ("summary_point_index", "document_id", "supporting_text"):
        with pytest.raises(FrozenInstanceError):
            setattr(citation, field_name, "Changed synthetic value.")

    assert not hasattr(citation, "__dict__")
    assert GroundedDraftCitation.__slots__ == (
        "summary_point_index",
        "document_id",
        "supporting_text",
    )


def test_grounded_draft_is_immutable_and_uses_slots() -> None:
    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(_citation(),),
    )

    for field_name in ("structured_draft", "citations"):
        with pytest.raises(FrozenInstanceError):
            setattr(grounded_draft, field_name, ())

    assert not hasattr(grounded_draft, "__dict__")
    assert GroundedDraft.__slots__ == ("structured_draft", "citations")


def test_grounded_draft_citation_keeps_valid_values_unchanged() -> None:
    document_id = " SYNTHETIC_SOURCE_Cafe\u0301 "
    supporting_text = "\nSynthetic Cafe\u0301 supporting text remains unchanged.\n"

    citation = GroundedDraftCitation(
        summary_point_index=1,
        document_id=document_id,
        supporting_text=supporting_text,
    )

    assert citation.summary_point_index == 1
    assert citation.document_id is document_id
    assert citation.supporting_text is supporting_text


def test_grounded_draft_keeps_draft_tuple_and_citation_identities() -> None:
    structured_draft = _structured_draft()
    first_citation = _citation(summary_point_index=0)
    second_citation = _citation(
        summary_point_index=1,
        document_id="SYNTHETIC_SOURCE_002",
    )
    citations = (first_citation, second_citation)

    grounded_draft = GroundedDraft(
        structured_draft=structured_draft,
        citations=citations,
    )

    assert grounded_draft.structured_draft is structured_draft
    assert grounded_draft.citations is citations
    assert grounded_draft.citations[0] is first_citation
    assert grounded_draft.citations[1] is second_citation


def test_grounded_draft_maps_citations_to_multiple_summary_points() -> None:
    first_citation = _citation(summary_point_index=0)
    second_citation = _citation(
        summary_point_index=1,
        document_id="SYNTHETIC_SOURCE_002",
        supporting_text="Synthetic support for the second summary point.",
    )

    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(first_citation, second_citation),
    )

    assert tuple(
        citation.summary_point_index for citation in grounded_draft.citations
    ) == (0, 1)


def test_grounded_draft_allows_multiple_citations_for_same_summary_point() -> None:
    first_citation = _citation(summary_point_index=0)
    second_citation = _citation(
        summary_point_index=0,
        supporting_text="Second synthetic supporting passage from the same source.",
    )

    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(first_citation, second_citation),
    )

    assert grounded_draft.citations == (first_citation, second_citation)
    assert {citation.document_id for citation in grounded_draft.citations} == {
        "SYNTHETIC_SOURCE_001"
    }


def test_grounded_draft_allows_empty_citations_with_summary_points() -> None:
    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(),
    )

    assert grounded_draft.citations == ()


def test_grounded_draft_allows_empty_draft_and_empty_citations() -> None:
    empty_draft = StructuredDraftOutput(
        summary_points=(),
        uncertainties=(),
        review_questions=(),
    )

    grounded_draft = GroundedDraft(
        structured_draft=empty_draft,
        citations=(),
    )

    assert grounded_draft.structured_draft is empty_draft
    assert grounded_draft.citations == ()


def test_grounded_draft_allows_partial_citation_coverage() -> None:
    citation = _citation(summary_point_index=1)

    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(citation,),
    )

    assert grounded_draft.citations == (citation,)
    assert grounded_draft.structured_draft.summary_points[0] == (
        "Synthetic first summary point."
    )


@pytest.mark.parametrize("summary_point_index", (None, 1.0, "1"))
def test_grounded_draft_citation_rejects_non_integer_index(
    summary_point_index: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^summary_point_index must be an integer\.$",
    ):
        GroundedDraftCitation(
            summary_point_index=summary_point_index,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic supporting passage.",
        )


@pytest.mark.parametrize("summary_point_index", (False, True))
def test_grounded_draft_citation_rejects_bool_index(
    summary_point_index: bool,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^summary_point_index must be an integer\.$",
    ):
        GroundedDraftCitation(
            summary_point_index=summary_point_index,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic supporting passage.",
        )


def test_grounded_draft_citation_rejects_negative_index() -> None:
    with pytest.raises(
        ValueError,
        match=r"^summary_point_index must not be negative\.$",
    ):
        GroundedDraftCitation(
            summary_point_index=-1,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Synthetic supporting passage.",
        )


def test_grounded_draft_rejects_index_outside_summary_points() -> None:
    citation = _citation(summary_point_index=2)

    with pytest.raises(
        ValueError,
        match=(
            r"^citation summary_point_index must reference an existing summary point\.$"
        ),
    ):
        GroundedDraft(
            structured_draft=_structured_draft(),
            citations=(citation,),
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("document_id", None),
        ("document_id", 1),
        ("supporting_text", None),
        ("supporting_text", ["Synthetic supporting passage."]),
    ),
)
def test_grounded_draft_citation_rejects_non_string_fields(
    field_name: str,
    invalid_value: object,
) -> None:
    arguments: dict[str, object] = _citation_arguments()
    arguments[field_name] = invalid_value

    with pytest.raises(TypeError, match=rf"^{field_name} must be a string\.$"):
        GroundedDraftCitation(**arguments)


@pytest.mark.parametrize("field_name", ("document_id", "supporting_text"))
@pytest.mark.parametrize("blank_value", ("", " \t\n"))
def test_grounded_draft_citation_rejects_blank_string_fields(
    field_name: str,
    blank_value: str,
) -> None:
    arguments: dict[str, object] = _citation_arguments()
    arguments[field_name] = blank_value

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        GroundedDraftCitation(**arguments)


def test_grounded_draft_rejects_wrong_structured_draft_type() -> None:
    with pytest.raises(
        TypeError,
        match=r"^structured_draft must be a StructuredDraftOutput\.$",
    ):
        GroundedDraft(
            structured_draft="Synthetic non-draft value.",
            citations=(),
        )


def test_grounded_draft_rejects_non_tuple_citation_collection() -> None:
    with pytest.raises(TypeError, match=r"^citations must be a tuple\.$"):
        GroundedDraft(
            structured_draft=_structured_draft(),
            citations=[_citation()],
        )


def test_grounded_draft_rejects_foreign_citation_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^citations must contain only GroundedDraftCitation objects\.$",
    ):
        GroundedDraft(
            structured_draft=_structured_draft(),
            citations=("Synthetic non-citation value.",),
        )


def test_grounded_draft_does_not_validate_document_or_supporting_text() -> None:
    citation = GroundedDraftCitation(
        summary_point_index=0,
        document_id="SYNTHETIC_SOURCE_NOT_IN_A_DOCUMENT_COLLECTION",
        supporting_text="Synthetic passage not checked against document content.",
    )

    grounded_draft = GroundedDraft(
        structured_draft=_structured_draft(),
        citations=(citation,),
    )

    assert grounded_draft.citations == (citation,)


def _citation(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic supporting passage for a summary point.",
) -> GroundedDraftCitation:
    return GroundedDraftCitation(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _citation_arguments() -> dict[str, object]:
    return {
        "summary_point_index": 0,
        "document_id": "SYNTHETIC_SOURCE_001",
        "supporting_text": "Synthetic supporting passage for a summary point.",
    }


def _structured_draft() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=(
            "Synthetic first summary point.",
            "Synthetic second summary point.",
        ),
        uncertainties=("Synthetic uncertainty remains for review.",),
        review_questions=("Which synthetic assumption requires review?",),
    )
