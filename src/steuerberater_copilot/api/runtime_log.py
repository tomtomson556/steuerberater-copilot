"""Structured runtime logging helpers for the HTTP AI-draft boundary.

Events are one JSON object per line on stdout so the existing awslogs path can
ingest them without an AWS SDK or logging dependency. Each POST /ai/draft event
is a CloudWatch Embedded Metric Format document plus stable operational
metadata. It must not include bodies, prompts, model text, secrets, exception
messages, or personal data.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TextIO

EVENT_NAME = "ai_draft_runtime"

METRIC_NAMESPACE = "SteuerberaterCopilot/Runtime"
METRIC_SERVICE = "steuerberater-copilot"
METRIC_OPERATION = "POST /ai/draft"
METRIC_STORAGE_RESOLUTION = 60
UNIT_COUNT = "Count"
UNIT_MILLISECONDS = "Milliseconds"
UNIT_NONE = "None"
FAKE_PROVIDER_NAME = "fake"
EMF_DIMENSION_NAMES = ("service", "operation")

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
    "service",
    "operation",
    "request_count",
    "success_count",
    "error_count",
    "provider_error_count",
    "parse_error_count",
    "validation_error_count",
    "abstention_count",
    "model_cost_usd",
    "_aws",
)

_BASE_METRIC_DEFINITIONS = (
    ("request_count", UNIT_COUNT),
    ("success_count", UNIT_COUNT),
    ("error_count", UNIT_COUNT),
    ("duration_ms", UNIT_MILLISECONDS),
    ("provider_error_count", UNIT_COUNT),
    ("parse_error_count", UNIT_COUNT),
    ("validation_error_count", UNIT_COUNT),
    ("abstention_count", UNIT_COUNT),
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
ERROR_CLASS_REQUEST_VALIDATION = "request_validation_error"

_NO_PROVIDER_CALL_STATUSES = frozenset(
    {
        WORKFLOW_STATUS_BLOCKED,
        WORKFLOW_STATUS_ABSTAINED,
        WORKFLOW_STATUS_NOT_RUN,
    }
)


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


def request_validation_log_fields() -> RuntimeLogFields:
    """Fields for a request rejected by HTTP body validation before the workflow."""
    return RuntimeLogFields(
        workflow_status=WORKFLOW_STATUS_NOT_RUN,
        gateway_decision=None,
        review_gate_status=None,
        provider_name=None,
        model_name=None,
        prompt_version=None,
        parse_status=STAGE_STATUS_NOT_RUN,
        validation_status=STAGE_STATUS_NOT_RUN,
        error_class=ERROR_CLASS_REQUEST_VALIDATION,
    )


def build_runtime_event(
    *,
    request_id: str,
    http_status: int,
    duration_ms: int,
    fields: RuntimeLogFields,
    timestamp_ms: int | None = None,
) -> dict[str, object]:
    """Build the stable one-line runtime event payload including EMF metadata."""
    success_count = _flag(200 <= http_status < 400)
    error_count = _flag(http_status >= 400)
    provider_error_count = _flag(fields.error_class == ERROR_CLASS_PROVIDER)
    parse_error_count = _flag(fields.error_class == ERROR_CLASS_PARSE)
    validation_error_count = _flag(fields.error_class == ERROR_CLASS_VALIDATION)
    abstention_count = _flag(fields.workflow_status == WORKFLOW_STATUS_ABSTAINED)
    model_cost_usd = _model_cost_usd(fields)
    resolved_timestamp_ms = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
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
        "service": METRIC_SERVICE,
        "operation": METRIC_OPERATION,
        "request_count": 1,
        "success_count": success_count,
        "error_count": error_count,
        "provider_error_count": provider_error_count,
        "parse_error_count": parse_error_count,
        "validation_error_count": validation_error_count,
        "abstention_count": abstention_count,
        "model_cost_usd": model_cost_usd,
        "_aws": {
            "Timestamp": resolved_timestamp_ms,
            "CloudWatchMetrics": [
                {
                    "Namespace": METRIC_NAMESPACE,
                    "Dimensions": [list(EMF_DIMENSION_NAMES)],
                    "Metrics": _metric_definitions(include_model_cost=model_cost_usd is not None),
                }
            ],
        },
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


def _flag(condition: bool) -> int:
    return 1 if condition else 0


def _model_cost_usd(fields: RuntimeLogFields) -> float | None:
    if fields.provider_name == FAKE_PROVIDER_NAME:
        return 0.0
    if fields.workflow_status in _NO_PROVIDER_CALL_STATUSES:
        return 0.0
    return None


def _metric_definitions(*, include_model_cost: bool) -> list[dict[str, object]]:
    metrics = [
        {
            "Name": name,
            "Unit": unit,
            "StorageResolution": METRIC_STORAGE_RESOLUTION,
        }
        for name, unit in _BASE_METRIC_DEFINITIONS
    ]
    if include_model_cost:
        metrics.append(
            {
                "Name": "model_cost_usd",
                "Unit": UNIT_NONE,
                "StorageResolution": METRIC_STORAGE_RESOLUTION,
            }
        )
    return metrics
