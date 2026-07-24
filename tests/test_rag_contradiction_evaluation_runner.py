from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_contradiction_runner as runner_module
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
    RAGContradictionEvaluationRunResult,
    run_offline_rag_contradiction_evaluation_case,
)
from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    SourceDocument,
)


def test_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _positive_case()
    observed_detection_result = _expected_positive_detection()

    result = RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_detection_result=observed_detection_result,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_detection_result is observed_detection_result
    assert result == RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_detection_result=observed_detection_result,
    )


def test_run_result_is_immutable_and_uses_slots() -> None:
    result = RAGContradictionEvaluationRunResult(
        evaluation_case=_positive_case(),
        observed_detection_result=_expected_positive_detection(),
    )

    with pytest.raises(FrozenInstanceError):
        result.observed_detection_result = ContradictionDetectionResult(
            contradiction_present=False,
            contradictions=(),
        )

    assert not hasattr(result, "__dict__")
    assert RAGContradictionEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "observed_detection_result",
    )


def test_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGContradictionEvaluationCase\.$",
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case="not-a-case",  # type: ignore[arg-type]
            observed_detection_result=_expected_positive_detection(),
        )


@pytest.mark.parametrize("value", (None, False, ()))
def test_run_result_rejects_invalid_observed_detection_result(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^observed_detection_result must be a "
            r"ContradictionDetectionResult\.$"
        ),
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case=_positive_case(),
            observed_detection_result=value,  # type: ignore[arg-type]
        )


def test_runner_observes_positive_case_with_detector_evidence_unchanged() -> None:
    evaluation_case = _positive_case()

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.observed_detection_result == _expected_positive_detection()
    contradiction = result.observed_detection_result.contradictions[0]
    assert contradiction.first.supporting_text == "The retention period is 10 years."
    assert contradiction.second.supporting_text == "The retention period is 7 years."
    assert not hasattr(result, "passed")
    assert not hasattr(result, "expected_contradiction_present")
    assert not hasattr(result, "contradicting_passages")


def test_runner_observes_negative_case() -> None:
    evaluation_case = _negative_case()

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.observed_detection_result == ContradictionDetectionResult(
        contradiction_present=False,
        contradictions=(),
    )


def test_runner_passes_only_source_documents_and_keeps_exact_detector_result(
    monkeypatch,
) -> None:
    evaluation_case = _positive_case()
    detector_result = _expected_positive_detection()
    captured_documents: list[tuple[SourceDocument, ...]] = []

    def capture_detector(
        documents: tuple[SourceDocument, ...],
    ) -> ContradictionDetectionResult:
        captured_documents.append(documents)
        return detector_result

    monkeypatch.setattr(
        runner_module,
        "detect_passage_contradictions",
        capture_detector,
    )

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert captured_documents == [evaluation_case.source_documents]
    assert captured_documents[0] is evaluation_case.source_documents
    assert result.observed_detection_result is detector_result


def test_ground_truth_does_not_influence_detection() -> None:
    documents = _contradicting_documents()
    positive_ground_truth = _positive_case(source_documents=documents)
    negative_ground_truth = RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_NEGATIVE_LABEL",
        source_documents=documents,
        expected_contradiction_present=False,
        contradicting_passages=(),
    )

    positive_result = run_offline_rag_contradiction_evaluation_case(
        positive_ground_truth
    )
    negative_result = run_offline_rag_contradiction_evaluation_case(
        negative_ground_truth
    )

    assert positive_ground_truth.expected_contradiction_present is True
    assert negative_ground_truth.expected_contradiction_present is False
    assert positive_result.observed_detection_result == (
        negative_result.observed_detection_result
    )
    assert positive_result.observed_detection_result == _expected_positive_detection()


def test_runner_results_are_deterministic() -> None:
    evaluation_case = _positive_case()

    first = run_offline_rag_contradiction_evaluation_case(evaluation_case)
    second = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert first == second
    assert first.observed_detection_result == _expected_positive_detection()


def test_evaluation_package_exports_rag_contradiction_runner_contract() -> None:
    assert (
        evaluation.RAGContradictionEvaluationRunResult
        is RAGContradictionEvaluationRunResult
    )
    assert (
        evaluation.run_offline_rag_contradiction_evaluation_case
        is run_offline_rag_contradiction_evaluation_case
    )
    assert evaluation.RAGContradictionEvaluationRunResult is (
        runner_module.RAGContradictionEvaluationRunResult
    )
    assert "RAGContradictionEvaluationRunResult" in evaluation.__all__
    assert "run_offline_rag_contradiction_evaluation_case" in evaluation.__all__
    assert "RAGContradictionEvaluationCase" in evaluation.__all__


def _positive_case(
    *,
    source_documents: tuple[SourceDocument, ...] | None = None,
) -> RAGContradictionEvaluationCase:
    documents = source_documents or _contradicting_documents()
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_POSITIVE",
        source_documents=documents,
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
                supporting_text="The retention period is 10 years.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
                supporting_text="The retention period is 7 years.",
            ),
        ),
    )


def _negative_case() -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_NEGATIVE",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_DIGITS",
                content="Synthetic orchard. The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_WORDS",
                content="Synthetic meadow. The retention period is ten years.",
            ),
        ),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _contradicting_documents() -> tuple[SourceDocument, ...]:
    return (
        _document(
            "SYNTHETIC_SOURCE_RETENTION_TEN",
            content="Synthetic orchard note. The retention period is 10 years. End.",
        ),
        _document(
            "SYNTHETIC_SOURCE_RETENTION_SEVEN",
            content="Synthetic meadow note. The retention period is 7 years. End.",
        ),
    )


def _expected_positive_detection() -> ContradictionDetectionResult:
    return ContradictionDetectionResult(
        contradiction_present=True,
        contradictions=(
            DetectedContradictionPair(
                claim_key="retention_years",
                first=DetectedClaimPassage(
                    document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
                    supporting_text="The retention period is 10 years.",
                    claim_key="retention_years",
                    claim_value="10",
                ),
                second=DetectedClaimPassage(
                    document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
                    supporting_text="The retention period is 7 years.",
                    claim_key="retention_years",
                    claim_value="7",
                ),
            ),
        ),
    )


def _document(document_id: str, *, content: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content,
    )
