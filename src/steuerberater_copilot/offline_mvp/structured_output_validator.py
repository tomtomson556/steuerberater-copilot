"""Deterministic semantic checks for parsed structured draft output."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .structured_output import StructuredDraftOutput

_FIELD_NAMES = (
    "summary_points",
    "uncertainties",
    "review_questions",
)

_PROFESSIONAL_REVIEW_CLAIM_PATTERNS = (
    re.compile(r"\Ader entwurf ist fachlich gepr\u00fcft\.?\Z", re.IGNORECASE),
    re.compile(r"\Ader entwurf wurde steuerlich gepr\u00fcft\.?\Z", re.IGNORECASE),
    re.compile(r"\Athe draft has been professionally reviewed\.?\Z", re.IGNORECASE),
    re.compile(r"\Athe result is tax reviewed\.?\Z", re.IGNORECASE),
)

_FINALITY_OR_RELEASE_CLAIM_PATTERNS = (
    re.compile(r"\Ader entwurf ist final freigegeben\.?\Z", re.IGNORECASE),
    re.compile(r"\Ader entwurf wurde endg\u00fcltig genehmigt\.?\Z", re.IGNORECASE),
    re.compile(
        r"\Ader entwurf ist zur einreichung freigegeben\.?\Z",
        re.IGNORECASE,
    ),
    re.compile(r"\Athe draft is finally approved\.?\Z", re.IGNORECASE),
    re.compile(r"\Athe draft is approved for filing\.?\Z", re.IGNORECASE),
    re.compile(r"\Athe result is cleared for submission\.?\Z", re.IGNORECASE),
)


class StructuredDraftOutputValidationError(ValueError):
    """Raised when parsed draft output violates deterministic semantic rules."""

    rule: str
    field_name: str
    item_index: int

    def __init__(self, rule: str, field_name: str, item_index: int) -> None:
        self.rule = rule
        self.field_name = field_name
        self.item_index = item_index
        super().__init__(
            "Structured draft output validation failed: "
            f"field={field_name}, index={item_index}, rule={rule}."
        )


def validate_structured_draft_output(
    output: StructuredDraftOutput,
) -> None:
    """Validate parsed draft output without modifying or normalizing strings."""
    for field_name in _FIELD_NAMES:
        _validate_field(field_name, getattr(output, field_name))


def _validate_field(field_name: str, entries: Iterable[str]) -> None:
    seen_entries: set[str] = set()
    for index, entry in enumerate(entries):
        if entry == "" or entry.isspace():
            _raise_validation_error("blank_entry", field_name, index)

        if entry in seen_entries:
            _raise_validation_error("duplicate_entry", field_name, index)
        seen_entries.add(entry)

        if _matches_any(entry, _PROFESSIONAL_REVIEW_CLAIM_PATTERNS):
            _raise_validation_error("professional_review_claim", field_name, index)

        if _matches_any(entry, _FINALITY_OR_RELEASE_CLAIM_PATTERNS):
            _raise_validation_error("finality_or_release_claim", field_name, index)


def _matches_any(entry: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.fullmatch(entry) for pattern in patterns)


def _raise_validation_error(rule: str, field_name: str, item_index: int) -> None:
    raise StructuredDraftOutputValidationError(
        rule=rule,
        field_name=field_name,
        item_index=item_index,
    )
