# Evaluation Guide

## Scope

The evaluation suites are deterministic, local, and synthetic. They are
engineering regression checks for the offline MVP and RAG demo. They do not
measure tax correctness, professional review quality, general semantic NLP
quality, or productive readiness.

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

On the experiment branch after the hardening pass, the portfolio baseline
currently aggregates **41** synthetic cases. The binary suites currently pass
**27 of 28** cases. The non-passing case is the documented contradiction
known limitation for informal "decade" wording, so `--portfolio-baseline`
returns exit code `1` until that limitation is intentionally resolved or the
baseline is re-scoped. This pass rate is regression information, not a quality
target and not evidence of productive RAG quality.

## Suite interpretation

Workflow, RAG abstention, RAG contradiction, and RAG freshness expose binary
pass rates because their synthetic cases have deterministic expected outcomes
that are compared against separately observed results.

Retrieval and grounding expose metrics such as recall and citation/source match
rates. The project does not invent a pass/fail threshold for those suites.

Contradiction detection on this branch uses a closed set of deterministic
templates over natural synthetic sentences. It is not a claim of general
semantic contradiction understanding. The suite intentionally includes one
expected-positive case that the detector misses for informal "decade" wording.

Freshness detection uses supersession, explicit validity windows, inclusive
`valid_to` closure, overlapping-window handling, and duplicate family/version
rejection. A past `valid_from` alone does not make a document outdated.

## Important boundaries

The evaluation suites:

- use synthetic fixtures only
- use `FakeModelProvider` unless a specific opt-in smoke path is invoked
- must not require network access in standard tests
- must not include secrets or real personal data
- must not be treated as productive tax-quality validation
- keep ground-truth labels separate from detector observations

The portfolio baseline is useful for regression review and portfolio
explanation. It does not replace Kanzlei review or Steuerberater responsibility.
