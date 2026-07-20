"""Offline evaluation contracts for synthetic controlled AI workflows."""

from .assessment import EvaluationCaseAssessment, assess_evaluation_run_result
from .case import EvaluationCase, ExpectedAIWorkflowOutcome
from .library import SyntheticEvaluationFixture, build_synthetic_evaluation_case_library
from .report import EvaluationMetricsReport, run_offline_evaluation_suite
from .retrieval_assessment import (
    RetrievalEvaluationCaseAssessment,
    assess_retrieval_evaluation_run_result,
)
from .retrieval_case import RetrievalEvaluationCase
from .retrieval_library import build_synthetic_retrieval_evaluation_case_library
from .retrieval_report import (
    RetrievalEvaluationMetricsReport,
    run_offline_retrieval_evaluation_suite,
)
from .retrieval_runner import (
    RetrievalEvaluationRunResult,
    run_offline_retrieval_evaluation_case,
)
from .runner import EvaluationRunResult, run_offline_evaluation_case

__all__ = [
    "EvaluationCase",
    "EvaluationCaseAssessment",
    "EvaluationMetricsReport",
    "EvaluationRunResult",
    "ExpectedAIWorkflowOutcome",
    "RetrievalEvaluationCase",
    "RetrievalEvaluationCaseAssessment",
    "RetrievalEvaluationMetricsReport",
    "RetrievalEvaluationRunResult",
    "SyntheticEvaluationFixture",
    "assess_evaluation_run_result",
    "assess_retrieval_evaluation_run_result",
    "build_synthetic_evaluation_case_library",
    "build_synthetic_retrieval_evaluation_case_library",
    "run_offline_evaluation_case",
    "run_offline_evaluation_suite",
    "run_offline_retrieval_evaluation_case",
    "run_offline_retrieval_evaluation_suite",
]
