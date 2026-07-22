import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    build_synthetic_rag_freshness_evaluation_case_library,
    run_offline_rag_freshness_evaluation_suite,
)

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_FRESHNESS_BASELINE_SUPERSEDED",
    "EVAL_RAG_FRESHNESS_BASELINE_EXPIRED",
    "EVAL_RAG_FRESHNESS_BASELINE_CURRENT",
    "EVAL_RAG_FRESHNESS_BASELINE_MIXED",
)


def test_library_has_exactly_four_cases_with_expected_ids() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    assert len(cases) == 4
    assert tuple(case.evaluation_id for case in cases) == EXPECTED_BASELINE_EVALUATION_IDS
    assert all(isinstance(case, RAGFreshnessEvaluationCase) for case in cases)


def test_library_cases_have_expected_outdated_document_ids() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    assert tuple(case.expected_outdated_document_ids for case in cases) == (
        ("SYNTHETIC_FRESHNESS_SUPERSEDED_V1",),
        ("SYNTHETIC_FRESHNESS_EXPIRED_NOTICE",),
        (),
        (
            "SYNTHETIC_FRESHNESS_MIXED_EXPIRED",
            "SYNTHETIC_FRESHNESS_MIXED_OLD",
        ),
    )


def test_freshness_suite_passes_without_model_provider() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    report = run_offline_rag_freshness_evaluation_suite(cases)

    assert report.total_case_count == 4
    assert report.passed_case_count == 4
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()


def test_evaluation_package_exports_freshness_library_contract() -> None:
    assert (
        evaluation.build_synthetic_rag_freshness_evaluation_case_library
        is build_synthetic_rag_freshness_evaluation_case_library
    )
    assert "build_synthetic_rag_freshness_evaluation_case_library" in evaluation.__all__
