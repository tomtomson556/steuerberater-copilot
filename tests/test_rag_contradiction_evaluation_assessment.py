from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_contradiction_assessment as assessment_module
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
    RAGContradictionEvaluationCaseAssessment,
    RAGContradictionEvaluationRunResult,
    assess_rag_contradiction_evaluation_run_result,
)
from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    SourceDocument,
)


def test_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=_detection(_retention_pair()))
    )

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result(
            expected=False,
            observed=_detection(),
        )

    assert not hasattr(assessment, "__dict__")
    assert RAGContradictionEvaluationCaseAssessment.__slots__ == (
        "evaluation_run_result",
    )


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result(expected=True, observed=_detection(_retention_pair()))

    assessment = assess_rag_contradiction_evaluation_run_result(result)

    assert isinstance(assessment, RAGContradictionEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


@pytest.mark.parametrize("value", (None, False, "not-a-run-result"))
def test_assessment_rejects_invalid_run_result(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^evaluation_run_result must be a "
            r"RAGContradictionEvaluationRunResult\.$"
        ),
    ):
        RAGContradictionEvaluationCaseAssessment(
            evaluation_run_result=value,  # type: ignore[arg-type]
        )


def test_true_expected_and_true_observed_with_exact_evidence_passes() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=_detection(_retention_pair()))
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradiction_evidence_matches is True
    assert assessment.passed is True


def test_true_expected_and_false_observed_fails() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=_detection())
    )

    assert assessment.contradiction_present_matches is False
    assert assessment.contradiction_evidence_matches is False
    assert assessment.passed is False


def test_false_expected_and_false_observed_passes() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=False, observed=_detection())
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradiction_evidence_matches is True
    assert assessment.passed is True


def test_false_expected_and_true_observed_fails() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=False, observed=_detection(_retention_pair()))
    )

    assert assessment.contradiction_present_matches is False
    assert assessment.contradiction_evidence_matches is False
    assert assessment.passed is False


def test_correct_bool_with_wrong_supporting_text_fails() -> None:
    wrong_evidence = _pair(
        claim_key="retention_years",
        first=(
            "SYNTHETIC_SOURCE_RETENTION_TEN",
            "Wrong observed retention passage for ten years.",
            "10",
        ),
        second=(
            "SYNTHETIC_SOURCE_RETENTION_SEVEN",
            "Wrong observed retention passage for seven years.",
            "7",
        ),
    )
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=_detection(wrong_evidence))
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradiction_evidence_matches is False
    assert assessment.passed is False


def test_reversed_observed_evidence_order_passes() -> None:
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=_detection(_retention_pair(reverse=True)))
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradiction_evidence_matches is True
    assert assessment.passed is True


@pytest.mark.parametrize("observed_kind", ("false", "additional", "duplicate"))
def test_false_additional_or_duplicate_observed_evidence_fails(
    observed_kind: str,
) -> None:
    observed_by_kind = {
        "false": _detection(_archive_pair()),
        "additional": _detection(_retention_pair(), _archive_pair()),
        "duplicate": _detection(_retention_pair(), _retention_pair()),
    }
    assessment = assess_rag_contradiction_evaluation_run_result(
        _run_result(expected=True, observed=observed_by_kind[observed_kind])
    )

    assert assessment.contradiction_present_matches is True
    assert assessment.contradiction_evidence_matches is False
    assert assessment.passed is False


def test_evaluation_package_exports_contradiction_assessment_contract() -> None:
    assert (
        evaluation.RAGContradictionEvaluationCaseAssessment
        is RAGContradictionEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_rag_contradiction_evaluation_run_result
        is assess_rag_contradiction_evaluation_run_result
    )
    assert evaluation.RAGContradictionEvaluationCaseAssessment is (
        assessment_module.RAGContradictionEvaluationCaseAssessment
    )
    assert "RAGContradictionEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_rag_contradiction_evaluation_run_result" in evaluation.__all__
    assert "RAGContradictionEvaluationCase" in evaluation.__all__
    assert "RAGContradictionEvaluationRunResult" in evaluation.__all__


def _run_result(
    *,
    expected: bool,
    observed: ContradictionDetectionResult,
) -> RAGContradictionEvaluationRunResult:
    return RAGContradictionEvaluationRunResult(
        evaluation_case=_evaluation_case(expected=expected),
        observed_detection_result=observed,
    )


def _evaluation_case(*, expected: bool) -> RAGContradictionEvaluationCase:
    contradicting_passages: tuple[ContradictionEvidenceLabel, ...] = ()
    if expected:
        contradicting_passages = (
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
                supporting_text="The retention period is 10 years.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
                supporting_text="The retention period is 7 years.",
            ),
        )
    return RAGContradictionEvaluationCase(
        evaluation_id=f"EVAL_RAG_CONTRADICTION_ASSESSMENT_{expected}",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_TEN",
                content="The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_SEVEN",
                content="The retention period is 7 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_REQUIRED",
                content="The archive is required.",
            ),
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_OPTIONAL",
                content="The archive is optional.",
            ),
        ),
        expected_contradiction_present=expected,
        contradicting_passages=contradicting_passages,
    )


def _retention_pair(*, reverse: bool = False) -> DetectedContradictionPair:
    first = (
        "SYNTHETIC_SOURCE_RETENTION_TEN",
        "The retention period is 10 years.",
        "10",
    )
    second = (
        "SYNTHETIC_SOURCE_RETENTION_SEVEN",
        "The retention period is 7 years.",
        "7",
    )
    if reverse:
        first, second = second, first
    return _pair(
        claim_key="retention_years",
        first=first,
        second=second,
    )


def _archive_pair() -> DetectedContradictionPair:
    return _pair(
        claim_key="archive_requirement",
        first=(
            "SYNTHETIC_SOURCE_ARCHIVE_REQUIRED",
            "The archive is required.",
            "required",
        ),
        second=(
            "SYNTHETIC_SOURCE_ARCHIVE_OPTIONAL",
            "The archive is optional.",
            "optional",
        ),
    )


def _pair(
    *,
    claim_key: str,
    first: tuple[str, str, str],
    second: tuple[str, str, str],
) -> DetectedContradictionPair:
    return DetectedContradictionPair(
        claim_key=claim_key,
        first=DetectedClaimPassage(
            document_id=first[0],
            supporting_text=first[1],
            claim_key=claim_key,
            claim_value=first[2],
        ),
        second=DetectedClaimPassage(
            document_id=second[0],
            supporting_text=second[1],
            claim_key=claim_key,
            claim_value=second[2],
        ),
    )


def _detection(
    *contradictions: DetectedContradictionPair,
) -> ContradictionDetectionResult:
    return ContradictionDetectionResult(
        contradiction_present=bool(contradictions),
        contradictions=contradictions,
    )


def _document(document_id: str, *, content: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content,
    )
