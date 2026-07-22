from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
    RAGContradictionEvaluationCaseAssessment,
    RAGContradictionEvaluationRunResult,
    assess_rag_contradiction_evaluation_run_result,
)
from steuerberater_copilot.rag import SourceDocument

RETENTION_SEVEN_YEARS = "The retention period is 7 years."
RETENTION_TEN_YEARS = "The retention period is 10 years."


def test_contradiction_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(_run_result())

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result()

    assert not hasattr(assessment, "__dict__")
    assert RAGContradictionEvaluationCaseAssessment.__slots__ == (
        "evaluation_run_result",
    )


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result()

    assessment = assess_rag_contradiction_evaluation_run_result(result)

    assert isinstance(assessment, RAGContradictionEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


def test_assessment_rejects_invalid_run_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^evaluation_run_result must be a "
            r"RAGContradictionEvaluationRunResult\.$"
        ),
    ):
        RAGContradictionEvaluationCaseAssessment(
            evaluation_run_result="not-a-run-result",
        )


def test_expected_and_observed_contradiction_with_matching_passages_passes() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=True, observed_passages=_labels())
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradicting_document_ids_match is True
    assert assessment.contradicting_passages_match is True
    assert assessment.passed is True


def test_expected_absent_and_observed_absent_passes() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=False, observed=False, observed_passages=())
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradicting_document_ids_match is True
    assert assessment.contradicting_passages_match is True
    assert assessment.passed is True


def test_presence_mismatch_fails_even_when_passage_sets_match() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=False, observed_passages=())
    )

    assert assessment.contradiction_present_matches is False
    assert assessment.contradicting_document_ids_match is False
    assert assessment.contradicting_passages_match is False
    assert assessment.passed is False


def test_document_id_mismatch_fails_even_when_presence_matches() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(
            expected=True,
            observed=True,
            observed_passages=(
                ContradictionEvidenceLabel(
                    document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
                    supporting_text=RETENTION_TEN_YEARS,
                ),
                ContradictionEvidenceLabel(
                    document_id="SYNTHETIC_SOURCE_OTHER",
                    supporting_text="The retention period is 8 years.",
                ),
            ),
        )
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradicting_document_ids_match is False
    assert assessment.contradicting_passages_match is False
    assert assessment.passed is False


def test_exact_passage_mismatch_is_diagnostic_only_when_document_ids_match() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(
            expected=True,
            observed=True,
            observed_passages=(
                ContradictionEvidenceLabel(
                    document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
                    supporting_text="A normalized paraphrase for ten years.",
                ),
                ContradictionEvidenceLabel(
                    document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
                    supporting_text="A normalized paraphrase for seven years.",
                ),
            ),
        )
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradicting_document_ids_match is True
    assert assessment.contradicting_passages_match is False
    assert assessment.passed is True


def test_passage_matching_ignores_observed_label_order() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(
            expected=True,
            observed=True,
            observed_passages=tuple(reversed(_labels())),
        )
    )

    assert assessment.contradicting_document_ids_match is True
    assert assessment.contradicting_passages_match is True
    assert assessment.passed is True


def test_assessment_contract_contains_only_expected_metrics() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(_run_result())

    assert not hasattr(assessment, "gateway_decision_matches")
    assert not hasattr(assessment, "review_gate_status_matches")
    assert not hasattr(assessment, "outcome_matches")


def test_evaluation_package_exports_contradiction_assessment_contract() -> None:
    assert (
        evaluation.RAGContradictionEvaluationCaseAssessment
        is RAGContradictionEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_rag_contradiction_evaluation_run_result
        is assess_rag_contradiction_evaluation_run_result
    )
    assert "RAGContradictionEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_rag_contradiction_evaluation_run_result" in evaluation.__all__


def _run_result(
    *,
    expected: bool = True,
    observed: bool = True,
    observed_passages: tuple[ContradictionEvidenceLabel, ...] | None = None,
) -> RAGContradictionEvaluationRunResult:
    if observed_passages is None:
        observed_passages = _labels()
    return RAGContradictionEvaluationRunResult(
        evaluation_case=_case(expected=expected),
        observed_contradiction_present=observed,
        observed_contradicting_passages=observed_passages,
    )


def _case(*, expected: bool) -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_ASSESSMENT",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_TEN",
                content=f"Synthetic orchard note. {RETENTION_TEN_YEARS}",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_SEVEN",
                content=f"Synthetic meadow note. {RETENTION_SEVEN_YEARS}",
            ),
            _document(
                "SYNTHETIC_SOURCE_OTHER",
                content="Synthetic meadow note. The retention period is 8 years.",
            ),
        ),
        expected_contradiction_present=expected,
        contradicting_passages=_labels() if expected else (),
    )


def _labels() -> tuple[ContradictionEvidenceLabel, ...]:
    return (
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
            supporting_text=RETENTION_TEN_YEARS,
        ),
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
            supporting_text=RETENTION_SEVEN_YEARS,
        ),
    )


def _document(document_id: str, *, content: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content,
    )
