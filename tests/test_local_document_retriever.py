from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.rag as rag
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument


def test_rag_package_exports_local_document_retriever() -> None:
    assert rag.LocalDocumentRetriever is LocalDocumentRetriever
    assert rag.__all__ == [
        "ContradictionDetectionResult",
        "DetectedClaimPassage",
        "DetectedContradictionPair",
        "DocumentVersionRecord",
        "LocalDocumentRetriever",
        "SourceDocument",
        "detect_synthetic_claim_contradictions",
        "find_outdated_document_ids",
    ]


def test_retriever_accepts_tuple_of_source_documents() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_002", title="Synthetic beta title"),
        _document("SYNTHETIC_SOURCE_001", title="Synthetic alpha title"),
    )

    retriever = LocalDocumentRetriever(documents=documents)

    assert retriever.documents is documents


def test_retriever_is_immutable_and_uses_slots() -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(FrozenInstanceError):
        retriever.documents = (_document("SYNTHETIC_SOURCE_001"),)

    assert not hasattr(retriever, "__dict__")
    assert LocalDocumentRetriever.__slots__ == ("documents",)


def test_retriever_rejects_non_tuple_document_collection() -> None:
    with pytest.raises(TypeError, match=r"^documents must be a tuple\.$"):
        LocalDocumentRetriever(documents=[_document("SYNTHETIC_SOURCE_001")])


def test_retriever_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^documents must contain only SourceDocument objects\.$",
    ):
        LocalDocumentRetriever(documents=("Synthetic non-document entry",))


def test_retriever_rejects_duplicate_document_ids() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_DUPLICATE", title="Synthetic first title"),
        _document("SYNTHETIC_SOURCE_DUPLICATE", title="Synthetic second title"),
    )

    with pytest.raises(
        ValueError,
        match=r"^documents must not contain duplicate document_id values\.$",
    ):
        LocalDocumentRetriever(documents=documents)


def test_empty_document_collection_returns_empty_tuple() -> None:
    result = LocalDocumentRetriever(documents=()).retrieve("synthetic query", top_k=3)

    assert result == ()
    assert isinstance(result, tuple)


def test_retrieve_matches_title_tokens() -> None:
    title_match = _document(
        "SYNTHETIC_SOURCE_TITLE",
        title="Synthetic orchard reference",
        content="Neutral example content.",
    )
    retriever = LocalDocumentRetriever(documents=(title_match,))

    assert retriever.retrieve("orchard", top_k=1) == (title_match,)


def test_retrieve_matches_content_tokens() -> None:
    content_match = _document(
        "SYNTHETIC_SOURCE_CONTENT",
        title="Neutral example title",
        content="Synthetic lantern reference.",
    )
    retriever = LocalDocumentRetriever(documents=(content_match,))

    assert retriever.retrieve("lantern", top_k=1) == (content_match,)


def test_retrieve_is_case_insensitive() -> None:
    document = _document(
        "SYNTHETIC_SOURCE_CASE",
        title="Synthetic MIXEDCASE reference",
    )
    retriever = LocalDocumentRetriever(documents=(document,))

    assert retriever.retrieve("mixedcase", top_k=1) == (document,)


def test_retrieve_normalizes_composed_and_decomposed_unicode() -> None:
    document = _document(
        "SYNTHETIC_SOURCE_UNICODE",
        title="Synthetic Caf\u00e9 reference",
    )
    retriever = LocalDocumentRetriever(documents=(document,))

    assert retriever.retrieve("Cafe\u0301", top_k=1) == (document,)


def test_retrieve_splits_tokens_at_punctuation() -> None:
    separated_tokens = _document(
        "SYNTHETIC_SOURCE_SEPARATED",
        content="Synthetic amber violet reference.",
    )
    joined_token = _document(
        "SYNTHETIC_SOURCE_JOINED",
        content="Synthetic amberviolet reference.",
    )
    retriever = LocalDocumentRetriever(documents=(joined_token, separated_tokens))

    assert retriever.retrieve("amber.violet", top_k=2) == (separated_tokens,)


def test_retrieve_ranks_by_distinct_matching_query_token_count() -> None:
    two_matches = _document(
        "SYNTHETIC_SOURCE_TWO",
        title="Synthetic copper reference",
        content="Synthetic silver example.",
    )
    one_match = _document(
        "SYNTHETIC_SOURCE_ONE",
        title="Synthetic copper reference",
        content="Neutral example content.",
    )
    retriever = LocalDocumentRetriever(documents=(one_match, two_matches))

    assert retriever.retrieve("copper silver quartz", top_k=2) == (
        two_matches,
        one_match,
    )


