from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_freshness_runner as runner_module
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    RAGFreshnessEvaluationRunResult,
    run_offline_rag_freshness_evaluation_case,
)
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument


def test_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _freshness_case()
    retrieved_documents = (evaluation_case.source_documents[0],)

    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )

    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents is retrieved_documents
    assert result.retrieved_documents[0] is evaluation_case.source_documents[0]
    assert result == RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )


def test_run_result_is_immutable_and_uses_slots() -> None:
    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=_freshness_case(),
        retrieved_documents=(),
    )

    with pytest.raises(FrozenInstanceError):
        result.retrieved_documents = ()

    assert not hasattr(result, "__dict__")
    assert RAGFreshnessEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "retrieved_documents",
    )


def test_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGFreshnessEvaluationCase\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case="not-a-case",  # type: ignore[arg-type]
            retrieved_documents=(),
        )


def test_run_result_rejects_non_tuple_documents() -> None:
    with pytest.raises(TypeError, match=r"^retrieved_documents must be a tuple\.$"):
        RAGFreshnessEvaluationRunResult(
            evaluation_case=_freshness_case(),
            retrieved_documents=[_documents()[0]],  # type: ignore[arg-type]
        )


def test_run_result_rejects_non_source_document_entry() -> None:
    with pytest.raises(
        TypeError,
        match=r"^retrieved_documents must contain only SourceDocument objects\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case=_freshness_case(),
            retrieved_documents=("not-a-document",),  # type: ignore[arg-type]
        )


def test_runner_retrieves_deterministically_and_preserves_document_identities() -> None:
    documents = _documents()
    evaluation_case = _freshness_case(source_documents=documents)

    first = run_offline_rag_freshness_evaluation_case(evaluation_case)
    second = run_offline_rag_freshness_evaluation_case(evaluation_case)

    assert first == second
    assert first.evaluation_case is evaluation_case
    assert first.retrieved_documents == (documents[0], documents[1])
    assert first.retrieved_documents[0] is documents[0]
    assert first.retrieved_documents[1] is documents[1]
    assert second.retrieved_documents[0] is documents[0]
    assert not hasattr(first, "passed")
    assert not hasattr(first, "current_document_matches")
    assert not hasattr(first, "stale_documents_retrieved")
    assert not hasattr(first, "expected_current_document_id")
    assert not hasattr(first, "stale_document_ids")


def test_runner_returns_empty_hits_without_assessment() -> None:
    evaluation_case = _freshness_case(
        retrieval_query="quartz",
        top_k=3,
    )

    result = run_offline_rag_freshness_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents == ()


def test_runner_uses_only_source_documents_query_and_top_k(monkeypatch) -> None:
    documents = _documents()
    evaluation_case = _freshness_case(
        source_documents=documents,
        retrieval_query="orchard copper",
        top_k=1,
    )
    observed_documents = (documents[1],)
    captured: dict[str, object] = {}

    def capture_retrieve(self, query: str, *, top_k: int):
        captured["documents"] = self.documents
        captured["query"] = query
        captured["top_k"] = top_k
        return observed_documents

    monkeypatch.setattr(LocalDocumentRetriever, "retrieve", capture_retrieve)

    result = run_offline_rag_freshness_evaluation_case(evaluation_case)

    assert captured["documents"] is evaluation_case.source_documents
    assert captured["query"] is evaluation_case.retrieval_query
    assert captured["top_k"] is evaluation_case.top_k
    assert result.retrieved_documents is observed_documents


def test_ground_truth_does_not_influence_retrieval() -> None:
    documents = _documents()
    first_ground_truth = _freshness_case(
        evaluation_id="EVAL_RAG_FRESHNESS_GROUND_TRUTH_A",
        source_documents=documents,
        expected_current_document_id=documents[0].document_id,
        stale_document_ids=(documents[1].document_id, documents[2].document_id),
    )
    second_ground_truth = _freshness_case(
        evaluation_id="EVAL_RAG_FRESHNESS_GROUND_TRUTH_B",
        source_documents=documents,
        expected_current_document_id=documents[1].document_id,
        stale_document_ids=(documents[0].document_id, documents[2].document_id),
    )

    first = run_offline_rag_freshness_evaluation_case(first_ground_truth)
    second = run_offline_rag_freshness_evaluation_case(second_ground_truth)

    assert first_ground_truth.expected_current_document_id != (
        second_ground_truth.expected_current_document_id
    )
    assert first_ground_truth.stale_document_ids != second_ground_truth.stale_document_ids
    assert first.retrieved_documents == second.retrieved_documents
    for first_document, second_document in zip(
        first.retrieved_documents,
        second.retrieved_documents,
        strict=True,
    ):
        assert first_document is second_document


def test_runner_propagates_unexpected_retriever_errors(monkeypatch) -> None:
    unexpected_error = RuntimeError("synthetic unexpected freshness runner failure")

    def fail_retrieve(self, query: str, *, top_k: int):
        raise unexpected_error

    monkeypatch.setattr(LocalDocumentRetriever, "retrieve", fail_retrieve)

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_rag_freshness_evaluation_case(_freshness_case())

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_freshness_runner_contract() -> None:
    assert (
        evaluation.RAGFreshnessEvaluationRunResult
        is RAGFreshnessEvaluationRunResult
    )
    assert (
        evaluation.run_offline_rag_freshness_evaluation_case
        is run_offline_rag_freshness_evaluation_case
    )
    assert evaluation.RAGFreshnessEvaluationRunResult is (
        runner_module.RAGFreshnessEvaluationRunResult
    )
    assert "RAGFreshnessEvaluationCase" in evaluation.__all__
    assert "RAGFreshnessEvaluationRunResult" in evaluation.__all__
    assert "run_offline_rag_freshness_evaluation_case" in evaluation.__all__


def _freshness_case(
    *,
    evaluation_id: str = "EVAL_RAG_FRESHNESS_RUNNER",
    source_documents: tuple[SourceDocument, ...] | None = None,
    retrieval_query: str = "orchard copper quartz",
    top_k: int = 2,
    expected_current_document_id: str | None = None,
    stale_document_ids: tuple[str, ...] | None = None,
) -> RAGFreshnessEvaluationCase:
    documents = source_documents if source_documents is not None else _documents()
    current_document_id = (
        expected_current_document_id
        if expected_current_document_id is not None
        else documents[0].document_id
    )
    stale_ids = (
        stale_document_ids
        if stale_document_ids is not None
        else (documents[1].document_id, documents[2].document_id)
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=documents,
        retrieval_query=retrieval_query,
        top_k=top_k,
        expected_current_document_id=current_document_id,
        stale_document_ids=stale_ids,
    )


def _documents() -> tuple[SourceDocument, ...]:
    return (
        SourceDocument(
            document_id="SYNTHETIC_FRESHNESS_RUNNER_CURRENT",
            title="Synthetic orchard copper current reference",
            content="Synthetic silver current content.",
        ),
        SourceDocument(
            document_id="SYNTHETIC_FRESHNESS_RUNNER_STALE_A",
            title="Synthetic orchard stale reference",
            content="Synthetic neutral stale content.",
        ),
        SourceDocument(
            document_id="SYNTHETIC_FRESHNESS_RUNNER_STALE_B",
            title="Synthetic meadow stale reference",
            content="Synthetic neutral meadow content.",
        ),
    )
