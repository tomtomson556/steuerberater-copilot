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
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
    "EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_SCOPES",
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_NEGATION",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_NOT_REQUIRED",
    "EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED",
    "EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE",
)


def test_library_has_exactly_nine_cases_with_expected_ids() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert len(cases) == 9
    assert tuple(case.evaluation_id for case in cases) == EXPECTED_BASELINE_EVALUATION_IDS
    assert all(isinstance(case, RAGContradictionEvaluationCase) for case in cases)


def test_library_cases_have_expected_positive_and_negative_labels() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    assert tuple(case.expected_contradiction_present for case in cases) == (
        True,
        False,
        False,
        False,
        False,
        True,
        True,
        False,
        True,
    )
    assert tuple(len(case.contradicting_passages) for case in cases) == (
        2,
        0,
        0,
        0,
        0,
        2,
        2,
        0,
        2,
    )


def test_contradiction_suite_records_known_limitation_failure() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert report.total_case_count == 9
    assert report.passed_case_count == 8
    assert report.failed_case_count == 1
    assert report.pass_rate == 8 / 9
    assert report.failed_evaluation_ids == (
        "EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE",
    )


def test_evaluation_package_exports_contradiction_library_contract() -> None:
    assert (
        evaluation.build_synthetic_rag_contradiction_evaluation_case_library
        is build_synthetic_rag_contradiction_evaluation_case_library
    )
    assert (
        "build_synthetic_rag_contradiction_evaluation_case_library"
        in evaluation.__all__
    )
