from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import RetrievalEvaluationCase
from steuerberater_copilot.rag import SourceDocument


def test_retrieval_evaluation_case_keeps_valid_values_and_object_identities() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_002", title="Synthetic beta title"),
        _document("SYNTHETIC_SOURCE_001", title="Synthetic alpha title"),
    )
    relevant_document_ids = ("SYNTHETIC_SOURCE_002", "SYNTHETIC_SOURCE_001")

    case = RetrievalEvaluationCase(
        evaluation_id=" EVAL_RETRIEVAL_001 ",
        source_documents=documents,
        retrieval_query=" synthetic orchard query ",
        top_k=2,
        relevant_document_ids=relevant_document_ids,
    )

    assert case.evaluation_id == " EVAL_RETRIEVAL_001 "
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.source_documents[1] is documents[1]
    assert case.retrieval_query == " synthetic orchard query "
    assert case.top_k == 2
    assert case.relevant_document_ids is relevant_document_ids


def test_retrieval_evaluation_case_uses_value_equality() -> None:
    assert _valid_case() == _valid_case()


def test_retrieval_evaluation_case_is_immutable_and_uses_slots() -> None:
    case = _valid_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert RetrievalEvaluationCase.__slots__ == (
        "evaluation_id",
        "source_documents",
        "retrieval_query",
        "top_k",
        "relevant_document_ids",
    )


def test_empty_source_documents_and_empty_relevance_labels_are_allowed() -> None:
    case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_EMPTY",
        source_documents=(),
        retrieval_query="synthetic query",
        top_k=1,
        relevant_document_ids=(),
    )

    assert case.source_documents == ()
    assert case.relevant_document_ids == ()


def test_irrelevant_documents_with_empty_relevance_labels_are_allowed() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_IRRELEVANT"),
        _document("SYNTHETIC_SOURCE_OTHER"),
    )

    case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_NO_RELEVANT",
        source_documents=documents,
        retrieval_query="synthetic query",
        top_k=2,
        relevant_document_ids=(),
    )

    assert case.source_documents is documents
    assert case.relevant_document_ids == ()


def test_top_k_may_exceed_document_count() -> None:
    documents = (_document("SYNTHETIC_SOURCE_001"),)

    case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_TOP_K",
        source_documents=documents,
        retrieval_query="synthetic query",
        top_k=5,
        relevant_document_ids=("SYNTHETIC_SOURCE_001",),
    )

    assert case.top_k == 5
    assert len(case.source_documents) == 1


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_retrieval_evaluation_case_rejects_blank_evaluation_id(
    evaluation_id: str,
) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        RetrievalEvaluationCase(
            evaluation_id=evaluation_id,
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(),
        )


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL_RETRIEVAL"]))
def test_retrieval_evaluation_case_rejects_non_string_evaluation_id(
    evaluation_id: object,
) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        RetrievalEvaluationCase(
            evaluation_id=evaluation_id,  # type: ignore[arg-type]
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(),
        )


@pytest.mark.parametrize("retrieval_query", ("", " \t\n"))
def test_retrieval_evaluation_case_rejects_blank_retrieval_query(
    retrieval_query: str,
) -> None:
    with pytest.raises(ValueError, match=r"^retrieval_query must not be blank\.$"):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_QUERY",
            source_documents=(),
            retrieval_query=retrieval_query,
            top_k=1,
            relevant_document_ids=(),
        )


@pytest.mark.parametrize("retrieval_query", (1, None, ["synthetic query"]))
def test_retrieval_evaluation_case_rejects_non_string_retrieval_query(
    retrieval_query: object,
) -> None:
    with pytest.raises(TypeError, match=r"^retrieval_query must be a string\.$"):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_QUERY",
            source_documents=(),
            retrieval_query=retrieval_query,  # type: ignore[arg-type]
            top_k=1,
            relevant_document_ids=(),
        )


@pytest.mark.parametrize("top_k", (0, -1))
def test_retrieval_evaluation_case_rejects_non_positive_top_k(top_k: int) -> None:
    with pytest.raises(ValueError, match=r"^top_k must be greater than zero\.$"):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_TOP_K",
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=top_k,
            relevant_document_ids=(),
        )


@pytest.mark.parametrize("top_k", (True, False, 1.5, "2"))
def test_retrieval_evaluation_case_rejects_non_int_top_k(top_k: object) -> None:
    with pytest.raises(TypeError, match=r"^top_k must be an integer\.$"):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_TOP_K",
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=top_k,  # type: ignore[arg-type]
            relevant_document_ids=(),
        )


def test_retrieval_evaluation_case_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_DOCS",
            source_documents=[_document("SYNTHETIC_SOURCE_001")],  # type: ignore[arg-type]
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(),
        )


def test_retrieval_evaluation_case_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_DOCS",
            source_documents=("Synthetic non-document entry",),  # type: ignore[arg-type]
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(),
        )


def test_retrieval_evaluation_case_rejects_duplicate_document_ids() -> None:
    documents = (
        _document("SYNTHETIC_SOURCE_DUPLICATE", title="Synthetic first title"),
        _document("SYNTHETIC_SOURCE_DUPLICATE", title="Synthetic second title"),
    )

    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_DOCS",
            source_documents=documents,
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(),
        )


def test_retrieval_evaluation_case_rejects_non_tuple_relevant_document_ids() -> None:
    with pytest.raises(
        TypeError,
        match=r"^relevant_document_ids must be a tuple\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=["SYNTHETIC_SOURCE_001"],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("document_id", (1, None, ["SYNTHETIC_SOURCE_001"]))
def test_retrieval_evaluation_case_rejects_non_string_relevant_ids(
    document_id: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^relevant_document_ids must contain only strings\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(document_id,),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("document_id", ("", " \t\n"))
def test_retrieval_evaluation_case_rejects_blank_relevant_ids(
    document_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^relevant_document_ids entries must not be blank\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(document_id,),
        )


def test_retrieval_evaluation_case_rejects_duplicate_relevant_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^relevant_document_ids must not contain duplicate values\.$",
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=(
                "SYNTHETIC_SOURCE_001",
                "SYNTHETIC_SOURCE_001",
            ),
        )


def test_retrieval_evaluation_case_rejects_relevant_ids_outside_corpus() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^relevant_document_ids must reference document_id values "
            r"present in source_documents\.$"
        ),
    ):
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_LABELS",
            source_documents=(_document("SYNTHETIC_SOURCE_001"),),
            retrieval_query="synthetic query",
            top_k=1,
            relevant_document_ids=("SYNTHETIC_SOURCE_MISSING",),
        )


def test_evaluation_package_exports_retrieval_evaluation_case() -> None:
    assert evaluation.RetrievalEvaluationCase is RetrievalEvaluationCase
    assert "RetrievalEvaluationCase" in evaluation.__all__


def _valid_case() -> RetrievalEvaluationCase:
    documents = (
        _document("SYNTHETIC_SOURCE_001"),
        _document("SYNTHETIC_SOURCE_002"),
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_VALID",
        source_documents=documents,
        retrieval_query="synthetic query",
        top_k=2,
        relevant_document_ids=("SYNTHETIC_SOURCE_001",),
    )


def _document(
    document_id: str,
    *,
    title: str = "Synthetic source title",
    content: str = "Synthetic source content for contract testing only.",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
