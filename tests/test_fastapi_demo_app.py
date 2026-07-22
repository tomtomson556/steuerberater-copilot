import pytest

from steuerberater_copilot.offline_mvp.prompt_definition import (
    SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1,
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
)


def test_fastapi_demo_health_and_version_use_fake_provider() -> None:
    client = _client()

    health_response = client.get("/health")
    version_response = client.get("/version")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert version_response.status_code == 200
    assert version_response.json()["provider_default"] == "FakeModelProvider"


def test_fastapi_demo_draft_for_case_002_omits_full_prompts() -> None:
    response = _client().get("/v1/demo/draft", params={"case_id": "CASE_002"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "CASE_002"
    assert payload["draft_available"] is True
    assert payload["structured_draft"]["summary_points"] == [
        "Synthetic API demo summary point."
    ]
    _assert_full_prompts_omitted(response.text)


def test_fastapi_demo_rag_for_case_002_omits_full_prompts() -> None:
    response = _client().get("/v1/demo/rag", params={"case_id": "CASE_002"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "CASE_002"
    assert payload["draft_available"] is True
    assert payload["retrieved_document_ids"] == ["SYNTHETIC_API_DEMO_SOURCE"]
    assert payload["structured_draft"]["summary_points"] == [
        "Synthetic API RAG summary point."
    ]
    assert payload["citations"] == [
        {
            "summary_point_index": 0,
            "document_id": "SYNTHETIC_API_DEMO_SOURCE",
            "supporting_text": "Synthetic orchard passage for API demo grounding.",
        }
    ]
    _assert_full_prompts_omitted(response.text)


def test_fastapi_demo_unknown_case_returns_404() -> None:
    response = _client().get("/v1/demo/draft", params={"case_id": "CASE_UNKNOWN"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown synthetic case_id."}


def _client():
    fastapi_testclient = pytest.importorskip("fastapi.testclient")

    from steuerberater_copilot.api.app import create_app
    from steuerberater_copilot.observability import RuntimeMetrics

    app = create_app()
    app.state.metrics = RuntimeMetrics()
    return fastapi_testclient.TestClient(app)


def _assert_full_prompts_omitted(response_text: str) -> None:
    prompt_fragments = (
        SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.system_prompt,
        SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.user_prompt_template,
        SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.system_prompt,
        SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.user_prompt_template,
        "Return exactly one valid JSON object with these keys in this order",
    )
    for fragment in prompt_fragments:
        assert fragment not in response_text
