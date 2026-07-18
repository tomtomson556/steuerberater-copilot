import json

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    GroundedDraftParseError,
    StructuredDraftOutput,
    parse_grounded_draft,
)


def test_parse_grounded_draft_returns_complete_contract() -> None:
    result = _parse(_valid_payload())

    assert isinstance(result, GroundedDraft)
    assert result.structured_draft == StructuredDraftOutput(
        summary_points=(
            "Synthetic supported summary point one.",
            "Synthetic supported summary point two.",
        ),
        uncertainties=("Synthetic uncertainty requiring review.",),
        review_questions=(
            "Which synthetic assumption requires human review?",
        ),
    )
    assert result.citations == (
        GroundedDraftCitation(
            summary_point_index=0,
            document_id="SYNTHETIC_SOURCE_001",
            supporting_text="Exact synthetic supporting passage one.",
        ),
        GroundedDraftCitation(
            summary_point_index=1,
            document_id="SYNTHETIC_SOURCE_002",
            supporting_text="Exact synthetic supporting passage two.",
        ),
    )


def test_parse_grounded_draft_preserves_all_array_orders() -> None:
    result = _parse(_valid_payload())

    assert result.structured_draft.summary_points == (
        "Synthetic supported summary point one.",
        "Synthetic supported summary point two.",
    )
    assert result.structured_draft.uncertainties == (
        "Synthetic uncertainty requiring review.",
    )
    assert result.structured_draft.review_questions == (
        "Which synthetic assumption requires human review?",
    )
    assert tuple(citation.document_id for citation in result.citations) == (
        "SYNTHETIC_SOURCE_001",
        "SYNTHETIC_SOURCE_002",
    )


def test_parse_grounded_draft_keeps_unicode_whitespace_and_strings_unchanged() -> None:
    decomposed_summary = " Synthetic Cafe\u0301 summary. "
    decomposed_document_id = " SYNTHETIC_SOURCE_Cafe\u0301 "
    supporting_text = "\nExact synthetic Cafe\u0301 supporting passage.\n"
    payload = {
        "summary_points": [decomposed_summary, "", " \t"],
        "uncertainties": [" Synthetic uncertainty. "],
        "review_questions": ["\nSynthetic review question?\n"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": decomposed_document_id,
                "supporting_text": supporting_text,
            }
        ],
    }

    result = _parse(payload)

    assert result.structured_draft.summary_points == (
        decomposed_summary,
        "",
        " \t",
    )
    assert result.structured_draft.uncertainties == (" Synthetic uncertainty. ",)
    assert result.structured_draft.review_questions == (
        "\nSynthetic review question?\n",
    )
    assert result.citations[0].document_id == decomposed_document_id
    assert result.citations[0].supporting_text == supporting_text


def test_parse_grounded_draft_accepts_different_json_field_order() -> None:
    content = json.dumps(
        {
            "citations": [
                {
                    "supporting_text": "Exact synthetic supporting passage.",
                    "document_id": "SYNTHETIC_SOURCE_001",
                    "summary_point_index": 0,
                }
            ],
            "review_questions": ["Synthetic review question?"],
            "summary_points": ["Synthetic supported summary point."],
            "uncertainties": ["Synthetic uncertainty."],
        }
    )

    result = parse_grounded_draft(content)

    assert result.citations[0].summary_point_index == 0
    assert result.structured_draft.summary_points == (
        "Synthetic supported summary point.",
    )


def test_parse_grounded_draft_accepts_empty_arrays() -> None:
    result = _parse(
        {
            "summary_points": [],
            "uncertainties": [],
            "review_questions": [],
            "citations": [],
        }
    )

    assert result == GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=(),
            uncertainties=(),
            review_questions=(),
        ),
        citations=(),
    )


def test_parse_grounded_draft_accepts_partial_citation_coverage() -> None:
    payload = _valid_payload()
    payload["citations"] = [payload["citations"][1]]

    result = _parse(payload)

    assert len(result.structured_draft.summary_points) == 2
    assert tuple(citation.summary_point_index for citation in result.citations) == (1,)


def test_parse_grounded_draft_accepts_repeated_summary_point_and_document_citations() -> None:
    payload = _valid_payload()
    payload["citations"] = [
        {
            "summary_point_index": 0,
            "document_id": "SYNTHETIC_SOURCE_001",
            "supporting_text": "First synthetic supporting passage.",
        },
        {
            "summary_point_index": 0,
            "document_id": "SYNTHETIC_SOURCE_001",
            "supporting_text": "Second synthetic supporting passage.",
        },
    ]

    result = _parse(payload)

    assert tuple(citation.summary_point_index for citation in result.citations) == (0, 0)
    assert tuple(citation.document_id for citation in result.citations) == (
        "SYNTHETIC_SOURCE_001",
        "SYNTHETIC_SOURCE_001",
    )


