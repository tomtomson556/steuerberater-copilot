import json

from steuerberater_copilot.offline_mvp.review_summary import build_review_summary
from steuerberater_copilot.offline_mvp.workflow import build_mock_workflow, load_fixture_cases

EXPECTED_SUMMARY_KEYS = {
    "total_cases",
    "gateway",
    "risk",
    "review_gate",
    "draft_availability",
    "open_questions",
    "highest_priority_cases",
}
EXPECTED_PRIORITY_CASE_KEYS = {
    "case_id",
    "priority",
    "gateway_decision",
    "risk_level",
    "review_gate_status",
    "draft_available",
    "open_questions_count",
}
AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS = (
    "Approved",
    "Final",
    "Freigegeben",
    "Rejected",
)


def test_review_summary_uses_stable_top_level_contract() -> None:
    summary = _summary()

    assert set(summary) == EXPECTED_SUMMARY_KEYS
    assert summary["total_cases"] == 5


def test_review_summary_counts_gateway_contract_values() -> None:
    summary = _summary()

    assert summary["gateway"] == {
        "allow_draft": 3,
        "escalate": 1,
        "block": 1,
    }


def test_review_summary_counts_risk_levels() -> None:
    summary = _summary()

    assert summary["risk"] == {
        "A": 1,
        "B": 1,
        "C": 1,
        "D": 2,
    }


def test_review_summary_counts_review_gate_statuses() -> None:
    summary = _summary()

    assert summary["review_gate"] == {
        "allowed_offline_mock_continuation": 1,
        "requires_human_review": 4,
    }


def test_review_summary_counts_draft_availability() -> None:
    summary = _summary()

    assert summary["draft_availability"] == {
        "available": 1,
        "unavailable": 4,
    }


def test_review_summary_counts_open_questions() -> None:
    summary = _summary()

    assert summary["open_questions"] == {
        "total": 2,
        "cases_with_open_questions": ["CASE_001"],
    }


def test_review_summary_includes_top_three_priority_cases_compactly() -> None:
    summary = _summary()

    assert summary["highest_priority_cases"] == [
        {
            "case_id": "CASE_005",
            "priority": 100,
            "gateway_decision": "block",
            "risk_level": "D",
            "review_gate_status": "requires_human_review",
            "draft_available": False,
            "open_questions_count": 0,
        },
        {
            "case_id": "CASE_004",
            "priority": 85,
            "gateway_decision": "allow_draft",
            "risk_level": "D",
            "review_gate_status": "requires_human_review",
            "draft_available": False,
            "open_questions_count": 0,
        },
        {
            "case_id": "CASE_001",
            "priority": 65,
            "gateway_decision": "escalate",
            "risk_level": "C",
            "review_gate_status": "requires_human_review",
            "draft_available": False,
            "open_questions_count": 2,
        },
    ]
    assert all(
        set(item) == EXPECTED_PRIORITY_CASE_KEYS
        for item in summary["highest_priority_cases"]
    )


def test_review_summary_does_not_emit_final_or_human_review_decisions() -> None:
    summary_text = json.dumps(_summary(), ensure_ascii=False, sort_keys=True)

    for marker in AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS:
        assert marker not in summary_text


def _summary() -> dict[str, object]:
    outputs = [build_mock_workflow(case) for case in load_fixture_cases()]
    return build_review_summary(outputs)
