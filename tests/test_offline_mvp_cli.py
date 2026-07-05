import json
import os
import subprocess
import sys
import tomllib
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
EXPECTED_WORKLIST_KEYS = {
    "case_id",
    "priority",
    "gateway",
    "risk",
    "review_gate",
    "draft",
    "open_questions_count",
    "open_questions",
}
EXPECTED_WORKLIST_GATEWAY_KEYS = {"decision", "reasons", "block_reasons"}
EXPECTED_WORKLIST_RISK_KEYS = {"level", "review_required", "basis"}
EXPECTED_WORKLIST_REVIEW_GATE_KEYS = {
    "status",
    "allows_offline_mock_continuation",
    "reason",
}
EXPECTED_WORKLIST_DRAFT_KEYS = {"available", "review_status"}
EXPECTED_SUMMARY_KEYS = {
    "total_cases",
    "gateway",
    "risk",
    "review_gate",
    "draft_availability",
    "open_questions",
    "highest_priority_cases",
}
EXPECTED_FILTERED_SUMMARY_KEYS = EXPECTED_SUMMARY_KEYS | {
    "summary_scope",
    "applied_filters",
}
EXPECTED_CASE_IDS = {"CASE_001", "CASE_002", "CASE_003", "CASE_004", "CASE_005"}
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
    "CASE_005": {
        "gateway_decision": "block",
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
AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS = {
    "approved",
    "final",
    "freigegeben",
    "rejected",
}


def test_pyproject_declares_offline_mvp_console_script():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["steuerberater-copilot-offline-mvp"] == (
        "steuerberater_copilot.offline_mvp.__main__:main"
    )


def test_cli_version_outputs_text_without_loading_workflow_json():
    result = _run_cli("--version")

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.startswith("steuerberater-copilot-offline-mvp ")
    assert result.stdout.endswith("\n")
    assert not result.stdout.lstrip().startswith(("{", "["))
    assert "CASE_001" not in result.stdout
    assert "gateway" not in result.stdout
    assert "review_gate" not in result.stdout


def test_cli_version_rejects_review_handoff_without_writing_file(tmp_path):
    handoff_path = tmp_path / "version.md"

    result = _run_cli("--version", "--review-handoff", str(handoff_path))

    assert result.returncode == 2
    assert result.stdout == ""
    assert "--review-handoff requires --case or --all." in result.stderr
    assert not handoff_path.exists()


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


def test_cli_block_case_stays_review_bound_without_available_draft():
    result = _run_cli("--case", "CASE_005")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_cli_json_contract(payload)
    assert payload["case_id"] == "CASE_005"
    assert payload["gateway"]["decision"] == "block"
    assert payload["gateway"]["reasons"] == []
    assert payload["gateway"]["block_reasons"] == ["forbidden_data_class:original_pii"]
    assert payload["risk"]["level"] == "D"
    assert payload["review_gate"]["status"] == "requires_human_review"
    assert payload["review_gate"]["allows_offline_mock_continuation"] is False
    assert payload["draft"]["available"] is False
    assert payload["draft"]["summary"] == []
    assert payload["draft"]["summary_points"] == []
    assert payload["draft"]["questions"] == []


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
    for case_id in ("CASE_003", "CASE_004", "CASE_005"):
        assert by_case_id[case_id]["draft"]["questions"] == []
    for case_id in ("CASE_001", "CASE_003", "CASE_004", "CASE_005"):
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
    assert json.loads(result.stdout) == [
        "CASE_001",
        "CASE_002",
        "CASE_003",
        "CASE_004",
        "CASE_005",
    ]


def test_cli_review_worklist_outputs_valid_json_list():
    result = _run_cli("--review-worklist")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert {item["case_id"] for item in payload} == EXPECTED_CASE_IDS
    assert [item["case_id"] for item in payload] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
        "CASE_003",
        "CASE_002",
    ]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_limit_outputs_existing_first_entries():
    result = _run_cli("--review-worklist", "--review-limit", "3")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_min_risk_outputs_existing_matching_entries():
    result = _run_cli("--review-worklist", "--review-min-risk", "D")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == ["CASE_005", "CASE_004"]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_gateway_outputs_existing_matching_entries():
    result = _run_cli("--review-worklist", "--review-gateway", "block")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == ["CASE_005"]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_open_questions_only_outputs_existing_matching_entries():
    result = _run_cli("--review-worklist", "--review-open-questions-only")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == ["CASE_001"]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_combines_filters_in_existing_order():
    result = _run_cli("--review-worklist", "--review-min-risk", "C", "--review-limit", "2")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == ["CASE_005", "CASE_004"]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_worklist_combined_filters_can_return_empty_json_list():
    result = _run_cli(
        "--review-worklist",
        "--review-gateway",
        "block",
        "--review-open-questions-only",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.lstrip().startswith("[")
    assert "# Review Handoff" not in result.stdout
    assert "```" not in result.stdout
    assert json.loads(result.stdout) == []


def test_cli_review_worklist_limit_applies_after_gateway_filter():
    result = _run_cli(
        "--review-worklist",
        "--review-gateway",
        "allow_draft",
        "--review-limit",
        "2",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert [item["case_id"] for item in payload] == ["CASE_004", "CASE_003"]
    for item in payload:
        _assert_review_worklist_contract(item)


def test_cli_review_limit_zero_is_rejected():
    result = _run_cli("--review-worklist", "--review-limit", "0")

    assert result.returncode == 2
    assert result.stdout == ""


def test_cli_review_worklist_rejects_invalid_filter_values():
    invalid_commands = [
        ("--review-worklist", "--review-min-risk", "E"),
        ("--review-worklist", "--review-gateway", "unknown"),
    ]

    for args in invalid_commands:
        result = _run_cli(*args)

        assert result.returncode == 2
        assert result.stdout == ""


def test_cli_review_filters_require_review_worklist_or_review_summary():
    invalid_commands = [
        ("--review-min-risk", "C"),
        ("--all", "--review-min-risk", "C"),
        ("--case", "CASE_001", "--review-gateway", "block"),
        ("--list-cases", "--review-open-questions-only"),
    ]

    for args in invalid_commands:
        result = _run_cli(*args)

        assert result.returncode == 2
        assert result.stdout == ""
        if "one of the arguments" not in result.stderr:
            assert (
                "review filters require --review-worklist or --review-summary."
                in result.stderr
            )


def test_cli_review_worklist_keeps_block_case_first_and_review_bound():
    result = _run_cli("--review-worklist")

    payload = json.loads(result.stdout)
    block_item = payload[0]
    assert block_item["case_id"] == "CASE_005"
    assert block_item["priority"] == 100
    assert block_item["gateway"]["decision"] == "block"
    assert block_item["gateway"]["block_reasons"] == [
        "forbidden_data_class:original_pii"
    ]
    assert block_item["risk"]["level"] == "D"
    assert block_item["draft"]["available"] is False
    assert block_item["review_gate"]["status"] == "requires_human_review"
    assert block_item["review_gate"]["allows_offline_mock_continuation"] is False
    assert block_item["open_questions_count"] == 0
    assert block_item["open_questions"] == []


def test_cli_review_worklist_rejects_review_handoff_without_workflow_result(tmp_path):
    result = _run_cli(
        "--review-worklist",
        "--review-handoff",
        str(tmp_path / "handoff.md"),
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "--review-handoff requires --case or --all." in result.stderr


def test_cli_workflow_does_not_auto_emit_final_or_human_review_decisions():
    result = _run_cli("--all")

    payload = json.loads(result.stdout)
    for item in payload:
        review_status = item["draft"]["review_status"].lower()
        assert not any(
            marker in review_status
            for marker in AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS
        )


def test_cli_review_handoff_writes_markdown_without_changing_stdout_json(tmp_path):
    handoff_path = tmp_path / "nested" / "review-handoff.md"

    result_with_handoff = _run_cli(
        "--case",
        "CASE_001",
        "--review-handoff",
        str(handoff_path),
    )
    result_without_handoff = _run_cli("--case", "CASE_001")

    assert result_with_handoff.returncode == 0
    assert result_with_handoff.stderr == ""
    assert json.loads(result_with_handoff.stdout) == json.loads(result_without_handoff.stdout)
    _assert_cli_json_contract(json.loads(result_with_handoff.stdout))
    assert handoff_path.exists()
    handoff = handoff_path.read_text(encoding="utf-8")
    assert handoff.startswith("# Review Handoff\n")
    assert "- Case ID: `CASE_001`" in handoff
    assert "Draft-/Review-Artefakt" in handoff


def test_cli_list_cases_rejects_review_handoff_without_workflow_result(tmp_path):
    result = _run_cli("--list-cases", "--review-handoff", str(tmp_path / "handoff.md"))

    assert result.returncode != 0
    assert result.stdout == ""
    assert "--review-handoff requires --case or --all." in result.stderr


def test_cli_review_worklist_stdout_contains_no_markdown() -> None:
    result = _run_cli("--review-worklist")

    assert result.returncode == 0
    assert result.stdout.lstrip().startswith("[")
    assert "# Review Handoff" not in result.stdout
    assert "```" not in result.stdout
    json.loads(result.stdout)


def test_cli_review_summary_outputs_valid_json_object() -> None:
    result = _run_cli("--review-summary")

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.lstrip().startswith("{")
    payload = json.loads(result.stdout)
    assert set(payload) == EXPECTED_SUMMARY_KEYS
    assert payload["total_cases"] == 5
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]
    assert "summary_scope" not in payload
    assert "applied_filters" not in payload


def test_cli_review_summary_counts_current_fixture_distribution() -> None:
    result = _run_cli("--review-summary")

    payload = json.loads(result.stdout)
    assert payload["gateway"] == {
        "allow_draft": 3,
        "escalate": 1,
        "block": 1,
    }
    assert payload["risk"] == {"A": 1, "B": 1, "C": 1, "D": 2}
    assert payload["review_gate"] == {
        "allowed_offline_mock_continuation": 1,
        "requires_human_review": 4,
    }
    assert payload["draft_availability"] == {
        "available": 1,
        "unavailable": 4,
    }
    assert payload["open_questions"] == {
        "total": 2,
        "cases_with_open_questions": ["CASE_001"],
    }


def test_cli_review_summary_min_risk_filter_counts_filtered_cases() -> None:
    result = _run_cli("--review-summary", "--review-min-risk", "C")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_filtered_summary_contract(payload, {"review_min_risk": "C"})
    assert payload["total_cases"] == 3
    assert payload["gateway"] == {"allow_draft": 1, "escalate": 1, "block": 1}
    assert payload["risk"] == {"A": 0, "B": 0, "C": 1, "D": 2}
    assert payload["review_gate"] == {
        "allowed_offline_mock_continuation": 0,
        "requires_human_review": 3,
    }
    assert payload["draft_availability"] == {"available": 0, "unavailable": 3}
    assert payload["open_questions"] == {
        "total": 2,
        "cases_with_open_questions": ["CASE_001"],
    }
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]


def test_cli_review_summary_gateway_filter_counts_filtered_cases() -> None:
    result = _run_cli("--review-summary", "--review-gateway", "block")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_filtered_summary_contract(payload, {"review_gateway": "block"})
    assert payload["total_cases"] == 1
    assert payload["gateway"] == {"allow_draft": 0, "escalate": 0, "block": 1}
    assert payload["risk"] == {"A": 0, "B": 0, "C": 0, "D": 1}
    assert payload["review_gate"] == {
        "allowed_offline_mock_continuation": 0,
        "requires_human_review": 1,
    }
    assert payload["draft_availability"] == {"available": 0, "unavailable": 1}
    assert payload["open_questions"] == {
        "total": 0,
        "cases_with_open_questions": [],
    }
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_005"
    ]


