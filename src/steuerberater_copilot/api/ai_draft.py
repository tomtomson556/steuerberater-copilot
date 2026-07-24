"""Controlled synthetic AI draft runner for the HTTP demo boundary.

The FastAPI route stays thin: this module owns known demo-case lookup,
FakeModelProvider wiring, LocalDocumentRetriever setup, and response mapping.
Workflow control logic remains in ``build_synthetic_rag_workflow``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from steuerberater_copilot.ai import FakeModelProvider, ModelResponse
from steuerberater_copilot.offline_mvp import (
    IntakeCase,
    ReviewStatus,
    SyntheticDocument,
    build_synthetic_rag_workflow,
)
from steuerberater_copilot.offline_mvp.rag_workflow import SyntheticRAGWorkflowOutput
from steuerberater_copilot.offline_mvp.workflow import load_fixture_cases
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

from .contracts import (
    AIDraftCitation,
    AIDraftContent,
    AIDraftGateway,
    AIDraftRequest,
    AIDraftResponse,
    AIDraftReviewGate,
    AIDraftRisk,
)

SUPPORTING_PASSAGE = "Synthetic invoices remain available for internal review."
RETRIEVAL_QUERY = "synthetic invoice retention"
RETRIEVAL_TOP_K = 1

GROUNDED_MODEL_CONTENT = json.dumps(
    {
        "summary_points": ["Synthetic grounded summary."],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": SUPPORTING_PASSAGE,
            }
        ],
    }
)


class UnknownSyntheticDemoCaseError(LookupError):
    """Raised when the request case_id is not a known synthetic demo case."""


@dataclass(frozen=True, slots=True)
class SyntheticAIDraftDemoCase:
    """Known synthetic demo configuration for the AI draft endpoint."""

    case_id: str
    intake: IntakeCase
    retrieval_query: str
    top_k: int
    source_documents: tuple[SourceDocument, ...]
    model_response: ModelResponse


def known_synthetic_ai_draft_case_ids() -> frozenset[str]:
    """Return the allowed synthetic demo case identifiers."""
    return frozenset(_demo_cases().keys())


def run_synthetic_ai_draft(request: AIDraftRequest) -> AIDraftResponse:
    """Run the controlled synthetic RAG workflow for one known demo case."""
    demo_case = _demo_cases().get(request.case_id)
    if demo_case is None:
        raise UnknownSyntheticDemoCaseError(request.case_id)

    workflow_output = build_synthetic_rag_workflow(
        demo_case.intake,
        provider=FakeModelProvider(demo_case.model_response),
        retriever=LocalDocumentRetriever(documents=demo_case.source_documents),
        retrieval_query=demo_case.retrieval_query,
        top_k=demo_case.top_k,
    )
    return _to_response(workflow_output)


def _demo_cases() -> dict[str, SyntheticAIDraftDemoCase]:
    fixtures = {case.case_id: case for case in load_fixture_cases()}
    grounded_documents = (
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_001",
            title="Synthetic invoice retention note",
            content=f"Prefix. {SUPPORTING_PASSAGE} Suffix.",
        ),
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_002",
            title="Synthetic invoice archive note",
            content="Secondary synthetic invoice archive content.",
        ),
    )
    unrelated_documents = (
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_UNRELATED",
            title="Payroll calendar overview",
            content="Completely unrelated payroll calendar body text.",
        ),
    )
    canned_response = ModelResponse(
        content=GROUNDED_MODEL_CONTENT,
        provider_name="fake",
        model_name="fake-model",
    )

    return {
        "CASE_002": SyntheticAIDraftDemoCase(
            case_id="CASE_002",
            intake=fixtures["CASE_002"],
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
            source_documents=grounded_documents,
            model_response=canned_response,
        ),
        "CASE_006": SyntheticAIDraftDemoCase(
            case_id="CASE_006",
            intake=_abstention_intake_case(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
            source_documents=unrelated_documents,
            model_response=canned_response,
        ),
        "CASE_005": SyntheticAIDraftDemoCase(
            case_id="CASE_005",
            intake=fixtures["CASE_005"],
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
            source_documents=grounded_documents,
            model_response=canned_response,
        ),
    }


def _abstention_intake_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_006",
        client_ref="CLIENT_006",
        scenario="synthetic AI draft abstention fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_007",
                label="synthetic abstention descriptor",
                period="2026-Q1",
                source_note="synthetic source note for empty retrieval abstention",
            ),
        ),
        notes=("Internal synthetic abstention preparation note.",),
    )


def _to_response(output: SyntheticRAGWorkflowOutput) -> AIDraftResponse:
    draft: AIDraftContent | None = None
    if output.grounded_draft is not None:
        structured = output.grounded_draft.structured_draft
        draft = AIDraftContent(
            review_status=ReviewStatus.DRAFT.value,
            summary_points=list(structured.summary_points),
            uncertainties=list(structured.uncertainties),
            review_questions=list(structured.review_questions),
            citations=[
                AIDraftCitation(
                    summary_point_index=citation.summary_point_index,
                    document_id=citation.document_id,
                    supporting_text=citation.supporting_text,
                )
                for citation in output.grounded_draft.citations
            ],
        )

    return AIDraftResponse(
        case_id=output.intake.case_id,
        gateway=AIDraftGateway(
            decision=output.gateway.decision.value,
            checks=list(output.gateway.checks),
            escalation_reasons=list(output.gateway.escalation_reasons),
            block_reasons=list(output.gateway.block_reasons),
        ),
        risk=AIDraftRisk(
            level=output.risk_classification.risk_level.value,
            review_required=output.risk_classification.review_required,
            basis=list(output.risk_classification.basis),
        ),
        review_gate=AIDraftReviewGate(
            status=output.review_gate.status.value,
            allows_offline_mock_continuation=(
                output.review_gate.allows_offline_mock_continuation
            ),
            reason=output.review_gate.reason,
        ),
        abstained_for_missing_evidence=output.abstained_for_missing_evidence,
        draft=draft,
    )
