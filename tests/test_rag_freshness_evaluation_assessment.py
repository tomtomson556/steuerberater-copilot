from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_freshness_assessment as assessment_module
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    RAGFreshnessEvaluationCaseAssessment,
    RAGFreshnessEvaluationRunResult,
    assess_rag_freshness_evaluation_run_result,
)
from steuerberater_copilot.rag import SourceDocument

CURRENT_ID = "SYNTHETIC_FRESHNESS_ASSESSMENT_CURRENT"
STALE_A_ID = "SYNTHETIC_FRESHNESS_ASSESSMENT_STALE_A"
STALE_B_ID = "SYNTHETIC_FRESHNESS_ASSESSMENT_STALE_B"
NEUTRAL_ID = "SYNTHETIC_FRESHNESS_ASSESSMENT_NEUTRAL"


def test_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(CURRENT_ID,))
    )

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result(
            retrieved_document_ids=(STALE_A_ID,)
        )

    assert not hasattr(assessment, "__dict__")
    assert RAGFreshnessEvaluationCaseAssessment.__slots__ == (
        "evaluation_run_result",
    )


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result(retrieved_document_ids=(CURRENT_ID,))

    assessment = assess_rag_freshness_evaluation_run_result(result)

    assert isinstance(assessment, RAGFreshnessEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


@pytest.mark.parametrize("value", (None, False, "not-a-run-result"))
def test_assessment_rejects_invalid_run_result(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^evaluation_run_result must be a "
            r"RAGFreshnessEvaluationRunResult\.$"
        ),
    ):
        RAGFreshnessEvaluationCaseAssessment(
            evaluation_run_result=value,  # type: ignore[arg-type]
        )


def test_current_without_stale_passes() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(CURRENT_ID,))
    )

    assert assessment.current_document_retrieved is True
    assert assessment.retrieved_stale_document_ids == ()
    assert assessment.stale_document_retrieved is False
    assert assessment.passed is True


def test_current_plus_stale_fails() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(CURRENT_ID, STALE_A_ID))
    )

    assert assessment.current_document_retrieved is True
    assert assessment.retrieved_stale_document_ids == (STALE_A_ID,)
    assert assessment.stale_document_retrieved is True
    assert assessment.passed is False


def test_no_current_without_stale_fails() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(NEUTRAL_ID,))
    )

    assert assessment.current_document_retrieved is False
    assert assessment.retrieved_stale_document_ids == ()
    assert assessment.stale_document_retrieved is False
    assert assessment.passed is False


def test_stale_without_current_fails() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(STALE_B_ID,))
    )

    assert assessment.current_document_retrieved is False
    assert assessment.retrieved_stale_document_ids == (STALE_B_ID,)
    assert assessment.stale_document_retrieved is True
    assert assessment.passed is False


def test_current_plus_neutral_passes() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(retrieved_document_ids=(NEUTRAL_ID, CURRENT_ID))
    )

    assert assessment.current_document_retrieved is True
    assert assessment.retrieved_stale_document_ids == ()
    assert assessment.stale_document_retrieved is False
    assert assessment.passed is True


def test_retrieved_stale_ids_preserve_retrieval_order() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(
            retrieved_document_ids=(STALE_B_ID, NEUTRAL_ID, STALE_A_ID),
            top_k=3,
        )
    )

    assert assessment.retrieved_stale_document_ids == (STALE_B_ID, STALE_A_ID)
    assert assessment.stale_document_retrieved is True


def test_only_documents_within_top_k_are_assessed() -> None:
    stale_beyond_top_k = assess_rag_freshness_evaluation_run_result(
        _run_result(
            retrieved_document_ids=(CURRENT_ID, STALE_A_ID),
            top_k=1,
        )
    )
    current_beyond_top_k = assess_rag_freshness_evaluation_run_result(
        _run_result(
            retrieved_document_ids=(NEUTRAL_ID, CURRENT_ID),
            top_k=1,
        )
    )

    assert stale_beyond_top_k.current_document_retrieved is True
    assert stale_beyond_top_k.retrieved_stale_document_ids == ()
    assert stale_beyond_top_k.passed is True
    assert current_beyond_top_k.current_document_retrieved is False
    assert current_beyond_top_k.stale_document_retrieved is False
    assert current_beyond_top_k.passed is False


def test_assessment_leaves_ground_truth_and_run_result_unchanged() -> None:
    result = _run_result(
        retrieved_document_ids=(CURRENT_ID, NEUTRAL_ID),
        top_k=2,
    )
    evaluation_case = result.evaluation_case
    source_documents = evaluation_case.source_documents
    stale_document_ids = evaluation_case.stale_document_ids
    retrieved_documents = result.retrieved_documents

    assessment = assess_rag_freshness_evaluation_run_result(result)

    assert assessment.current_document_retrieved is True
    assert assessment.retrieved_stale_document_ids == ()
    assert assessment.passed is True
    assert assessment.evaluation_run_result is result
    assert result.evaluation_case is evaluation_case
    assert result.retrieved_documents is retrieved_documents
    assert evaluation_case.source_documents is source_documents
    assert evaluation_case.expected_current_document_id == CURRENT_ID
    assert evaluation_case.stale_document_ids is stale_document_ids
    assert evaluation_case.stale_document_ids == (STALE_A_ID, STALE_B_ID)


def test_evaluation_package_exports_freshness_assessment_contract() -> None:
    assert (
        evaluation.RAGFreshnessEvaluationCaseAssessment
        is RAGFreshnessEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_rag_freshness_evaluation_run_result
        is assess_rag_freshness_evaluation_run_result
    )
    assert evaluation.RAGFreshnessEvaluationCaseAssessment is (
        assessment_module.RAGFreshnessEvaluationCaseAssessment
    )
    assert "RAGFreshnessEvaluationCase" in evaluation.__all__
    assert "RAGFreshnessEvaluationRunResult" in evaluation.__all__
    assert "RAGFreshnessEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_rag_freshness_evaluation_run_result" in evaluation.__all__


def _run_result(
    *,
    retrieved_document_ids: tuple[str, ...],
    top_k: int | None = None,
) -> RAGFreshnessEvaluationRunResult:
    documents = _documents()
    documents_by_id = {document.document_id: document for document in documents}
    evaluation_case = RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_ASSESSMENT",
        source_documents=documents,
        retrieval_query="synthetic freshness query",
        top_k=top_k if top_k is not None else len(retrieved_document_ids) or 1,
        expected_current_document_id=CURRENT_ID,
        stale_document_ids=(STALE_A_ID, STALE_B_ID),
    )
    return RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=tuple(
            documents_by_id[document_id]
            for document_id in retrieved_document_ids
        ),
    )


def _documents() -> tuple[SourceDocument, ...]:
    return (
        _document(CURRENT_ID),
        _document(STALE_A_ID),
        _document(STALE_B_ID),
        _document(NEUTRAL_ID),
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
