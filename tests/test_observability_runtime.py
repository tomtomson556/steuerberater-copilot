import json
from io import StringIO

import pytest

from steuerberater_copilot.observability import (
    RuntimeEvent,
    RuntimeMetrics,
    emit_runtime_event,
)


def test_runtime_event_validates_required_fields_and_duration() -> None:
    event = _runtime_event()

    assert event.request_id == "REQUEST_OBSERVABILITY_TEST"
    assert event.duration_ms == 12.5

    with pytest.raises(ValueError, match=r"^workflow_status must not be blank\.$"):
        _runtime_event(workflow_status=" ")

    with pytest.raises(TypeError, match=r"^duration_ms must be a float\.$"):
        _runtime_event(duration_ms=12)


def test_runtime_metrics_snapshot_counts_requests_and_rates() -> None:
    metrics = RuntimeMetrics()

    metrics.record_request(success=True, duration_ms=10.0, abstained=True)
    metrics.record_request(
        success=False,
        duration_ms=20.0,
        provider_error=True,
        parse_error=True,
        validation_error=True,
        contradiction=True,
    )

    assert metrics.snapshot() == {
        "request_count": 2,
        "success_count": 1,
        "error_count": 1,
        "success_rate": 0.5,
        "error_rate": 0.5,
        "provider_error_count": 1,
        "parse_error_count": 1,
        "validation_error_count": 1,
        "abstention_count": 1,
        "abstention_rate": 0.5,
        "contradiction_count": 1,
        "p95_latency_ms": 20.0,
        "estimated_model_cost": None,
    }


def test_emit_runtime_event_writes_one_json_line() -> None:
    stream = StringIO()

    emit_runtime_event(_runtime_event(error_class="SyntheticError"), stream=stream)

    line = stream.getvalue()
    assert line.endswith("\n")
    payload = json.loads(line)
    assert payload == {
        "duration_ms": 12.5,
        "error_class": "SyntheticError",
        "event_type": "runtime",
        "gateway_decision": "allow_draft",
        "model_name": "fake-observability-test",
        "parse_status": "ok",
        "prompt_version": "1",
        "provider_name": "fake",
        "request_id": "REQUEST_OBSERVABILITY_TEST",
        "review_decision": "allowed_offline_mock_continuation",
        "validation_status": "ok",
        "workflow_status": "ok",
    }


def _runtime_event(**changes: object) -> RuntimeEvent:
    values = {
        "request_id": "REQUEST_OBSERVABILITY_TEST",
        "workflow_status": "ok",
        "gateway_decision": "allow_draft",
        "review_decision": "allowed_offline_mock_continuation",
        "provider_name": "fake",
        "model_name": "fake-observability-test",
        "prompt_version": "1",
        "duration_ms": 12.5,
        "parse_status": "ok",
        "validation_status": "ok",
        "error_class": None,
    }
    values.update(changes)
    return RuntimeEvent(**values)
