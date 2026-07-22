from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
    RAGContradictionEvaluationRunResult,
    run_offline_rag_contradiction_evaluation_case,
)
from steuerberater_copilot.rag import SourceDocument

RETENTION_SEVEN_YEARS = "The retention period is 7 years."
RETENTION_TEN_YEARS = "The retention period is 10 years."


def test_run_result_keeps_fields_and_identities() -> None:
    evaluation_case = _positive_case()
    labels = _labels()

    result = RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_contradiction_present=True,
        observed_contradicting_passages=labels,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_contradiction_present is True
    assert result.observed_contradicting_passages is labels
    assert result == RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_contradiction_present=True,
        observed_contradicting_passages=labels,
    )


def test_run_result_is_immutable_and_uses_slots() -> None:
    result = RAGContradictionEvaluationRunResult(
        evaluation_case=_positive_case(),
        observed_contradiction_present=True,
        observed_contradicting_passages=_labels(),
    )

    with pytest.raises(FrozenInstanceError):
        result.observed_contradiction_present = False

    assert not hasattr(result, "__dict__")
    assert RAGContradictionEvaluationRunResult.__slots__ == (
        "evaluation_case",
        "observed_contradiction_present",
        "observed_contradicting_passages",
    )


def test_run_result_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGContradictionEvaluationCase\.$",
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case="not-a-case",
            observed_contradiction_present=False,
            observed_contradicting_passages=(),
        )


@pytest.mark.parametrize("value", (0, 1, "true", None))
def test_run_result_rejects_non_bool_observation(value: object) -> None:
    with pytest.raises(
        TypeError,
        match=r"^observed_contradiction_present must be a boolean\.$",
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case=_positive_case(),
            observed_contradiction_present=value,
            observed_contradicting_passages=_labels(),
        )


def test_run_result_rejects_non_tuple_observed_passages() -> None:
    with pytest.raises(
        TypeError,
        match=r"^observed_contradicting_passages must be a tuple\.$",
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case=_positive_case(),
            observed_contradiction_present=True,
            observed_contradicting_passages=list(_labels()),
        )


def test_run_result_rejects_non_label_observed_passage() -> None:
    with pytest.raises(
        TypeError,
        match=(
            r"^observed_contradicting_passages must contain only "
            r"ContradictionEvidenceLabel objects\.$"
        ),
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case=_positive_case(),
            observed_contradiction_present=True,
            observed_contradicting_passages=("not-a-label",),
        )


def test_run_result_rejects_inconsistent_observation_and_passages() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^observed_contradiction_present must be True exactly when "
            r"observed_contradicting_passages is non-empty\.$"
        ),
    ):
        RAGContradictionEvaluationRunResult(
            evaluation_case=_positive_case(),
            observed_contradiction_present=False,
            observed_contradicting_passages=_labels(),
        )


def test_runner_observes_contradiction_and_first_passage_pair() -> None:
    evaluation_case = _positive_case()

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert result.evaluation_case is evaluation_case
    assert result.observed_contradiction_present is True
    assert result.observed_contradicting_passages == _labels()
    assert not hasattr(result, "passed")
    assert not hasattr(result, "expected_contradiction_present")


def test_runner_observes_no_contradiction_for_same_claim_value() -> None:
    evaluation_case = RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_SAME_VALUE",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_ALPHA",
                content=f"Synthetic orchard note. {RETENTION_TEN_YEARS}",
            ),
            _document(
                "SYNTHETIC_SOURCE_BETA",
                content="Synthetic meadow note. The retention period is ten years.",
            ),
        ),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert result.observed_contradiction_present is False
    assert result.observed_contradicting_passages == ()


def test_runner_observes_polarity_based_retention_contradiction() -> None:
    evaluation_case = RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_NEGATION",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_AFFIRM",
                content="Natural sentence. The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_DENY",
                content="Natural sentence. The retention period is not 10 years.",
            ),
        ),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_AFFIRM",
                supporting_text="The retention period is 10 years.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_SOURCE_RETENTION_DENY",
                supporting_text="The retention period is not 10 years.",
            ),
        ),
    )

    result = run_offline_rag_contradiction_evaluation_case(evaluation_case)

    assert result.observed_contradiction_present is True
    assert result.observed_contradicting_passages == (
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_AFFIRM",
            supporting_text="The retention period is 10 years.",
        ),
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_DENY",
            supporting_text="The retention period is not 10 years.",
        ),
    )


def test_runner_rejects_invalid_evaluation_case() -> None:
    with pytest.raises(
        TypeError,
        match=r"^evaluation_case must be a RAGContradictionEvaluationCase\.$",
    ):
        run_offline_rag_contradiction_evaluation_case("not-a-case")


def test_evaluation_package_exports_rag_contradiction_runner_contract() -> None:
    assert (
        evaluation.RAGContradictionEvaluationRunResult
        is RAGContradictionEvaluationRunResult
    )
    assert (
        evaluation.run_offline_rag_contradiction_evaluation_case
        is run_offline_rag_contradiction_evaluation_case
    )
    assert "RAGContradictionEvaluationRunResult" in evaluation.__all__
    assert "run_offline_rag_contradiction_evaluation_case" in evaluation.__all__


def _positive_case() -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_RUNNER_POSITIVE",
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_TEN",
                content=f"Synthetic orchard note. {RETENTION_TEN_YEARS}",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_SEVEN",
                content=f"Synthetic meadow note. {RETENTION_SEVEN_YEARS}",
            ),
        ),
        expected_contradiction_present=True,
        contradicting_passages=_labels(),
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
