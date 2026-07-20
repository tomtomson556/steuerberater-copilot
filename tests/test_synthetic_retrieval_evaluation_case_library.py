import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RetrievalEvaluationCase,
    SyntheticEvaluationFixture,
    assess_retrieval_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_retrieval_evaluation_case,
)
from steuerberater_copilot.rag import SourceDocument

EXPECTED_RETRIEVAL_EVALUATION_IDS = (
    "EVAL_RETRIEVAL_BASELINE_FULL_RECALL",
    "EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL",
    "EVAL_RETRIEVAL_BASELINE_ZERO_RECALL",
    "EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE",
)

EXPECTED_RETRIEVED_DOCUMENT_IDS = {
    "EVAL_RETRIEVAL_BASELINE_FULL_RECALL": (
        "SYNTHETIC_RETRIEVAL_FULL_RELEVANT_ALPHA",
        "SYNTHETIC_RETRIEVAL_FULL_RELEVANT_BETA",
    ),
    "EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL": (
        "SYNTHETIC_RETRIEVAL_PARTIAL_RELEVANT_STRONG",
    ),
    "EVAL_RETRIEVAL_BASELINE_ZERO_RECALL": (
        "SYNTHETIC_RETRIEVAL_ZERO_IRRELEVANT",
    ),
    "EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE": (),
}

EXPECTED_RECALL_AT_K = {
    "EVAL_RETRIEVAL_BASELINE_FULL_RECALL": 1.0,
    "EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL": 0.5,
    "EVAL_RETRIEVAL_BASELINE_ZERO_RECALL": 0.0,
    "EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE": None,
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
    cases = build_synthetic_retrieval_evaluation_case_library()
    evaluation_ids = tuple(case.evaluation_id for case in cases)

    assert isinstance(cases, tuple)
    assert len(cases) == 4
    assert evaluation_ids == EXPECTED_RETRIEVAL_EVALUATION_IDS
    assert all(isinstance(case, RetrievalEvaluationCase) for case in cases)


def test_library_evaluation_ids_are_unique() -> None:
    evaluation_ids = tuple(
        case.evaluation_id
        for case in build_synthetic_retrieval_evaluation_case_library()
    )

    assert len(evaluation_ids) == len(set(evaluation_ids))


def test_library_uses_only_explicitly_synthetic_content() -> None:
    for case in build_synthetic_retrieval_evaluation_case_library():
        combined_text = " ".join(
            (
                case.evaluation_id,
                case.retrieval_query,
                *case.relevant_document_ids,
                *(document.document_id for document in case.source_documents),
                *(document.title for document in case.source_documents),
                *(document.content for document in case.source_documents),
            )
        ).lower()

        assert case.evaluation_id.startswith("EVAL_RETRIEVAL_BASELINE_")
        assert all(
            document.document_id.startswith("SYNTHETIC_RETRIEVAL_")
            for document in case.source_documents
        )
        assert all(
            document.title.startswith("Synthetic ")
            for document in case.source_documents
        )
        assert all(
            document.content.startswith("Synthetic ")
            for document in case.source_documents
        )
        assert all(
            forbidden_marker not in combined_text
            for forbidden_marker in FORBIDDEN_MARKERS
        )


def test_separate_library_builds_share_no_case_or_document_instances() -> None:
    first_library = build_synthetic_retrieval_evaluation_case_library()
    second_library = build_synthetic_retrieval_evaluation_case_library()

    assert first_library is not second_library
    for first_case, second_case in zip(first_library, second_library, strict=True):
        assert first_case is not second_case
        assert first_case.source_documents is not second_case.source_documents
        for first_document, second_document in zip(
            first_case.source_documents,
            second_case.source_documents,
            strict=True,
        ):
            assert first_document is not second_document
            assert isinstance(first_document, SourceDocument)
            assert isinstance(second_document, SourceDocument)


def test_all_baseline_cases_run_and_assess_with_exact_recall() -> None:
    for case in build_synthetic_retrieval_evaluation_case_library():
        result = run_offline_retrieval_evaluation_case(case)
        assessment = assess_retrieval_evaluation_run_result(result)
        retrieved_ids = tuple(
            document.document_id for document in result.retrieved_documents
        )

        assert result.evaluation_case is case
        assert assessment.evaluation_run_result is result
        assert retrieved_ids == EXPECTED_RETRIEVED_DOCUMENT_IDS[case.evaluation_id]
        assert assessment.recall_at_k == EXPECTED_RECALL_AT_K[case.evaluation_id]
        assert not hasattr(assessment, "passed")
        assert not hasattr(assessment, "abstained")
        assert not hasattr(assessment, "abstention")


def test_no_evidence_case_returns_no_retrieval_hits() -> None:
    cases = {
        case.evaluation_id: case
        for case in build_synthetic_retrieval_evaluation_case_library()
    }
    no_evidence_case = cases["EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE"]

    result = run_offline_retrieval_evaluation_case(no_evidence_case)
    assessment = assess_retrieval_evaluation_run_result(result)

    assert no_evidence_case.relevant_document_ids == ()
    assert result.retrieved_documents == ()
    assert assessment.recalled_document_ids_at_k == ()
    assert assessment.recall_at_k is None


def test_evaluation_package_exports_retrieval_library_contract() -> None:
    assert (
        evaluation.build_synthetic_retrieval_evaluation_case_library
        is build_synthetic_retrieval_evaluation_case_library
    )
    assert (
        "build_synthetic_retrieval_evaluation_case_library" in evaluation.__all__
    )


def test_existing_ai_evaluation_case_library_remains_unchanged() -> None:
    fixtures = build_synthetic_evaluation_case_library()
    evaluation_ids = tuple(
        fixture.evaluation_case.evaluation_id for fixture in fixtures
    )

    assert isinstance(fixtures, tuple)
    assert len(fixtures) == 7
    assert evaluation_ids == (
        "EVAL_BASELINE_GATEWAY_BLOCK",
        "EVAL_BASELINE_GATEWAY_ESCALATION",
        "EVAL_BASELINE_REVIEW_GATE_STOP",
        "EVAL_BASELINE_STRUCTURED_DRAFT",
        "EVAL_BASELINE_PROVIDER_ERROR",
        "EVAL_BASELINE_PARSE_ERROR",
        "EVAL_BASELINE_VALIDATION_ERROR",
    )
    assert evaluation.SyntheticEvaluationFixture is SyntheticEvaluationFixture
    assert (
        evaluation.build_synthetic_evaluation_case_library
        is build_synthetic_evaluation_case_library
    )
    assert "SyntheticEvaluationFixture" in evaluation.__all__
    assert "build_synthetic_evaluation_case_library" in evaluation.__all__
