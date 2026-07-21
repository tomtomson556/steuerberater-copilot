import json

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_abstention_library as rag_abstention_library
from steuerberater_copilot.ai import FakeModelProvider, ModelResponse
from steuerberater_copilot.evaluation import (
    RAGAbstentionEvaluationCase,
    SyntheticEvaluationFixture,
    assess_rag_abstention_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    build_synthetic_grounding_evaluation_case_library,
    build_synthetic_rag_abstention_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_rag_abstention_evaluation_case,
)
from steuerberater_copilot.rag import SourceDocument

EXPECTED_ABSTENTION_EVALUATION_IDS = (
    "EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE",
    "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE",
    "EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP",
    "EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP",
)

EXPECTED_ABSTENTION = {
    "EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE": True,
    "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE": False,
    "EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP": False,
    "EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP": False,
}

FORBIDDEN_MARKERS = (
    "@",
    "api key",
    "bank account",
    "iban",
    "password",
    "tax identifier",
    "secret",
    "credential",
)


def test_library_returns_tuple_with_exact_stable_order() -> None:
    cases = build_synthetic_rag_abstention_evaluation_case_library()
    evaluation_ids = tuple(case.evaluation_id for case in cases)

    assert isinstance(cases, tuple)
    assert len(cases) == 4
    assert evaluation_ids == EXPECTED_ABSTENTION_EVALUATION_IDS
    assert all(isinstance(case, RAGAbstentionEvaluationCase) for case in cases)


def test_library_evaluation_ids_are_unique() -> None:
    evaluation_ids = tuple(
        case.evaluation_id
        for case in build_synthetic_rag_abstention_evaluation_case_library()
    )

    assert len(evaluation_ids) == len(set(evaluation_ids))


def test_library_uses_only_explicitly_synthetic_content() -> None:
    for case in build_synthetic_rag_abstention_evaluation_case_library():
        combined_text = " ".join(
            (
                case.evaluation_id,
                case.intake.case_id,
                case.intake.client_ref,
                case.intake.scenario,
                case.retrieval_query,
                *(document.document_id for document in case.intake.documents),
                *(document.label for document in case.intake.documents),
                *(document.document_id for document in case.source_documents),
                *(document.title for document in case.source_documents),
                *(document.content for document in case.source_documents),
            )
        ).lower()

        assert case.evaluation_id.startswith("EVAL_RAG_ABSTENTION_BASELINE_")
        assert all(
            document.document_id.startswith("SYNTHETIC_RAG_ABSTENTION_")
            for document in case.source_documents
        )
        assert all(
            document.title.startswith("Synthetic ")
            for document in case.source_documents
        )
        assert all(
            document.content.startswith("Synthetic ")
            or document.content.startswith("Prefix. Synthetic ")
            for document in case.source_documents
        )
        assert all(
            forbidden_marker not in combined_text
            for forbidden_marker in FORBIDDEN_MARKERS
        )


def test_separate_library_builds_share_no_case_or_nested_instances() -> None:
    first_library = build_synthetic_rag_abstention_evaluation_case_library()
    second_library = build_synthetic_rag_abstention_evaluation_case_library()

    assert first_library is not second_library
    for first_case, second_case in zip(first_library, second_library, strict=True):
        assert first_case is not second_case
        assert first_case.intake is not second_case.intake
        assert first_case.source_documents is not second_case.source_documents
        for first_document, second_document in zip(
            first_case.source_documents,
            second_case.source_documents,
            strict=True,
        ):
            assert first_document is not second_document
            assert isinstance(first_document, SourceDocument)
            assert isinstance(second_document, SourceDocument)


def test_all_baseline_cases_run_and_assess_with_exact_expectation() -> None:
    for case in build_synthetic_rag_abstention_evaluation_case_library():
        provider = _provider_for_case(case)
        result = run_offline_rag_abstention_evaluation_case(case, provider=provider)
        assessment = assess_rag_abstention_evaluation_run_result(result)

        assert result.evaluation_case is case
        assert assessment.evaluation_run_result is result
        assert case.expected_abstained_for_missing_evidence is (
            EXPECTED_ABSTENTION[case.evaluation_id]
        )
        assert result.observed_abstained_for_missing_evidence is (
            EXPECTED_ABSTENTION[case.evaluation_id]
        )
        assert assessment.abstained_for_missing_evidence_matches is True
        assert assessment.passed is True