def test_cli_review_summary_open_questions_filter_counts_filtered_cases() -> None:
    result = _run_cli("--review-summary", "--review-open-questions-only")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_filtered_summary_contract(payload, {"review_open_questions_only": True})
    assert payload["total_cases"] == 1
    assert payload["gateway"] == {"allow_draft": 0, "escalate": 1, "block": 0}
    assert payload["risk"] == {"A": 0, "B": 0, "C": 1, "D": 0}
    assert payload["open_questions"] == {
        "total": 2,
        "cases_with_open_questions": ["CASE_001"],
    }
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_001"
    ]


def test_cli_review_summary_limit_filter_counts_existing_first_entries() -> None:
    result = _run_cli("--review-summary", "--review-limit", "3")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_filtered_summary_contract(payload, {"review_limit": 3})
    assert payload["total_cases"] == 3
    assert payload["gateway"] == {"allow_draft": 1, "escalate": 1, "block": 1}
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]


def test_cli_review_summary_filtered_scope_matches_review_worklist_scope() -> None:
    scenarios = [
        (("--review-min-risk", "C"), {"review_min_risk": "C"}),
        (("--review-gateway", "block"), {"review_gateway": "block"}),
        (("--review-open-questions-only",), {"review_open_questions_only": True}),
    ]

    for args, applied_filters in scenarios:
        summary_result = _run_cli("--review-summary", *args)
        worklist_result = _run_cli("--review-worklist", *args)

        assert summary_result.returncode == 0
        assert summary_result.stderr == ""
        assert worklist_result.returncode == 0
        assert worklist_result.stderr == ""

        summary_payload = json.loads(summary_result.stdout)
        worklist_payload = json.loads(worklist_result.stdout)
        worklist_case_ids = [item["case_id"] for item in worklist_payload]
        worklist_open_question_case_ids = [
            item["case_id"]
            for item in worklist_payload
            if item["open_questions_count"] > 0
        ]

        _assert_filtered_summary_contract(summary_payload, applied_filters)
        assert summary_payload["total_cases"] == len(worklist_payload)
        assert [item["case_id"] for item in summary_payload["highest_priority_cases"]] == (
            worklist_case_ids[:3]
        )
        assert summary_payload["open_questions"]["total"] == sum(
            item["open_questions_count"] for item in worklist_payload
        )
        assert summary_payload["open_questions"]["cases_with_open_questions"] == (
            worklist_open_question_case_ids
        )


