from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import RAGFreshnessEvaluationCase
from steuerberater_copilot.rag import SourceDocument


def test_freshness_case_keeps_valid_values_and_object_identities() -> None:
    documents = _documents()
    retrieval_query = " synthetic orchard query "
    expected_current_document_id = "SYNTHETIC_FRESHNESS_CURRENT"
    stale_document_ids = (
        "SYNTHETIC_FRESHNESS_STALE_A",
        "SYNTHETIC_FRESHNESS_STALE_B",
    )

    case = RAGFreshnessEvaluationCase(
        evaluation_id=" EVAL_RAG_FRESHNESS_001 ",
        source_documents=documents,
        retrieval_query=retrieval_query,
        top_k=2,
        expected_current_document_id=expected_current_document_id,
        stale_document_ids=stale_document_ids,
    )

    assert case.evaluation_id == " EVAL_RAG_FRESHNESS_001 "
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.retrieval_query is retrieval_query
    assert case.top_k == 2
    assert case.expected_current_document_id is expected_current_document_id
    assert case.stale_document_ids is stale_document_ids


def test_freshness_case_uses_value_equality() -> None:
    assert _valid_case() == _valid_case()


def test_freshness_case_is_immutable_and_uses_slots() -> None:
    case = _valid_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert RAGFreshnessEvaluationCase.__slots__ == (
        "evaluation_id",
        "source_documents",
        "retrieval_query",
        "top_k",
        "expected_current_document_id",
        "stale_document_ids",
    )


def test_top_k_may_exceed_document_count() -> None:
    case = RAGFreshnessEvaluationCase(
        **_arguments(top_k=10),
    )

    assert case.top_k == 10
    assert len(case.source_documents) == 3


def test_case_contains_ground_truth_but_no_observed_retrieval_result() -> None:
    case = _valid_case()

    assert case.expected_current_document_id == "SYNTHETIC_FRESHNESS_CURRENT"
    assert case.stale_document_ids == (
        "SYNTHETIC_FRESHNESS_STALE_A",
        "SYNTHETIC_FRESHNESS_STALE_B",
    )
    assert not hasattr(case, "retrieved_documents")
    assert not hasattr(case, "observed_current_document_id")
    assert not hasattr(case, "current_document_matches")
    assert not hasattr(case, "passed")


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_rejects_blank_evaluation_id(evaluation_id: str) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        RAGFreshnessEvaluationCase(**_arguments(evaluation_id=evaluation_id))


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL_RAG_FRESHNESS"]))
def test_rejects_non_string_evaluation_id(evaluation_id: object) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        RAGFreshnessEvaluationCase(**_arguments(evaluation_id=evaluation_id))


@pytest.mark.parametrize("retrieval_query", ("", " \t\n"))
def test_rejects_blank_retrieval_query(retrieval_query: str) -> None:
    with pytest.raises(ValueError, match=r"^retrieval_query must not be blank\.$"):
        RAGFreshnessEvaluationCase(**_arguments(retrieval_query=retrieval_query))


@pytest.mark.parametrize("retrieval_query", (1, None, ["synthetic query"]))
def test_rejects_non_string_retrieval_query(retrieval_query: object) -> None:
    with pytest.raises(TypeError, match=r"^retrieval_query must be a string\.$"):
        RAGFreshnessEvaluationCase(**_arguments(retrieval_query=retrieval_query))


@pytest.mark.parametrize("top_k", (0, -1))
def test_rejects_non_positive_top_k(top_k: int) -> None:
    with pytest.raises(ValueError, match=r"^top_k must be greater than zero\.$"):
        RAGFreshnessEvaluationCase(**_arguments(top_k=top_k))


@pytest.mark.parametrize("top_k", (True, False, 1.5, "2"))
def test_rejects_non_integer_top_k(top_k: object) -> None:
    with pytest.raises(TypeError, match=r"^top_k must be an integer\.$"):
        RAGFreshnessEvaluationCase(**_arguments(top_k=top_k))


def test_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        RAGFreshnessEvaluationCase(
            **_arguments(source_documents=list(_documents()))
        )


def test_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(source_documents=("not-a-document",))
        )


def test_rejects_duplicate_source_document_ids() -> None:
    duplicate_documents = (
        _document("SYNTHETIC_FRESHNESS_CURRENT"),
        _document("SYNTHETIC_FRESHNESS_CURRENT"),
        _document("SYNTHETIC_FRESHNESS_STALE_A"),
    )

    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(source_documents=duplicate_documents)
        )


