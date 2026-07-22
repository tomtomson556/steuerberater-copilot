"""Deterministic contradiction detection over natural synthetic passages.

This detector extracts a **closed** set of attribute/value facts from natural
synthetic sentences using explicit regex templates. It then flags pairs that
assign different values to the same attribute across source documents.

It is intentionally limited:

- offline and deterministic
- no embeddings, no LLM calls, no general semantic NLP claim
- only attributes covered by the published extraction templates are visible

Ground-truth labels for evaluation live outside this module and must not be
read by the detector.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

from .source_document import SourceDocument

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
}


@dataclass(frozen=True, slots=True)
class DetectedClaimPassage:
    """One extracted attribute/value fact and its supporting sentence."""

    document_id: str
    supporting_text: str
    claim_key: str
    claim_value: str

    def __post_init__(self) -> None:
        for field_name in (
            "document_id",
            "supporting_text",
            "claim_key",
            "claim_value",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")


@dataclass(frozen=True, slots=True)
class DetectedContradictionPair:
    """Two passages with the same attribute key but different values."""

    claim_key: str
    first: DetectedClaimPassage
    second: DetectedClaimPassage

    def __post_init__(self) -> None:
        if not isinstance(self.claim_key, str):
            raise TypeError("claim_key must be a string.")
        if not self.claim_key or self.claim_key.isspace():
            raise ValueError("claim_key must not be blank.")
        if not isinstance(self.first, DetectedClaimPassage):
            raise TypeError("first must be a DetectedClaimPassage.")
        if not isinstance(self.second, DetectedClaimPassage):
            raise TypeError("second must be a DetectedClaimPassage.")
        if self.first.claim_key != self.claim_key or self.second.claim_key != self.claim_key:
            raise ValueError("both passages must use the contradiction claim_key.")
        if self.first.claim_value == self.second.claim_value:
            raise ValueError("contradicting passages must have different claim values.")


@dataclass(frozen=True, slots=True)
class ContradictionDetectionResult:
    """Observed contradictions from the closed-template fact extractor.

    ``contradiction_present`` is an observation only. It is not ground truth and
    does not assert general semantic understanding or steuerliche correctness.
    """

    contradiction_present: bool
    contradictions: tuple[DetectedContradictionPair, ...]

    def __post_init__(self) -> None:
        if type(self.contradiction_present) is not bool:
            raise TypeError("contradiction_present must be a boolean.")
        if not isinstance(self.contradictions, tuple):
            raise TypeError("contradictions must be a tuple.")
        for contradiction in self.contradictions:
            if not isinstance(contradiction, DetectedContradictionPair):
                raise TypeError(
                    "contradictions must contain only DetectedContradictionPair objects."
                )
        if self.contradiction_present != bool(self.contradictions):
            raise ValueError(
                "contradiction_present must be True exactly when contradictions "
                "is non-empty."
            )


def detect_passage_contradictions(
    documents: tuple[SourceDocument, ...],
) -> ContradictionDetectionResult:
    """Detect attribute-value conflicts across natural synthetic passages."""
    if not isinstance(documents, tuple):
        raise TypeError("documents must be a tuple.")

    passages_by_key: dict[str, list[DetectedClaimPassage]] = {}
    seen_document_ids: set[str] = set()
    for document in documents:
        if not isinstance(document, SourceDocument):
            raise TypeError("documents must contain only SourceDocument objects.")
        if document.document_id in seen_document_ids:
            raise ValueError("documents must not contain duplicate document_id values.")
        seen_document_ids.add(document.document_id)
        for passage in _extract_facts(document):
            passages_by_key.setdefault(passage.claim_key, []).append(passage)

    contradictions: list[DetectedContradictionPair] = []
    for claim_key in sorted(passages_by_key):
        passages = passages_by_key[claim_key]
        first_by_value: dict[str, DetectedClaimPassage] = {}
        for passage in passages:
            if passage.claim_value not in first_by_value:
                first_by_value[passage.claim_value] = passage
        distinct_values = sorted(first_by_value)
        if len(distinct_values) < 2:
            continue
        first = first_by_value[distinct_values[0]]
        second = first_by_value[distinct_values[1]]
        contradictions.append(
            DetectedContradictionPair(
                claim_key=claim_key,
                first=first,
                second=second,
            )
        )

    return ContradictionDetectionResult(
        contradiction_present=bool(contradictions),
        contradictions=tuple(contradictions),
    )


# Backward-compatible alias used by earlier experiment commits.
detect_synthetic_claim_contradictions = detect_passage_contradictions


def _extract_facts(document: SourceDocument) -> tuple[DetectedClaimPassage, ...]:
    facts: list[DetectedClaimPassage] = []
    for sentence in _split_sentences(document.content):
        normalized_sentence = _normalize_text(sentence)
        for claim_key, pattern, normalize_value in _FACT_EXTRACTORS:
            match = pattern.search(normalized_sentence)
            if match is None:
                continue
            raw_value = match.group("value")
            facts.append(
                DetectedClaimPassage(
                    document_id=document.document_id,
                    supporting_text=sentence,
                    claim_key=claim_key,
                    claim_value=normalize_value(raw_value),
                )
            )
    return tuple(facts)


def _split_sentences(text: str) -> tuple[str, ...]:
    chunks = [
        chunk.strip()
        for chunk in _SENTENCE_SPLIT_PATTERN.split(text.strip())
        if chunk.strip()
    ]
    return tuple(chunks)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = (
        normalized.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    return " ".join(normalized.casefold().split())


def _normalize_number_token(value: str) -> str:
    token = value.casefold().strip()
    return _NUMBER_WORDS.get(token, token)


def _normalize_binary_requirement(value: str) -> str:
    token = value.casefold().strip()
    if token in {"required", "pflicht", "mandatory", "erforderlich"}:
        return "required"
    if token in {"optional", "freiwillig", "not required"}:
        return "optional"
    return token


_FACT_EXTRACTORS: tuple[
    tuple[str, re.Pattern[str], Callable[[str], str]],
    ...,
] = (
    (
        "retention_years",
        re.compile(
            r"(?:the\s+)?retention(?:\s+period)?\s+is\s+(?P<value>\d+|ten|eleven|twelve)\s+years?"
        ),
        _normalize_number_token,
    ),
    (
        "retention_years",
        re.compile(
            r"aufbewahrungsfrist\s+betraegt\s+(?P<value>\d+|zehn|elf|zwoelf)\s+jahre?"
        ),
        lambda value: _normalize_number_token(
            {
                "zehn": "ten",
                "elf": "eleven",
                "zwoelf": "twelve",
            }.get(value.casefold(), value)
        ),
    ),
    (
        "filing_deadline",
        re.compile(
            r"(?:the\s+)?filing\s+deadline\s+is\s+(?P<value>\d{4}-\d{2}-\d{2})"
        ),
        str.strip,
    ),
    (
        "filing_deadline",
        re.compile(
            r"abgabefrist\s+endet\s+am\s+(?P<value>\d{4}-\d{2}-\d{2})"
        ),
        str.strip,
    ),
    (
        "archive_requirement",
        re.compile(
            r"(?:the\s+)?archive\s+is\s+(?P<value>required|optional|mandatory|not required)"
        ),
        _normalize_binary_requirement,
    ),
    (
        "archive_requirement",
        re.compile(
            r"archivierung\s+ist\s+(?P<value>pflicht|freiwillig|erforderlich|optional)"
        ),
        _normalize_binary_requirement,
    ),
)