def test_cli_review_summary_combined_filters_count_filtered_cases() -> None:
    result = _run_cli(
        "--review-summary",
        "--review-min-risk",
        "C",
        "--review-gateway",
        "block",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    _assert_filtered_summary_contract(
        payload,
        {
            "review_min_risk": "C",
            "review_gateway": "block",
        },
    )
    assert payload["total_cases"] == 1
    assert payload["gateway"] == {"allow_draft": 0, "escalate": 0, "block": 1}
    assert payload["risk"] == {"A": 0, "B": 0, "C": 0, "D": 1}
    assert [item["case_id"] for item in payload["highest_priority_cases"]] == [
        "CASE_005"
    ]


def test_cli_review_summary_rejects_invalid_filter_values() -> None:
    invalid_commands = [
        ("--review-summary", "--review-limit", "0"),
        ("--review-summary", "--review-min-risk", "E"),
        ("--review-summary", "--review-gateway", "unknown"),
    ]

    for args in invalid_commands:
        result = _run_cli(*args)

        assert result.returncode == 2
        assert result.stdout == ""


def test_cli_review_summary_rejects_review_handoff_without_workflow_result(tmp_path):
    result = _run_cli(
        "--review-summary",
        "--review-handoff",
        str(tmp_path / "handoff.md"),
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "--review-handoff requires --case or --all." in result.stderr


def test_cli_review_summary_stdout_contains_no_markdown() -> None:
    result = _run_cli("--review-summary")

    assert result.returncode == 0
    assert "# Review Handoff" not in result.stdout
    assert "```" not in result.stdout
    json.loads(result.stdout)


def test_cli_review_handoff_writes_markdown_for_all_without_changing_stdout_json(
    tmp_path,
):
    handoff_path = tmp_path / "nested" / "all-review-handoff.md"

    result_with_handoff = _run_cli("--all", "--review-handoff", str(handoff_path))
    result_without_handoff = _run_cli("--all")

    assert result_with_handoff.returncode == 0
    assert result_with_handoff.stderr == ""
    assert json.loads(result_with_handoff.stdout) == json.loads(result_without_handoff.stdout)
    assert handoff_path.exists()
    handoff = handoff_path.read_text(encoding="utf-8")
    assert handoff.count("# Review Handoff") == len(EXPECTED_CASE_IDS)


def _assert_filtered_summary_contract(
    payload: dict[str, object], applied_filters: dict[str, object]
) -> None:
    assert set(payload) == EXPECTED_FILTERED_SUMMARY_KEYS
    assert payload["summary_scope"] == "filtered"
    assert payload["applied_filters"] == applied_filters


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


def _assert_review_worklist_contract(payload: dict[str, object]) -> None:
    assert set(payload) == EXPECTED_WORKLIST_KEYS
    assert isinstance(payload["case_id"], str)
    assert isinstance(payload["priority"], int)

    gateway = payload["gateway"]
    assert isinstance(gateway, dict)
    assert set(gateway) == EXPECTED_WORKLIST_GATEWAY_KEYS
    assert isinstance(gateway["decision"], str)
    assert gateway["decision"] in GATEWAY_DECISIONS
    _assert_string_list(gateway["reasons"])
    _assert_string_list(gateway["block_reasons"])

    risk = payload["risk"]
    assert isinstance(risk, dict)
    assert set(risk) == EXPECTED_WORKLIST_RISK_KEYS
    assert isinstance(risk["level"], str)
    assert risk["level"] in RISK_LEVELS
    assert isinstance(risk["review_required"], bool)
    _assert_string_list(risk["basis"])

    review_gate = payload["review_gate"]
    assert isinstance(review_gate, dict)
    assert set(review_gate) == EXPECTED_WORKLIST_REVIEW_GATE_KEYS
    assert isinstance(review_gate["status"], str)
    assert review_gate["status"] in REVIEW_GATE_STATUSES
    assert isinstance(review_gate["allows_offline_mock_continuation"], bool)
    assert isinstance(review_gate["reason"], str)

    draft = payload["draft"]
    assert isinstance(draft, dict)
    assert set(draft) == EXPECTED_WORKLIST_DRAFT_KEYS
    assert isinstance(draft["available"], bool)
    assert isinstance(draft["review_status"], str)
    assert draft["review_status"] in REVIEW_STATUSES

    assert isinstance(payload["open_questions_count"], int)
    _assert_string_list(payload["open_questions"])
    assert payload["open_questions_count"] == len(payload["open_questions"])


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
