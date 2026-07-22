# Evaluation Guide

## Scope

The evaluation suites are deterministic, local, and synthetic. They are
engineering regression checks for the offline MVP and RAG demo. They do not
measure tax correctness, professional review quality, or productive readiness.

Human Review remains mandatory for tax-relevant draft material.

## Install test dependencies

```bash
python -m pip install -e ".[dev]"
```

The default verification gates remain:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

## Portfolio baseline

Run the aggregate portfolio baseline:

```bash
python -m steuerberater_copilot.evaluation --portfolio-baseline
steuerberater-copilot-evaluate --portfolio-baseline
```

The command prints JSON with:

- `total_case_count`
- `binary_suite_case_count`
- `binary_suite_passed_case_count`
- `binary_suite_pass_rate`
- `suite_summaries`
- boundary notes

On the experiment branch, the expected portfolio case count is 32 and the
expected binary-suite pass rate is `1.0`.

## Suite interpretation

Workflow, RAG abstention, RAG contradiction, and RAG freshness expose binary
pass rates because their synthetic cases have deterministic expected outcomes.

Retrieval and grounding expose metrics such as recall and citation/source match
rates. The project does not invent a pass/fail threshold for those suites in
this branch.

## Important boundaries

The evaluation suites:

- use synthetic fixtures only
- use `FakeModelProvider` unless a specific opt-in smoke path is invoked
- must not require network access in standard tests
- must not include secrets or real personal data
- must not be treated as productive tax-quality validation

The portfolio baseline is useful for regression review and portfolio
explanation. It does not replace Kanzlei review or Steuerberater responsibility.
