import json
from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_abstention_runner as rag_abstention_runner_module
from steuerberater_copilot.ai import FakeModelProvider, ModelResponse
from steuerberater_copilot.evaluation import (
    RAGAbstentionEvaluationCase,
    RAGAbstentionEvaluationRunResult,
    run_offline_rag_abstention_evaluation_case,
)
from steuerberater_copilot.offline_mvp import IntakeCase, SyntheticDocument
from steuerberater_copilot.offline_mvp.models import MockRiskSignal
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

SUPPORTING_PASSAGE = "Synthetic orchard passage for abstention runner testing."

VALID_GROUNDED_CONTENT = json.dumps(
    {
        "summary_points": ["Synthetic grounded orchard summary."],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_MATCH",
                "supporting_text": SUPPORTING_PASSAGE,
            }
        ],
    }
)


def test_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _abstention_case(expected=True)

    result = RAGAbstentionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_abstained_for_missing_evidence=True,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_abstained_for_missing_evidence is True
    assert result == RAGAbstentionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_abstained_for_missing_evidence=True,
    )


def test_run_result_is_immutable_and_uses_slots() -> None:
    result = RAGAbstentionEvaluationRunResult(
        evaluation_case=_abstention_case(expected=True),
        observed_abstained_for_missing_evidence=False,
    )

    with pytest.raises(FrozenInstanceError):
        result.observed_abstained_for_missing_evidence = True

    assert not hasattr(result, "__dict__")
    assert RAGAbstentionEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "observed_abstained_for_missing_evidence",
    )


def test_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGAbstentionEvaluationCase\.$",
    ):
        RAGAbstentionEvaluationRunResult(
            evaluation_case="not-a-case",  # type: ignore[arg-type]
            observed_abstained_for_missing_evidence=True,
        )


@pytest.mark.parametrize("value", (0, 1, "true", None))
def test_run_result_rejects_non_bool_observation(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=r"^observed_abstained_for_missing_evidence must be a boolean\.$",
    ):
        RAGAbstentionEvaluationRunResult(
            evaluation_case=_abstention_case(expected=True),
            observed_abstained_for_missing_evidence=value,  # type: ignore[arg-type]
        )


def test_runner_observes_true_for_missing_evidence_without_provider_call() -> None:
    evaluation_case = _abstention_case(
        expected=True,
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_UNRELATED",
                title="Synthetic meadow reference",
                content="Synthetic meadow content without matching query tokens.",
            ),
        ),
        retrieval_query="orchard",
    )
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))

    result = run_offline_rag_abstention_evaluation_case(
        evaluation_case,
        provider=provider,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_abstained_for_missing_evidence is True
    assert provider.requests == ()
    assert not hasattr(result, "passed")
    assert not hasattr(result, "expected_abstained_for_missing_evidence")


def test_runner_observes_false_when_evidence_is_retrieved() -> None:
    match = _document(
        "SYNTHETIC_SOURCE_MATCH",
        title="Synthetic orchard reference",
        content=f"Prefix. {SUPPORTING_PASSAGE} Suffix.",
    )
    evaluation_case = _abstention_case(
        expected=False,
        source_documents=(match,),
        retrieval_query="orchard",
        top_k=1,
    )
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))

    result = run_offline_rag_abstention_evaluation_case(
        evaluation_case,
        provider=provider,
    )

    assert result.observed_abstained_for_missing_evidence is False
    assert len(provider.requests) == 1


def test_runner_observes_false_for_gateway_stop_without_provider_call() -> None:
    evaluation_case = RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_GATEWAY_STOP",
        intake=_gateway_stop_intake(),
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_MATCH",
                title="Synthetic orchard reference",
                content=SUPPORTING_PASSAGE,
            ),
        ),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=False,
    )
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))

    result = run_offline_rag_abstention_evaluation_case(
        evaluation_case,
        provider=provider,
    )

    assert result.observed_abstained_for_missing_evidence is False
    assert provider.requests == ()


def test_runner_observes_false_for_review_gate_stop_without_provider_call() -> None:
    evaluation_case = RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_REVIEW_STOP",
        intake=_review_gate_stop_intake(),
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_MATCH",
                title="Synthetic orchard reference",
                content=SUPPORTING_PASSAGE,
            ),
        ),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=False,
    )
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))

    result = run_offline_rag_abstention_evaluation_case(
        evaluation_case,
        provider=provider,
    )

    assert result.observed_abstained_for_missing_evidence is False
    assert provider.requests == ()


