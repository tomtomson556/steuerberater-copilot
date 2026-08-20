"""Structured runtime logging helpers for the HTTP AI-draft boundary.

Events are one JSON object per line on stdout so the existing awslogs path can
ingest them without an AWS SDK or logging dependency. The payload contains only
stable operational metadata. It must not include bodies, prompts, model text,
secrets, exception messages, or personal data.
"""

from __future__ import annotations

import json
import sys
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TextIO

EVENT_NAME = "ai_draft_runtime"

RUNTIME_EVENT_KEYS = (
    "event",
    "request_id",
    "http_status",
    "workflow_status",
    "gateway_decision",
    "review_gate_status",
    "provider_name",
    "model_name",
    "prompt_version",
    "duration_ms",
    "parse_status",
    "validation_status",
    "error_class",
)

WORKFLOW_STATUS_COMPLETED = "completed"
WORKFLOW_STATUS_BLOCKED = "blocked"
WORKFLOW_STATUS_ABSTAINED = "abstained"
WORKFLOW_STATUS_NOT_RUN = "not_run"
WORKFLOW_STATUS_ERROR = "error"

STAGE_STATUS_OK = "ok"
STAGE_STATUS_ERROR = "error"
STAGE_STATUS_NOT_RUN = "not_run"

ERROR_CLASS_UNKNOWN_CASE = "unknown_case_id"
ERROR_CLASS_PARSE = "parse_error"
ERROR_CLASS_VALIDATION = "validation_error"
ERROR_CLASS_PROVIDER = "provider_error"
ERROR_CLASS_INTERNAL = "internal_error"


@dataclass(frozen=True, slots=True)
class RuntimeLogFields:
    """Workflow-derived runtime fields excluding request identity and timing."""

    workflow_status: str
    gateway_decision: str | None
    review_gate_status: str | None
    provider_name: str | None
    model_name: str | None
    prompt_version: str | None
    parse_status: str
    validation_status: str
    error_class: str | None


def new_request_id() -> str:
    """Return a server-generated request identifier."""
    return str(uuid.uuid4())


def unknown_case_log_fields() -> RuntimeLogFields:
    """Fields for a request that never entered the synthetic workflow."""
    return RuntimeLogFields(
        workflow_status=WORKFLOW_STATUS_NOT_RUN,
        gateway_decision=None,
        review_gate_status=None,
        provider_name=None,
        model_name=None,
        prompt_version=None,
        parse_status=STAGE_STATUS_NOT_RUN,
        validation_status=STAGE_STATUS_NOT_RUN,
        error_class=ERROR_CLASS_UNKNOWN_CASE,
    )


def build_runtime_event(
    *,
    request_id: str,
    http_status: int,
    duration_ms: int,
    fields: RuntimeLogFields,
) -> dict[str, object]:
    """Build the stable one-line runtime event payload."""
    return {
        "event": EVENT_NAME,
        "request_id": request_id,
        "http_status": http_status,
        "workflow_status": fields.workflow_status,
        "gateway_decision": fields.gateway_decision,
        "review_gate_status": fields.review_gate_status,
        "provider_name": fields.provider_name,
        "model_name": fields.model_name,
        "prompt_version": fields.prompt_version,
        "duration_ms": duration_ms,
        "parse_status": fields.parse_status,
        "validation_status": fields.validation_status,
        "error_class": fields.error_class,
    }


def emit_runtime_event(
    event: Mapping[str, object],
    *,
    stream: TextIO | None = None,
) -> None:
    """Write exactly one compact JSON object followed by a newline."""
    payload = {key: event[key] for key in RUNTIME_EVENT_KEYS}
    line = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    if "\n" in line or "\r" in line:
        raise ValueError("runtime event must serialize to a single line")
    output = sys.stdout if stream is None else stream
    output.write(line + "\n")
    output.flush()
