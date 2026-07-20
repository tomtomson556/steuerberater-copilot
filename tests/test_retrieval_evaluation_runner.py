from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.retrieval_runner as retrieval_runner_module
from steuerberater_copilot.evaluation import (
    RetrievalEvaluationCase,
    RetrievalEvaluationRunResult,
    run_offline_retrieval_evaluation_case,
)
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument


def test_retrieval_evaluation_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _retrieval_case()
    retrieved_documents = (evaluation_case.source_documents[0],)

    result = RetrievalEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )

    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents is retrieved_documents
    assert result.retrieved_documents[0] is evaluation_case.source_documents[0]
    assert result == RetrievalEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )


def test_retrieval_evaluation_run_result_is_immutable_and_uses_slots() -> None:
    result = RetrievalEvaluationRunResult(
        evaluation_case=_retrieval_case(),
        retrieved_documents=(),
    )

    with pytest.raises(FrozenInstanceError):
        result.retrieved_documents = ()

    assert not hasattr(result, "__dict__")
    assert RetrievalEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "retrieved_documents",
    )


def test_retrieval_evaluation_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RetrievalEvaluationCase\.$",
    ):
        RetrievalEvaluationRunResult(
            evaluation_case="not-a-case",  # type: ignore[arg-type]
            retrieved_documents=(),
        )


def test_retrieval_evaluation_run_result_rejects_non_tuple_documents() -> None:
    with pytest.raises(TypeError, match=r"^retrieved_documents must be a tuple\.$"):
        RetrievalEvaluationRunResult(
            evaluation_case=_retrieval_case(),
            retrieved_documents=[_document("SYNTHETIC_SOURCE_001")],  # type: ignore[arg-type]
        )


def test_retrieval_evaluation_run_result_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^retrieved_documents must contain only SourceDocument objects\.$",
    ):
        RetrievalEvaluationRunResult(
            evaluation_case=_retrieval_case(),
            retrieved_documents=("not-a-document",),  # type: ignore[arg-type]
        )


def test_runner_forwards_case_values_and_preserves_document_identities() -> None:
    match = _document(
        "SYNTHETIC_SOURCE_MATCH",
        title="Synthetic orchard reference",
        content="Neutral example content.",
    )
    other = _document(
        "SYNTHETIC_SOURCE_OTHER",
        title="Synthetic meadow reference",
        content="Neutral example content.",
    )
    evaluation_case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_RUNNER_FORWARD",
        source_documents=(other, match),
        retrieval_query="orchard",
        top_k=1,
        relevant_document_ids=("SYNTHETIC_SOURCE_MATCH",),
    )

    result = run_offline_retrieval_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents == (match,)
    assert result.retrieved_documents[0] is match
    assert not hasattr(result, "passed")
    assert not hasattr(result, "recall_at_k")


def test_runner_returns_empty_hits_without_assessment() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_NO_MATCH",
            title="Synthetic meadow reference",
        ),
    )
    evaluation_case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_RUNNER_EMPTY",
        source_documents=documents,
        retrieval_query="orchard",
        top_k=3,
        relevant_document_ids=(),
    )

    result = run_offline_retrieval_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents == ()


def test_runner_results_are_deterministic() -> None:
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
    evaluation_case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_RUNNER_DETERMINISTIC",
        source_documents=(one_match, two_matches),
        retrieval_query="copper silver quartz",
        top_k=2,
        relevant_document_ids=("SYNTHETIC_SOURCE_TWO", "SYNTHETIC_SOURCE_ONE"),
    )

    first = run_offline_retrieval_evaluation_case(evaluation_case)
    second = run_offline_retrieval_evaluation_case(evaluation_case)

    assert first == second
    assert first.retrieved_documents == (two_matches, one_match)
    assert second.retrieved_documents == (two_matches, one_match)


def test_runner_propagates_unexpected_retriever_errors(monkeypatch) -> None:
    unexpected_error = RuntimeError("synthetic unexpected retriever failure")

    def fail_retrieve(self, query: str, *, top_k: int):
        raise unexpected_error

    monkeypatch.setattr(LocalDocumentRetriever, "retrieve", fail_retrieve)

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_retrieval_evaluation_case(_retrieval_case())

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_retrieval_runner_contract() -> None:
    assert evaluation.RetrievalEvaluationCase is RetrievalEvaluationCase
    assert evaluation.RetrievalEvaluationRunResult is RetrievalEvaluationRunResult
    assert (
        evaluation.run_offline_retrieval_evaluation_case
        is run_offline_retrieval_evaluation_case
    )
    assert evaluation.RetrievalEvaluationRunResult is (
        retrieval_runner_module.RetrievalEvaluationRunResult
    )
    assert "RetrievalEvaluationRunResult" in evaluation.__all__
    assert "run_offline_retrieval_evaluation_case" in evaluation.__all__


def _retrieval_case() -> RetrievalEvaluationCase:
    match = _document(
        "SYNTHETIC_SOURCE_MATCH",
        title="Synthetic orchard reference",
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_RUNNER",
        source_documents=(match,),
        retrieval_query="orchard",
        top_k=1,
        relevant_document_ids=("SYNTHETIC_SOURCE_MATCH",),
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