@pytest.mark.parametrize("document_id", (1, None, ["SYNTHETIC_FRESHNESS_CURRENT"]))
def test_rejects_non_string_expected_current_document_id(
    document_id: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^expected_current_document_id must be a string\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(expected_current_document_id=document_id)
        )


@pytest.mark.parametrize("document_id", ("", " \t\n"))
def test_rejects_blank_expected_current_document_id(document_id: str) -> None:
    with pytest.raises(
        ValueError,
        match=r"^expected_current_document_id must not be blank\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(expected_current_document_id=document_id)
        )


def test_rejects_current_document_id_outside_source_documents() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^expected_current_document_id must reference a document_id value "
            r"present in source_documents\.$"
        ),
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(
                expected_current_document_id="SYNTHETIC_FRESHNESS_MISSING"
            )
        )


def test_rejects_non_tuple_stale_document_ids() -> None:
    with pytest.raises(TypeError, match=r"^stale_document_ids must be a tuple\.$"):
        RAGFreshnessEvaluationCase(
            **_arguments(
                stale_document_ids=[
                    "SYNTHETIC_FRESHNESS_STALE_A",
                    "SYNTHETIC_FRESHNESS_STALE_B",
                ]
            )
        )


def test_rejects_empty_stale_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^stale_document_ids must not be empty\.$",
    ):
        RAGFreshnessEvaluationCase(**_arguments(stale_document_ids=()))


@pytest.mark.parametrize("document_id", (1, None, ["SYNTHETIC_FRESHNESS_STALE_A"]))
def test_rejects_non_string_stale_document_id(document_id: object) -> None:
    with pytest.raises(
        TypeError,
        match=r"^stale_document_ids must contain only strings\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(stale_document_ids=(document_id,))
        )


@pytest.mark.parametrize("document_id", ("", " \t\n"))
def test_rejects_blank_stale_document_id(document_id: str) -> None:
    with pytest.raises(
        ValueError,
        match=r"^stale_document_ids entries must not be blank\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(stale_document_ids=(document_id,))
        )


def test_rejects_duplicate_stale_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^stale_document_ids must not contain duplicate values\.$",
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(
                stale_document_ids=(
                    "SYNTHETIC_FRESHNESS_STALE_A",
                    "SYNTHETIC_FRESHNESS_STALE_A",
                )
            )
        )


def test_rejects_stale_document_id_outside_source_documents() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^stale_document_ids must reference document_id values "
            r"present in source_documents\.$"
        ),
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(
                stale_document_ids=("SYNTHETIC_FRESHNESS_MISSING",)
            )
        )


def test_rejects_current_document_id_among_stale_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^expected_current_document_id must not appear in "
            r"stale_document_ids\.$"
        ),
    ):
        RAGFreshnessEvaluationCase(
            **_arguments(
                stale_document_ids=(
                    "SYNTHETIC_FRESHNESS_CURRENT",
                    "SYNTHETIC_FRESHNESS_STALE_A",
                )
            )
        )


def test_evaluation_package_exports_freshness_case_contract() -> None:
    assert evaluation.RAGFreshnessEvaluationCase is RAGFreshnessEvaluationCase
    assert "RAGFreshnessEvaluationCase" in evaluation.__all__


def _valid_case() -> RAGFreshnessEvaluationCase:
    return RAGFreshnessEvaluationCase(**_arguments())


def _arguments(**overrides: object) -> dict[str, object]:
    arguments: dict[str, object] = {
        "evaluation_id": "EVAL_RAG_FRESHNESS_VALID",
        "source_documents": _documents(),
        "retrieval_query": "synthetic orchard query",
        "top_k": 2,
        "expected_current_document_id": "SYNTHETIC_FRESHNESS_CURRENT",
        "stale_document_ids": (
            "SYNTHETIC_FRESHNESS_STALE_A",
            "SYNTHETIC_FRESHNESS_STALE_B",
        ),
    }
    arguments.update(overrides)
    return arguments


def _documents() -> tuple[SourceDocument, ...]:
    return (
        _document("SYNTHETIC_FRESHNESS_CURRENT"),
        _document("SYNTHETIC_FRESHNESS_STALE_A"),
        _document("SYNTHETIC_FRESHNESS_STALE_B"),
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
