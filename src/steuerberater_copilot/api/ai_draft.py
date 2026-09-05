"""Controlled synthetic AI draft runner for the HTTP demo boundary.

The FastAPI route stays thin: this module owns known demo-case lookup,
FakeModelProvider wiring, LocalDocumentRetriever setup, and response mapping.
Workflow control logic remains in ``build_synthetic_rag_workflow``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    GroundedDraftParseError,
    GroundedDraftValidationError,
    IntakeCase,
    ReviewStatus,
    StructuredDraftOutputParseError,
    StructuredDraftOutputValidationError,
    SyntheticDocument,
    build_synthetic_rag_workflow,
    classify_internal_risk,
    run_human_review_gate,
)
from steuerberater_copilot.offline_mvp.rag_workflow import SyntheticRAGWorkflowOutput
from steuerberater_copilot.offline_mvp.workflow import load_fixture_cases, run_mock_gateway
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument
from steuerberater_copilot.rag.source_document import SYNTHETIC_FIXTURE_DATA_CLASS

from .contracts import (
    AIDraftCitation,
    AIDraftContent,
    AIDraftGateway,
    AIDraftRequest,
    AIDraftResponse,
    AIDraftReviewGate,
    AIDraftRisk,
)
from .runtime_log import (
    ERROR_CLASS_INTERNAL,
    ERROR_CLASS_PARSE,
    ERROR_CLASS_PROVIDER,
    ERROR_CLASS_VALIDATION,
    STAGE_STATUS_ERROR,
    STAGE_STATUS_NOT_RUN,
    STAGE_STATUS_OK,
    WORKFLOW_STATUS_ABSTAINED,
    WORKFLOW_STATUS_BLOCKED,
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_ERROR,
    RuntimeLogFields,
    unknown_case_log_fields,
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


@dataclass(frozen=True, slots=True)
class AIDraftBoundaryResult:
    """HTTP-boundary outcome including metadata for one runtime log event."""

    http_status: int
    payload: AIDraftResponse | None
    error_detail: str | None
    log_fields: RuntimeLogFields


class _ObservingModelProvider:
    """Record request/response metadata at the HTTP boundary without logging content."""

    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider
        self.last_request: ModelRequest | None = None
        self.last_response: ModelResponse | None = None
        self.provider_failed = False

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        try:
            self.last_response = self._provider.generate(request)
        except Exception:
            self.provider_failed = True
            raise
        return self.last_response


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


def execute_synthetic_ai_draft(request: AIDraftRequest) -> AIDraftBoundaryResult:
    """Run one demo case and return HTTP payload plus runtime log fields.

    Workflow exceptions are translated into a generic HTTP 500 detail. Exception
    text never becomes part of the log fields or the HTTP body.
    """
    demo_case = _demo_cases().get(request.case_id)
    if demo_case is None:
        return AIDraftBoundaryResult(
            http_status=404,
            payload=None,
            error_detail=f"Unknown synthetic demo case_id: {request.case_id}",
            log_fields=unknown_case_log_fields(),
        )

    observer = _ObservingModelProvider(FakeModelProvider(demo_case.model_response))
    try:
        workflow_output = build_synthetic_rag_workflow(
            demo_case.intake,
            provider=observer,
            retriever=LocalDocumentRetriever(documents=demo_case.source_documents),
            retrieval_query=demo_case.retrieval_query,
            top_k=demo_case.top_k,
        )
    except Exception as exc:
        return AIDraftBoundaryResult(
            http_status=500,
            payload=None,
            error_detail="Internal Server Error",
            log_fields=_log_fields_from_failure(demo_case.intake, observer, exc),
        )
    return AIDraftBoundaryResult(
        http_status=200,
        payload=_to_response(workflow_output),
        error_detail=None,
        log_fields=_log_fields_from_success(workflow_output, observer),
    )


def _demo_cases() -> dict[str, SyntheticAIDraftDemoCase]:
    fixtures = {case.case_id: case for case in load_fixture_cases()}
    grounded_documents = (
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_001",
            title="Synthetic invoice retention note",
            content=f"Prefix. {SUPPORTING_PASSAGE} Suffix.",
            data_class=SYNTHETIC_FIXTURE_DATA_CLASS,
        ),
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_002",
            title="Synthetic invoice archive note",
            content="Secondary synthetic invoice archive content.",
            data_class=SYNTHETIC_FIXTURE_DATA_CLASS,
        ),
    )
    unrelated_documents = (
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_UNRELATED",
            title="Payroll calendar overview",
            content="Completely unrelated payroll calendar body text.",
            data_class=SYNTHETIC_FIXTURE_DATA_CLASS,
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


def _log_fields_from_success(
    output: SyntheticRAGWorkflowOutput,
    observer: _ObservingModelProvider,
) -> RuntimeLogFields:
    if output.abstained_for_missing_evidence:
        workflow_status = WORKFLOW_STATUS_ABSTAINED
    elif (
        output.gateway.decision is not GatewayDecision.ALLOW_DRAFT
        or not output.review_gate.allows_offline_mock_continuation
    ):
        workflow_status = WORKFLOW_STATUS_BLOCKED
    else:
        workflow_status = WORKFLOW_STATUS_COMPLETED

    model_response = output.model_response
    if model_response is None:
        parse_status = STAGE_STATUS_NOT_RUN
        validation_status = STAGE_STATUS_NOT_RUN
        provider_name = None
        model_name = None
        prompt_version = None
    else:
        parse_status = STAGE_STATUS_OK
        validation_status = STAGE_STATUS_OK
        provider_name = model_response.provider_name
        model_name = model_response.model_name
        prompt_version = _prompt_version(observer)

    return RuntimeLogFields(
        workflow_status=workflow_status,
        gateway_decision=output.gateway.decision.value,
        review_gate_status=output.review_gate.status.value,
        provider_name=provider_name,
        model_name=model_name,
        prompt_version=prompt_version,
        parse_status=parse_status,
        validation_status=validation_status,
        error_class=None,
    )


def _log_fields_from_failure(
    intake: IntakeCase,
    observer: _ObservingModelProvider,
    exc: BaseException,
) -> RuntimeLogFields:
    gateway = run_mock_gateway(intake)
    review_gate = run_human_review_gate(classify_internal_risk(intake, gateway))
    error_class = _classify_workflow_error(exc, provider_failed=observer.provider_failed)
    last_response = observer.last_response
    if error_class == ERROR_CLASS_PARSE:
        parse_status = STAGE_STATUS_ERROR
        validation_status = STAGE_STATUS_NOT_RUN
    elif error_class == ERROR_CLASS_VALIDATION:
        parse_status = STAGE_STATUS_OK
        validation_status = STAGE_STATUS_ERROR
    else:
        parse_status = STAGE_STATUS_NOT_RUN
        validation_status = STAGE_STATUS_NOT_RUN

    return RuntimeLogFields(
        workflow_status=WORKFLOW_STATUS_ERROR,
        gateway_decision=gateway.decision.value,
        review_gate_status=review_gate.status.value,
        provider_name=None if last_response is None else last_response.provider_name,
        model_name=None if last_response is None else last_response.model_name,
        prompt_version=_prompt_version(observer),
        parse_status=parse_status,
        validation_status=validation_status,
        error_class=error_class,
    )


def _classify_workflow_error(exc: BaseException, *, provider_failed: bool) -> str:
    if provider_failed:
        return ERROR_CLASS_PROVIDER
    if isinstance(exc, GroundedDraftParseError | StructuredDraftOutputParseError):
        return ERROR_CLASS_PARSE
    if isinstance(
        exc,
        GroundedDraftValidationError | StructuredDraftOutputValidationError,
    ):
        return ERROR_CLASS_VALIDATION
    return ERROR_CLASS_INTERNAL


def _prompt_version(observer: _ObservingModelProvider) -> str | None:
    if observer.last_request is None:
        return None
    return observer.last_request.prompt_version
