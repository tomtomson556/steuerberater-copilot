import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOP_LEVEL_KEYS = {"case_id", "gateway", "risk", "review_gate", "draft"}
EXPECTED_CASE_IDS = {"CASE_001", "CASE_002", "CASE_003", "CASE_004"}


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
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["draft"]["available"] is False
    assert payload["draft"]["summary"] == []
    assert payload["draft"]["summary_points"] == []
    assert payload["draft"]["questions"] == []


def test_cli_fixture_cases_keep_expected_gateway_risk_and_draft_semantics():
    result = _run_cli("--all")

    payload = json.loads(result.stdout)
    by_case_id = {item["case_id"]: item for item in payload}

    assert by_case_id["CASE_002"]["gateway"]["decision"] == "allow_draft"
    assert by_case_id["CASE_002"]["risk"]["level"] == "A"
    assert by_case_id["CASE_002"]["draft"]["available"] is True
    assert by_case_id["CASE_002"]["draft"]["questions"] == []

    assert by_case_id["CASE_001"]["gateway"]["decision"] == "escalate"
    assert by_case_id["CASE_001"]["risk"]["level"] == "C"
    assert by_case_id["CASE_001"]["draft"]["available"] is False

    assert by_case_id["CASE_003"]["risk"]["level"] == "B"
    assert by_case_id["CASE_003"]["draft"]["available"] is False

    assert by_case_id["CASE_004"]["risk"]["level"] == "D"
    assert by_case_id["CASE_004"]["draft"]["available"] is False

    for case_id in ("CASE_001", "CASE_003", "CASE_004"):
        assert by_case_id[case_id]["draft"]["available"] is False


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

    gateway = payload["gateway"]
    assert isinstance(gateway, dict)
    assert {"decision", "reasons", "block_reasons"} <= set(gateway)
    assert isinstance(gateway["reasons"], list)
    assert isinstance(gateway["block_reasons"], list)

    risk = payload["risk"]
    assert isinstance(risk, dict)
    assert {"level", "review_required"} <= set(risk)
    assert isinstance(risk["review_required"], bool)

    review_gate = payload["review_gate"]
    assert isinstance(review_gate, dict)
    assert {"status", "decision"} <= set(review_gate)
    assert review_gate["decision"] == review_gate["status"]

    draft = payload["draft"]
    assert isinstance(draft, dict)
    assert {"available", "draft_only", "summary", "questions"} <= set(draft)
    assert isinstance(draft["available"], bool)
    assert isinstance(draft["draft_only"], bool)
    assert isinstance(draft["summary"], list)
    assert isinstance(draft["questions"], list)


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
