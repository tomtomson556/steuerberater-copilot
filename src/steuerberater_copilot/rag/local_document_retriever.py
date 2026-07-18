"""Deterministic local retrieval over source documents."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .source_document import SourceDocument

_WORD_TOKEN_PATTERN = re.compile(r"\w+")


@dataclass(frozen=True, slots=True)
class LocalDocumentRetriever:
    """Retrieve source documents by deterministic token overlap."""

    documents: tuple[SourceDocument, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.documents, tuple):
            raise TypeError("documents must be a tuple.")

        seen_document_ids: set[str] = set()
        for document in self.documents:
            if not isinstance(document, SourceDocument):
                raise TypeError("documents must contain only SourceDocument objects.")
            if document.document_id in seen_document_ids:
                raise ValueError("documents must not contain duplicate document_id values.")
            seen_document_ids.add(document.document_id)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int,
    ) -> tuple[SourceDocument, ...]:
        """Return up to ``top_k`` documents ranked by distinct token overlap."""
        if not isinstance(query, str):
            raise TypeError("query must be a string.")
        if not query or query.isspace():
            raise ValueError("query must not be blank.")
        if type(top_k) is not int:
            raise TypeError("top_k must be an integer.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_tokens = _tokenize(query)
        ranked_documents: list[tuple[int, str, SourceDocument]] = []
        for document in self.documents:
            document_tokens = _tokenize(document.title) | _tokenize(document.content)
            score = len(query_tokens & document_tokens)
            if score:
                ranked_documents.append((-score, document.document_id, document))

        ranked_documents.sort(key=lambda ranked: (ranked[0], ranked[1]))
        return tuple(ranked[2] for ranked in ranked_documents[:top_k])


def _tokenize(text: str) -> frozenset[str]:
    normalized_text = unicodedata.normalize("NFKC", text).casefold()
    return frozenset(_WORD_TOKEN_PATTERN.findall(normalized_text))
