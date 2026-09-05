# Testing and Quality Strategy

## Purpose

The current portfolio uses a deterministic, synthetic verification set to
keep the project reviewable and compliance-first. The quality gates check
implementation behavior, documentation boundaries, and pull request
readiness for the local AI-engineering scope.

This strategy follows the project principle:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

All outputs remain drafts. Human Review is a mandatory project rule before any
output is relied on or used fachlich by the Kanzlei.

Evaluation reports are a deterministic engineering record against synthetic
fixtures. They are not a productive model-quality claim and do not replace
Human Review.

## Current Quality Gates

Local and CI verification use the same core commands:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python tools/policy_claim_check.py
```

Standard pytest stays docker-free and network-free. `FakeModelProvider` is
the safe default for AI, RAG, evaluation, and HTTP-demo tests.

- Ruff checks static linting rules configured in `pyproject.toml`.
- pytest runs the automated test suite for the modular monolith and tooling.
- pytest also checks repository text files for problematic invisible or
  typographic characters in Markdown, Python, JSON, TOML, text, and YAML files
  while allowing normal UTF-8 text such as German umlauts.
- The policy claim check scans Markdown files for risky policy-boundary claims
  without a clear negative context.
- GitHub Actions CI is the required automated verification gate for pull
  requests. The policy-and-tests job runs the commands above. A separate
  docker-smoke job builds the local image and checks `/health`, `/version`,
  and `POST /ai/draft`; it is not part of standard pytest.
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
- provider-neutral `ModelProvider` and deterministic `FakeModelProvider`
  behavior
- versioned synthetic prompts, structured JSON parsing, and separate semantic
  validation
- Model Invocation Policy and response-gateway marker checks
- the OpenAI Responses adapter against `openai==2.45.0` without a live network
  call, including a local SDK contract check
- local deterministic RAG retrieval, grounding, abstention, contradiction,
  and freshness evaluation
- the evaluation CLI over six synthetic suites and 38 cases
- FastAPI `/health`, `/version`, and `POST /ai/draft` HTTP contracts with
  `FakeModelProvider`
- one structured CloudWatch Embedded Metric Format event per `POST /ai/draft`
- static Docker runtime checks (pinned image, non-root user, allowlist,
  hashed lockfile); standard pytest does not start Docker
- static checks for reference-cloud artefacts in the repository; they do not
  prove a live AWS deployment
- repository text character hygiene for common invisible or typographic
  characters
- policy claim checker behavior for allowed and blocked Markdown wording

The current CLI JSON contract is documented in
[offline-mvp-cli-json-contract.md](offline-mvp-cli-json-contract.md).

The optional OpenAI live smoke is a separate opt-in tool. It is not part of
pytest, not started by the CLIs, and has not been verified for a concrete
target model.

## Quality Boundaries

These checks are intentionally limited. They do not validate:

- tax correctness
- real client data
- productive integrations
- professional human review decisions
- productive model quality
- a live OpenAI connection
- a live AWS deployment or real CloudWatch EMF extraction

The tests and checks support local engineering confidence for the synthetic
portfolio. They do not replace professional Human Review, Steuerberater
responsibility, or verification that would be required for productive use.
They do not show that Phase 5 is complete or that the project is a finished
Kanzlei product.
