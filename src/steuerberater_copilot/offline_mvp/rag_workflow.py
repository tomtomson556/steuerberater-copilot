"""Controlled synthetic RAG workflow for offline grounded draft checks."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.ai import ModelProvider, ModelResponse
from steuerberater_copilot.rag import (
    LocalDocumentRetriever,
    SourceDocument,
    detect_passage_contradictions,
)

from ._response_markers import OFFLINE_DRAFT_TITLE_PREFIX
from .grounded_draft import GroundedDraft
from .grounded_draft_parser import parse_grounded_draft
from .grounded_draft_validator import validate_grounded_draft
from .model_invocation import (
    SYNTHETIC_RAG_MODEL_INVOCATION_POLICY,
    invoke_model_if_allowed,
)
from .models import (
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    ReviewGateDecision,
    ReviewStatus,
    RiskClassification,
)
from .privacy_gateway import combine_gateway_results, run_response_gateway_check
from .prompt_builder import build_synthetic_grounded_model_request
from .structured_output_validator import validate_structured_draft_output
from .workflow import classify_internal_risk, run_human_review_gate, run_mock_gateway


@dataclass(frozen=True)
class SyntheticRAGWorkflowOutput:
    """Synthetic RAG workflow state after response controls, without fachliche validation.

    ``abstained_for_missing_evidence`` is True only when controls allowed
    continuation, retrieval ran, and no documents were returned. In that case
    the provider is not called and ``grounded_draft`` remains None.

    ``contradiction_detected`` is True only when controls allowed continuation,
    retrieval returned documents, and the closed-template passage contradiction
    detector found conflicting attribute values among those documents. In that
    case the provider is not called and ``grounded_draft`` remains None. This is
    distinct from missing-evidence abstention and is not a general semantic NLP
    claim.
    """

    intake: IntakeCase
    gateway: GatewayResult
    risk_classification: RiskClassification
    review_gate: ReviewGateDecision
    retrieved_documents: tuple[SourceDocument, ...]
    model_response: ModelResponse | None
    grounded_draft: GroundedDraft | None
    abstained_for_missing_evidence: bool
    contradiction_detected: bool = False


def build_synthetic_rag_workflow(
    case: IntakeCase,
    *,
    provider: ModelProvider,
    retriever: LocalDocumentRetriever,
    retrieval_query: str,
    top_k: int,
) -> SyntheticRAGWorkflowOutput:
    """Run the separate synthetic RAG path after existing offline MVP controls.

    Gateway and human review run before retrieval and provider invocation. The
    same ``retrieved_documents`` tuple is passed to the grounded prompt and the
    grounding validator. Empty retrieval abstains without a provider call.
    """

    gateway = run_mock_gateway(case)
    risk_classification = classify_internal_risk(case, gateway)
    review_gate = run_human_review_gate(risk_classification)

    if (
        gateway.decision is not GatewayDecision.ALLOW_DRAFT
        or not review_gate.allows_offline_mock_continuation
    ):
        return SyntheticRAGWorkflowOutput(
            intake=case,
            gateway=gateway,
            risk_classification=risk_classification,
            review_gate=review_gate,
            retrieved_documents=(),
            model_response=None,
            grounded_draft=None,
            abstained_for_missing_evidence=False,
            contradiction_detected=False,
        )

    retrieved_documents = retriever.retrieve(retrieval_query, top_k=top_k)
    if not retrieved_documents:
        return SyntheticRAGWorkflowOutput(
            intake=case,
            gateway=gateway,
            risk_classification=risk_classification,
            review_gate=review_gate,
            retrieved_documents=retrieved_documents,
            model_response=None,
            grounded_draft=None,
            abstained_for_missing_evidence=True,
            contradiction_detected=False,
        )

    contradiction = detect_passage_contradictions(retrieved_documents)
    if contradiction.contradiction_present:
        return SyntheticRAGWorkflowOutput(
            intake=case,
            gateway=gateway,
            risk_classification=risk_classification,
            review_gate=review_gate,
            retrieved_documents=retrieved_documents,
            model_response=None,
            grounded_draft=None,
            abstained_for_missing_evidence=False,
            contradiction_detected=True,
        )

    request = build_synthetic_grounded_model_request(
        case,
        retrieved_documents=retrieved_documents,
    )
    model_response = invoke_model_if_allowed(
        provider=provider,
        request=request,
        gateway=gateway,
        review_gate=review_gate,
        policy=SYNTHETIC_RAG_MODEL_INVOCATION_POLICY,
    )
    grounded_draft = parse_grounded_draft(model_response.content)
    validate_structured_draft_output(grounded_draft.structured_draft)
    validate_grounded_draft(
        grounded_draft,
        retrieved_documents=retrieved_documents,
    )
    response_draft_package = DraftPackage(
        title=f"{OFFLINE_DRAFT_TITLE_PREFIX} {case.case_id}",
        review_status=ReviewStatus.DRAFT,
        risk_classification=risk_classification,
        review_required=risk_classification.review_required,
        summary_points=grounded_draft.structured_draft.summary_points,
        question_drafts=grounded_draft.structured_draft.review_questions,
        handoff_notes=grounded_draft.structured_draft.uncertainties,
    )
    gateway = combine_gateway_results(
        gateway,
        run_response_gateway_check(response_draft_package),
    )

    if gateway.decision is not GatewayDecision.ALLOW_DRAFT:
        grounded_draft = None

    return SyntheticRAGWorkflowOutput(
        intake=case,
        gateway=gateway,
        risk_classification=risk_classification,
        review_gate=review_gate,
        retrieved_documents=retrieved_documents,
        model_response=model_response,
        grounded_draft=grounded_draft,
        abstained_for_missing_evidence=False,
        contradiction_detected=False,
    )
