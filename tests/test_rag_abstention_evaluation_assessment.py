from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGAbstentionEvaluationCase,
    RAGAbstentionEvaluationCaseAssessment,
    RAGAbstentionEvaluationRunResult,
    assess_rag_abstention_evaluation_run_result,
)
from steuerberater_copilot.offline_mvp import IntakeCase, SyntheticDocument
from steuerberater_copilot.rag import SourceDocument


def test_abstention_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_rag_abstention_evaluation_run_result(_run_result())

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result()

    assert not hasattr(assessment, "__dict__")
    assert RAGAbstentionEvaluationCaseAssessment.__slots__ == (
        "evaluation_run_result",
    )


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result()

    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert isinstance(assessment, RAGAbstentionEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


def test_true_expected_and_true_observed_passes() -> None:
    assessment = assess_rag_abstention_evaluation_run_result(
        _run_result(expected=True, observed=True)
    )

    assert assessment.abstained_for_missing_evidence_matches is True
    assert assessment.passed is True


def test_false_expected_and_false_observed_passes() -> None:
    assessment = assess_rag_abstention_evaluation_run_result(
        _run_result(expected=False, observed=False)
    )

    assert assessment.abstained_for_missing_evidence_matches is True
    assert assessment.passed is True


def test_true_expected_and_false_observed_fails() -> None:
    assessment = assess_rag_abstention_evaluation_run_result(
        _run_result(expected=True, observed=False)
    )

    assert assessment.abstained_for_missing_evidence_matches is False
    assert assessment.passed is False


def test_false_expected_and_true_observed_fails() -> None:
    assessment = assess_rag_abstention_evaluation_run_result(
        _run_result(expected=False, observed=True)
    )

    assert assessment.abstained_for_missing_evidence_matches is False
    assert assessment.passed is False


def test_assessment_compares_only_missing_evidence_bools() -> None:
    result = _run_result(expected=False, observed=False)
    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert assessment.abstained_for_missing_evidence_matches is (
        result.evaluation_case.expected_abstained_for_missing_evidence
        == result.observed_abstained_for_missing_evidence
    )
    assert assessment.passed is assessment.abstained_for_missing_evidence_matches
    assert not hasattr(assessment, "gateway_decision_matches")
    assert not hasattr(assessment, "review_gate_status_matches")
    assert not hasattr(assessment, "outcome_matches")


def test_evaluation_package_exports_abstention_assessment_contract() -> None:
    assert (
        evaluation.RAGAbstentionEvaluationCaseAssessment
        is RAGAbstentionEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_rag_abstention_evaluation_run_result
        is assess_rag_abstention_evaluation_run_result
    )
    assert "RAGAbstentionEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_rag_abstention_evaluation_run_result" in evaluation.__all__
    assert "RAGAbstentionEvaluationCase" in evaluation.__all__
    assert "RAGAbstentionEvaluationRunResult" in evaluation.__all__


def _run_result(
    *,
    expected: bool = True,
    observed: bool = True,
) -> RAGAbstentionEvaluationRunResult:
    evaluation_case = RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_ASSESSMENT",
        intake=_allowed_intake(),
        source_documents=(
            SourceDocument(
                document_id="SYNTHETIC_SOURCE_UNRELATED",
                title="Synthetic meadow reference",
                content="Synthetic meadow content without matching query tokens.",
            ),
        ),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=expected,
    )
    return RAGAbstentionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_abstained_for_missing_evidence=observed,
    )


def _allowed_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_ABSTENTION_ASSESSMENT",
        client_ref="CLIENT_ABSTENTION_ASSESSMENT",
        scenario="Synthetic RAG abstention assessment fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_ABSTENTION_ASSESSMENT",
                label="Synthetic abstention assessment document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic abstention assessment note.",),
    )
