"""FastAPI demo surface at the HTTP system boundary.

No fachliche workflow logic lives here. The API only adapts existing offline
MVP and RAG workflows for a synthetic local or container demo.
"""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from steuerberater_copilot.ai import FakeModelProvider, ModelResponse
from steuerberater_copilot.observability import (
    DEFAULT_RUNTIME_METRICS,
    DurationTimer,
    RuntimeEvent,
    emit_runtime_event,
    new_request_id,
)
from steuerberater_copilot.offline_mvp import (
    build_synthetic_ai_workflow,
    build_synthetic_rag_workflow,
)
from steuerberater_copilot.offline_mvp.prompt_definition import (
    SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1,
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
)
from steuerberater_copilot.offline_mvp.workflow import load_fixture_cases
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

PACKAGE_NAME = "steuerberater-copilot"
DEMO_SOURCE = SourceDocument(
    document_id="SYNTHETIC_API_DEMO_SOURCE",
    title="Synthetic API demo orchard reference",
    content=(
        "Synthetic invoices remain available for internal review. "
        "Synthetic orchard passage for API demo grounding."
    ),
)


def create_app() -> FastAPI:
    """Application factory for the synthetic FastAPI demo."""
    app = FastAPI(
        title="Steuerberater-Copilot Demo API",
        description=(
            "Synthetic offline demo only. No productive data, no tax advice, "
            "and Human Review remains required for tax-relevant drafts."
        ),
        version=_package_version(),
    )
    app.state.metrics = DEFAULT_RUNTIME_METRICS

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def api_version() -> dict[str, str]:
        return {
            "package": PACKAGE_NAME,
            "version": _package_version(),
            "provider_default": "FakeModelProvider",
        }

    @app.get("/metrics")
    def metrics() -> dict[str, object]:
        return app.state.metrics.snapshot()

    @app.get("/v1/demo/draft")
    def demo_draft(
        case_id: str = Query(..., description="Synthetic fixture case ID."),
    ) -> JSONResponse:
        timer = DurationTimer()
        request_id = new_request_id()
        try:
            intake = _load_case(case_id)
            provider = FakeModelProvider(_structured_demo_response())
            output = build_synthetic_ai_workflow(intake, provider=provider)
            payload = {
                "request_id": request_id,
                "case_id": intake.case_id,
                "gateway_decision": output.gateway.decision.value,
                "review_gate_status": output.review_gate.status.value,
                "review_required": output.risk_classification.review_required,
                "risk_level": output.risk_classification.risk_level.value,
                "draft_available": output.structured_draft is not None,
                "structured_draft": (
                    {
                        "summary_points": list(
                            output.structured_draft.summary_points
                        ),
                        "uncertainties": list(output.structured_draft.uncertainties),
                        "review_questions": list(
                            output.structured_draft.review_questions
                        ),
                    }
                    if output.structured_draft is not None
                    else None
                ),
                "notes": [
                    "Synthetic demo draft only.",
                    "Human Review required before any fachliche use.",
                    "Full prompts are intentionally omitted.",
                ],
            }
            duration_ms = timer.elapsed_ms()
            app.state.metrics.record_request(success=True, duration_ms=duration_ms)
            emit_runtime_event(
                RuntimeEvent(
                    request_id=request_id,
                    workflow_status="demo_draft",
                    gateway_decision=output.gateway.decision.value,
                    review_decision=output.review_gate.status.value,
                    provider_name="fake",
                    model_name="fake-demo",
                    prompt_version=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version,
                    duration_ms=duration_ms,
                    parse_status="ok" if output.structured_draft else "skipped",
                    validation_status="ok" if output.structured_draft else "skipped",
                )
            )
            return JSONResponse(payload)
        except HTTPException:
            raise
        except Exception as error:  # noqa: BLE001 - demo boundary translation
            duration_ms = timer.elapsed_ms()
            app.state.metrics.record_request(
                success=False,
                duration_ms=duration_ms,
                parse_error="Parse" in type(error).__name__,
                validation_error="Validation" in type(error).__name__,
            )
            emit_runtime_event(
                RuntimeEvent(
                    request_id=request_id,
                    workflow_status="demo_draft_error",
                    gateway_decision="unknown",
                    review_decision="unknown",
                    provider_name="fake",
                    model_name="fake-demo",
                    prompt_version=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version,
                    duration_ms=duration_ms,
                    parse_status="error",
                    validation_status="error",
                    error_class=type(error).__name__,
                )
            )
            raise HTTPException(status_code=500, detail=type(error).__name__) from error

    @app.get("/v1/demo/rag")
    def demo_rag(
        case_id: str = Query(..., description="Synthetic fixture case ID."),
        retrieval_query: str = Query(
            "orchard invoice",
            description="Synthetic retrieval query for the local document store.",
        ),
    ) -> JSONResponse:
        timer = DurationTimer()
        request_id = new_request_id()
        try:
            intake = _load_case(case_id)
            provider = FakeModelProvider(_grounded_demo_response())
            retriever = LocalDocumentRetriever(documents=(DEMO_SOURCE,))
            output = build_synthetic_rag_workflow(
                intake,
                provider=provider,
                retriever=retriever,
                retrieval_query=retrieval_query,
                top_k=1,
            )
            citations: list[dict[str, Any]] = []
            if output.grounded_draft is not None:
                citations = [
                    {
                        "summary_point_index": citation.summary_point_index,
                        "document_id": citation.document_id,
                        "supporting_text": citation.supporting_text,
                    }
                    for citation in output.grounded_draft.citations
                ]
            payload = {
                "request_id": request_id,
                "case_id": intake.case_id,
                "gateway_decision": output.gateway.decision.value,
                "review_gate_status": output.review_gate.status.value,
                "review_required": output.risk_classification.review_required,
                "risk_level": output.risk_classification.risk_level.value,
                "retrieved_document_ids": [
                    document.document_id for document in output.retrieved_documents
                ],
                "abstained_for_missing_evidence": output.abstained_for_missing_evidence,
                "contradiction_detected": output.contradiction_detected,
                "draft_available": output.grounded_draft is not None,
                "citations": citations,
                "structured_draft": (
                    {
                        "summary_points": list(
                            output.grounded_draft.structured_draft.summary_points
                        ),
                        "uncertainties": list(
                            output.grounded_draft.structured_draft.uncertainties
                        ),
                        "review_questions": list(
                            output.grounded_draft.structured_draft.review_questions
                        ),
                    }
                    if output.grounded_draft is not None
                    else None
                ),
                "notes": [
                    "Synthetic RAG demo only.",
                    "Sources are local synthetic documents.",
                    "Human Review required before any fachliche use.",
                ],
            }
            duration_ms = timer.elapsed_ms()
            app.state.metrics.record_request(
                success=True,
                duration_ms=duration_ms,
                abstained=output.abstained_for_missing_evidence,
                contradiction=output.contradiction_detected,
            )
            emit_runtime_event(
                RuntimeEvent(
                    request_id=request_id,
                    workflow_status="demo_rag",
                    gateway_decision=output.gateway.decision.value,
                    review_decision=output.review_gate.status.value,
                    provider_name="fake",
                    model_name="fake-demo",
                    prompt_version=SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version,
                    duration_ms=duration_ms,
                    parse_status="ok" if output.grounded_draft else "skipped",
                    validation_status="ok" if output.grounded_draft else "skipped",
                )
            )
            return JSONResponse(payload)
        except HTTPException:
            raise
        except Exception as error:  # noqa: BLE001 - demo boundary translation
            duration_ms = timer.elapsed_ms()
            app.state.metrics.record_request(success=False, duration_ms=duration_ms)
            emit_runtime_event(
                RuntimeEvent(
                    request_id=request_id,
                    workflow_status="demo_rag_error",
                    gateway_decision="unknown",
                    review_decision="unknown",
                    provider_name="fake",
                    model_name="fake-demo",
                    prompt_version=SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version,
                    duration_ms=duration_ms,
                    parse_status="error",
                    validation_status="error",
                    error_class=type(error).__name__,
                )
            )
            raise HTTPException(status_code=500, detail=type(error).__name__) from error

    return app


def _load_case(case_id: str):
    cases = {case.case_id: case for case in load_fixture_cases()}
    case = cases.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Unknown synthetic case_id.")
    return case


def _structured_demo_response() -> ModelResponse:
    return ModelResponse(
        content=json.dumps(
            {
                "summary_points": ["Synthetic API demo summary point."],
                "uncertainties": ["Synthetic API demo uncertainty."],
                "review_questions": ["Synthetic API demo review question?"],
            }
        ),
        provider_name="fake",
        model_name="fake-demo",
    )


def _grounded_demo_response() -> ModelResponse:
    return ModelResponse(
        content=json.dumps(
            {
                "summary_points": ["Synthetic API RAG summary point."],
                "uncertainties": ["Synthetic API RAG uncertainty."],
                "review_questions": ["Synthetic API RAG review question?"],
                "citations": [
                    {
                        "summary_point_index": 0,
                        "document_id": DEMO_SOURCE.document_id,
                        "supporting_text": (
                            "Synthetic orchard passage for API demo grounding."
                        ),
                    }
                ],
            }
        ),
        provider_name="fake",
        model_name="fake-demo",
    )


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.1.0"
