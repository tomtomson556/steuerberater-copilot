"""Minimal FastAPI application factory at the HTTP system boundary."""

from __future__ import annotations

import time
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, HTTPException, Response

from .ai_draft import AIDraftBoundaryResult, execute_synthetic_ai_draft
from .contracts import AIDraftRequest, AIDraftResponse
from .runtime_log import (
    ERROR_CLASS_INTERNAL,
    STAGE_STATUS_NOT_RUN,
    WORKFLOW_STATUS_ERROR,
    RuntimeLogFields,
    build_runtime_event,
    emit_runtime_event,
    new_request_id,
)

PACKAGE_NAME = "steuerberater-copilot"
REQUEST_ID_HEADER = "X-Request-ID"
_INTERNAL_FAILURE_FIELDS = RuntimeLogFields(
    workflow_status=WORKFLOW_STATUS_ERROR,
    gateway_decision=None,
    review_gate_status=None,
    provider_name=None,
    model_name=None,
    prompt_version=None,
    parse_status=STAGE_STATUS_NOT_RUN,
    validation_status=STAGE_STATUS_NOT_RUN,
    error_class=ERROR_CLASS_INTERNAL,
)


def create_app() -> FastAPI:
    """Create an independent FastAPI app with health, version, and AI draft routes."""
    app = FastAPI(title="steuerberater-copilot")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def package_version_endpoint() -> dict[str, str]:
        return {"version": _package_version()}

    @app.post("/ai/draft", response_model=AIDraftResponse)
    def ai_draft(request: AIDraftRequest, response: Response) -> AIDraftResponse:
        request_id = new_request_id()
        started = time.perf_counter()
        result: AIDraftBoundaryResult | None = None
        try:
            result = execute_synthetic_ai_draft(request)
        except Exception:
            result = AIDraftBoundaryResult(
                http_status=500,
                payload=None,
                error_detail="Internal Server Error",
                log_fields=_INTERNAL_FAILURE_FIELDS,
            )
        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        emit_runtime_event(
            build_runtime_event(
                request_id=request_id,
                http_status=result.http_status,
                duration_ms=duration_ms,
                fields=result.log_fields,
            )
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        if result.payload is None:
            raise HTTPException(
                status_code=result.http_status,
                detail=result.error_detail,
                headers={REQUEST_ID_HEADER: request_id},
            )
        return result.payload

    return app


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"
