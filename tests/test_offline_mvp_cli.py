import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOP_LEVEL_KEYS = {"case_id", "gateway", "risk", "review_gate", "draft"}
EXPECTED_GATEWAY_KEYS = {"decision", "reasons", "block_reasons", "checks"}
EXPECTED_RISK_KEYS = {"level", "review_required", "basis"}
EXPECTED_REVIEW_GATE_KEYS = {
    "status",
    "decision",
    "allows_offline_mock_continuation",
    "reason",
}
EXPECTED_DRAFT_KEYS = {
    "available",
    "draft_only",
    "summary",
    "summary_points",
    "questions",
    "review_status",
    "handoff_notes",
    "disclaimers",
}
EXPECTED_CASE_IDS = {"CASE_001", "CASE_002", "CASE_003", "CASE_004"}
EXPECTED_CASE_SEMANTICS = {
    "CASE_001": {
        "gateway_decision": "escalate",
        "risk_level": "C",
        "draft_available": False,
        "review_status": "Escalated",
        "review_gate_status": "requires_human_review",
    },
    "CASE_002": {
        "gateway_decision": "allow_draft",
        "risk_level": "A",
        "draft_available": True,
        "review_status": "Draft",
        "review_gate_status": "allowed_offline_mock_continuation",
    },
    "CASE_003": {
        "gateway_decision": "allow_draft",
        "risk_level": "B",
        "draft_available": False,
        "review_status": "In review",
        "review_gate_status": "requires_human_review",
    },
    "CASE_004": {
        "gateway_decision": "allow_draft",
        "risk_level": "D",
        "draft_available": False,
        "review_status": "Escalated",
        "review_gate_status": "requires_human_review",
    },
}
GATEWAY_DECISIONS = {"allow_draft", "block", "escalate"}
RISK_LEVELS = {"A", "B", "C", "D"}
REVIEW_GATE_STATUSES = {
    "allowed_offline_mock_continuation",
    "requires_human_review",
}
REVIEW_STATUSES = {"Draft", "In review", "Rejected", "Escalated"}


def test_cli_case_outputs_valid_json_object():
    result = _run_cli("--case", "CASE_001")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["case_id"] == "CASE_001"
    _assert_cli_json_contract(payload)


def test_cli_all_outputs_valid_json_list():
    result = _run_cli("--all")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert len(payload) == len(EXPECTED_CASE_IDS)
    assert {item["case_id"] for item in payload} == EXPECTED_CASE_IDS
    for item in payload:
        _assert_cli_json_contract(item)


def test_cli_case_002_allows_draft_when_existing_logic_allows_it():
    result = _run_cli("--case", "CASE_002")

    payload = json.loads(result.stdout)
    _assert_cli_json_contract(payload)
    assert payload["gateway"]["decision"] == "allow_draft"
    assert payload["risk"]["level"] == "A"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is True
    assert payload["draft"]["available"] is True
    assert payload["draft"]["draft_only"] is True
    assert payload["draft"]["summary"]
    assert payload["draft"]["summary"] == payload["draft"]["summary_points"]
    assert payload["draft"]["summary_points"]
    assert payload["draft"]["questions"] == []


def test_cli_escalated_case_has_no_available_draft():
    result = _run_cli("--case", "CASE_001")

    payload = json.loads(result.stdout)
    _assert_cli_json_contract(payload)
    assert payload["gateway"]["decision"] == "escalate"
    assert payload["risk"]["level"] == "C"
    assert payload["review_gate"]["status"] == "requires_human_review"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["draft"]["available"] is False
    assert payload["draft"]["summary"] == []
    assert payload["draft"]["summary_points"] == []
    assert payload["draft"]["questions"] == [
        "Bitte im Human Review intern klaeren: "
        "Quellenbezug fuer Beispiel-Dokument DOCUMENT_001.",
        "Bitte im Human Review intern klaeren: "
        "Zeitraumabgrenzung fuer synthetische Zahlungsuebersicht.",
    ]
    assert all(isinstance(question, str) for question in payload["draft"]["questions"])
    assert any(
        "Quellenbezug fuer Beispiel-Dokument DOCUMENT_001" in question
        for question in payload["draft"]["questions"]
    )
    assert any(
        "Zeitraumabgrenzung fuer synthetische Zahlungsuebersicht" in question
        for question in payload["draft"]["questions"]
    )


