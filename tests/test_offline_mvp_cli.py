import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cli_case_outputs_valid_json_object():
    result = _run_cli("--case", "CASE_001")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["case_id"] == "CASE_001"
    assert set(payload) == {"case_id", "gateway", "risk", "review_gate", "draft"}


def test_cli_all_outputs_valid_json_list():
    result = _run_cli("--all")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert {item["case_id"] for item in payload} == {
        "CASE_001",
        "CASE_002",
        "CASE_003",
        "CASE_004",
    }


def test_cli_case_002_allows_draft_when_existing_logic_allows_it():
    result = _run_cli("--case", "CASE_002")

    payload = json.loads(result.stdout)
    assert payload["gateway"]["decision"] == "allow_draft"
    assert payload["risk"]["level"] == "A"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is True
    assert payload["draft"]["available"] is True
    assert payload["draft"]["draft_only"] is True
    assert payload["draft"]["summary_points"]


def test_cli_escalated_case_has_no_available_draft():
    result = _run_cli("--case", "CASE_001")

    payload = json.loads(result.stdout)
    assert payload["gateway"]["decision"] == "escalate"
    assert payload["risk"]["level"] == "C"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["draft"]["available"] is False
    assert payload["draft"]["summary_points"] == []
    assert payload["draft"]["questions"] == []


def test_cli_risk_b_c_and_d_cases_have_no_available_draft():
    result = _run_cli("--all")

    payload = json.loads(result.stdout)
    by_case_id = {item["case_id"]: item for item in payload}
    for case_id in ("CASE_001", "CASE_003", "CASE_004"):
        assert by_case_id[case_id]["draft"]["available"] is False


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