def test_parse_grounded_draft_does_not_validate_document_or_supporting_text() -> None:
    payload = _valid_payload()
    payload["citations"] = [
        {
            "summary_point_index": 0,
            "document_id": "SYNTHETIC_UNKNOWN_SOURCE",
            "supporting_text": "Synthetic passage not checked against any document.",
        }
    ]

    result = _parse(payload)

    assert result.citations[0].document_id == "SYNTHETIC_UNKNOWN_SOURCE"
    assert result.citations[0].supporting_text == (
        "Synthetic passage not checked against any document."
    )


def test_parse_grounded_draft_rejects_invalid_json_with_cause() -> None:
    invalid_content = (
        '{"summary_points": [], "uncertainties": [], '
        '"review_questions": [], "citations": [}'
    )

    with pytest.raises(GroundedDraftParseError) as exc_info:
        parse_grounded_draft(invalid_content)

    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)
    assert "not valid JSON" in str(exc_info.value)
    assert invalid_content not in str(exc_info.value)


def test_parse_grounded_draft_rejects_markdown_code_fences() -> None:
    content = (
        "```json\n"
        '{"summary_points": [], "uncertainties": [], '
        '"review_questions": [], "citations": []}\n'
        "```"
    )

    with pytest.raises(GroundedDraftParseError, match="not valid JSON"):
        parse_grounded_draft(content)


@pytest.mark.parametrize("content", ("[]", '"synthetic output"', "null"))
def test_parse_grounded_draft_rejects_non_object_top_level(content: str) -> None:
    with pytest.raises(GroundedDraftParseError, match="must be an object"):
        parse_grounded_draft(content)


@pytest.mark.parametrize(
    "missing_field",
    ("summary_points", "uncertainties", "review_questions", "citations"),
)
def test_parse_grounded_draft_rejects_missing_top_level_fields(
    missing_field: str,
) -> None:
    payload = _valid_payload()
    del payload[missing_field]

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert "missing fields" in str(exc_info.value)
    assert missing_field in str(exc_info.value)


def test_parse_grounded_draft_rejects_unexpected_top_level_fields() -> None:
    payload = _valid_payload()
    payload["confidence"] = "SYNTHETIC_INVALID_VALUE"

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert "unexpected fields" in str(exc_info.value)
    assert "confidence" in str(exc_info.value)
    assert "SYNTHETIC_INVALID_VALUE" not in str(exc_info.value)


def test_parse_grounded_draft_rejects_duplicate_top_level_fields() -> None:
    content = (
        "{"
        '"summary_points":[],'
        '"summary_points":["Synthetic replacement."],'
        '"uncertainties":[],'
        '"review_questions":[],'
        '"citations":[]'
        "}"
    )

    with pytest.raises(GroundedDraftParseError) as exc_info:
        parse_grounded_draft(content)

    assert "duplicate field" in str(exc_info.value)
    assert "summary_points" in str(exc_info.value)
    assert "Synthetic replacement." not in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    ("summary_points", "uncertainties", "review_questions"),
)
def test_parse_grounded_draft_rejects_non_array_draft_fields(
    field_name: str,
) -> None:
    payload = _valid_payload()
    payload[field_name] = "Synthetic non-array value."

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert f"'{field_name}'" in str(exc_info.value)
    assert "must be an array" in str(exc_info.value)
    assert "Synthetic non-array value." not in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    ("summary_points", "uncertainties", "review_questions"),
)
def test_parse_grounded_draft_rejects_non_string_draft_array_items(
    field_name: str,
) -> None:
    payload = _valid_payload()
    payload[field_name] = ["Synthetic valid item.", 42]

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert f"'{field_name}'" in str(exc_info.value)
    assert "must contain only strings" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_value",
    (None, "Synthetic non-array value.", {"synthetic": "object"}),
)
def test_parse_grounded_draft_rejects_non_array_citations(
    invalid_value: object,
) -> None:
    payload = _valid_payload()
    payload["citations"] = invalid_value

    with pytest.raises(GroundedDraftParseError, match="must be an array"):
        _parse(payload)


@pytest.mark.parametrize(
    "invalid_entry",
    (None, "Synthetic non-object citation.", ["synthetic", "citation"]),
)
def test_parse_grounded_draft_rejects_non_object_citation_entries(
    invalid_entry: object,
) -> None:
    payload = _valid_payload()
    payload["citations"] = [invalid_entry]

    with pytest.raises(GroundedDraftParseError, match="contain only objects"):
        _parse(payload)


@pytest.mark.parametrize(
    "missing_field",
    ("summary_point_index", "document_id", "supporting_text"),
)
def test_parse_grounded_draft_rejects_missing_citation_fields(
    missing_field: str,
) -> None:
    payload = _valid_payload()
    del payload["citations"][0][missing_field]

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert "citation object" in str(exc_info.value)
    assert "missing fields" in str(exc_info.value)
    assert missing_field in str(exc_info.value)


def test_parse_grounded_draft_rejects_unexpected_citation_fields() -> None:
    payload = _valid_payload()
    payload["citations"][0]["confidence"] = "SYNTHETIC_INVALID_VALUE"

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert "citation object" in str(exc_info.value)
    assert "unexpected fields" in str(exc_info.value)
    assert "confidence" in str(exc_info.value)
    assert "SYNTHETIC_INVALID_VALUE" not in str(exc_info.value)