def test_cli_fixture_cases_keep_expected_gateway_risk_and_draft_semantics():
    result = _run_cli("--all")

    payload = json.loads(result.stdout)
    by_case_id = {item["case_id"]: item for item in payload}

    for case_id, expected in EXPECTED_CASE_SEMANTICS.items():
        item = by_case_id[case_id]
        assert item["gateway"]["decision"] == expected["gateway_decision"]
        assert item["risk"]["level"] == expected["risk_level"]
        assert item["draft"]["available"] is expected["draft_available"]
        assert item["draft"]["review_status"] == expected["review_status"]
        assert item["review_gate"]["status"] == expected["review_gate_status"]

    assert by_case_id["CASE_002"]["draft"]["questions"] == []
    assert by_case_id["CASE_001"]["draft"]["questions"]
    assert by_case_id["CASE_001"]["review_gate"][
        "allows_offline_mock_continuation"
    ] is False
    for case_id in ("CASE_003", "CASE_004"):
        assert by_case_id[case_id]["draft"]["questions"] == []
    for case_id in ("CASE_001", "CASE_003", "CASE_004"):
        assert by_case_id[case_id]["draft"]["available"] is False
        assert by_case_id[case_id]["draft"]["summary"] == []
        assert by_case_id[case_id]["draft"]["summary_points"] == []


def test_cli_escalate_or_block_and_risk_b_c_d_have_no_available_draft():
    result = _run_cli("--all")

    payload = json.loads(result.stdout)
    for item in payload:
        if item["gateway"]["decision"] in {"escalate", "block"}:
            assert item["draft"]["available"] is False
        if item["risk"]["level"] in {"B", "C", "D"}:
            assert item["draft"]["available"] is False


def test_cli_unknown_case_returns_non_zero_with_stderr():
    result = _run_cli("--case", "CASE_UNKNOWN")

    assert result.returncode != 0
    assert result.stdout == ""
    assert "Unknown synthetic case ID: CASE_UNKNOWN" in result.stderr


def test_cli_list_cases_outputs_case_ids():
    result = _run_cli("--list-cases")

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == ["CASE_001", "CASE_002", "CASE_003", "CASE_004"]


def _assert_cli_json_contract(payload: dict[str, object]) -> None:
    assert set(payload) == EXPECTED_TOP_LEVEL_KEYS
    assert isinstance(payload["case_id"], str)

    gateway = payload["gateway"]
    assert isinstance(gateway, dict)
    assert set(gateway) == EXPECTED_GATEWAY_KEYS
    assert isinstance(gateway["decision"], str)
    assert gateway["decision"] in GATEWAY_DECISIONS
    _assert_string_list(gateway["reasons"])
    _assert_string_list(gateway["block_reasons"])
    _assert_string_list(gateway["checks"])

    risk = payload["risk"]
    assert isinstance(risk, dict)
    assert set(risk) == EXPECTED_RISK_KEYS
    assert isinstance(risk["level"], str)
    assert risk["level"] in RISK_LEVELS
    assert isinstance(risk["review_required"], bool)
    _assert_string_list(risk["basis"])

    review_gate = payload["review_gate"]
    assert isinstance(review_gate, dict)
    assert set(review_gate) == EXPECTED_REVIEW_GATE_KEYS
    assert isinstance(review_gate["status"], str)
    assert review_gate["status"] in REVIEW_GATE_STATUSES
    assert isinstance(review_gate["decision"], str)
    assert review_gate["decision"] == review_gate["status"]
    assert isinstance(review_gate["allows_offline_mock_continuation"], bool)
    assert isinstance(review_gate["reason"], str)

    draft = payload["draft"]
    assert isinstance(draft, dict)
    assert set(draft) == EXPECTED_DRAFT_KEYS
    assert isinstance(draft["available"], bool)
    assert isinstance(draft["draft_only"], bool)
    assert isinstance(draft["review_status"], str)
    assert draft["review_status"] in REVIEW_STATUSES
    _assert_string_list(draft["summary"])
    _assert_string_list(draft["summary_points"])
    assert draft["summary"] == draft["summary_points"]
    _assert_string_list(draft["questions"])
    _assert_string_list(draft["handoff_notes"])
    _assert_string_list(draft["disclaimers"])


def _assert_string_list(value: object) -> None:
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = (
        src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    )
    return subprocess.run(
        [sys.executable, "-m", "steuerberater_copilot.offline_mvp", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