def test_repeated_query_tokens_do_not_increase_score() -> None:
    alphabetically_first = _document(
        "SYNTHETIC_SOURCE_ALPHA",
        title="Synthetic alpha reference",
    )
    repeated_match = _document(
        "SYNTHETIC_SOURCE_ZETA",
        title="Synthetic beta reference",
    )
    retriever = LocalDocumentRetriever(
        documents=(repeated_match, alphabetically_first)
    )

    assert retriever.retrieve("beta beta beta alpha", top_k=2) == (
        alphabetically_first,
        repeated_match,
    )


def test_ties_use_document_id_independently_of_input_order() -> None:
    first_by_id = _document(
        "SYNTHETIC_SOURCE_001",
        title="Synthetic shared reference",
    )
    second_by_id = _document(
        "SYNTHETIC_SOURCE_002",
        title="Synthetic shared reference",
    )
    forward_retriever = LocalDocumentRetriever(
        documents=(first_by_id, second_by_id)
    )
    reverse_retriever = LocalDocumentRetriever(
        documents=(second_by_id, first_by_id)
    )

    expected = (first_by_id, second_by_id)
    assert forward_retriever.retrieve("shared", top_k=2) == expected
    assert reverse_retriever.retrieve("shared", top_k=2) == expected


def test_top_k_limits_result_count() -> None:
    first = _document("SYNTHETIC_SOURCE_001", title="Synthetic shared reference")
    second = _document("SYNTHETIC_SOURCE_002", title="Synthetic shared reference")
    retriever = LocalDocumentRetriever(documents=(second, first))

    assert retriever.retrieve("shared", top_k=1) == (first,)


def test_documents_without_token_overlap_are_excluded() -> None:
    match = _document(
        "SYNTHETIC_SOURCE_MATCH",
        title="Synthetic comet reference",
    )
    no_match = _document(
        "SYNTHETIC_SOURCE_NO_MATCH",
        title="Synthetic meadow reference",
    )
    retriever = LocalDocumentRetriever(documents=(no_match, match))

    assert retriever.retrieve("comet", top_k=2) == (match,)


def test_retrieve_returns_empty_tuple_when_no_document_matches() -> None:
    document = _document(
        "SYNTHETIC_SOURCE_NO_MATCH",
        title="Synthetic meadow reference",
    )
    retriever = LocalDocumentRetriever(documents=(document,))

    result = retriever.retrieve("comet", top_k=1)

    assert result == ()
    assert isinstance(result, tuple)


def test_retrieve_keeps_source_document_values_unchanged() -> None:
    document = SourceDocument(
        document_id=" SYNTHETIC_SOURCE_UNCHANGED ",
        title=" Synthetic Caf\u00e9 Title ",
        content="\nSynthetic Content Remains Unchanged.\n",
    )
    original_values = (document.document_id, document.title, document.content)
    retriever = LocalDocumentRetriever(documents=(document,))

    retriever.retrieve("cafe\u0301 content", top_k=1)

    assert (document.document_id, document.title, document.content) == original_values


@pytest.mark.parametrize("query", (None, 7, ("synthetic", "query")))
def test_retrieve_rejects_non_string_query(query: object) -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(TypeError, match=r"^query must be a string\.$"):
        retriever.retrieve(query, top_k=1)


def test_retrieve_rejects_empty_query() -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(ValueError, match=r"^query must not be blank\.$"):
        retriever.retrieve("", top_k=1)


def test_retrieve_rejects_whitespace_only_query() -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(ValueError, match=r"^query must not be blank\.$"):
        retriever.retrieve(" \t\n", top_k=1)


@pytest.mark.parametrize("top_k", (None, 1.0, "1"))
def test_retrieve_rejects_non_integer_top_k(top_k: object) -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(TypeError, match=r"^top_k must be an integer\.$"):
        retriever.retrieve("synthetic query", top_k=top_k)


@pytest.mark.parametrize("top_k", (False, True))
def test_retrieve_rejects_bool_top_k(top_k: bool) -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(TypeError, match=r"^top_k must be an integer\.$"):
        retriever.retrieve("synthetic query", top_k=top_k)


def test_retrieve_rejects_zero_top_k() -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(ValueError, match=r"^top_k must be greater than zero\.$"):
        retriever.retrieve("synthetic query", top_k=0)


def test_retrieve_rejects_negative_top_k() -> None:
    retriever = LocalDocumentRetriever(documents=())

    with pytest.raises(ValueError, match=r"^top_k must be greater than zero\.$"):
        retriever.retrieve("synthetic query", top_k=-1)


def test_retrieve_returns_tuple_of_original_source_document_objects() -> None:
    first = _document("SYNTHETIC_SOURCE_001", title="Synthetic shared reference")
    second = _document("SYNTHETIC_SOURCE_002", content="Synthetic shared reference")
    retriever = LocalDocumentRetriever(documents=(second, first))

    result = retriever.retrieve("shared", top_k=2)

    assert isinstance(result, tuple)
    assert result[0] is first
    assert result[1] is second


def _document(
    document_id: str,
    *,
    title: str = "Synthetic neutral title",
    content: str = "Synthetic neutral content.",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
