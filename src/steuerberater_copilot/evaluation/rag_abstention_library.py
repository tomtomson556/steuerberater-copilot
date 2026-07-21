"""Deterministic synthetic baseline cases for offline RAG abstention evaluation."""

from __future__ import annotations

from steuerberater_copilot.offline_mvp import IntakeCase, SyntheticDocument
from steuerberater_copilot.offline_mvp.models import MockRiskSignal
from steuerberater_copilot.rag import SourceDocument

from .rag_abstention_case import RAGAbstentionEvaluationCase

MISSING_EVIDENCE_PASSAGE = (
    "Synthetic meadow baseline content without matching query tokens."
)
WITH_EVIDENCE_PASSAGE = (
    "Synthetic orchard passage for abstention baseline with evidence."
)


def build_synthetic_rag_abstention_evaluation_case_library() -> tuple[
    RAGAbstentionEvaluationCase, ...
]:
    """Build the four fresh synthetic RAG abstention baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE``
    2. ``EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE``
    3. ``EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP``
    4. ``EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP``

    Each call returns a new immutable tuple of fresh
    ``RAGAbstentionEvaluationCase``, ``IntakeCase``, and ``SourceDocument``
    instances. Cases are designed for the existing synthetic RAG workflow and
    can be executed with ``run_offline_rag_abstention_evaluation_case`` plus a
    ``FakeModelProvider``, then assessed with
    ``assess_rag_abstention_evaluation_run_result``.
    """
    return (
        _missing_evidence_case(),
        _with_evidence_case(),
        _gateway_stop_case(),
        _review_gate_stop_case(),
    )


def _missing_evidence_case() -> RAGAbstentionEvaluationCase:
    """Controls allow continuation, but retrieval finds no evidence."""
    unrelated = SourceDocument(
        document_id="SYNTHETIC_RAG_ABSTENTION_MISSING_MEADOW",
        title="Synthetic meadow reference",
        content=MISSING_EVIDENCE_PASSAGE,
    )
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE",
        intake=_allowed_intake(case_number="501"),
        source_documents=(unrelated,),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=True,
    )


def _with_evidence_case() -> RAGAbstentionEvaluationCase:
    """Controls allow continuation and retrieval returns matching evidence."""
    match = SourceDocument(
        document_id="SYNTHETIC_RAG_ABSTENTION_WITH_EVIDENCE_ORCHARD",
        title="Synthetic orchard reference",
        content=f"Prefix. {WITH_EVIDENCE_PASSAGE} Suffix.",
    )
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE",
        intake=_allowed_intake(case_number="502"),
        source_documents=(match,),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=False,
    )


def _gateway_stop_case() -> RAGAbstentionEvaluationCase:
    """Gateway stop is not missing-evidence abstention, even with evidence present."""
    match = SourceDocument(
        document_id="SYNTHETIC_RAG_ABSTENTION_GATEWAY_ORCHARD",
        title="Synthetic orchard reference",
        content=WITH_EVIDENCE_PASSAGE,
    )
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP",
        intake=_gateway_stop_intake(case_number="503"),
        source_documents=(match,),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=False,
    )


def _review_gate_stop_case() -> RAGAbstentionEvaluationCase:
    """Review-gate stop is not missing-evidence abstention, even with evidence present."""
    match = SourceDocument(
        document_id="SYNTHETIC_RAG_ABSTENTION_REVIEW_ORCHARD",
        title="Synthetic orchard reference",
        content=WITH_EVIDENCE_PASSAGE,
    )
    return RAGAbstentionEvaluationCase(
        evaluation_id="EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP",
        intake=_review_gate_stop_intake(case_number="504"),
        source_documents=(match,),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=False,
    )


def _allowed_intake(*, case_number: str) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{case_number}",
        client_ref=f"CLIENT_{case_number}",
        scenario="Synthetic RAG abstention baseline fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{case_number}",
                label="Synthetic abstention baseline document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic abstention baseline note.",),
    )


def _gateway_stop_intake(*, case_number: str) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{case_number}",
        client_ref=f"CLIENT_{case_number}",
        scenario="Synthetic RAG abstention gateway-stop baseline.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{case_number}",
                label="Synthetic abstention gateway-stop document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        missing_items=("Synthetic missing source reference.",),
    )


def _review_gate_stop_intake(*, case_number: str) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{case_number}",
        client_ref=f"CLIENT_{case_number}",
        scenario="Synthetic RAG abstention review-gate-stop baseline.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{case_number}",
                label="Synthetic abstention review-gate-stop document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        mock_risk_signals=(MockRiskSignal.DOCUMENT_PREPARATION.value,),
    )