def test_parse_grounded_draft_rejects_duplicate_citation_fields() -> None:
    content = (
        "{"
        '"summary_points":["Synthetic summary."],'
        '"uncertainties":[],'
        '"review_questions":[],'
        '"citations":[{'
        '"summary_point_index":0,'
        '"document_id":"SYNTHETIC_SOURCE_001",'
        '"document_id":"SYNTHETIC_REPLACEMENT_SOURCE",'
        '"supporting_text":"Synthetic supporting passage."'
        "}]"
        "}"
    )

    with pytest.raises(GroundedDraftParseError) as exc_info:
        parse_grounded_draft(content)

    assert "duplicate field" in str(exc_info.value)
    assert "document_id" in str(exc_info.value)
    assert "SYNTHETIC_REPLACEMENT_SOURCE" not in str(exc_info.value)


@pytest.mark.parametrize("invalid_index", (None, 1.5, "0"))
def test_parse_grounded_draft_rejects_non_integer_citation_index(
    invalid_index: object,
) -> None:
    payload = _valid_payload()
    payload["citations"][0]["summary_point_index"] = invalid_index

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, TypeError)
    assert "invalid field values" in str(exc_info.value)


@pytest.mark.parametrize("invalid_index", (False, True))
def test_parse_grounded_draft_rejects_bool_citation_index(
    invalid_index: bool,
) -> None:
    payload = _valid_payload()
    payload["citations"][0]["summary_point_index"] = invalid_index

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, TypeError)


def test_parse_grounded_draft_rejects_negative_citation_index() -> None:
    payload = _valid_payload()
    payload["citations"][0]["summary_point_index"] = -1

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "invalid field values" in str(exc_info.value)


def test_parse_grounded_draft_rejects_citation_index_outside_summary_points() -> None:
    payload = _valid_payload()
    payload["citations"][0]["summary_point_index"] = 2

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "do not match the structured draft" in str(exc_info.value)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("document_id", None),
        ("document_id", ["SYNTHETIC_INVALID_VALUE"]),
        ("supporting_text", None),
        ("supporting_text", ["SYNTHETIC_INVALID_VALUE"]),
    ),
)
def test_parse_grounded_draft_rejects_non_string_citation_fields(
    field_name: str,
    invalid_value: object,
) -> None:
    payload = _valid_payload()
    payload["citations"][0][field_name] = invalid_value

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, TypeError)
    assert "SYNTHETIC_INVALID_VALUE" not in str(exc_info.value)


@pytest.mark.parametrize("field_name", ("document_id", "supporting_text"))
@pytest.mark.parametrize("blank_value", ("", " \t\n"))
def test_parse_grounded_draft_rejects_blank_citation_strings(
    field_name: str,
    blank_value: str,
) -> None:
    payload = _valid_payload()
    payload["citations"][0][field_name] = blank_value

    with pytest.raises(GroundedDraftParseError) as exc_info:
        _parse(payload)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_parse_grounded_draft_error_does_not_expose_content_or_invalid_values() -> None:
    invalid_value = "SYNTHETIC_INVALID_VALUE_MUST_NOT_APPEAR"
    payload = _valid_payload()
    payload["citations"][0]["document_id"] = [invalid_value]
    content = json.dumps(payload)

    with pytest.raises(GroundedDraftParseError) as exc_info:
        parse_grounded_draft(content)

    error_message = str(exc_info.value)
    assert content not in error_message
    assert invalid_value not in error_message


@pytest.mark.parametrize("content", (None, 1, b"{}"))
def test_parse_grounded_draft_rejects_non_string_content(content: object) -> None:
    with pytest.raises(
        GroundedDraftParseError,
        match=r"^Model response content must be a string\.$",
    ):
        parse_grounded_draft(content)


def test_grounded_draft_parser_public_exports() -> None:
    assert offline_mvp.GroundedDraftParseError is GroundedDraftParseError
    assert offline_mvp.parse_grounded_draft is parse_grounded_draft
    assert "GroundedDraftParseError" in offline_mvp.__all__
    assert "parse_grounded_draft" in offline_mvp.__all__


def _parse(payload: dict[str, object]) -> GroundedDraft:
    return parse_grounded_draft(json.dumps(payload, ensure_ascii=False))


def _valid_payload() -> dict[str, object]:
    return {
        "summary_points": [
            "Synthetic supported summary point one.",
            "Synthetic supported summary point two.",
        ],
        "uncertainties": ["Synthetic uncertainty requiring review."],
        "review_questions": [
            "Which synthetic assumption requires human review?",
        ],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": "Exact synthetic supporting passage one.",
            },
            {
                "summary_point_index": 1,
                "document_id": "SYNTHETIC_SOURCE_002",
                "supporting_text": "Exact synthetic supporting passage two.",
            },
        ],
    }
