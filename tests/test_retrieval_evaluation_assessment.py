from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseAssessment,
    RetrievalEvaluationRunResult,
    assess_retrieval_evaluation_run_result,
)
from steuerberater_copilot.rag import SourceDocument


def test_retrieval_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_retrieval_evaluation_run_result(_run_result())

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result()

    assert not hasattr(assessment, "__dict__")
    assert RetrievalEvaluationCaseAssessment.__slots__ == ("evaluation_run_result",)


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result()

    assessment = assess_retrieval_evaluation_run_result(result)

    assert isinstance(assessment, RetrievalEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


def test_full_recall_is_one() -> None:
    relevant_a = _document("SYNTHETIC_SOURCE_A")
    relevant_b = _document("SYNTHETIC_SOURCE_B")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant_a, relevant_b),
            retrieved_documents=(relevant_b, relevant_a),
            relevant_document_ids=("SYNTHETIC_SOURCE_A", "SYNTHETIC_SOURCE_B"),
            top_k=2,
        )
    )

    assert assessment.recalled_document_ids_at_k == (
        "SYNTHETIC_SOURCE_B",
        "SYNTHETIC_SOURCE_A",
    )
    assert assessment.recall_at_k == 1.0


def test_partial_recall_is_fraction_of_relevant_labels() -> None:
    relevant_a = _document("SYNTHETIC_SOURCE_A")
    relevant_b = _document("SYNTHETIC_SOURCE_B")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant_a, relevant_b),
            retrieved_documents=(relevant_a,),
            relevant_document_ids=("SYNTHETIC_SOURCE_A", "SYNTHETIC_SOURCE_B"),
            top_k=2,
        )
    )

    assert assessment.recalled_document_ids_at_k == ("SYNTHETIC_SOURCE_A",)
    assert assessment.recall_at_k == 0.5


def test_no_relevant_hit_with_labels_is_zero() -> None:
    relevant = _document("SYNTHETIC_SOURCE_RELEVANT")
    other = _document("SYNTHETIC_SOURCE_OTHER")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant, other),
            retrieved_documents=(other,),
            relevant_document_ids=("SYNTHETIC_SOURCE_RELEVANT",),
            top_k=1,
        )
    )

    assert assessment.recalled_document_ids_at_k == ()
    assert assessment.recall_at_k == 0.0


def test_irrelevant_hits_do_not_change_recall() -> None:
    relevant = _document("SYNTHETIC_SOURCE_RELEVANT")
    other = _document("SYNTHETIC_SOURCE_OTHER")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant, other),
            retrieved_documents=(other, relevant),
            relevant_document_ids=("SYNTHETIC_SOURCE_RELEVANT",),
            top_k=2,
        )
    )

    assert assessment.recalled_document_ids_at_k == ("SYNTHETIC_SOURCE_RELEVANT",)
    assert assessment.recall_at_k == 1.0


def test_recalled_ids_preserve_retrieval_order() -> None:
    relevant_a = _document("SYNTHETIC_SOURCE_A")
    relevant_b = _document("SYNTHETIC_SOURCE_B")
    relevant_c = _document("SYNTHETIC_SOURCE_C")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant_a, relevant_b, relevant_c),
            retrieved_documents=(relevant_c, relevant_a, relevant_b),
            relevant_document_ids=(
                "SYNTHETIC_SOURCE_A",
                "SYNTHETIC_SOURCE_B",
                "SYNTHETIC_SOURCE_C",
            ),
            top_k=3,
        )
    )

    assert assessment.recalled_document_ids_at_k == (
        "SYNTHETIC_SOURCE_C",
        "SYNTHETIC_SOURCE_A",
        "SYNTHETIC_SOURCE_B",
    )


def test_documents_beyond_top_k_are_not_counted() -> None:
    relevant_a = _document("SYNTHETIC_SOURCE_A")
    relevant_b = _document("SYNTHETIC_SOURCE_B")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant_a, relevant_b),
            retrieved_documents=(relevant_a, relevant_b),
            relevant_document_ids=("SYNTHETIC_SOURCE_A", "SYNTHETIC_SOURCE_B"),
            top_k=1,
        )
    )

    assert assessment.recalled_document_ids_at_k == ("SYNTHETIC_SOURCE_A",)
    assert assessment.recall_at_k == 0.5


def test_duplicate_observed_relevant_ids_are_counted_once() -> None:
    relevant = _document("SYNTHETIC_SOURCE_RELEVANT")
    other = _document("SYNTHETIC_SOURCE_OTHER")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(relevant, other),
            retrieved_documents=(relevant, relevant, other),
            relevant_document_ids=("SYNTHETIC_SOURCE_RELEVANT",),
            top_k=3,
        )
    )

    assert assessment.recalled_document_ids_at_k == ("SYNTHETIC_SOURCE_RELEVANT",)
    assert assessment.recall_at_k == 1.0


def test_empty_relevance_labels_make_recall_inapplicable() -> None:
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(),
            retrieved_documents=(),
            relevant_document_ids=(),
            top_k=1,
        )
    )

    assert assessment.recalled_document_ids_at_k == ()
    assert assessment.recall_at_k is None
    assert not hasattr(assessment, "passed")
    assert not hasattr(assessment, "abstained")
    assert not hasattr(assessment, "abstention")


def test_empty_labels_with_irrelevant_hits_remain_inapplicable() -> None:
    other = _document("SYNTHETIC_SOURCE_OTHER")
    assessment = assess_retrieval_evaluation_run_result(
        _run_result(
            source_documents=(other,),
            retrieved_documents=(other,),
            relevant_document_ids=(),
            top_k=1,
        )
    )

    assert assessment.recalled_document_ids_at_k == ()
    assert assessment.recall_at_k is None
    assert assessment.recall_at_k != 1.0
    assert not hasattr(assessment, "passed")
    assert not hasattr(assessment, "abstained")


def test_evaluation_package_exports_retrieval_assessment_contract() -> None:
    assert (
        evaluation.RetrievalEvaluationCaseAssessment
        is RetrievalEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_retrieval_evaluation_run_result
        is assess_retrieval_evaluation_run_result
    )
    assert "RetrievalEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_retrieval_evaluation_run_result" in evaluation.__all__
    assert "EvaluationCaseAssessment" in evaluation.__all__
    assert "assess_evaluation_run_result" in evaluation.__all__


def _run_result(
    *,
    source_documents: tuple[SourceDocument, ...] | None = None,
    retrieved_documents: tuple[SourceDocument, ...] | None = None,
    relevant_document_ids: tuple[str, ...] | None = None,
    top_k: int = 2,
) -> RetrievalEvaluationRunResult:
    if source_documents is None:
        source_documents = (
            _document("SYNTHETIC_SOURCE_A"),
            _document("SYNTHETIC_SOURCE_B"),
        )
    if retrieved_documents is None:
        retrieved_documents = source_documents[:1]
    if relevant_document_ids is None:
        relevant_document_ids = tuple(
            document.document_id for document in source_documents[:1]
        )

    evaluation_case = RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_ASSESSMENT",
        source_documents=source_documents,
        retrieval_query="synthetic query",
        top_k=top_k,
        relevant_document_ids=relevant_document_ids,
    )
    return RetrievalEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=retrieved_documents,
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
