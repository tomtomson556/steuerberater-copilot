import json

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import (
    StructuredDraftOutput,
    StructuredDraftOutputParseError,
    parse_structured_draft_output,
)


def test_parse_structured_draft_output_returns_ordered_contract_values() -> None:
    result = parse_structured_draft_output(
        json.dumps(
            {
                "summary_points": [
                    "Synthetic fact one.",
                    "Synthetic fact two.",
                ],
                "uncertainties": [
                    "Synthetic uncertainty one.",
                    "Synthetic uncertainty two.",
                ],
                "review_questions": [
                    "Synthetic question one?",
                    "Synthetic question two?",
                ],
            }
        )
    )

    assert isinstance(result, StructuredDraftOutput)
    assert result.summary_points == (
        "Synthetic fact one.",
        "Synthetic fact two.",
    )
    assert result.uncertainties == (
        "Synthetic uncertainty one.",
        "Synthetic uncertainty two.",
    )
    assert result.review_questions == (
        "Synthetic question one?",
        "Synthetic question two?",
    )


def test_parse_structured_draft_output_accepts_different_key_order() -> None:
    result = parse_structured_draft_output(
        json.dumps(
            {
                "review_questions": ["Synthetic question?"],
                "summary_points": ["Synthetic fact."],
                "uncertainties": ["Synthetic uncertainty."],
            }
        )
    )

    assert result == StructuredDraftOutput(
        summary_points=("Synthetic fact.",),
        uncertainties=("Synthetic uncertainty.",),
        review_questions=("Synthetic question?",),
    )


def test_parse_structured_draft_output_accepts_surrounding_json_whitespace() -> None:
    result = parse_structured_draft_output(
        '\n  {"summary_points": [], "uncertainties": [], "review_questions": []} \n'
    )

    assert result == StructuredDraftOutput(
        summary_points=(),
        uncertainties=(),
        review_questions=(),
    )


def test_parse_structured_draft_output_accepts_empty_arrays() -> None:
    result = parse_structured_draft_output(
        '{"summary_points": [], "uncertainties": [], "review_questions": []}'
    )

    assert result.summary_points == ()
    assert result.uncertainties == ()
    assert result.review_questions == ()


def test_parse_structured_draft_output_does_not_normalize_string_values() -> None:
    result = parse_structured_draft_output(
        json.dumps(
            {
                "summary_points": [
                    " leading space",
                    "trailing space ",
                    "",
                    "   ",
                    "synthetische Umlaute ä ö ü ß and €",
                    "escaped\nnewline",
                ],
                "uncertainties": [],
                "review_questions": [],
            },
            ensure_ascii=False,
        )
    )

    assert result.summary_points == (
        " leading space",
        "trailing space ",
        "",
        "   ",
        "synthetische Umlaute ä ö ü ß and €",
        "escaped\nnewline",
    )


def test_parse_structured_draft_output_rejects_invalid_json_with_cause() -> None:
    invalid_content = (
        '{"summary_points": [], "uncertainties": [], "review_questions": [}'
    )

    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(invalid_content)

    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)
    assert "not valid JSON" in str(exc_info.value)
    assert invalid_content not in str(exc_info.value)


def test_parse_structured_draft_output_rejects_markdown_code_fences() -> None:
    with pytest.raises(StructuredDraftOutputParseError, match="not valid JSON"):
        parse_structured_draft_output(
            '```json\n'
            '{"summary_points": [], "uncertainties": [], "review_questions": []}\n'
            "```"
        )


@pytest.mark.parametrize("content", ("[]", '"output"'))
def test_parse_structured_draft_output_rejects_non_object_top_level(
    content: str,
) -> None:
    with pytest.raises(StructuredDraftOutputParseError, match="must be an object"):
        parse_structured_draft_output(content)


@pytest.mark.parametrize(
    "missing_field",
    ("summary_points", "uncertainties", "review_questions"),
)
def test_parse_structured_draft_output_rejects_missing_fields(
    missing_field: str,
) -> None:
    payload = {
        "summary_points": [],
        "uncertainties": [],
        "review_questions": [],
    }
    del payload[missing_field]

    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(json.dumps(payload))

    assert "missing fields" in str(exc_info.value)
    assert missing_field in str(exc_info.value)


def test_parse_structured_draft_output_rejects_unexpected_fields() -> None:
    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(
            json.dumps(
                {
                    "summary_points": [],
                    "uncertainties": [],
                    "review_questions": [],
                    "confidence": 0.9,
                }
            )
        )

    assert "unexpected fields" in str(exc_info.value)
    assert "confidence" in str(exc_info.value)


def test_parse_structured_draft_output_rejects_duplicate_fields() -> None:
    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(
            '{'
            '"summary_points": [],'
            '"summary_points": ["replacement"],'
            '"uncertainties": [],'
            '"review_questions": []'
            "}"
        )

    assert "duplicate field" in str(exc_info.value)
    assert "summary_points" in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    ("summary_points", "uncertainties", "review_questions"),
)
@pytest.mark.parametrize("invalid_value", (None, "single string", {}, 42))
def test_parse_structured_draft_output_rejects_non_array_fields(
    field_name: str,
    invalid_value: object,
) -> None:
    payload = {
        "summary_points": [],
        "uncertainties": [],
        "review_questions": [],
    }
    payload[field_name] = invalid_value

    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(json.dumps(payload))

    assert f"'{field_name}'" in str(exc_info.value)
    assert "must be an array" in str(exc_info.value)


@pytest.mark.parametrize(
    "field_name",
    ("summary_points", "uncertainties", "review_questions"),
)
@pytest.mark.parametrize("invalid_array", (["valid", 42], [None]))
def test_parse_structured_draft_output_rejects_non_string_array_items(
    field_name: str,
    invalid_array: list[object],
) -> None:
    payload = {
        "summary_points": [],
        "uncertainties": [],
        "review_questions": [],
    }
    payload[field_name] = invalid_array

    with pytest.raises(StructuredDraftOutputParseError) as exc_info:
        parse_structured_draft_output(json.dumps(payload))

    assert f"'{field_name}'" in str(exc_info.value)
    assert "must contain only strings" in str(exc_info.value)


def test_parse_structured_draft_output_public_export() -> None:
    assert offline_mvp.parse_structured_draft_output is parse_structured_draft_output
    assert offline_mvp.StructuredDraftOutputParseError is StructuredDraftOutputParseError
    assert "parse_structured_draft_output" in offline_mvp.__all__
    assert "StructuredDraftOutputParseError" in offline_mvp.__all__
