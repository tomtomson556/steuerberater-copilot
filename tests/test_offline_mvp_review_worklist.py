from copy import deepcopy

from steuerberater_copilot.offline_mvp.models import ReviewStatus
from steuerberater_copilot.offline_mvp.review_worklist import (
    build_review_worklist,
    filter_review_worklist,
    review_priority,
)
from steuerberater_copilot.offline_mvp.workflow import build_mock_workflow, load_fixture_cases

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
EXPECTED_GATEWAY_KEYS = {"decision", "reasons", "block_reasons"}
EXPECTED_RISK_KEYS = {"level", "review_required", "basis"}
EXPECTED_REVIEW_GATE_KEYS = {
    "status",
    "allows_offline_mock_continuation",
    "reason",
}
EXPECTED_DRAFT_KEYS = {"available", "review_status"}
AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS = {
    "approved",
    "final",
    "freigegeben",
    "rejected",
}


def test_review_worklist_contains_all_fixture_cases_in_priority_order() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]

    worklist = build_review_worklist(outputs)

    assert [item["case_id"] for item in worklist] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
        "CASE_003",
        "CASE_002",
    ]
    assert [item["priority"] for item in worklist] == sorted(
        (item["priority"] for item in worklist),
        reverse=True,
    )


def test_review_worklist_keeps_block_case_review_bound() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]

    worklist = build_review_worklist(outputs)
    block_item = worklist[0]

    assert block_item["case_id"] == "CASE_005"
    assert block_item["priority"] == 100
    assert block_item["gateway"]["decision"] == "block"
    assert block_item["gateway"]["block_reasons"] == [
        "forbidden_data_class:original_pii"
    ]
    assert block_item["risk"]["level"] == "D"
    assert block_item["review_gate"]["status"] == "requires_human_review"
    assert block_item["review_gate"]["allows_offline_mock_continuation"] is False
    assert block_item["draft"]["available"] is False
    assert block_item["draft"]["review_status"] == "Escalated"
    assert block_item["open_questions_count"] == 0
    assert block_item["open_questions"] == []


def test_review_worklist_uses_compact_stable_contract() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]

    worklist = build_review_worklist(outputs)

    for item in worklist:
        assert set(item) == EXPECTED_WORKLIST_KEYS
        assert isinstance(item["case_id"], str)
        assert isinstance(item["priority"], int)
        assert set(item["gateway"]) == EXPECTED_GATEWAY_KEYS
        assert set(item["risk"]) == EXPECTED_RISK_KEYS
        assert set(item["review_gate"]) == EXPECTED_REVIEW_GATE_KEYS
        assert set(item["draft"]) == EXPECTED_DRAFT_KEYS
        assert item["open_questions_count"] == len(item["open_questions"])


def test_filter_review_worklist_keeps_input_unchanged() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)
    original = deepcopy(worklist)

    filter_review_worklist(
        worklist,
        limit=2,
        min_risk="C",
        gateway_decision="allow_draft",
        open_questions_only=True,
    )

    assert worklist == original


def test_filter_review_worklist_limit_keeps_first_existing_entries() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)

    filtered = filter_review_worklist(worklist, limit=3)

    assert [item["case_id"] for item in filtered] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]


def test_filter_review_worklist_by_min_risk() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)

    risk_d = filter_review_worklist(worklist, min_risk="D")
    risk_c = filter_review_worklist(worklist, min_risk="C")

    assert [item["case_id"] for item in risk_d] == ["CASE_005", "CASE_004"]
    assert [item["case_id"] for item in risk_c] == [
        "CASE_005",
        "CASE_004",
        "CASE_001",
    ]


def test_filter_review_worklist_by_gateway_decision() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)

    block = filter_review_worklist(worklist, gateway_decision="block")
    allow_draft = filter_review_worklist(worklist, gateway_decision="allow_draft")

    assert [item["case_id"] for item in block] == ["CASE_005"]
    assert [item["case_id"] for item in allow_draft] == [
        "CASE_004",
        "CASE_003",
        "CASE_002",
    ]


def test_filter_review_worklist_by_open_questions() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)

    filtered = filter_review_worklist(worklist, open_questions_only=True)

    assert [item["case_id"] for item in filtered] == ["CASE_001"]


def test_filter_review_worklist_combines_filters_in_existing_order() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    worklist = build_review_worklist(outputs)

    filtered = filter_review_worklist(worklist, min_risk="C", limit=2)

    assert [item["case_id"] for item in filtered] == ["CASE_005", "CASE_004"]


def test_review_priority_is_deterministic_from_existing_workflow_markers() -> None:
    outputs = {
        output.intake.case_id: output
        for output in (build_mock_workflow(case) for case in load_fixture_cases())
    }

    assert review_priority(outputs["CASE_005"]) == 100
    assert review_priority(outputs["CASE_004"]) == 85
    assert review_priority(outputs["CASE_001"]) == 65
    assert review_priority(outputs["CASE_003"]) == 45
    assert review_priority(outputs["CASE_002"]) == 20


def test_review_worklist_never_auto_emits_final_or_human_review_decisions() -> None:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]

    worklist = build_review_worklist(outputs)

    for item in worklist:
        review_status = item["draft"]["review_status"].lower()
        assert ReviewStatus(item["draft"]["review_status"]) is not ReviewStatus.REJECTED
        assert not any(
            marker in review_status
            for marker in AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS
        )
