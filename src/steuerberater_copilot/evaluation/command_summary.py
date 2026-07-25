"""Deterministic summary and JSON serialization for the evaluation CLI."""

from __future__ import annotations

import json
from typing import Any

from steuerberater_copilot.ai import FakeModelProvider, ModelResponse

from .grounding_library import build_synthetic_grounding_evaluation_case_library
from .grounding_report import (
    GroundingEvaluationMetricsReport,
    run_offline_grounding_evaluation_suite,
)
from .library import build_synthetic_evaluation_case_library
from .rag_abstention_case import RAGAbstentionEvaluationCase
from .rag_abstention_library import (
    WITH_EVIDENCE_PASSAGE,
    build_synthetic_rag_abstention_evaluation_case_library,
)
from .rag_abstention_report import (
    RAGAbstentionEvaluationMetricsReport,
    run_offline_rag_abstention_evaluation_suite,
)
from .rag_contradiction_library import (
    build_synthetic_rag_contradiction_evaluation_case_library,
)
from .rag_contradiction_report import (
    RAGContradictionEvaluationMetricsReport,
    run_offline_rag_contradiction_evaluation_suite,
)
from .rag_freshness_library import (
    build_synthetic_rag_freshness_evaluation_case_library,
)
from .rag_freshness_report import (
    RAGFreshnessEvaluationMetricsReport,
    run_offline_rag_freshness_evaluation_suite,
)
from .report import EvaluationMetricsReport, run_offline_evaluation_suite
from .retrieval_library import build_synthetic_retrieval_evaluation_case_library
from .retrieval_report import (
    RetrievalEvaluationMetricsReport,
    run_offline_retrieval_evaluation_suite,
)

SCHEMA_VERSION = 1

SUITE_ID_AI_WORKFLOW = "ai_workflow"
SUITE_ID_RETRIEVAL = "retrieval"
SUITE_ID_GROUNDING = "grounding"
SUITE_ID_RAG_ABSTENTION = "rag_abstention"
SUITE_ID_RAG_CONTRADICTION = "rag_contradiction"
SUITE_ID_RAG_FRESHNESS = "rag_freshness"

_WITH_EVIDENCE_EVALUATION_ID = "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE"


def build_evaluation_command_summary() -> dict[str, Any]:
    """Run all synthetic suites and return the stable CLI summary payload."""
    suites = (
        _ai_workflow_suite_summary(),
        _retrieval_suite_summary(),
        _grounding_suite_summary(),
        _rag_abstention_suite_summary(),
        _rag_contradiction_suite_summary(),
        _rag_freshness_suite_summary(),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "synthetic_only": True,
        "total_case_count": sum(suite["total_case_count"] for suite in suites),
        "suites": list(suites),
    }


def serialize_evaluation_command_summary(summary: dict[str, Any]) -> str:
    """Serialize a summary payload as deterministic UTF-8 JSON text."""
    return json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)


def evaluation_metrics_report_to_summary(
    report: EvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_AI_WORKFLOW,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "passed_case_count": report.passed_case_count,
        "failed_case_count": report.failed_case_count,
        "pass_rate": report.pass_rate,
        "failed_evaluation_ids": list(report.failed_evaluation_ids),
        "gateway_decision_match_rate": report.gateway_decision_match_rate,
        "review_gate_status_match_rate": report.review_gate_status_match_rate,
        "outcome_match_rate": report.outcome_match_rate,
        "provider_call_count_match_rate": report.provider_call_count_match_rate,
        "structured_draft_case_count": report.structured_draft_case_count,
        "structured_draft_match_rate": report.structured_draft_match_rate,
        "total_provider_call_count": report.total_provider_call_count,
        "unexpected_provider_call_count": report.unexpected_provider_call_count,
    }


def retrieval_metrics_report_to_summary(
    report: RetrievalEvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_RETRIEVAL,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "applicable_recall_case_count": report.applicable_recall_case_count,
        "inapplicable_recall_case_count": report.inapplicable_recall_case_count,
        "mean_recall_at_k": report.mean_recall_at_k,
    }


def grounding_metrics_report_to_summary(
    report: GroundingEvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_GROUNDING,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "applicable_citation_coverage_case_count": (
            report.applicable_citation_coverage_case_count
        ),
        "inapplicable_citation_coverage_case_count": (
            report.inapplicable_citation_coverage_case_count
        ),
        "mean_citation_coverage": report.mean_citation_coverage,
        "applicable_source_match_case_count": report.applicable_source_match_case_count,
        "inapplicable_source_match_case_count": (
            report.inapplicable_source_match_case_count
        ),
        "mean_source_match_rate": report.mean_source_match_rate,
        "applicable_passage_match_case_count": (
            report.applicable_passage_match_case_count
        ),
        "inapplicable_passage_match_case_count": (
            report.inapplicable_passage_match_case_count
        ),
        "mean_passage_match_rate": report.mean_passage_match_rate,
        "applicable_unsupported_summary_point_case_count": (
            report.applicable_unsupported_summary_point_case_count
        ),
        "inapplicable_unsupported_summary_point_case_count": (
            report.inapplicable_unsupported_summary_point_case_count
        ),
        "mean_unsupported_summary_point_rate": (
            report.mean_unsupported_summary_point_rate
        ),
    }


