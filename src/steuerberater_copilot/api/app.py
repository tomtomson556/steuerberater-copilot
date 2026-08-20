"""Minimal FastAPI application factory at the HTTP system boundary."""

from __future__ import annotations

import time
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, HTTPException, Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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
    request_validation_log_fields,
)

PACKAGE_NAME = "steuerberater-copilot"
REQUEST_ID_HEADER = "X-Request-ID"
_AI_DRAFT_PATH = "/ai/draft"
_AI_DRAFT_METHOD = "POST"
_LOG_FIELDS_STATE_KEY = "ai_draft_log_fields"
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


class AIDraftRuntimeLoggingMiddleware:
    """Emit one runtime event and X-Request-ID before body validation runs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not _is_ai_draft_post(scope):
            await self.app(scope, receive, send)
            return

        request_id = new_request_id()
        started = time.perf_counter()
        scope.setdefault("state", {})
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                raw_headers = message.get("headers")
                if not isinstance(raw_headers, list):
                    raw_headers = list(raw_headers or [])
                    message["headers"] = raw_headers
                MutableHeaders(raw=raw_headers)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = max(0, round((time.perf_counter() - started) * 1000))
            emit_runtime_event(
                build_runtime_event(
                    request_id=request_id,
                    http_status=status_code,
                    duration_ms=duration_ms,
                    fields=_log_fields_for_response(scope, status_code),
                )
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
    def ai_draft(payload: AIDraftRequest, request: Request) -> AIDraftResponse:
        try:
            result = execute_synthetic_ai_draft(payload)
        except Exception:
            result = AIDraftBoundaryResult(
                http_status=500,
                payload=None,
                error_detail="Internal Server Error",
                log_fields=_INTERNAL_FAILURE_FIELDS,
            )
        setattr(request.state, _LOG_FIELDS_STATE_KEY, result.log_fields)
        if result.payload is None:
            raise HTTPException(
                status_code=result.http_status,
                detail=result.error_detail,
            )
        return result.payload

    app.add_middleware(AIDraftRuntimeLoggingMiddleware)
    return app


def _is_ai_draft_post(scope: Scope) -> bool:
    return (
        scope.get("type") == "http"
        and scope.get("method") == _AI_DRAFT_METHOD
        and scope.get("path") == _AI_DRAFT_PATH
    )


def _log_fields_for_response(scope: Scope, status_code: int) -> RuntimeLogFields:
    fields = scope.get("state", {}).get(_LOG_FIELDS_STATE_KEY)
    if isinstance(fields, RuntimeLogFields):
        return fields
    if status_code == 422:
        return request_validation_log_fields()
    return _INTERNAL_FAILURE_FIELDS


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"
