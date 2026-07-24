import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_contradiction_library as library_module
from steuerberater_copilot.evaluation import (
    RAGContradictionEvaluationCase,
    assess_rag_contradiction_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    build_synthetic_grounding_evaluation_case_library,
    build_synthetic_rag_abstention_evaluation_case_library,
    build_synthetic_rag_contradiction_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_rag_contradiction_evaluation_case,
)
from steuerberater_copilot.rag import SourceDocument

EXPECTED_CONTRADICTION_EVALUATION_IDS = (
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_VALUES",
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_AFFIRM_NEGATION",
    "EVAL_RAG_CONTRADICTION_BASELINE_SUBJECT_SCOPE",
    "EVAL_RAG_CONTRADICTION_BASELINE_FILING_DEADLINES",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT",
    "EVAL_RAG_CONTRADICTION_BASELINE_NORMALIZED_RETENTION",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES",
    "EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_HEDGES",
)

EXPECTED_POSITIVE_CLAIM_KEYS = {
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_VALUES": "retention_years",
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_AFFIRM_NEGATION": (
        "retention_years"
    ),
    "EVAL_RAG_CONTRADICTION_BASELINE_SUBJECT_SCOPE": (
        "retention_years::client_alpha"
    ),
    "EVAL_RAG_CONTRADICTION_BASELINE_FILING_DEADLINES": "filing_deadline",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT": "archive_requirement",
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


def test_library_returns_exact_nine_cases_in_stable_order_with_unique_ids() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()
    evaluation_ids = tuple(case.evaluation_id for case in cases)
    document_ids = tuple(
        document.document_id
        for case in cases
        for document in case.source_documents
    )

    assert isinstance(cases, tuple)
    assert len(cases) == 9
    assert evaluation_ids == EXPECTED_CONTRADICTION_EVALUATION_IDS
    assert len(evaluation_ids) == len(set(evaluation_ids))
    assert len(document_ids) == len(set(document_ids))
    assert all(isinstance(case, RAGContradictionEvaluationCase) for case in cases)


def test_library_has_expected_positive_and_negative_distribution() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()
    expected_flags = tuple(
        case.expected_contradiction_present
        for case in cases
    )

    assert expected_flags == (True, True, True, True, True, False, False, False, False)
    assert sum(expected_flags) == 5
    for case in cases:
        if case.expected_contradiction_present:
            assert len(case.contradicting_passages) == 2
        else:
            assert case.contradicting_passages == ()


def test_library_cases_keep_structurally_exact_ground_truth() -> None:
    for case in build_synthetic_rag_contradiction_evaluation_case_library():
        documents_by_id = {
            document.document_id: document for document in case.source_documents
        }

        assert len(case.source_documents) == 2
        assert all(
            isinstance(document, SourceDocument)
            for document in case.source_documents
        )
        for label in case.contradicting_passages:
            assert label.document_id in documents_by_id
            assert label.supporting_text in documents_by_id[label.document_id].content


def test_library_uses_only_explicitly_synthetic_content() -> None:
    for case in build_synthetic_rag_contradiction_evaluation_case_library():
        combined_text = " ".join(
            (
                case.evaluation_id,
                *(document.document_id for document in case.source_documents),
                *(document.title for document in case.source_documents),
                *(document.content for document in case.source_documents),
            )
        ).lower()

        assert case.evaluation_id.startswith("EVAL_RAG_CONTRADICTION_BASELINE_")
        assert all(
            document.document_id.startswith("SYNTHETIC_RAG_CONTRADICTION_")
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


def test_all_library_cases_run_deterministically_and_pass_assessment() -> None:
    for case in build_synthetic_rag_contradiction_evaluation_case_library():
        first_result = run_offline_rag_contradiction_evaluation_case(case)
        second_result = run_offline_rag_contradiction_evaluation_case(case)
        assessment = assess_rag_contradiction_evaluation_run_result(first_result)

        assert first_result == second_result
        assert first_result.evaluation_case is case
        assert assessment.evaluation_run_result is first_result
        assert assessment.contradiction_present_matches is True
        assert assessment.contradiction_evidence_matches is True
        assert assessment.passed is True

        if case.expected_contradiction_present:
            contradictions = first_result.observed_detection_result.contradictions
            assert len(contradictions) == 1
            assert (
                contradictions[0].claim_key
                == EXPECTED_POSITIVE_CLAIM_KEYS[case.evaluation_id]
            )
        else:
            assert first_result.observed_detection_result.contradictions == ()


def test_separate_library_builds_share_no_case_label_or_document_instances() -> None:
    first_library = build_synthetic_rag_contradiction_evaluation_case_library()
    second_library = build_synthetic_rag_contradiction_evaluation_case_library()

    assert first_library == second_library
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
        for first_label, second_label in zip(
            first_case.contradicting_passages,
            second_case.contradicting_passages,
            strict=True,
        ):
            assert first_label is not second_label


def test_evaluation_package_exports_contradiction_library_builder() -> None:
    assert (
        evaluation.build_synthetic_rag_contradiction_evaluation_case_library
        is build_synthetic_rag_contradiction_evaluation_case_library
    )
    assert evaluation.build_synthetic_rag_contradiction_evaluation_case_library is (
        library_module.build_synthetic_rag_contradiction_evaluation_case_library
    )
    assert (
        "build_synthetic_rag_contradiction_evaluation_case_library"
        in evaluation.__all__
    )


def test_stable_synthetic_evaluation_libraries_total_thirty_three_cases() -> None:
    ai_fixtures = build_synthetic_evaluation_case_library()
    retrieval_cases = build_synthetic_retrieval_evaluation_case_library()
    grounding_cases = build_synthetic_grounding_evaluation_case_library()
    abstention_cases = build_synthetic_rag_abstention_evaluation_case_library()
    contradiction_cases = build_synthetic_rag_contradiction_evaluation_case_library()
    all_evaluation_ids = (
        tuple(fixture.evaluation_case.evaluation_id for fixture in ai_fixtures)
        + tuple(case.evaluation_id for case in retrieval_cases)
        + tuple(case.evaluation_id for case in grounding_cases)
        + tuple(case.evaluation_id for case in abstention_cases)
        + tuple(case.evaluation_id for case in contradiction_cases)
    )

    assert tuple(
        len(library)
        for library in (
            ai_fixtures,
            retrieval_cases,
            grounding_cases,
            abstention_cases,
            contradiction_cases,
        )
    ) == (7, 4, 9, 4, 9)
    assert len(all_evaluation_ids) == 33
    assert len(all_evaluation_ids) == len(set(all_evaluation_ids))
