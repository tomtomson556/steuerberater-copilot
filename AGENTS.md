# Development Agent Instructions

These instructions apply only to development agents that modify this repository,
such as Codex, GitHub Copilot, Cursor, DeepSeek via GitHub Copilot, or other
coding assistants.

These instructions are not runtime instructions for the future
steuerberater-copilot application, client-facing AI, Kanzlei-facing AI,
productive advisory system, or tax assistant.

This file is the central repository instruction for development agent behavior,
where supported by the respective tool.

## Project Scope

This project is compliance-first, local-first, and currently non-productive.
The safe default is local and offline: synthetic data, deterministic and
network-free standard tests, the `FakeModelProvider`, and no secrets.

External, provider, API, or cloud integrations are not generally permitted.
They may be added or changed only when the current binding roadmap explicitly
provides for them, applicable accepted ADRs are followed, and the current
branch scope expressly authorizes the work. Such integrations must remain
isolated at system boundaries.

The binding strategic source is
`docs/10-mvp-scope/ai-engineering-roadmap-2026.md`. The current architecture
decision is
`docs/15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md`.

The binding project principle is:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Development agents support repository work only. They do not make tax decisions,
provide individual tax advice, or perform tax-relevant actions. Tax-relevant
outputs remain drafts and require Human Review.

Controls sit before and beside the model, especially in the Policy and Privacy
Gateway, not inside the model itself.

## Related Agent Files

| File | Purpose |
| --- | --- |
| `.github/copilot-instructions.md` | Short instructions for GitHub Copilot and coding assistants |
| `.cursor/rules/steuerberater-copilot.mdc` | Cursor project rule, if present |
| `docs/04-mcp/agent-mcp-boundaries.md` | MCP boundaries for repository agent work |

## Required Startup Workflow

At the start of each task, agents must inspect the current repository state:

```bash
pwd
git branch --show-current
git status --short
git checkout main
git pull --ff-only origin main
git log --oneline --max-count=5
```

After that, agents must use their own small working branch. Agents must read
relevant existing files before creating new content or changing existing
content. Already merged pull request content must not be recreated or
duplicated.

## Development Agent Rules

- Agents may only prepare small, reviewable pull requests.
- Agents must never push directly to `main`.
- Agents must never merge pull requests.
- Merges are performed only by the user in the terminal.
- Squash merge is the standard merge method.
- `main` remains protected.
- CI must be green before merge.
- Required Status Check remains binding.
- Human Review remains the fachliche project rule.
- Scope must be clarified and kept narrow before changes are made.

## Forbidden Changes

Agents must not introduce, generate, configure, use, or weaken any of the
following:

- productive integrations or productive external services
- real Mandanten-, Kanzlei-, Beleg-, Steuer-, or other confidential data or
  metadata
- derived confidential content in public LLMs
- secrets, tokens, credentials, certificates, or private keys in repository
  content, fixtures, logs, prompts, or model inputs
- individual tax advice by a model or development agent
- tax calculation logic
- productive tax actions
- autonomous tax decisions
- bypassing the Gateway, Model Invocation Policy, or Human Review
- automatic tax submission or productive transmission
- productive Agenda, DATEV, ELSTER, banking, or email integration
- unplanned external, provider, API, or cloud integrations
- Multi-Cloud support
- network access in standard tests
- productive MCP servers or productive MCP configuration
- direct write access to productive or client systems, including Agenda,
  DATEV, ELSTER, banking, email, cloud, or external APIs
- productive data paths in development or test contexts
- changes outside an explicitly authorized branch and roadmap scope
- weakening of Compliance, Privacy, Security, AI Transparency, StBerG, Human
  Review, Risk Classification, Offline MVP Operations, Testing/Quality, or
  Release Governance policies

The LLM must not receive direct access to databases, file systems, object
storage, Agenda, DATEV, ELSTER, banking systems, email systems, cloud systems,
audit logs, token maps, or secrets.

## Roadmap-Authorized System-Boundary Work

The following capabilities are not blanket permissions. Agents may work on
them only when the current binding roadmap explicitly provides for the
capability, applicable accepted ADRs are followed, and the current branch scope
expressly authorizes it:

- exactly one controlled real `ModelProvider`, with its provider SDK isolated
  at a clear system boundary
- explicit opt-in live smoke tests using synthetic data only
- the planned FastAPI interface and Docker runtime
- HTTP transport at a system boundary
- exactly one reference cloud
- secret integration at a system boundary, without repository-stored secrets
- Cloud Logging and Cloud Metrics at system boundaries
- Infrastructure as Code only in the planned reference-cloud deployment scope

All such work must preserve the safe offline default, synthetic-data-only
operation, deterministic and network-free standard tests, Gateway and Human
Review controls, the Model Invocation Policy, and a cloud-neutral application
core. Provider and cloud SDKs must remain outside the application core. The
work must not anticipate Multi-Cloud support or a general adapter architecture
without a current need.

## Risk Behavior

- `RiskLevel A` may continue only through the controlled workflow. The safe
  default remains the offline `FakeModelProvider`; any real-provider execution
  must be explicitly authorized, opt-in, and synthetic-data-only.
- `RiskLevel B`, `RiskLevel C`, and `RiskLevel D` must stop before automatic
  continuation and require Human Review.
- Human Review must never be bypassed, removed, or weakened.

## MCP Boundaries

MCP use for repository agent work is currently limited to documentation or
read-only access to public or explicitly approved documentation sources.

Productive MCP servers, MCPs with real or derived confidential content, MCPs
with repository secrets, and MCP write tools for productive systems are not
allowed. MCP must not bypass the Policy and Privacy Gateway. Details are
documented in `docs/04-mcp/agent-mcp-boundaries.md`.

## Required Workflow After Changes

After changes, agents must inspect the working state:

```bash
git status --short
git diff --check
git diff --stat
git diff
```

For new untracked files, agents must also read the affected files directly
because `git diff` does not fully show untracked content.

## Required Local Verification Before PR

Before opening a pull request, agents must run:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

## Required Final Output From Agents

Agents must report:

- branch name
- commit hash
- PR URL
- changed files
- verification results
- explicit note that the pull request was not merged

## Cursor Cloud specific instructions

This is a CLI-first, offline Python package (`src` layout, no server or
frontend). The "application" is the offline MVP CLI. Standard commands live in
`README.md` (Lokale Entwickler-Validierung) and `pyproject.toml`; do not
duplicate them here.

Non-obvious environment notes:

- The VM exposes `python3` only; there is no `python` alias. README/CI examples
  written as `python ...` should be run as `python3 ...`.
- `pip install -e ".[dev]"` places console scripts (`pytest`, `ruff`,
  `steuerberater-copilot-offline-mvp`) in `~/.local/bin`, which is not on
  `PATH` by default. Either invoke via module form (`python3 -m pytest`,
  `python3 -m ruff`, `python3 -m steuerberater_copilot.offline_mvp`) or prepend
  `~/.local/bin` to `PATH`.
- Standard tests and the CLI are fully offline and deterministic; no network,
  services, or secrets are required. Any real OpenAI call is strictly opt-in via
  `RUN_OPENAI_LIVE_SMOKE=1` (see README) and must never be run automatically.
