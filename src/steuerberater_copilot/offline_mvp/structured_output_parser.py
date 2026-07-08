"""Parse raw model content into the structured draft output contract."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from .structured_output import StructuredDraftOutput

_EXPECTED_FIELDS = frozenset(
    {
        "summary_points",
        "uncertainties",
        "review_questions",
    }
)


class StructuredDraftOutputParseError(ValueError):
    """Raised when raw model content does not match the structural output contract."""


def parse_structured_draft_output(content: str) -> StructuredDraftOutput:
    """Parse raw JSON model content into a structurally checked draft output."""
    try:
        payload = json.loads(content, object_pairs_hook=_reject_duplicate_fields)
    except json.JSONDecodeError as exc:
        raise StructuredDraftOutputParseError(
            "Model response content is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise StructuredDraftOutputParseError("Model response JSON must be an object.")

    _check_exact_fields(payload)

    summary_points = _get_string_array(payload, "summary_points")
    uncertainties = _get_string_array(payload, "uncertainties")
    review_questions = _get_string_array(payload, "review_questions")

    return StructuredDraftOutput(
        summary_points=tuple(summary_points),
        uncertainties=tuple(uncertainties),
        review_questions=tuple(review_questions),
    )


def _reject_duplicate_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise StructuredDraftOutputParseError(
                f"Model response JSON contains duplicate field: {key}."
            )
        payload[key] = value
    return payload


def _check_exact_fields(payload: dict[str, Any]) -> None:
    fields = set(payload)
    missing_fields = _EXPECTED_FIELDS - fields
    if missing_fields:
        raise StructuredDraftOutputParseError(
            "Model response JSON has missing fields: "
            f"{_format_field_names(missing_fields)}."
        )

    unexpected_fields = fields - _EXPECTED_FIELDS
    if unexpected_fields:
        raise StructuredDraftOutputParseError(
            "Model response JSON has unexpected fields: "
            f"{_format_field_names(unexpected_fields)}."
        )


def _get_string_array(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload[field_name]
    if not isinstance(value, list):
        raise StructuredDraftOutputParseError(
            f"Model response field '{field_name}' must be an array."
        )

    if not all(isinstance(item, str) for item in value):
        raise StructuredDraftOutputParseError(
            f"Model response field '{field_name}' must contain only strings."
        )

    return value


def _format_field_names(field_names: Iterable[str]) -> str:
    return ", ".join(sorted(field_names))
