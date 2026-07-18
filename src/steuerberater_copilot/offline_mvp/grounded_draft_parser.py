"""Parse raw model content into the grounded draft contracts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from .grounded_draft import GroundedDraft, GroundedDraftCitation
from .structured_output import StructuredDraftOutput

_DRAFT_FIELDS = (
    "summary_points",
    "uncertainties",
    "review_questions",
)
_EXPECTED_TOP_LEVEL_FIELDS = frozenset((*_DRAFT_FIELDS, "citations"))
_EXPECTED_CITATION_FIELDS = frozenset(
    {
        "summary_point_index",
        "document_id",
        "supporting_text",
    }
)


class GroundedDraftParseError(ValueError):
    """Raised when model content does not match the grounded draft structure."""


def parse_grounded_draft(content: str) -> GroundedDraft:
    """Parse strict JSON model content into a grounded draft contract."""
    if not isinstance(content, str):
        raise GroundedDraftParseError("Model response content must be a string.")

    try:
        payload = json.loads(content, object_pairs_hook=_reject_duplicate_fields)
    except json.JSONDecodeError as exc:
        raise GroundedDraftParseError(
            "Model response content is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise GroundedDraftParseError("Model response JSON must be an object.")

    _check_exact_fields(
        payload,
        expected_fields=_EXPECTED_TOP_LEVEL_FIELDS,
        object_name="top-level object",
    )

    structured_draft = StructuredDraftOutput(
        summary_points=tuple(_get_string_array(payload, "summary_points")),
        uncertainties=tuple(_get_string_array(payload, "uncertainties")),
        review_questions=tuple(_get_string_array(payload, "review_questions")),
    )
    citations = tuple(_get_citation_array(payload))

    try:
        return GroundedDraft(
            structured_draft=structured_draft,
            citations=citations,
        )
    except (TypeError, ValueError) as exc:
        raise GroundedDraftParseError(
            "Model response citations do not match the structured draft."
        ) from exc


def _reject_duplicate_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise GroundedDraftParseError(
                f"Model response JSON contains duplicate field: {key}."
            )
        payload[key] = value
    return payload


def _check_exact_fields(
    payload: dict[str, Any],
    *,
    expected_fields: frozenset[str],
    object_name: str,
) -> None:
    fields = set(payload)
    missing_fields = expected_fields - fields
    if missing_fields:
        raise GroundedDraftParseError(
            f"Model response JSON {object_name} has missing fields: "
            f"{_format_field_names(missing_fields)}."
        )

    unexpected_fields = fields - expected_fields
    if unexpected_fields:
        raise GroundedDraftParseError(
            f"Model response JSON {object_name} has unexpected fields: "
            f"{_format_field_names(unexpected_fields)}."
        )


def _get_string_array(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload[field_name]
    if not isinstance(value, list):
        raise GroundedDraftParseError(
            f"Model response field '{field_name}' must be an array."
        )
    if not all(isinstance(item, str) for item in value):
        raise GroundedDraftParseError(
            f"Model response field '{field_name}' must contain only strings."
        )
    return value


def _get_citation_array(payload: dict[str, Any]) -> list[GroundedDraftCitation]:
    value = payload["citations"]
    if not isinstance(value, list):
        raise GroundedDraftParseError(
            "Model response field 'citations' must be an array."
        )

    citations = []
    for citation_payload in value:
        if not isinstance(citation_payload, dict):
            raise GroundedDraftParseError(
                "Model response field 'citations' must contain only objects."
            )
        _check_exact_fields(
            citation_payload,
            expected_fields=_EXPECTED_CITATION_FIELDS,
            object_name="citation object",
        )
        try:
            citation = GroundedDraftCitation(
                summary_point_index=citation_payload["summary_point_index"],
                document_id=citation_payload["document_id"],
                supporting_text=citation_payload["supporting_text"],
            )
        except (TypeError, ValueError) as exc:
            raise GroundedDraftParseError(
                "Model response citation has invalid field values."
            ) from exc
        citations.append(citation)

    return citations


def _format_field_names(field_names: Iterable[str]) -> str:
    return ", ".join(sorted(field_names))