def test_runner_forwards_source_documents_query_and_top_k(monkeypatch) -> None:
    match = _document(
        "SYNTHETIC_SOURCE_MATCH",
        title="Synthetic orchard reference",
        content=SUPPORTING_PASSAGE,
    )
    other = _document(
        "SYNTHETIC_SOURCE_OTHER",
        title="Synthetic meadow reference",
        content="Synthetic meadow content.",
    )
    evaluation_case = _abstention_case(
        expected=False,
        source_documents=(other, match),
        retrieval_query="orchard quartz",
        top_k=1,
    )
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    captured: dict[str, object] = {}

    def capture_workflow(case, *, provider, retriever, retrieval_query, top_k):
        captured["intake"] = case
        captured["provider"] = provider
        captured["retriever"] = retriever
        captured["retrieval_query"] = retrieval_query
        captured["top_k"] = top_k
        return type(
            "SyntheticWorkflowOutput",
            (),
            {"abstained_for_missing_evidence": False},
        )()

    monkeypatch.setattr(
        rag_abstention_runner_module,
        "build_synthetic_rag_workflow",
        capture_workflow,
    )

    result = run_offline_rag_abstention_evaluation_case(
        evaluation_case,
        provider=provider,
    )

    assert captured["intake"] is evaluation_case.intake
    assert captured["provider"] is provider
    assert isinstance(captured["retriever"], LocalDocumentRetriever)
    assert captured["retriever"].documents is evaluation_case.source_documents
    assert captured["retrieval_query"] is evaluation_case.retrieval_query
    assert captured["top_k"] is evaluation_case.top_k
    assert result.observed_abstained_for_missing_evidence is False


def test_runner_propagates_unexpected_workflow_errors(monkeypatch) -> None:
    unexpected_error = RuntimeError("synthetic unexpected abstention runner failure")

    def fail_workflow(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        rag_abstention_runner_module,
        "build_synthetic_rag_workflow",
        fail_workflow,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_rag_abstention_evaluation_case(
            _abstention_case(expected=True),
            provider=FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT)),
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_rag_abstention_runner_contract() -> None:
    assert (
        evaluation.RAGAbstentionEvaluationRunResult
        is RAGAbstentionEvaluationRunResult
    )
    assert (
        evaluation.run_offline_rag_abstention_evaluation_case
        is run_offline_rag_abstention_evaluation_case
    )
    assert evaluation.RAGAbstentionEvaluationRunResult is (
        rag_abstention_runner_module.RAGAbstentionEvaluationRunResult
    )
    assert "RAGAbstentionEvaluationRunResult" in evaluation.__all__
    assert "run_offline_rag_abstention_evaluation_case" in evaluation.__all__
    assert "RAGAbstentionEvaluationCase" in evaluation.__all__


def _abstention_case(
    *,
    expected: bool,
    source_documents: tuple[SourceDocument, ...] | None = None,
    retrieval_query: str = "orchard",
    top_k: int = 1,
) -> RAGAbstentionEvaluationCase:
    if source_documents is None:
        source_documents = (
            _document(
                "SYNTHETIC_SOURCE_UNRELATED",
                title="Synthetic meadow reference",
                content="Synthetic meadow content without matching query tokens.",
            ),
        )
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_RUNNER",
        intake=_allowed_intake(),
        source_documents=source_documents,
        retrieval_query=retrieval_query,
        top_k=top_k,
        expected_abstained_for_missing_evidence=expected,
    )


def _allowed_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_310",
        client_ref="CLIENT_310",
        scenario="Synthetic RAG abstention runner fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_310",
                label="Synthetic abstention runner document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic abstention runner note.",),
    )


def _gateway_stop_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_311",
        client_ref="CLIENT_311",
        scenario="Synthetic missing context fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_311",
                label="Synthetic payment overview descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note.",
            ),
        ),
        missing_items=("Synthetic missing source reference.",),
    )


def _review_gate_stop_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_312",
        client_ref="CLIENT_312",
        scenario="Synthetic document preparation fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_312",
                label="Synthetic document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note.",
            ),
        ),
        mock_risk_signals=(MockRiskSignal.DOCUMENT_PREPARATION.value,),
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


def _model_response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="fake",
        model_name="fake-model",
    )
