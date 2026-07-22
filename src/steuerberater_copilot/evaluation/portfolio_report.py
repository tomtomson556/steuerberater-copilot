"""Aggregate offline evaluation baseline across all synthetic suites."""

from __future__ import annotations

import json
from dataclasses import dataclass

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
from .rag_freshness_library import build_synthetic_rag_freshness_evaluation_case_library
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


@dataclass(frozen=True, slots=True)
class PortfolioEvaluationBaselineReport:
    """Immutable aggregate baseline across the synthetic offline evaluation suites.

    Workflow, abstention, contradiction, and freshness suites expose binary pass
    rates. Retrieval and grounding remain metric suites without invented
    pass/fail thresholds. This report is a portfolio and regression artifact,
    not productive evaluation or steuerliche Qualitaetsaussage.
    """

    workflow: EvaluationMetricsReport
    retrieval: RetrievalEvaluationMetricsReport
    grounding: GroundingEvaluationMetricsReport
    abstention: RAGAbstentionEvaluationMetricsReport
    contradiction: RAGContradictionEvaluationMetricsReport
    freshness: RAGFreshnessEvaluationMetricsReport

    @property
    def total_case_count(self) -> int:
        return (
            self.workflow.total_case_count
            + self.retrieval.total_case_count
            + self.grounding.total_case_count
            + self.abstention.total_case_count
            + self.contradiction.total_case_count
            + self.freshness.total_case_count
        )

    @property
    def binary_suite_case_count(self) -> int:
        return (
            self.workflow.total_case_count
            + self.abstention.total_case_count
            + self.contradiction.total_case_count
            + self.freshness.total_case_count
        )

    @property
    def binary_suite_passed_case_count(self) -> int:
        return (
            self.workflow.passed_case_count
            + self.abstention.passed_case_count
            + self.contradiction.passed_case_count
            + self.freshness.passed_case_count
        )

    @property
    def binary_suite_pass_rate(self) -> float:
        return self.binary_suite_passed_case_count / self.binary_suite_case_count

    @property
    def suite_summaries(self) -> dict[str, dict[str, object]]:
        return {
            "workflow": {
                "case_count": self.workflow.total_case_count,
                "pass_rate": self.workflow.pass_rate,
            },
            "retrieval": {
                "case_count": self.retrieval.total_case_count,
                "mean_recall_at_k": self.retrieval.mean_recall_at_k,
            },
            "grounding": {
                "case_count": self.grounding.total_case_count,
                "mean_citation_coverage": self.grounding.mean_citation_coverage,
                "mean_source_match_rate": self.grounding.mean_source_match_rate,
                "mean_passage_match_rate": self.grounding.mean_passage_match_rate,
                "mean_unsupported_summary_point_rate": (
                    self.grounding.mean_unsupported_summary_point_rate
                ),
            },
            "abstention": {
                "case_count": self.abstention.total_case_count,
                "pass_rate": self.abstention.pass_rate,
                "missing_evidence_abstention_rate": (
                    self.abstention.missing_evidence_abstention_rate
                ),
            },
            "contradiction": {
                "case_count": self.contradiction.total_case_count,
                "pass_rate": self.contradiction.pass_rate,
                "contradiction_detection_rate": (
                    self.contradiction.contradiction_detection_rate
                ),
            },
            "freshness": {
                "case_count": self.freshness.total_case_count,
                "pass_rate": self.freshness.pass_rate,
                "outdated_detection_rate": self.freshness.outdated_detection_rate,
            },
        }


def build_portfolio_evaluation_baseline_report() -> PortfolioEvaluationBaselineReport:
    """Run every synthetic offline evaluation suite with fixture providers."""
    return PortfolioEvaluationBaselineReport(
        workflow=run_offline_evaluation_suite(
            build_synthetic_evaluation_case_library()
        ),
        retrieval=run_offline_retrieval_evaluation_suite(
            build_synthetic_retrieval_evaluation_case_library()
        ),
        grounding=run_offline_grounding_evaluation_suite(
            build_synthetic_grounding_evaluation_case_library()
        ),
        abstention=run_offline_rag_abstention_evaluation_suite(
            build_synthetic_rag_abstention_evaluation_case_library(),
            provider_factory=_abstention_provider_factory,
        ),
        contradiction=run_offline_rag_contradiction_evaluation_suite(
            build_synthetic_rag_contradiction_evaluation_case_library()
        ),
        freshness=run_offline_rag_freshness_evaluation_suite(
            build_synthetic_rag_freshness_evaluation_case_library()
        ),
    )


def portfolio_evaluation_baseline_to_dict(
    report: PortfolioEvaluationBaselineReport,
) -> dict[str, object]:
    """Serialize the portfolio baseline to a compact JSON-friendly mapping."""
    return {
        "total_case_count": report.total_case_count,
        "binary_suite_case_count": report.binary_suite_case_count,
        "binary_suite_passed_case_count": report.binary_suite_passed_case_count,
        "binary_suite_pass_rate": report.binary_suite_pass_rate,
        "suite_summaries": report.suite_summaries,
        "notes": [
            "Synthetic offline baseline only.",
            "Experiment-branch aggregation; not a main-branch completion claim.",
            "Binary pass rate reflects exact expected/observed agreement on "
            "current deterministic fixtures only.",
            "Contradiction detection uses closed templates, not general NLP.",
            "Freshness uses supersession and validity windows, not past-start=outdated.",
            "Retrieval and grounding remain metric suites without invented pass thresholds.",
            "Not productive evaluation.",
            "Not individual tax advice.",
            "Human Review remains required for tax-relevant drafts.",
        ],
    }


def _abstention_provider_factory(
    evaluation_case: RAGAbstentionEvaluationCase,
) -> FakeModelProvider:
    document = evaluation_case.source_documents[0]
    supporting_text = (
        WITH_EVIDENCE_PASSAGE
        if (
            evaluation_case.evaluation_id
            == "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE"
        )
        else document.content
    )
    return FakeModelProvider(
        ModelResponse(
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
            model_name="fake-portfolio-baseline",
        )
    )
