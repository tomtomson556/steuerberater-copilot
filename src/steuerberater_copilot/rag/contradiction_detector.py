"""Deterministic contradiction detection over natural synthetic passages.

This detector extracts a **closed** set of attribute/value facts from natural
synthetic sentences using explicit regex templates. It then flags pairs that
conflict on the same scoped attribute key.

It is intentionally limited:

- offline and deterministic
- no embeddings, no LLM calls, no general semantic NLP claim
- only attributes covered by the published extraction templates are visible
- temporally hedged sentences are skipped for unscoped extraction
- subject-scoped claims do not collide with other subjects

Ground-truth labels for evaluation live outside this module and must not be
read by the detector. Observed results do not assert steuerliche correctness.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

from .source_document import SourceDocument

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_TEMPORAL_HEDGE_PATTERN = re.compile(
    r"\b(?:until|from|before|after|between|starting|through|during|as of|effective)\b"
)
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
_ALLOWED_POLARITIES = frozenset({"affirm", "deny"})


@dataclass(frozen=True, slots=True)
class DetectedClaimPassage:
    """One extracted attribute/value fact and its supporting sentence."""

    document_id: str
    supporting_text: str
    claim_key: str
    claim_value: str
    polarity: str = "affirm"

    def __post_init__(self) -> None:
        for field_name in (
            "document_id",
            "supporting_text",
            "claim_key",
            "claim_value",
            "polarity",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")
        if self.polarity not in _ALLOWED_POLARITIES:
            raise ValueError("polarity must be 'affirm' or 'deny'.")


@dataclass(frozen=True, slots=True)
class DetectedContradictionPair:
    """Two passages that conflict on the same scoped claim key."""

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
        if not _claims_conflict(self.first, self.second):
            raise ValueError("passages must form a contradiction under closed rules.")


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
    """Detect scoped attribute-value conflicts across natural synthetic passages."""
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
        pair = _canonical_conflict_pair(claim_key, passages)
        if pair is not None:
            contradictions.append(pair)

    return ContradictionDetectionResult(
        contradiction_present=bool(contradictions),
        contradictions=tuple(contradictions),
    )


def _claims_conflict(
    first: DetectedClaimPassage,
    second: DetectedClaimPassage,
) -> bool:
    if first.claim_key != second.claim_key:
        return False
    if first.polarity == "affirm" and second.polarity == "affirm":
        return first.claim_value != second.claim_value
    if first.claim_value == second.claim_value and first.polarity != second.polarity:
        return True
    return False


def _passage_sort_key(
    passage: DetectedClaimPassage,
) -> tuple[str, str, str, str]:
    return (
        passage.claim_value,
        passage.polarity,
        passage.document_id,
        passage.supporting_text,
    )


def _canonical_conflict_pair(
    claim_key: str,
    passages: list[DetectedClaimPassage],
) -> DetectedContradictionPair | None:
    """Return one conflict pair independent of input document order.

    Candidates are sorted canonically first. The first conflicting pair in that
    ordered scan is selected, so three or more candidates for the same
    ``claim_key`` always yield the same observed pair.
    """
    ordered_passages = sorted(passages, key=_passage_sort_key)
    for index, first in enumerate(ordered_passages):
        for second in ordered_passages[index + 1 :]:
            if _claims_conflict(first, second):
                return DetectedContradictionPair(
                    claim_key=claim_key,
                    first=first,
                    second=second,
                )
    return None


def _extract_facts(document: SourceDocument) -> tuple[DetectedClaimPassage, ...]:
    facts: list[DetectedClaimPassage] = []
    for sentence in _split_sentences(document.content):
        normalized_sentence = _normalize_text(sentence)
        match_text = normalized_sentence.rstrip(".!?")
        for extractor in _FACT_EXTRACTORS:
            match = extractor.pattern.search(match_text)
            if match is None:
                continue
            if extractor.skip_temporal_hedges and _TEMPORAL_HEDGE_PATTERN.search(
                match_text
            ):
                continue
            subject = match.groupdict().get("subject")
            claim_key = extractor.attribute
            if subject:
                claim_key = f"{extractor.attribute}::client_{subject}"
            facts.append(
                DetectedClaimPassage(
                    document_id=document.document_id,
                    supporting_text=sentence,
                    claim_key=claim_key,
                    claim_value=extractor.normalize_value(match.group("value")),
                    polarity=extractor.polarity,
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
    if token in {"optional", "freiwillig"}:
        return "optional"
    return token


@dataclass(frozen=True, slots=True)
class _FactExtractor:
    attribute: str
    pattern: re.Pattern[str]
    normalize_value: Callable[[str], str]
    polarity: str = "affirm"
    skip_temporal_hedges: bool = True


_FACT_EXTRACTORS: tuple[_FactExtractor, ...] = (
    _FactExtractor(
        attribute="retention_years",
        pattern=re.compile(
            r"^client\s+(?P<subject>[a-z0-9_-]+)\s+retention(?:\s+period)?\s+is\s+"
            r"(?P<value>\d+|ten|eleven|twelve)\s+years?$"
        ),
        normalize_value=_normalize_number_token,
        skip_temporal_hedges=False,
    ),
    _FactExtractor(
        attribute="retention_years",
        pattern=re.compile(
            r"^client\s+(?P<subject>[a-z0-9_-]+)\s+retention(?:\s+period)?\s+is\s+not\s+"
            r"(?P<value>\d+|ten|eleven|twelve)\s+years?$"
        ),
        normalize_value=_normalize_number_token,
        polarity="deny",
        skip_temporal_hedges=False,
    ),
    _FactExtractor(
        attribute="retention_years",
        pattern=re.compile(
            r"^(?:the\s+)?retention(?:\s+period)?\s+is\s+not\s+"
            r"(?P<value>\d+|ten|eleven|twelve)\s+years?$"
        ),
        normalize_value=_normalize_number_token,
        polarity="deny",
    ),
    _FactExtractor(
        attribute="retention_years",
        pattern=re.compile(
            r"^(?:the\s+)?retention(?:\s+period)?\s+is\s+"
            r"(?P<value>\d+|ten|eleven|twelve)\s+years?$"
        ),
        normalize_value=_normalize_number_token,
    ),
    _FactExtractor(
        attribute="retention_years",
        pattern=re.compile(
            r"^(?:die\s+)?aufbewahrungsfrist\s+betraegt\s+"
            r"(?P<value>\d+|zehn|elf|zwoelf)\s+jahre?$"
        ),
        normalize_value=lambda value: _normalize_number_token(
            {
                "zehn": "ten",
                "elf": "eleven",
                "zwoelf": "twelve",
            }.get(value.casefold(), value)
        ),
    ),
    _FactExtractor(
        attribute="filing_deadline",
        pattern=re.compile(
            r"^(?:the\s+)?filing\s+deadline\s+is\s+(?P<value>\d{4}-\d{2}-\d{2})$"
        ),
        normalize_value=str.strip,
    ),
    _FactExtractor(
        attribute="filing_deadline",
        pattern=re.compile(
            r"^abgabefrist\s+endet\s+am\s+(?P<value>\d{4}-\d{2}-\d{2})$"
        ),
        normalize_value=str.strip,
    ),
    # Negated archive wording normalizes to optional; list before positive form.
    _FactExtractor(
        attribute="archive_requirement",
        pattern=re.compile(
            r"^(?:the\s+)?archive\s+is\s+not\s+(?P<value>required|mandatory)$"
        ),
        normalize_value=lambda _value: "optional",
    ),
    _FactExtractor(
        attribute="archive_requirement",
        pattern=re.compile(
            r"^(?:the\s+)?archive\s+is\s+(?P<value>required|optional|mandatory)$"
        ),
        normalize_value=_normalize_binary_requirement,
    ),
    _FactExtractor(
        attribute="archive_requirement",
        pattern=re.compile(
            r"^archivierung\s+ist\s+(?P<value>pflicht|freiwillig|erforderlich|optional)$"
        ),
        normalize_value=_normalize_binary_requirement,
    ),
)
