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

_GERMAN_DRAFT_OR_RESULT = (
    r"(?:(?:der|dieser)\s+entwurf|(?:das|dieses)\s+ergebnis)"
)
_ENGLISH_DRAFT_OR_RESULT = r"(?:(?:the|this)\s+(?:draft|result))"
# Closed, claim-local negation markers. Multi-word forms must be listed as
# whole phrases so intervening-token matching cannot skip past them.
_GERMAN_NEGATION = (
    r"(?:nicht|niemals|noch\s+nicht|keineswegs|keinesfalls|"
    r"in\s+keiner\s+weise)\b"
)
_ENGLISH_NEGATION = r"(?:not|never|in\s+no\s+way)\b"
# Bounded non-negated tokens between finite verb/copula and claim predicate.
# Avoids maintaining an open-ended adverb allowlist while keeping matches local.
_GERMAN_INTERVENING_TOKENS = (
    rf"(?:(?!{_GERMAN_NEGATION})\w+(?:-\w+)*\s+){{0,3}}"
)
_ENGLISH_INTERVENING_TOKENS = (
    rf"(?:(?!{_ENGLISH_NEGATION})\w+(?:-\w+)*\s+){{0,3}}"
)
_GERMAN_COORDINATION = r"(?:,\s*)?(?:aber|sondern|und)\s+"
_ENGLISH_COORDINATION = r"(?:,\s*)?(?:but|and)\s+"
# First conjunct in a coordinated draft/result claim; reuse existing claim vocabulary only.
_GERMAN_COORDINATED_PRIOR_CLAIM = (
    r"(?:"
    r"(?:fachlich|steuerlich)\s+gepr\u00fcft|"
    r"(?:zur|f\u00fcr\s+die)\s+einreichung\s+freigegeben|"
    r"(?:freigegeben|genehmigt)"
    r")\b"
)
_ENGLISH_COORDINATED_PRIOR_CLAIM = (
    r"(?:"
    r"(?:professionally|tax)\s+reviewed|"
    r"approved(?:\s+for\s+(?:filing|submission))?|"
    r"cleared\s+for\s+submission"
    r")\b"
)

_PROFESSIONAL_REVIEW_CLAIM_PATTERNS = (
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+"
        r"(?:ist|wurde|gilt\s+als)\s+"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:fachlich|steuerlich)\s+gepr\u00fcft\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:die|diese)\s+(?:fachliche|steuerliche)\s+pr\u00fcfung\s+"
        r"(?:ist|wurde)\s+"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:abgeschlossen|durchgef\u00fchrt|best\u00e4tigt|erfolgt)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+"
        r"(?:ist|wurde|gilt\s+als)\s+"
        rf"(?:{_GERMAN_NEGATION}\s+)?"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        rf"{_GERMAN_COORDINATED_PRIOR_CLAIM}"
        rf"{_GERMAN_COORDINATION}"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:fachlich|steuerlich)\s+gepr\u00fcft\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_ENGLISH_DRAFT_OR_RESULT}\s+"
        r"(?:is|was|has\s+been)\s+"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"(?:professionally|tax)\s+reviewed\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the|this)\s+(?:professional|tax)\s+review\s+"
        r"(?:is|was|has\s+been)\s+"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"(?:complete|completed|performed|confirmed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_ENGLISH_DRAFT_OR_RESULT}\s+"
        r"(?:is|was|has\s+been)\s+"
        rf"(?:{_ENGLISH_NEGATION}\s+)?"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        rf"{_ENGLISH_COORDINATED_PRIOR_CLAIM}"
        rf"{_ENGLISH_COORDINATION}"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"(?:professionally|tax)\s+reviewed\b",
        re.IGNORECASE,
    ),
)

_FINALITY_OR_RELEASE_CLAIM_PATTERNS = (
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+"
        r"(?:ist|wurde|gilt\s+als)\s+"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:freigegeben|genehmigt)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+(?:ist|wurde)\s+"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:zur|f\u00fcr\s+die)\s+einreichung\s+freigegeben\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+"
        r"(?:ist|wurde|gilt\s+als)\s+"
        rf"(?:{_GERMAN_NEGATION}\s+)?"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        rf"{_GERMAN_COORDINATED_PRIOR_CLAIM}"
        rf"{_GERMAN_COORDINATION}"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:freigegeben|genehmigt)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_GERMAN_DRAFT_OR_RESULT}\s+(?:hat|hatte)\s+"
        r"(?!nicht\b|keine\b|noch\s+keine\b)"
        rf"{_GERMAN_INTERVENING_TOKENS}"
        r"(?:die\s+)?(?:finale|endg\u00fcltige)\s+"
        r"freigabe\s+erhalten\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_ENGLISH_DRAFT_OR_RESULT}\s+"
        r"(?:is|was|has\s+been)\s+"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"(?:approved(?:\s+for\s+(?:filing|submission))?"
        r"|cleared\s+for\s+submission)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_ENGLISH_DRAFT_OR_RESULT}\s+"
        r"(?:is|was|has\s+been)\s+"
        rf"(?:{_ENGLISH_NEGATION}\s+)?"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        rf"{_ENGLISH_COORDINATED_PRIOR_CLAIM}"
        rf"{_ENGLISH_COORDINATION}"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"(?:approved(?:\s+for\s+(?:filing|submission))?"
        r"|cleared\s+for\s+submission)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{_ENGLISH_DRAFT_OR_RESULT}\s+(?:has|had)\s+"
        rf"(?!{_ENGLISH_NEGATION})"
        rf"{_ENGLISH_INTERVENING_TOKENS}"
        r"received\s+final\s+approval\b",
        re.IGNORECASE,
    ),
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
    return any(pattern.search(entry) for pattern in patterns)


def _raise_validation_error(rule: str, field_name: str, item_index: int) -> None:
    raise StructuredDraftOutputValidationError(
        rule=rule,
        field_name=field_name,
        item_index=item_index,
    )
