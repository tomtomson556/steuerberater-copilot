import json

from steuerberater_copilot.evaluation import (
    build_portfolio_evaluation_baseline_report,
    portfolio_evaluation_baseline_to_dict,
)
from steuerberater_copilot.evaluation.__main__ import main


def test_portfolio_baseline_has_expected_case_count_and_binary_pass_rate() -> None:
    report = build_portfolio_evaluation_baseline_report()
    payload = portfolio_evaluation_baseline_to_dict(report)

    assert report.total_case_count == 41
    assert report.binary_suite_case_count == 28
    assert report.binary_suite_passed_case_count == 27
    assert report.binary_suite_pass_rate == 27 / 28
    assert payload["total_case_count"] == 41
    assert payload["binary_suite_case_count"] == 28
    assert payload["binary_suite_passed_case_count"] == 27
    assert payload["binary_suite_pass_rate"] == 27 / 28


def test_portfolio_baseline_cli_exits_one_for_known_limitation(capsys) -> None:
    exit_code = main(["--portfolio-baseline"])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["total_case_count"] == 41
    assert output["binary_suite_case_count"] == 28
    assert output["binary_suite_passed_case_count"] == 27
    assert output["binary_suite_pass_rate"] == 27 / 28
