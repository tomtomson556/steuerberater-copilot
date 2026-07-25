"""Tests for the offline synthetic evaluation CLI command."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

import steuerberater_copilot.evaluation.command_summary as command_summary
from steuerberater_copilot.ai import FakeModelProvider
from steuerberater_copilot.evaluation import __main__ as evaluation_cli
from steuerberater_copilot.evaluation.rag_abstention_case import (
    RAGAbstentionEvaluationCase,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SUITE_IDS = (
    "ai_workflow",
    "retrieval",
    "grounding",
    "rag_abstention",
    "rag_contradiction",
    "rag_freshness",
)
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "suites",
    "synthetic_only",
    "total_case_count",
}
FORBIDDEN_JSON_MARKERS = (
    "system_prompt",
    "user_prompt",
    "model_response",
    "ModelResponse",
    "provider_name",
    "fake-model",
    "FakeModelProvider",
    "openai",
    "api_key",
    "secret",
    "assessments",
)


def test_pyproject_declares_evaluation_console_script() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["steuerberater-copilot-evaluate"] == (
        "steuerberater_copilot.evaluation.__main__:main"
    )
    assert pyproject["project"]["scripts"]["steuerberater-copilot-offline-mvp"] == (
        "steuerberater_copilot.offline_mvp.__main__:main"
    )


def test_module_invocation_emits_deterministic_json() -> None:
    result = _run_evaluation_module()

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert set(payload) == EXPECTED_TOP_LEVEL_KEYS
    assert payload["schema_version"] == 1
    assert payload["synthetic_only"] is True
    assert payload["total_case_count"] == 38
    assert [suite["suite_id"] for suite in payload["suites"]] == list(EXPECTED_SUITE_IDS)


def test_direct_main_invocation_matches_module_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = evaluation_cli.main([])
    captured = capsys.readouterr()
    module_result = _run_evaluation_module()

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == module_result.stdout
    assert module_result.returncode == 0


def test_full_run_contains_exactly_six_suites_and_38_cases() -> None:
    summary = command_summary.build_evaluation_command_summary()

    assert len(summary["suites"]) == 6
    assert summary["total_case_count"] == 38
    assert sum(suite["total_case_count"] for suite in summary["suites"]) == 38
    assert [suite["suite_id"] for suite in summary["suites"]] == list(EXPECTED_SUITE_IDS)


def test_baseline_metrics_match_existing_report_baselines() -> None:
    suites = {
        suite["suite_id"]: suite
        for suite in command_summary.build_evaluation_command_summary()["suites"]
    }

    ai = suites["ai_workflow"]
    assert ai["total_case_count"] == 7
    assert ai["passed_case_count"] == 7
    assert ai["failed_case_count"] == 0
    assert ai["pass_rate"] == 1.0
    assert ai["failed_evaluation_ids"] == []
    assert ai["gateway_decision_match_rate"] == 1.0
    assert ai["review_gate_status_match_rate"] == 1.0
    assert ai["outcome_match_rate"] == 1.0
    assert ai["provider_call_count_match_rate"] == 1.0
    assert ai["structured_draft_case_count"] == 1
    assert ai["structured_draft_match_rate"] == 1.0
    assert ai["total_provider_call_count"] == 4
    assert ai["unexpected_provider_call_count"] == 0

    retrieval = suites["retrieval"]
    assert retrieval["total_case_count"] == 4
    assert retrieval["applicable_recall_case_count"] == 3
    assert retrieval["inapplicable_recall_case_count"] == 1
    assert retrieval["mean_recall_at_k"] == 0.5
    assert "pass_rate" not in retrieval
    assert "failed_evaluation_ids" not in retrieval

    grounding = suites["grounding"]
    assert grounding["total_case_count"] == 9
    assert grounding["applicable_citation_coverage_case_count"] == 8
    assert grounding["inapplicable_citation_coverage_case_count"] == 1
    assert grounding["applicable_source_match_case_count"] == 7
    assert grounding["inapplicable_source_match_case_count"] == 2
    assert grounding["applicable_passage_match_case_count"] == 7
    assert grounding["inapplicable_passage_match_case_count"] == 2
    assert grounding["applicable_unsupported_summary_point_case_count"] == 8
    assert grounding["inapplicable_unsupported_summary_point_case_count"] == 1
    assert grounding["mean_citation_coverage"] == 6.5 / 8
    assert grounding["mean_source_match_rate"] == (14 / 3) / 7
    assert grounding["mean_passage_match_rate"] == (10 / 3) / 7
    assert grounding["mean_unsupported_summary_point_rate"] == 5.0 / 8
    assert "pass_rate" not in grounding
    assert "failed_evaluation_ids" not in grounding

    abstention = suites["rag_abstention"]
    assert abstention["total_case_count"] == 4
    assert abstention["passed_case_count"] == 4
    assert abstention["failed_case_count"] == 0
    assert abstention["pass_rate"] == 1.0
    assert abstention["failed_evaluation_ids"] == []
    assert abstention["expected_missing_evidence_case_count"] == 1
    assert abstention["missing_evidence_abstention_rate"] == 1.0
    assert abstention["false_negative_case_count"] == 0
    assert abstention["false_positive_case_count"] == 0

    contradiction = suites["rag_contradiction"]
    assert contradiction["total_case_count"] == 9
    assert contradiction["passed_case_count"] == 9
    assert contradiction["failed_case_count"] == 0
    assert contradiction["pass_rate"] == 1.0
    assert contradiction["failed_evaluation_ids"] == []
    assert contradiction["expected_contradiction_case_count"] == 5
    assert contradiction["contradiction_detection_rate"] == 1.0
    assert contradiction["false_negative_case_count"] == 0
    assert contradiction["false_positive_case_count"] == 0

    freshness = suites["rag_freshness"]
    assert freshness["total_case_count"] == 5
    assert freshness["passed_case_count"] == 5
    assert freshness["failed_case_count"] == 0
    assert freshness["pass_rate"] == 1.0
    assert freshness["failed_evaluation_ids"] == []
    assert freshness["current_document_retrieval_rate"] == 1.0
    assert freshness["stale_document_retrieval_rate"] == 0.0
    assert freshness["missing_current_document_case_count"] == 0
    assert freshness["stale_document_retrieval_case_count"] == 0


def test_consecutive_runs_produce_byte_identical_json() -> None:
    first = command_summary.serialize_evaluation_command_summary(
        command_summary.build_evaluation_command_summary()
    )
    second = command_summary.serialize_evaluation_command_summary(
        command_summary.build_evaluation_command_summary()
    )

    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")


def test_serialized_json_contains_no_prompts_provider_or_secret_content() -> None:
    serialized = command_summary.serialize_evaluation_command_summary(
        command_summary.build_evaluation_command_summary()
    )
    lowered = serialized.lower()

    for marker in FORBIDDEN_JSON_MARKERS:
        assert marker.lower() not in lowered


def test_full_run_works_with_blocked_network_sockets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _block_network(monkeypatch)

    exit_code = evaluation_cli.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["total_case_count"] == 38
    assert len(payload["suites"]) == 6


def test_rag_abstention_uses_only_fresh_fake_model_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_providers: list[FakeModelProvider] = []
    original_factory = command_summary._rag_abstention_provider_factory

    def recording_factory(
        evaluation_case: RAGAbstentionEvaluationCase,
    ) -> FakeModelProvider:
        provider = original_factory(evaluation_case)
        created_providers.append(provider)
        return provider

    monkeypatch.setattr(
        command_summary,
        "_rag_abstention_provider_factory",
        recording_factory,
    )

    suites = {
        suite["suite_id"]: suite
        for suite in command_summary.build_evaluation_command_summary()["suites"]
    }

    assert suites["rag_abstention"]["total_case_count"] == 4
    assert len(created_providers) == 4
    assert len({id(provider) for provider in created_providers}) == 4
    assert all(isinstance(provider, FakeModelProvider) for provider in created_providers)


def test_offline_mvp_cli_remains_functional() -> None:
    result = _run_offline_mvp_module("--list-cases")

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == [
        "CASE_001",
        "CASE_002",
        "CASE_003",
        "CASE_004",
        "CASE_005",
    ]


def test_unknown_cli_arguments_are_rejected_with_argparse_exit_code() -> None:
    result = _run_evaluation_module("--unknown-flag")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "unrecognized arguments" in result.stderr


def test_unexpected_suite_errors_are_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unexpected = RuntimeError("Synthetic unexpected evaluation command failure.")

    def fail_suite() -> dict[str, Any]:
        raise unexpected

    monkeypatch.setattr(command_summary, "_ai_workflow_suite_summary", fail_suite)

    with pytest.raises(RuntimeError) as exc_info:
        command_summary.build_evaluation_command_summary()

    assert exc_info.value is unexpected


def test_none_metrics_are_preserved_as_json_null() -> None:
    class _FakeRetrievalReport:
        total_case_count = 2
        applicable_recall_case_count = 0
        inapplicable_recall_case_count = 2
        mean_recall_at_k = None

    summary = command_summary.retrieval_metrics_report_to_summary(_FakeRetrievalReport())
    serialized = command_summary.serialize_evaluation_command_summary(
        {
            "schema_version": 1,
            "synthetic_only": True,
            "total_case_count": 2,
            "suites": [summary],
        }
    )

    assert summary["mean_recall_at_k"] is None
    assert '"mean_recall_at_k": null' in serialized


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    real_socket = socket.socket

    def fail_network_socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=0,
        fileno=None,
    ):
        if family in {socket.AF_INET, socket.AF_INET6}:
            raise AssertionError("Evaluation command must not open network sockets")
        return real_socket(family, type, proto, fileno)

    monkeypatch.setattr(socket, "socket", fail_network_socket)


def _run_evaluation_module(*args: str) -> subprocess.CompletedProcess[str]:
    return _run_module("steuerberater_copilot.evaluation", *args)


def _run_offline_mvp_module(*args: str) -> subprocess.CompletedProcess[str]:
    return _run_module("steuerberater_copilot.offline_mvp", *args)


def _run_module(module: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = (
        src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    )
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
