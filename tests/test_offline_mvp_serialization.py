import json
import os
import subprocess
import sys
from pathlib import Path

from steuerberater_copilot.offline_mvp.review_handoff import render_review_handoff
from steuerberater_copilot.offline_mvp.serialization import workflow_to_json
from steuerberater_copilot.offline_mvp.workflow import (
    build_mock_workflow,
    load_fixture_cases,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOP_LEVEL_KEYS = {"case_id", "gateway", "risk", "review_gate", "draft"}
EXPECTED_GATEWAY_KEYS = {"decision", "checks", "reasons", "block_reasons"}
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
    "review_status",
    "summary",
    "summary_points",
    "questions",
    "handoff_notes",
    "disclaimers",
}


def test_workflow_to_json_preserves_top_level_contract_for_all_cases() -> None:
    for case in load_fixture_cases():
        payload = workflow_to_json(build_mock_workflow(case))

        assert set(payload) == EXPECTED_TOP_LEVEL_KEYS


def test_workflow_to_json_preserves_nested_contract_for_all_cases() -> None:
    for case in load_fixture_cases():
        payload = workflow_to_json(build_mock_workflow(case))

        assert set(payload["gateway"]) == EXPECTED_GATEWAY_KEYS
        assert set(payload["risk"]) == EXPECTED_RISK_KEYS
        assert set(payload["review_gate"]) == EXPECTED_REVIEW_GATE_KEYS
        assert set(payload["draft"]) == EXPECTED_DRAFT_KEYS


def test_workflow_to_json_preserves_alias_invariants_for_all_cases() -> None:
    for case in load_fixture_cases():
        payload = workflow_to_json(build_mock_workflow(case))

        assert payload["review_gate"]["decision"] == payload["review_gate"]["status"]
        assert payload["draft"]["summary"] == payload["draft"]["summary_points"]


def test_workflow_to_json_keeps_restrictive_cases_without_available_draft() -> None:
    cases = _cases_by_id()

    for case_id in ("CASE_001", "CASE_003", "CASE_004"):
        payload = workflow_to_json(build_mock_workflow(cases[case_id]))

        assert payload["draft"]["available"] is False
        assert payload["draft"]["summary"] == []
        assert payload["draft"]["summary_points"] == []


def test_workflow_to_json_keeps_case_001_questions_review_bound() -> None:
    cases = _cases_by_id()
    payload = workflow_to_json(build_mock_workflow(cases["CASE_001"]))

    assert payload["case_id"] == "CASE_001"
    assert payload["gateway"]["decision"] == "escalate"
    assert payload["risk"]["level"] == "C"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["draft"]["available"] is False
    assert payload["draft"]["questions"]
    assert payload["draft"]["summary"] == []
    assert payload["draft"]["summary_points"] == []


def test_workflow_to_json_keeps_case_002_as_available_draft_case() -> None:
    cases = _cases_by_id()
    payload = workflow_to_json(build_mock_workflow(cases["CASE_002"]))

    assert payload["case_id"] == "CASE_002"
    assert payload["gateway"]["decision"] == "allow_draft"
    assert payload["risk"]["level"] == "A"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is True
    assert payload["draft"]["available"] is True
    assert payload["draft"]["summary"]
    assert payload["draft"]["summary"] == payload["draft"]["summary_points"]
    assert payload["draft"]["draft_only"] is True


def test_json_and_review_handoff_use_shared_draft_availability_rule() -> None:
    for case in load_fixture_cases():
        output = build_mock_workflow(case)
        payload = workflow_to_json(output)
        handoff = render_review_handoff(output)

        assert payload["draft"]["available"] is output.draft_available
        assert f"Draft available: `{output.draft_available}`" in handoff


def test_cli_case_output_matches_serializer_payload_for_all_cases() -> None:
    cases = _cases_by_id()

    for case_id, case in cases.items():
        result = _run_cli("--case", case_id)

        assert json.loads(result.stdout) == workflow_to_json(build_mock_workflow(case))


def test_cli_all_output_matches_serializer_payloads() -> None:
    cases = load_fixture_cases()

    result = _run_cli("--all")

    assert json.loads(result.stdout) == [
        workflow_to_json(build_mock_workflow(case)) for case in cases
    ]


def _cases_by_id():
    return {case.case_id: case for case in load_fixture_cases()}


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
        check=True,
    )