def test_missing_evidence_case_abstains_without_provider_call() -> None:
    case = _case("EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE")
    provider = FakeModelProvider(_grounded_model_response(case))

    result = run_offline_rag_abstention_evaluation_case(case, provider=provider)
    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert case.expected_abstained_for_missing_evidence is True
    assert result.observed_abstained_for_missing_evidence is True
    assert provider.requests == ()
    assert assessment.passed is True


def test_with_evidence_case_does_not_abstain_and_calls_provider() -> None:
    case = _case("EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE")
    provider = FakeModelProvider(_grounded_model_response(case))

    result = run_offline_rag_abstention_evaluation_case(case, provider=provider)
    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert case.expected_abstained_for_missing_evidence is False
    assert result.observed_abstained_for_missing_evidence is False
    assert len(provider.requests) == 1
    assert assessment.passed is True
    assert rag_abstention_library.WITH_EVIDENCE_PASSAGE in (
        case.source_documents[0].content
    )


def test_gateway_stop_case_is_not_missing_evidence_abstention() -> None:
    case = _case("EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP")
    provider = FakeModelProvider(_grounded_model_response(case))

    result = run_offline_rag_abstention_evaluation_case(case, provider=provider)
    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert case.intake.missing_items
    assert case.expected_abstained_for_missing_evidence is False
    assert result.observed_abstained_for_missing_evidence is False
    assert provider.requests == ()
    assert assessment.passed is True


def test_review_gate_stop_case_is_not_missing_evidence_abstention() -> None:
    case = _case("EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP")
    provider = FakeModelProvider(_grounded_model_response(case))

    result = run_offline_rag_abstention_evaluation_case(case, provider=provider)
    assessment = assess_rag_abstention_evaluation_run_result(result)

    assert case.intake.mock_risk_signals
    assert case.expected_abstained_for_missing_evidence is False
    assert result.observed_abstained_for_missing_evidence is False
    assert provider.requests == ()
    assert assessment.passed is True


def test_evaluation_package_exports_abstention_library_builder() -> None:
    assert (
        evaluation.build_synthetic_rag_abstention_evaluation_case_library
        is build_synthetic_rag_abstention_evaluation_case_library
    )
    assert (
        "build_synthetic_rag_abstention_evaluation_case_library"
        in evaluation.__all__
    )


def test_existing_evaluation_libraries_remain_unchanged() -> None:
    ai_fixtures = build_synthetic_evaluation_case_library()
    retrieval_cases = build_synthetic_retrieval_evaluation_case_library()
    grounding_cases = build_synthetic_grounding_evaluation_case_library()

    assert isinstance(ai_fixtures, tuple)
    assert len(ai_fixtures) == 7
    assert evaluation.SyntheticEvaluationFixture is SyntheticEvaluationFixture
    assert isinstance(retrieval_cases, tuple)
    assert len(retrieval_cases) == 4
    assert isinstance(grounding_cases, tuple)
    assert len(grounding_cases) == 9


def _case(evaluation_id: str) -> RAGAbstentionEvaluationCase:
    cases = {
        case.evaluation_id: case
        for case in build_synthetic_rag_abstention_evaluation_case_library()
    }
    return cases[evaluation_id]


def _provider_for_case(case: RAGAbstentionEvaluationCase) -> FakeModelProvider:
    return FakeModelProvider(_grounded_model_response(case))


def _grounded_model_response(case: RAGAbstentionEvaluationCase) -> ModelResponse:
    document = case.source_documents[0]
    supporting_text = (
        rag_abstention_library.WITH_EVIDENCE_PASSAGE
        if case.evaluation_id == "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE"
        else document.content
    )
    return ModelResponse(
        content=json.dumps(
            {
                "summary_points": ["Synthetic grounded orchard summary."],
                "uncertainties": ["Synthetic grounded uncertainty."],
                "review_questions": ["Synthetic grounded review question?"],
                "citations": [
                    {
                        "summary_point_index": 0,
                        "document_id": document.document_id,
                        "supporting_text": supporting_text,
                    }
                ],
            }
        ),
        provider_name="fake",
        model_name="fake-model",
    )
