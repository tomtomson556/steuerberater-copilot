import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGContradictionEvaluationCase,
    build_synthetic_rag_contradiction_evaluation_case_library,
    run_offline_rag_contradiction_evaluation_suite,
)

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT",
    "EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP",
    "EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE",
    "EVAL_RAG_CONTRADICTION_BASELINE_DEADLINE_CONFLICT",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES_SAME_NUMBER",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT_CONFLICT",
    "EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED",
)


def test_library_has_exactly_seven_cases_with_expected_ids() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert len(cases) == 7
    assert tuple(case.evaluation_id for case in cases) == EXPECTED_BASELINE_EVALUATION_IDS
    assert all(isinstance(case, RAGContradictionEvaluationCase) for case in cases)


def test_library_cases_have_expected_positive_and_negative_labels() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert tuple(case.expected_contradiction_present for case in cases) == (
        True,
        False,
        False,
        True,
        False,
        True,
        False,
    )
    assert tuple(len(case.contradicting_passages) for case in cases) == (
        2,
        0,
        0,
        2,
        0,
        2,
        0,
    )


def test_contradiction_suite_passes_without_model_provider() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert report.total_case_count == 7
    assert report.passed_case_count == 7
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()


def test_evaluation_package_exports_contradiction_library_contract() -> None:
    assert (
        evaluation.build_synthetic_rag_contradiction_evaluation_case_library
        is build_synthetic_rag_contradiction_evaluation_case_library
    )
    assert (
        "build_synthetic_rag_contradiction_evaluation_case_library"
        in evaluation.__all__
    )
