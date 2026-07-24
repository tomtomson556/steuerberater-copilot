import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_freshness_library as library_module
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    assess_rag_freshness_evaluation_run_result,
    build_synthetic_rag_freshness_evaluation_case_library,
    run_offline_rag_freshness_evaluation_case,
)
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

EXPECTED_FRESHNESS_EVALUATION_IDS = (
    "EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD",
    "EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K",
    "EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR",
    "EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE",
    "EVAL_RAG_FRESHNESS_BASELINE_NORMALIZED_QUERY",
)

EXPECTED_RETRIEVED_DOCUMENT_IDS = {
    "EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD": (
        "SYNTHETIC_RAG_FRESHNESS_CURRENT_AHEAD_CURRENT",
    ),
    "EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K": (
        "SYNTHETIC_RAG_FRESHNESS_OUTSIDE_TOP_K_CURRENT",
    ),
    "EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR": (
        "SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_CURRENT",
        "SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_NEUTRAL",
    ),
    "EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE": (
        "SYNTHETIC_RAG_FRESHNESS_MULTIPLE_CURRENT",
    ),
    "EVAL_RAG_FRESHNESS_BASELINE_NORMALIZED_QUERY": (
        "SYNTHETIC_RAG_FRESHNESS_NORMALIZED_CURRENT",
    ),
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


def test_library_returns_exact_five_cases_in_stable_order_with_unique_ids() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()
    evaluation_ids = tuple(case.evaluation_id for case in cases)
    document_ids = tuple(
        document.document_id
        for case in cases
        for document in case.source_documents
    )

    assert isinstance(cases, tuple)
    assert len(cases) == 5
    assert evaluation_ids == EXPECTED_FRESHNESS_EVALUATION_IDS
    assert len(evaluation_ids) == len(set(evaluation_ids))
    assert len(document_ids) == len(set(document_ids))
    assert all(isinstance(case, RAGFreshnessEvaluationCase) for case in cases)


def test_library_covers_required_current_stale_retrieval_situations() -> None:
    cases = {
        case.evaluation_id: case
        for case in build_synthetic_rag_freshness_evaluation_case_library()
    }

    current_ahead = cases["EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD"]
    current_ahead_result = run_offline_rag_freshness_evaluation_case(current_ahead)
    current_ahead_full_ranking = LocalDocumentRetriever(
        current_ahead.source_documents
    ).retrieve(
        current_ahead.retrieval_query,
        top_k=len(current_ahead.source_documents),
    )
    assert current_ahead.source_documents[0].document_id in (
        current_ahead.stale_document_ids
    )
    assert tuple(
        document.document_id for document in current_ahead_full_ranking
    ) == (
        current_ahead.expected_current_document_id,
        *current_ahead.stale_document_ids,
    )
    assert current_ahead_result.retrieved_documents == current_ahead_full_ranking[:1]

    outside_top_k = cases["EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K"]
    outside_top_k_result = run_offline_rag_freshness_evaluation_case(outside_top_k)
    outside_top_k_full_ranking = LocalDocumentRetriever(
        outside_top_k.source_documents
    ).retrieve(
        outside_top_k.retrieval_query,
        top_k=len(outside_top_k.source_documents),
    )
    assert outside_top_k.top_k == 1
    assert outside_top_k_full_ranking[1].document_id in (
        outside_top_k.stale_document_ids
    )
    assert all(
        document.document_id not in outside_top_k.stale_document_ids
        for document in outside_top_k_result.retrieved_documents
    )

    neutral_distractor = cases[
        "EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR"
    ]
    neutral_result = run_offline_rag_freshness_evaluation_case(neutral_distractor)
    assert neutral_result.retrieved_documents[1].document_id == (
        "SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_NEUTRAL"
    )
    assert neutral_result.retrieved_documents[1].document_id not in (
        neutral_distractor.stale_document_ids
    )

    multiple_stale = cases["EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE"]
    multiple_stale_full_ranking = LocalDocumentRetriever(
        multiple_stale.source_documents
    ).retrieve(
        multiple_stale.retrieval_query,
        top_k=len(multiple_stale.source_documents),
    )
    assert len(multiple_stale.stale_document_ids) == 3
    assert multiple_stale_full_ranking[0].document_id == (
        multiple_stale.expected_current_document_id
    )
    assert {
        document.document_id for document in multiple_stale_full_ranking[1:]
    } == set(multiple_stale.stale_document_ids)


def test_library_uses_only_explicitly_synthetic_content() -> None:
    for case in build_synthetic_rag_freshness_evaluation_case_library():
        combined_text = " ".join(
            (
                case.evaluation_id,
                case.retrieval_query,
                *(document.document_id for document in case.source_documents),
                *(document.title for document in case.source_documents),
                *(document.content for document in case.source_documents),
            )
        ).lower()

        assert case.evaluation_id.startswith("EVAL_RAG_FRESHNESS_BASELINE_")
        assert all(
            document.document_id.startswith("SYNTHETIC_RAG_FRESHNESS_")
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
    first_library = build_synthetic_rag_freshness_evaluation_case_library()
    second_library = build_synthetic_rag_freshness_evaluation_case_library()

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
            assert isinstance(first_document, SourceDocument)
            assert isinstance(second_document, SourceDocument)
            assert first_document is not second_document


def test_all_library_cases_run_deterministically_and_pass_assessment() -> None:
    for case in build_synthetic_rag_freshness_evaluation_case_library():
        first_result = run_offline_rag_freshness_evaluation_case(case)
        second_result = run_offline_rag_freshness_evaluation_case(case)
        assessment = assess_rag_freshness_evaluation_run_result(first_result)

        retrieved_document_ids = tuple(
            document.document_id for document in first_result.retrieved_documents
        )
        assert first_result == second_result
        assert first_result.evaluation_case is case
        assert retrieved_document_ids == EXPECTED_RETRIEVED_DOCUMENT_IDS[
            case.evaluation_id
        ]
        assert assessment.evaluation_run_result is first_result
        assert assessment.current_document_retrieved is True
        assert assessment.retrieved_stale_document_ids == ()
        assert assessment.stale_document_retrieved is False
        assert assessment.passed is True


def test_evaluation_package_exports_freshness_library_builder() -> None:
    assert evaluation.build_synthetic_rag_freshness_evaluation_case_library is (
        build_synthetic_rag_freshness_evaluation_case_library
    )
    assert evaluation.build_synthetic_rag_freshness_evaluation_case_library is (
        library_module.build_synthetic_rag_freshness_evaluation_case_library
    )
    assert (
        "build_synthetic_rag_freshness_evaluation_case_library"
        in evaluation.__all__
    )
