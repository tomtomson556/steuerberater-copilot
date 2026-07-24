from importlib.metadata import PackageNotFoundError

import pytest
from fastapi.testclient import TestClient

from steuerberater_copilot.api import app as api_app
from steuerberater_copilot.api import create_app


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
