from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import RAGAbstentionEvaluationCase
from steuerberater_copilot.offline_mvp import IntakeCase, SyntheticDocument
from steuerberater_copilot.rag import SourceDocument


def test_rag_abstention_case_keeps_valid_values_and_object_identities() -> None:
    intake = _synthetic_intake()
    documents = (
        _document("SYNTHETIC_SOURCE_002"),
        _document("SYNTHETIC_SOURCE_001"),
    )

    case = RAGAbstentionEvaluationCase(
        evaluation_id=" EVAL_RAG_ABSTENTION_001 ",
        intake=intake,
        source_documents=documents,
        retrieval_query=" synthetic orchard query ",
        top_k=2,
        expected_abstained_for_missing_evidence=True,
    )

    assert case.evaluation_id == " EVAL_RAG_ABSTENTION_001 "
    assert case.intake is intake
    assert case.source_documents is documents
    assert case.source_documents[0] is documents[0]
    assert case.retrieval_query == " synthetic orchard query "
    assert case.top_k == 2
    assert case.expected_abstained_for_missing_evidence is True


def test_rag_abstention_case_is_immutable_and_uses_slots() -> None:
    case = _valid_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")
    assert RAGAbstentionEvaluationCase.__slots__ == (
        "evaluation_id",
        "intake",
        "source_documents",
        "retrieval_query",
        "top_k",
        "expected_abstained_for_missing_evidence",
    )


def test_rag_abstention_case_uses_value_equality() -> None:
    assert _valid_case() == _valid_case()


def test_expected_abstention_true_and_false_are_allowed() -> None:
    assert (
        _valid_case(expected_abstained_for_missing_evidence=True)
        .expected_abstained_for_missing_evidence
        is True
    )
    assert (
        _valid_case(expected_abstained_for_missing_evidence=False)
        .expected_abstained_for_missing_evidence
        is False
    )


def test_empty_source_documents_are_allowed_for_missing_evidence_cases() -> None:
    case = RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_EMPTY_CORPUS",
        intake=_synthetic_intake(),
        source_documents=(),
        retrieval_query="synthetic orchard query",
        top_k=1,
        expected_abstained_for_missing_evidence=True,
    )

    assert case.source_documents == ()
    assert case.expected_abstained_for_missing_evidence is True


def test_case_contract_contains_no_observed_workflow_result() -> None:
    case = _valid_case()

    assert not hasattr(case, "observed_abstained_for_missing_evidence")
    assert not hasattr(case, "workflow_output")
    assert not hasattr(case, "retrieved_documents")
    assert not hasattr(case, "grounded_draft")
    assert not hasattr(case, "model_response")
    assert not hasattr(case, "passed")


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_rejects_blank_evaluation_id(evaluation_id: str) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id=evaluation_id,
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("evaluation_id", (1, None, ["EVAL"]))
def test_rejects_non_string_evaluation_id(evaluation_id: object) -> None:
    with pytest.raises(TypeError, match=r"^evaluation_id must be a string\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id=evaluation_id,  # type: ignore[arg-type]
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


def test_rejects_non_intake_case() -> None:
    with pytest.raises(TypeError, match=r"^intake must be an IntakeCase\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_INTAKE",
            intake="not-an-intake",  # type: ignore[arg-type]
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("retrieval_query", ("", " \t\n"))
def test_rejects_blank_retrieval_query(retrieval_query: str) -> None:
    with pytest.raises(ValueError, match=r"^retrieval_query must not be blank\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_QUERY",
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query=retrieval_query,
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("top_k", (0, -1))
def test_rejects_non_positive_top_k(top_k: int) -> None:
    with pytest.raises(ValueError, match=r"^top_k must be greater than zero\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_TOP_K",
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=top_k,
            expected_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("top_k", (True, False, 1.5, "1"))
def test_rejects_non_int_top_k(top_k: object) -> None:
    with pytest.raises(TypeError, match=r"^top_k must be an integer\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_TOP_K",
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=top_k,  # type: ignore[arg-type]
            expected_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("value", (0, 1, "true", None))
def test_rejects_non_bool_expected_abstention(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=r"^expected_abstained_for_missing_evidence must be a boolean\.$",
    ):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_FLAG",
            intake=_synthetic_intake(),
            source_documents=(),
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=value,  # type: ignore[arg-type]
        )


def test_rejects_non_tuple_source_documents() -> None:
    with pytest.raises(TypeError, match=r"^source_documents must be a tuple\.$"):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_DOCS",
            intake=_synthetic_intake(),
            source_documents=[_document("SYNTHETIC_SOURCE_001")],  # type: ignore[arg-type]
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


def test_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^source_documents must contain only SourceDocument objects\.$",
    ):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_DOCS",
            intake=_synthetic_intake(),
            source_documents=("not-a-document",),  # type: ignore[arg-type]
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


def test_rejects_duplicate_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^source_documents must not contain duplicate document_id values\.$",
    ):
        RAGAbstentionEvaluationCase(
            evaluation_id="EVAL_RAG_ABSTENTION_DOCS",
            intake=_synthetic_intake(),
            source_documents=(
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
            ),
            retrieval_query="synthetic query",
            top_k=1,
            expected_abstained_for_missing_evidence=True,
        )


def test_evaluation_package_exports_rag_abstention_case_contract() -> None:
    assert evaluation.RAGAbstentionEvaluationCase is RAGAbstentionEvaluationCase
    assert "RAGAbstentionEvaluationCase" in evaluation.__all__


def _valid_case(
    *,
    expected_abstained_for_missing_evidence: bool = True,
) -> RAGAbstentionEvaluationCase:
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_VALID",
        intake=_synthetic_intake(),
        source_documents=(_document("SYNTHETIC_SOURCE_001"),),
        retrieval_query="synthetic orchard query",
        top_k=1,
        expected_abstained_for_missing_evidence=(
            expected_abstained_for_missing_evidence
        ),
    )


def _synthetic_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_RAG_ABSTENTION_TEST",
        client_ref="CLIENT_RAG_ABSTENTION_TEST",
        scenario="Synthetic RAG abstention contract test.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_RAG_ABSTENTION_TEST",
                label="Synthetic abstention document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic abstention test note.",),
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
