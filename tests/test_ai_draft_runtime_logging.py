from __future__ import annotations

import json
import socket
import uuid
from dataclasses import replace
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from steuerberater_copilot.ai import ModelResponse
from steuerberater_copilot.api import ai_draft as ai_draft_module
from steuerberater_copilot.api import app as app_module
from steuerberater_copilot.api import create_app
from steuerberater_copilot.api.runtime_log import (
    EMF_DIMENSION_NAMES,
    ERROR_CLASS_INTERNAL,
    ERROR_CLASS_REQUEST_VALIDATION,
    EVENT_NAME,
    FAKE_PROVIDER_NAME,
    METRIC_NAMESPACE,
    METRIC_OPERATION,
    METRIC_SERVICE,
    METRIC_STORAGE_RESOLUTION,
    RUNTIME_EVENT_KEYS,
    STAGE_STATUS_ERROR,
    STAGE_STATUS_NOT_RUN,
    STAGE_STATUS_OK,
    UNIT_COUNT,
    UNIT_MILLISECONDS,
    UNIT_NONE,
    WORKFLOW_STATUS_ABSTAINED,
    WORKFLOW_STATUS_BLOCKED,
    WORKFLOW_STATUS_COMPLETED,
    WORKFLOW_STATUS_ERROR,
    WORKFLOW_STATUS_NOT_RUN,
    RuntimeLogFields,
    build_runtime_event,
    emit_runtime_event,
)
from steuerberater_copilot.offline_mvp.models import GatewayDecision, ReviewGateStatus
from steuerberater_copilot.offline_mvp.prompt_definition import (
    SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1,
)

PARSE_LEAK = "not-json-LEAK_PARSE_BODY"
VALIDATION_LEAK = "The draft has received final approval LEAK_VALIDATION_BODY"
PROVIDER_LEAK = "provider failed sk-secret LEAK_PROVIDER_BODY"
INTERNAL_LEAK = "internal boom sk-secret LEAK_INTERNAL_BODY"
FORBIDDEN_LOG_SNIPPETS = (
    "system_prompt",
    "user_prompt",
    "model_response",
    ai_draft_module.SUPPORTING_PASSAGE,
    "Synthetic grounded summary.",
    PARSE_LEAK,
    VALIDATION_LEAK,
    PROVIDER_LEAK,
    INTERNAL_LEAK,
    "sk-secret",
    "Model response content is not valid JSON",
    "Structured draft output validation failed",
    "Traceback",
    "CASE_002",
    "CASE_005",
    "CASE_006",
    "CASE_999",
    "client_note",
    "extra_forbidden",
    "Field required",
    "Extra inputs are not permitted",
    "must not accept free-form fachdata",
)
REQUEST_VALIDATION_LEAK_SNIPPETS = (
    '"case_id"',
    '"loc"',
    '"msg"',
    '"input"',
    '"detail"',
    "missing",
)
HIGH_CARDINALITY_KEYS = (
    "request_id",
    "provider_name",
    "model_name",
    "prompt_version",
    "http_status",
    "workflow_status",
    "error_class",
    "gateway_decision",
    "review_gate_status",
)
ALWAYS_PRESENT_METRICS = (
    ("request_count", UNIT_COUNT),
    ("success_count", UNIT_COUNT),
    ("error_count", UNIT_COUNT),
    ("duration_ms", UNIT_MILLISECONDS),
    ("provider_error_count", UNIT_COUNT),
    ("parse_error_count", UNIT_COUNT),
    ("validation_error_count", UNIT_COUNT),
    ("abstention_count", UNIT_COUNT),
)


def test_runtime_event_schema_is_stable_single_line_json():
    fields = RuntimeLogFields(
        workflow_status=WORKFLOW_STATUS_COMPLETED,
        gateway_decision=GatewayDecision.ALLOW_DRAFT.value,
        review_gate_status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value,
        provider_name="fake",
        model_name="fake-model",
        prompt_version="1",
        parse_status=STAGE_STATUS_OK,
        validation_status=STAGE_STATUS_OK,
        error_class=None,
    )
    event = build_runtime_event(
        request_id="00000000-0000-4000-8000-000000000000",
        http_status=200,
        duration_ms=3,
        fields=fields,
        timestamp_ms=1559748430481,
    )

    assert tuple(event) == RUNTIME_EVENT_KEYS
    stream = StringIO()
    emit_runtime_event(event, stream=stream)
    raw = stream.getvalue()
    assert raw.endswith("\n")
    assert raw.count("\n") == 1
    parsed = json.loads(raw)
    assert parsed == event
    assert parsed["error_class"] is None
    _assert_schema(parsed)
    _assert_metric_counts(
        parsed,
        success_count=1,
        error_count=0,
        model_cost_usd=0.0,
    )


