import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    RAGContradictionEvaluationCase,
    build_synthetic_rag_contradiction_evaluation_case_library,
    run_offline_rag_contradiction_evaluation_suite,
)

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_CONTRADICTION_BASELINE_PRESENT",
    "EVAL_RAG_CONTRADICTION_BASELINE_ABSENT",
    "EVAL_RAG_CONTRADICTION_BASELINE_SAME_VALUE",
    "EVAL_RAG_CONTRADICTION_BASELINE_MULTI_KEY",
)


def test_library_has_exactly_four_cases_with_expected_ids() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert len(cases) == 4
    assert tuple(case.evaluation_id for case in cases) == EXPECTED_BASELINE_EVALUATION_IDS
    assert all(isinstance(case, RAGContradictionEvaluationCase) for case in cases)


def test_library_cases_have_expected_positive_and_negative_labels() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert tuple(case.expected_contradiction_present for case in cases) == (
        True,
        False,
        False,
        True,
    )
    assert tuple(len(case.contradicting_passages) for case in cases) == (2, 0, 0, 2)


def test_contradiction_suite_passes_without_model_provider() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert report.total_case_count == 4
    assert report.passed_case_count == 4
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