def rag_abstention_metrics_report_to_summary(
    report: RAGAbstentionEvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_RAG_ABSTENTION,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "passed_case_count": report.passed_case_count,
        "failed_case_count": report.failed_case_count,
        "pass_rate": report.pass_rate,
        "failed_evaluation_ids": list(report.failed_evaluation_ids),
        "expected_missing_evidence_case_count": (
            report.expected_missing_evidence_case_count
        ),
        "missing_evidence_abstention_rate": report.missing_evidence_abstention_rate,
        "false_negative_case_count": report.false_negative_case_count,
        "false_positive_case_count": report.false_positive_case_count,
    }


def rag_contradiction_metrics_report_to_summary(
    report: RAGContradictionEvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_RAG_CONTRADICTION,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "passed_case_count": report.passed_case_count,
        "failed_case_count": report.failed_case_count,
        "pass_rate": report.pass_rate,
        "failed_evaluation_ids": list(report.failed_evaluation_ids),
        "expected_contradiction_case_count": report.expected_contradiction_case_count,
        "contradiction_detection_rate": report.contradiction_detection_rate,
        "false_negative_case_count": report.false_negative_case_count,
        "false_positive_case_count": report.false_positive_case_count,
    }


def rag_freshness_metrics_report_to_summary(
    report: RAGFreshnessEvaluationMetricsReport,
    *,
    suite_id: str = SUITE_ID_RAG_FRESHNESS,
) -> dict[str, Any]:
    return {
        "suite_id": suite_id,
        "total_case_count": report.total_case_count,
        "passed_case_count": report.passed_case_count,
        "failed_case_count": report.failed_case_count,
        "pass_rate": report.pass_rate,
        "failed_evaluation_ids": list(report.failed_evaluation_ids),
        "current_document_retrieval_rate": report.current_document_retrieval_rate,
        "stale_document_retrieval_rate": report.stale_document_retrieval_rate,
        "missing_current_document_case_count": (
            report.missing_current_document_case_count
        ),
        "stale_document_retrieval_case_count": (
            report.stale_document_retrieval_case_count
        ),
    }


def _ai_workflow_suite_summary() -> dict[str, Any]:
    report = run_offline_evaluation_suite(build_synthetic_evaluation_case_library())
    return evaluation_metrics_report_to_summary(report)


def _retrieval_suite_summary() -> dict[str, Any]:
    report = run_offline_retrieval_evaluation_suite(
        build_synthetic_retrieval_evaluation_case_library()
    )
    return retrieval_metrics_report_to_summary(report)


def _grounding_suite_summary() -> dict[str, Any]:
    report = run_offline_grounding_evaluation_suite(
        build_synthetic_grounding_evaluation_case_library()
    )
    return grounding_metrics_report_to_summary(report)


def _rag_abstention_suite_summary() -> dict[str, Any]:
    report = run_offline_rag_abstention_evaluation_suite(
        build_synthetic_rag_abstention_evaluation_case_library(),
        provider_factory=_rag_abstention_provider_factory,
    )
    return rag_abstention_metrics_report_to_summary(report)


def _rag_contradiction_suite_summary() -> dict[str, Any]:
    report = run_offline_rag_contradiction_evaluation_suite(
        build_synthetic_rag_contradiction_evaluation_case_library()
    )
    return rag_contradiction_metrics_report_to_summary(report)


def _rag_freshness_suite_summary() -> dict[str, Any]:
    report = run_offline_rag_freshness_evaluation_suite(
        build_synthetic_rag_freshness_evaluation_case_library()
    )
    return rag_freshness_metrics_report_to_summary(report)


def _rag_abstention_provider_factory(
    evaluation_case: RAGAbstentionEvaluationCase,
) -> FakeModelProvider:
    """Build a fresh FakeModelProvider for one synthetic abstention case."""
    return FakeModelProvider(_rag_abstention_model_response(evaluation_case))


def _rag_abstention_model_response(
    evaluation_case: RAGAbstentionEvaluationCase,
) -> ModelResponse:
    document = evaluation_case.source_documents[0]
    supporting_text = (
        WITH_EVIDENCE_PASSAGE
        if evaluation_case.evaluation_id == _WITH_EVIDENCE_EVALUATION_ID
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
