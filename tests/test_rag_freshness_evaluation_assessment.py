from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    RAGFreshnessEvaluationCaseAssessment,
    RAGFreshnessEvaluationRunResult,
    assess_rag_freshness_evaluation_run_result,
)
from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument


def test_freshness_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(_run_result())

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _run_result()

    assert not hasattr(assessment, "__dict__")
    assert RAGFreshnessEvaluationCaseAssessment.__slots__ == (
        "evaluation_run_result",
    )


def test_assessment_function_keeps_exact_run_result_instance() -> None:
    result = _run_result()

    assessment = assess_rag_freshness_evaluation_run_result(result)

    assert isinstance(assessment, RAGFreshnessEvaluationCaseAssessment)
    assert assessment.evaluation_run_result is result


def test_assessment_rejects_invalid_run_result() -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^evaluation_run_result must be a "
            r"RAGFreshnessEvaluationRunResult\.$"
        ),
    ):
        RAGFreshnessEvaluationCaseAssessment(
            evaluation_run_result="not-a-run-result",
        )


def test_expected_and_observed_outdated_ids_pass() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(
            expected=("SYNTHETIC_SOURCE_ORCHARD_V1",),
            observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        )
    )

    assert assessment.outdated_document_ids_match is True
    assert assessment.passed is True


def test_empty_expected_and_empty_observed_pass() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(expected=(), observed=())
    )

    assert assessment.outdated_document_ids_match is True
    assert assessment.passed is True


def test_missing_outdated_observation_fails() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(
            expected=("SYNTHETIC_SOURCE_ORCHARD_V1",),
            observed=(),
        )
    )

    assert assessment.outdated_document_ids_match is False
    assert assessment.passed is False


def test_unexpected_outdated_observation_fails() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(
            expected=(),
            observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        )
    )

    assert assessment.outdated_document_ids_match is False
    assert assessment.passed is False


def test_outdated_id_matching_ignores_observed_order() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(
        _run_result(
            expected=(
                "SYNTHETIC_SOURCE_ORCHARD_V1",
                "SYNTHETIC_SOURCE_MEADOW_EXPIRED",
            ),
            observed=(
                "SYNTHETIC_SOURCE_MEADOW_EXPIRED",
                "SYNTHETIC_SOURCE_ORCHARD_V1",
            ),
        )
    )

    assert assessment.outdated_document_ids_match is True
    assert assessment.passed is True


def test_assessment_contract_contains_only_expected_metrics() -> None:
    assessment = assess_rag_freshness_evaluation_run_result(_run_result())

    assert not hasattr(assessment, "gateway_decision_matches")
    assert not hasattr(assessment, "review_gate_status_matches")
    assert not hasattr(assessment, "outcome_matches")


def test_evaluation_package_exports_freshness_assessment_contract() -> None:
    assert (
        evaluation.RAGFreshnessEvaluationCaseAssessment
        is RAGFreshnessEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_rag_freshness_evaluation_run_result
        is assess_rag_freshness_evaluation_run_result
    )
    assert "RAGFreshnessEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_rag_freshness_evaluation_run_result" in evaluation.__all__


def _run_result(
    *,
    expected: tuple[str, ...] = ("SYNTHETIC_SOURCE_ORCHARD_V1",),
    observed: tuple[str, ...] = ("SYNTHETIC_SOURCE_ORCHARD_V1",),
) -> RAGFreshnessEvaluationRunResult:
    return RAGFreshnessEvaluationRunResult(
        evaluation_case=_case(expected=expected),
        observed_outdated_document_ids=observed,
    )


def _case(*, expected: tuple[str, ...]) -> RAGFreshnessEvaluationCase:
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_ASSESSMENT",
        source_documents=(
            _document("SYNTHETIC_SOURCE_ORCHARD_V1"),
            _document("SYNTHETIC_SOURCE_ORCHARD_V2"),
            _document("SYNTHETIC_SOURCE_MEADOW_EXPIRED"),
        ),
        version_records=(
            _record("SYNTHETIC_SOURCE_ORCHARD_V1", family="orchard", version=1),
            _record("SYNTHETIC_SOURCE_ORCHARD_V2", family="orchard", version=2),
            _record(
                "SYNTHETIC_SOURCE_MEADOW_EXPIRED",
                family="meadow",
                version=1,
                valid_from="2025-01-01",
                valid_to="2026-01-01",
            ),
        ),
        reference_date="2026-07-01",
        expected_outdated_document_ids=expected,
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic orchard content for {document_id}.",
    )


def _record(
    document_id: str,
    *,
    family: str,
    version: int,
    valid_from: str = "2026-01-01",
    valid_to: str | None = None,
) -> DocumentVersionRecord:
    return DocumentVersionRecord(
        document_id=document_id,
        document_family=family,
        version_number=version,
        valid_from=valid_from,
        valid_to=valid_to,
    )
