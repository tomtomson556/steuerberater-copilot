"""Cloud-neutral structured runtime event logging helpers."""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, TextIO


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """Structured runtime event without secrets or raw model payloads.

    Allowed fields mirror the portfolio observability baseline. Prompt text,
    raw model responses, secrets, and real personal data must not be attached.
    """

    request_id: str
    workflow_status: str
    gateway_decision: str
    review_decision: str
    provider_name: str
    model_name: str
    prompt_version: str
    duration_ms: float
    parse_status: str
    validation_status: str
    error_class: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "workflow_status",
            "gateway_decision",
            "review_decision",
            "provider_name",
            "model_name",
            "prompt_version",
            "parse_status",
            "validation_status",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")
        if type(self.duration_ms) is not float:
            raise TypeError("duration_ms must be a float.")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must not be negative.")
        if self.error_class is not None:
            if not isinstance(self.error_class, str):
                raise TypeError("error_class must be a string or None.")
            if not self.error_class or self.error_class.isspace():
                raise ValueError("error_class must not be blank when provided.")


def new_request_id() -> str:
    """Create a synthetic request identifier."""
    return str(uuid.uuid4())


def emit_runtime_event(
    event: RuntimeEvent,
    *,
    stream: TextIO | None = None,
) -> None:
    """Write one JSON runtime event line to the given stream."""
    if not isinstance(event, RuntimeEvent):
        raise TypeError("event must be a RuntimeEvent.")
    target = sys.stdout if stream is None else stream
    payload: dict[str, Any] = asdict(event)
    payload["event_type"] = "runtime"
    target.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    target.write("\n")


class DurationTimer:
    """Simple monotonic duration helper for structured runtime events."""

    def __init__(self) -> None:
        self._started = time.perf_counter()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._started) * 1000.0
