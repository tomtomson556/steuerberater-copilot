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

This project is compliance-first, offline-only, deterministic, and currently
non-productive.

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

- productive integrations
- real Mandanten-, Beleg-, Steuer-, Kanzlei-, or metadata
- derived confidential content in public LLMs
- secrets, tokens, credentials, certificates, or private keys
- tax advice
- tax calculation logic
- external services
- automatic submission or transmission
- Agenda integration
- DATEV integration
- ELSTER integration
- banking integration
- email integration
- cloud integration
- API integration
- productive MCP servers or productive MCP configuration
- autonomous tax decisions
- direct write access to Agenda, DATEV, ELSTER, banking, email, cloud, API, or
  client systems
- productive data paths in development or test contexts
- weakening of Compliance, Privacy, Security, AI Transparency, StBerG, Human
  Review, Risk Classification, Offline MVP Operations, Testing/Quality, or
  Release Governance policies

The LLM must not receive direct access to databases, file systems, object
storage, Agenda, DATEV, ELSTER, banking systems, email systems, cloud systems,
audit logs, token maps, or secrets.

## Risk Behavior

- `RiskLevel A` may continue only as offline mock behavior.
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