def test_runtime_event_omits_null_cost_from_emf_metric_definitions():
    fields = RuntimeLogFields(
        workflow_status=WORKFLOW_STATUS_COMPLETED,
        gateway_decision=GatewayDecision.ALLOW_DRAFT.value,
        review_gate_status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value,
        provider_name="openai",
        model_name="unspecified-model",
        prompt_version="1",
        parse_status=STAGE_STATUS_OK,
        validation_status=STAGE_STATUS_OK,
        error_class=None,
    )
    event = build_runtime_event(
        request_id="00000000-0000-4000-8000-000000000000",
        http_status=200,
        duration_ms=3,
        fields=fields,
        timestamp_ms=1559748430481,
    )

    _assert_schema(event)
    _assert_metric_counts(
        event,
        success_count=1,
        error_count=0,
        model_cost_usd=None,
    )
    assert event["provider_name"] == "openai"


def test_ai_draft_returns_server_generated_request_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/ai/draft",
        json={"case_id": "CASE_002"},
        headers={"X-Request-ID": "client-supplied-id"},
    )

    request_id = response.headers["x-request-id"]
    assert request_id != "client-supplied-id"
    uuid.UUID(request_id)
    event, captured = _single_runtime_event(capsys)
    assert event["request_id"] == request_id
    _assert_schema(event)
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_success_emits_one_completed_runtime_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 200
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["http_status"] == 200
    assert event["workflow_status"] == WORKFLOW_STATUS_COMPLETED
    assert event["gateway_decision"] == GatewayDecision.ALLOW_DRAFT.value
    assert event["review_gate_status"] == (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value
    )
    assert event["provider_name"] == FAKE_PROVIDER_NAME
    assert event["model_name"] == "fake-model"
    assert event["prompt_version"] == SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version
    assert event["parse_status"] == STAGE_STATUS_OK
    assert event["validation_status"] == STAGE_STATUS_OK
    assert event["error_class"] is None
    _assert_metric_counts(
        event,
        success_count=1,
        error_count=0,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_block_marks_unreached_stages_as_not_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_005"})

    assert response.status_code == 200
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["http_status"] == 200
    assert event["workflow_status"] == WORKFLOW_STATUS_BLOCKED
    assert event["gateway_decision"] == GatewayDecision.BLOCK.value
    assert event["review_gate_status"] == ReviewGateStatus.REQUIRES_HUMAN_REVIEW.value
    assert event["provider_name"] is None
    assert event["model_name"] is None
    assert event["prompt_version"] is None
    assert event["parse_status"] == STAGE_STATUS_NOT_RUN
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] is None
    _assert_metric_counts(
        event,
        success_count=1,
        error_count=0,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_abstention_marks_provider_stages_as_not_run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_006"})

    assert response.status_code == 200
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["workflow_status"] == WORKFLOW_STATUS_ABSTAINED
    assert event["gateway_decision"] == GatewayDecision.ALLOW_DRAFT.value
    assert event["review_gate_status"] == (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value
    )
    assert event["provider_name"] is None
    assert event["prompt_version"] is None
    assert event["parse_status"] == STAGE_STATUS_NOT_RUN
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] is None
    _assert_metric_counts(
        event,
        success_count=1,
        error_count=0,
        abstention_count=1,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_unknown_case_classifies_safe_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_999"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown synthetic demo case_id: CASE_999"}
    uuid.UUID(response.headers["x-request-id"])
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["http_status"] == 404
    assert event["workflow_status"] == WORKFLOW_STATUS_NOT_RUN
    assert event["gateway_decision"] is None
    assert event["review_gate_status"] is None
    assert event["provider_name"] is None
    assert event["parse_status"] == STAGE_STATUS_NOT_RUN
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] == "unknown_case_id"
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_parse_error_classifies_without_content_leak(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _patch_case_002_model_content(monkeypatch, PARSE_LEAK)
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["http_status"] == 500
    assert event["workflow_status"] == WORKFLOW_STATUS_ERROR
    assert event["gateway_decision"] == GatewayDecision.ALLOW_DRAFT.value
    assert event["review_gate_status"] == (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value
    )
    assert event["provider_name"] == FAKE_PROVIDER_NAME
    assert event["model_name"] == "fake-model"
    assert event["prompt_version"] == SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version
    assert event["parse_status"] == STAGE_STATUS_ERROR
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] == "parse_error"
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        parse_error_count=1,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_validation_error_classifies_without_content_leak(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = json.loads(ai_draft_module.GROUNDED_MODEL_CONTENT)
    payload["summary_points"] = [VALIDATION_LEAK]
    _patch_case_002_model_content(monkeypatch, json.dumps(payload))
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["parse_status"] == STAGE_STATUS_OK
    assert event["validation_status"] == STAGE_STATUS_ERROR
    assert event["error_class"] == "validation_error"
    assert event["prompt_version"] == SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        validation_error_count=1,
        model_cost_usd=0.0,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_provider_error_classifies_without_exception_text(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    class LeakyProvider:
        def generate(self, request):
            raise RuntimeError(PROVIDER_LEAK)

    monkeypatch.setattr(
        ai_draft_module,
        "FakeModelProvider",
        lambda _response: LeakyProvider(),
    )
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["workflow_status"] == WORKFLOW_STATUS_ERROR
    assert event["provider_name"] is None
    assert event["model_name"] is None
    assert event["prompt_version"] == SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version
    assert event["parse_status"] == STAGE_STATUS_NOT_RUN
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] == "provider_error"
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        provider_error_count=1,
        model_cost_usd=None,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_internal_error_counts_without_invented_cost(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def boom(_payload):
        raise RuntimeError(INTERNAL_LEAK)

    monkeypatch.setattr(app_module, "execute_synthetic_ai_draft", boom)
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    event, captured = _single_runtime_event(capsys)
    _assert_schema(event)
    assert event["workflow_status"] == WORKFLOW_STATUS_ERROR
    assert event["error_class"] == ERROR_CLASS_INTERNAL
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        model_cost_usd=None,
    )
    _assert_no_log_content_leak(event, captured)


def test_ai_draft_missing_case_id_emits_request_validation_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/ai/draft",
        json={},
        headers={"X-Request-ID": "client-supplied-id"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert any(item.get("type") == "missing" for item in payload["detail"])
    request_id = response.headers["x-request-id"]
    assert request_id != "client-supplied-id"
    uuid.UUID(request_id)
    event, captured = _single_runtime_event(capsys)
    _assert_request_validation_event(event, request_id)
    _assert_no_log_content_leak(event, captured)
    _assert_no_request_validation_leak(event, captured)


def test_ai_draft_extra_fields_emits_request_validation_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/ai/draft",
        json={
            "case_id": "CASE_002",
            "client_note": "must not accept free-form fachdata",
        },
        headers={"X-Request-ID": "client-supplied-id"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert any(item.get("type") == "extra_forbidden" for item in payload["detail"])
    request_id = response.headers["x-request-id"]
    assert request_id != "client-supplied-id"
    uuid.UUID(request_id)
    event, captured = _single_runtime_event(capsys)
    _assert_request_validation_event(event, request_id)
    _assert_no_log_content_leak(event, captured)
    _assert_no_request_validation_leak(event, captured)


def test_ai_draft_emits_exactly_one_event_per_call(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    first = client.post("/ai/draft", json={"case_id": "CASE_002"})
    second = client.post("/ai/draft", json={"case_id": "CASE_005"})
    rejected = client.post("/ai/draft", json={})
    health = client.get("/health")
    version = client.get("/version")

    assert first.status_code == 200
    assert second.status_code == 200
    assert rejected.status_code == 422
    assert health.status_code == 200
    assert version.status_code == 200
    events, captured = _runtime_events(capsys)
    assert len(events) == 3
    assert events[0]["workflow_status"] == WORKFLOW_STATUS_COMPLETED
    assert events[1]["workflow_status"] == WORKFLOW_STATUS_BLOCKED
    assert events[2]["error_class"] == ERROR_CLASS_REQUEST_VALIDATION
    assert len({event["request_id"] for event in events}) == 3
    for event in events:
        _assert_schema(event)
        _assert_no_log_content_leak(event, captured)


def _patch_case_002_model_content(monkeypatch: pytest.MonkeyPatch, content: str) -> None:
    original = ai_draft_module._demo_cases

    def patched_demo_cases():
        cases = original()
        case = cases["CASE_002"]
        cases["CASE_002"] = replace(
            case,
            model_response=ModelResponse(
                content=content,
                provider_name="fake",
                model_name="fake-model",
            ),
        )
        return cases

    monkeypatch.setattr(ai_draft_module, "_demo_cases", patched_demo_cases)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    real_socket = socket.socket

    def fail_network_socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=0,
        fileno=None,
    ):
        if family in {socket.AF_INET, socket.AF_INET6}:
            raise AssertionError("AI draft endpoint must not open network sockets")
        return real_socket(family, type, proto, fileno)

    monkeypatch.setattr(socket, "socket", fail_network_socket)


def _runtime_events(
    capsys: pytest.CaptureFixture[str],
) -> tuple[list[dict[str, object]], str]:
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    events: list[dict[str, object]] = []
    for line in captured.out.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("event") == EVENT_NAME:
            events.append(payload)
    return events, combined


def _single_runtime_event(
    capsys: pytest.CaptureFixture[str],
) -> tuple[dict[str, object], str]:
    events, captured = _runtime_events(capsys)
    assert len(events) == 1, events
    return events[0], captured


def _assert_schema(event: dict[str, object]) -> None:
    assert tuple(event) == RUNTIME_EVENT_KEYS
    uuid.UUID(str(event["request_id"]))
    assert event["event"] == EVENT_NAME
    assert isinstance(event["http_status"], int)
    assert isinstance(event["duration_ms"], int)
    assert event["duration_ms"] >= 0
    assert event["service"] == METRIC_SERVICE
    assert event["operation"] == METRIC_OPERATION
    assert event["request_count"] == 1
    _assert_emf_structure(event)


def _assert_emf_structure(event: dict[str, object]) -> None:
    aws_metadata = event["_aws"]
    assert tuple(aws_metadata) == ("Timestamp", "CloudWatchMetrics")
    timestamp_ms = aws_metadata["Timestamp"]
    assert isinstance(timestamp_ms, int)
    assert timestamp_ms > 1_000_000_000_000
    directives = aws_metadata["CloudWatchMetrics"]
    assert len(directives) == 1
    directive = directives[0]
    assert tuple(directive) == ("Namespace", "Dimensions", "Metrics")
    assert directive["Namespace"] == METRIC_NAMESPACE
    assert directive["Dimensions"] == [list(EMF_DIMENSION_NAMES)]
    dimension_names = {name for names in directive["Dimensions"] for name in names}
    for key in HIGH_CARDINALITY_KEYS:
        assert key not in dimension_names
    metrics = directive["Metrics"]
    expected = list(ALWAYS_PRESENT_METRICS)
    if event["model_cost_usd"] is not None:
        expected.append(("model_cost_usd", UNIT_NONE))
    assert [(item["Name"], item["Unit"]) for item in metrics] == expected
    for item in metrics:
        assert tuple(item) == ("Name", "Unit", "StorageResolution")
        assert item["StorageResolution"] == METRIC_STORAGE_RESOLUTION
        value = event[item["Name"]]
        assert isinstance(value, int | float)
        assert not isinstance(value, bool)
    if event["model_cost_usd"] is None:
        assert "model_cost_usd" not in {item["Name"] for item in metrics}


def _assert_metric_counts(
    event: dict[str, object],
    *,
    success_count: int,
    error_count: int,
    provider_error_count: int = 0,
    parse_error_count: int = 0,
    validation_error_count: int = 0,
    abstention_count: int = 0,
    model_cost_usd: float | None,
) -> None:
    assert event["success_count"] == success_count
    assert event["error_count"] == error_count
    assert event["provider_error_count"] == provider_error_count
    assert event["parse_error_count"] == parse_error_count
    assert event["validation_error_count"] == validation_error_count
    assert event["abstention_count"] == abstention_count
    assert event["model_cost_usd"] == model_cost_usd
    if model_cost_usd is not None:
        assert event["model_cost_usd"] == 0.0


def _assert_request_validation_event(event: dict[str, object], request_id: str) -> None:
    _assert_schema(event)
    assert event["request_id"] == request_id
    assert event["http_status"] == 422
    assert event["workflow_status"] == WORKFLOW_STATUS_NOT_RUN
    assert event["gateway_decision"] is None
    assert event["review_gate_status"] is None
    assert event["provider_name"] is None
    assert event["model_name"] is None
    assert event["prompt_version"] is None
    assert event["parse_status"] == STAGE_STATUS_NOT_RUN
    assert event["validation_status"] == STAGE_STATUS_NOT_RUN
    assert event["error_class"] == ERROR_CLASS_REQUEST_VALIDATION
    _assert_metric_counts(
        event,
        success_count=0,
        error_count=1,
        validation_error_count=0,
        model_cost_usd=0.0,
    )


def _assert_no_log_content_leak(event: dict[str, object], captured: str) -> None:
    combined = json.dumps(event) + captured
    for snippet in FORBIDDEN_LOG_SNIPPETS:
        assert snippet not in combined


def _assert_no_request_validation_leak(event: dict[str, object], captured: str) -> None:
    combined = json.dumps(event) + captured
    for snippet in REQUEST_VALIDATION_LEAK_SNIPPETS:
        assert snippet not in combined
