# Testing and Quality Strategy

## Purpose

The current offline MVP uses a small, deterministic verification set to keep the
project reviewable and compliance-first. The quality gates check implementation
behavior, documentation boundaries, and pull request readiness for the local MVP
scope.

This strategy follows the project principle:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

All outputs remain drafts. Human Review is a mandatory project rule before any
output is relied on or used fachlich by the Kanzlei.

## Current Quality Gates

Local and CI verification use the same core commands:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python tools/policy_claim_check.py
```

- Ruff checks static linting rules configured in `pyproject.toml`.
- pytest runs the automated test suite for the offline MVP and tooling.
- pytest also checks repository text files for problematic invisible or
  typographic characters in Markdown, Python, JSON, TOML, text, and YAML files
  while allowing normal UTF-8 text such as German umlauts.
- The policy claim check scans Markdown files for risky policy-boundary claims
  without a clear negative context.
- GitHub Actions CI is the required automated verification gate for pull
  requests.
- Human Review remains mandatory before relying on any generated draft output.

## Current Test Scope

The automated tests currently cover:

- loading synthetic offline fixtures
- deterministic `RiskLevel` A, B, C, and D behavior
- the synthetic `CASE_005` `gateway=block`/RiskLevel-D path end to end through
  fixture loading, workflow, CLI, and JSON output
- `review_required` behavior for internal risk classifications
- Human Review Gate stop behavior for B, C, and D
- regression boundaries that prevent the deterministic workflow from
  automatically emitting final or human review decision statuses
- draft-only workflow output boundaries
- review-bound question drafts in CLI JSON output, including visibility when
  `draft.available` is `false`
- `CASE_001` securing visible review-bound `draft.questions` while the Review
  Gate and `draft.available` remain restrictive
- offline MVP CLI JSON contract boundaries
- repository text character hygiene for common invisible or typographic
  characters
- policy claim checker behavior for allowed and blocked Markdown wording

The current CLI JSON contract is documented in
[offline-mvp-cli-json-contract.md](offline-mvp-cli-json-contract.md).

## Quality Boundaries

These checks are intentionally limited. They do not validate:

- tax correctness
- real client data
- productive integrations
- professional human review decisions

The tests and checks support local engineering confidence for the offline MVP.
They do not replace professional Human Review, Steuerberater responsibility, or
future verification that may be required for productive use.
