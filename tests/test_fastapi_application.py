import json
import socket
from importlib.metadata import PackageNotFoundError

import pytest
from fastapi.testclient import TestClient

from steuerberater_copilot.api import app as api_app
from steuerberater_copilot.api import create_app
from steuerberater_copilot.api.ai_draft import (
    SUPPORTING_PASSAGE,
    known_synthetic_ai_draft_case_ids,
)
from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    ReviewGateStatus,
    ReviewStatus,
    RiskLevel,
)


def test_create_app_returns_independent_instances():
    first = create_app()
    second = create_app()

    assert first is not second
    assert first.title == "steuerberater-copilot"
    assert second.title == "steuerberater-copilot"


def test_health_returns_deterministic_ok_payload():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok"}


def test_version_returns_package_metadata_version(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_version(package_name: str) -> str:
        calls.append(package_name)
        return "9.8.7"

    monkeypatch.setattr(api_app, "version", fake_version)
    client = TestClient(create_app())

    response = client.get("/version")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"version": "9.8.7"}
    assert calls == [api_app.PACKAGE_NAME]


def test_version_returns_unknown_when_metadata_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    def missing_version(package_name: str) -> str:
        raise PackageNotFoundError(package_name)

    monkeypatch.setattr(api_app, "version", missing_version)
    client = TestClient(create_app())

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "unknown"}


def test_version_does_not_load_workflow_or_fixtures(monkeypatch: pytest.MonkeyPatch):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("version endpoint must not load workflow or fixtures")

    monkeypatch.setattr(api_app, "version", lambda _name: "1.2.3")
    monkeypatch.setattr(
        "steuerberater_copilot.offline_mvp.workflow.load_fixture_cases",
        fail_if_called,
        raising=False,
    )
    monkeypatch.setattr(
        "steuerberater_copilot.offline_mvp.workflow.build_mock_workflow",
        fail_if_called,
        raising=False,
    )
    client = TestClient(create_app())

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "1.2.3"}


def test_unknown_route_returns_404():
    client = TestClient(create_app())

    response = client.get("/does-not-exist")

    assert response.status_code == 404


def test_ai_draft_returns_grounded_draft_for_known_synthetic_case(
    monkeypatch: pytest.MonkeyPatch,
):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    payload = response.json()
    assert payload == {
        "case_id": "CASE_002",
        "gateway": {
            "decision": GatewayDecision.ALLOW_DRAFT.value,
            "checks": [
                "request_purpose_documented",
                "request_data_classes_allowed",
                "request_pseudonyms_non_reidentifying",
                "request_review_path_present",
                "request_context_minimized",
                "response_keeps_draft_status",
                "response_requires_human_review_when_needed",
                "response_no_productive_transmission",
                "response_no_tax_advice_or_calculation_claim",
            ],
            "escalation_reasons": [],
            "block_reasons": [],
        },
        "risk": {
            "level": RiskLevel.CLASS_A.value,
            "review_required": False,
            "basis": ["internal_admin_note"],
        },
        "review_gate": {
            "status": ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value,
            "allows_offline_mock_continuation": True,
            "reason": "RiskLevel A permits offline mock continuation only.",
        },
        "abstained_for_missing_evidence": False,
        "draft": {
            "review_status": ReviewStatus.DRAFT.value,
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
        },
    }
    _assert_no_raw_model_or_prompt_leak(payload)


def test_ai_draft_rejects_unknown_case_id(monkeypatch: pytest.MonkeyPatch):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_999"})

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Unknown synthetic demo case_id: CASE_999",
    }


def test_ai_draft_abstains_for_missing_evidence(monkeypatch: pytest.MonkeyPatch):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_006"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "CASE_006"
    assert payload["gateway"]["decision"] == GatewayDecision.ALLOW_DRAFT.value
    assert payload["risk"]["level"] == RiskLevel.CLASS_A.value
    assert payload["review_gate"]["allows_offline_mock_continuation"] is True
    assert payload["abstained_for_missing_evidence"] is True
    assert payload["draft"] is None
    _assert_no_raw_model_or_prompt_leak(payload)


def test_ai_draft_returns_controlled_gateway_block(monkeypatch: pytest.MonkeyPatch):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_005"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "CASE_005"
    assert payload["gateway"]["decision"] == GatewayDecision.BLOCK.value
    assert payload["gateway"]["block_reasons"] == ["forbidden_data_class:original_pii"]
    assert payload["risk"]["level"] == RiskLevel.CLASS_D.value
    assert payload["risk"]["review_required"] is True
    assert payload["review_gate"]["status"] == (
        ReviewGateStatus.REQUIRES_HUMAN_REVIEW.value
    )
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["abstained_for_missing_evidence"] is False
    assert payload["draft"] is None
    _assert_no_raw_model_or_prompt_leak(payload)


def test_ai_draft_rejects_extra_request_fields(monkeypatch: pytest.MonkeyPatch):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/ai/draft",
        json={
            "case_id": "CASE_002",
            "client_note": "must not accept free-form fachdata",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item.get("type") == "extra_forbidden" for item in detail)


def test_ai_draft_rejects_missing_case_id(monkeypatch: pytest.MonkeyPatch):
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={})

    assert response.status_code == 422


def test_ai_draft_demo_catalog_is_synthetic_only():
    assert known_synthetic_ai_draft_case_ids() == frozenset(
        {"CASE_002", "CASE_005", "CASE_006"}
    )


def test_ai_draft_uses_fake_model_provider_only(monkeypatch: pytest.MonkeyPatch):
    from steuerberater_copilot.ai import FakeModelProvider
    from steuerberater_copilot.api import ai_draft as ai_draft_module

    created: list[object] = []
    original = FakeModelProvider

    def tracking_provider(response):
        provider = original(response)
        created.append(provider)
        return provider

    monkeypatch.setattr(ai_draft_module, "FakeModelProvider", tracking_provider)
    _block_network(monkeypatch)
    client = TestClient(create_app())

    response = client.post("/ai/draft", json={"case_id": "CASE_002"})

    assert response.status_code == 200
    assert len(created) == 1
    assert isinstance(created[0], original)
    assert created[0].requests[0].prompt_id == "synthetic_grounded_draft"


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


def _assert_no_raw_model_or_prompt_leak(payload: dict) -> None:
    serialized = json.dumps(payload)
    assert "system_prompt" not in serialized
    assert "user_prompt" not in serialized
    assert "model_response" not in serialized
    assert "provider_name" not in serialized
    assert "fake-model" not in serialized
