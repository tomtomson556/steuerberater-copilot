from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    RAGFreshnessEvaluationRunResult,
    run_offline_rag_freshness_evaluation_case,
)
from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument


def test_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _freshness_case()
    observed = ("SYNTHETIC_SOURCE_ORCHARD_V1",)

    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_outdated_document_ids=observed,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_outdated_document_ids is observed
    assert result == RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_outdated_document_ids=observed,
    )


def test_run_result_is_immutable_and_uses_slots() -> None:
    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=_freshness_case(),
        observed_outdated_document_ids=("SYNTHETIC_SOURCE_ORCHARD_V1",),
    )

    with pytest.raises(FrozenInstanceError):
        result.observed_outdated_document_ids = ()

    assert not hasattr(result, "__dict__")
    assert RAGFreshnessEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "observed_outdated_document_ids",
    )


def test_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGFreshnessEvaluationCase\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case="not-a-case",
            observed_outdated_document_ids=(),
        )


def test_run_result_rejects_non_tuple_observed_ids() -> None:
    with pytest.raises(
        TypeError,
        match=r"^observed_outdated_document_ids must be a tuple\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case=_freshness_case(),
            observed_outdated_document_ids=["SYNTHETIC_SOURCE_ORCHARD_V1"],
        )


def test_run_result_rejects_non_string_observed_id() -> None:
    with pytest.raises(
        TypeError,
        match=r"^observed_outdated_document_ids must contain only strings\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case=_freshness_case(),
            observed_outdated_document_ids=(1,),
        )


def test_run_result_rejects_blank_observed_id() -> None:
    with pytest.raises(
        ValueError,
        match=r"^observed_outdated_document_ids must not contain blank values\.$",
    ):
        RAGFreshnessEvaluationRunResult(
            evaluation_case=_freshness_case(),
            observed_outdated_document_ids=(" \t\n",),
        )


def test_runner_observes_outdated_document_ids() -> None:
    evaluation_case = _freshness_case()

    result = run_offline_rag_freshness_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.observed_outdated_document_ids == ("SYNTHETIC_SOURCE_ORCHARD_V1",)
    assert not hasattr(result, "passed")
    assert not hasattr(result, "expected_outdated_document_ids")


def test_runner_observes_empty_tuple_for_current_documents() -> None:
    evaluation_case = RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_RUNNER_CURRENT",
        source_documents=(_document("SYNTHETIC_SOURCE_CURRENT"),),
        version_records=(_record("SYNTHETIC_SOURCE_CURRENT", version=2),),
        reference_date="2026-07-01",
        expected_outdated_document_ids=(),
    )

    result = run_offline_rag_freshness_evaluation_case(evaluation_case)

    assert result.observed_outdated_document_ids == ()


def test_runner_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGFreshnessEvaluationCase\.$",
    ):
        run_offline_rag_freshness_evaluation_case("not-a-case")


def test_evaluation_package_exports_rag_freshness_runner_contract() -> None:
    assert evaluation.RAGFreshnessEvaluationRunResult is RAGFreshnessEvaluationRunResult
    assert (
        evaluation.run_offline_rag_freshness_evaluation_case
        is run_offline_rag_freshness_evaluation_case
    )
    assert "RAGFreshnessEvaluationRunResult" in evaluation.__all__
    assert "run_offline_rag_freshness_evaluation_case" in evaluation.__all__


def _freshness_case() -> RAGFreshnessEvaluationCase:
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_RUNNER",
        source_documents=(
            _document("SYNTHETIC_SOURCE_ORCHARD_V1"),
            _document("SYNTHETIC_SOURCE_ORCHARD_V2"),
        ),
        version_records=(
            _record("SYNTHETIC_SOURCE_ORCHARD_V1", version=1),
            _record("SYNTHETIC_SOURCE_ORCHARD_V2", version=2),
        ),
        reference_date="2026-07-01",
        expected_outdated_document_ids=("SYNTHETIC_SOURCE_ORCHARD_V1",),
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
    family: str = "orchard_policy",
    version: int = 1,
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
