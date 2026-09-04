# Development Agent Instructions

These instructions apply only to development agents that modify this repository.
They are not runtime instructions for the steuerberater-copilot application.

`AGENTS.md` is the context router. Persistent detail lives in existing repository
documents. Load those documents only when the current task needs them.

## Source of truth

```text
current main
→ docs/10-mvp-scope/ai-engineering-roadmap-2026.md
→ accepted ADRs
→ implementation and tests
```

`docs/00-project/current-state.md` is an agent-context inventory snapshot of a
dated `main` commit. It is not a source of truth. When it disagrees with live
Git state, the roadmap, accepted ADRs, or the code, those win.

The binding project principle:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Repository map

| Need | Read |
| --- | --- |
| Agent context / inventory snapshot | `docs/00-project/current-state.md` |
| Project brief | `docs/00-project/project-brief.md` |
| Strategy / 2026 scope | `docs/10-mvp-scope/ai-engineering-roadmap-2026.md` |
| Architecture | `docs/03-architecture/system-overview.md` |
| AWS reference cloud | `docs/03-architecture/aws-reference-cloud-deployment.md` |
| ADRs | `docs/15-decisions/adr/` |
| Security baseline | `docs/02-security/security-baseline-policy.md` |
| Gateway | `docs/05-privacy-gateway/privacy-gateway-contract.md` |
| Human Review | `docs/06-human-review/human-review-policy.md` |
| Risk classes | `docs/07-risk-classification/risk-classification-policy.md` |
| MCP | `docs/04-mcp/agent-mcp-boundaries.md` |
| AWS IAM / runbook | `docs/09-operations/aws-reference-demo-runbook.md` |
| Tests | `docs/10-testing-quality/testing-strategy.md` |
| Git / `main` | `docs/03-workflow/main-branch-protection-policy.md` |

Do not add parallel root files such as `ARCHITECTURE.md`, `DECISIONS.md`, or
`SECURITY_INVARIANTS.md` while these documents already hold that role.

## Required startup workflow

```bash
pwd
git branch --show-current
git status --short
git checkout main
git pull --ff-only origin main
git log --oneline --max-count=5
```

Then use a small working branch. Use `docs/00-project/current-state.md` only as
a convenience inventory index, then load the detail documents relevant to the
task. Do not recreate already merged work.

## Git workflow

- Prepare only small, reviewable pull requests.
- Never push directly to `main`.
- Never merge pull requests. The user merges in the terminal.
- Squash merge is the standard method. `main` stays protected.
- CI and the Required Status Check must be green before merge.
- Keep scope narrow and authorized by the current branch plus the binding
  roadmap.

## Core invariants

- Non-productive. Synthetic data only. No repository-stored secrets.
- Safe default: local, offline, deterministic, network-free standard tests,
  `FakeModelProvider`.
- Dependency direction is `offline_mvp -> ai`. `ai -> offline_mvp` is forbidden.
- No Multi-Cloud. Exactly one reference cloud, only when the roadmap and ADRs
  authorize it.
- Human Review stays. Agents do not make tax decisions, give individual tax
  advice, or perform tax-relevant actions. Tax-relevant outputs remain drafts.
- Do not weaken Gateway, Model Invocation Policy, Human Review, or existing
  compliance policies.
- System-boundary work (one real provider, FastAPI/Docker, HTTP, secrets,
  Cloud Logging/Metrics, IaC) is allowed only when the current roadmap, accepted
  ADRs, and branch scope expressly authorize it. Keep provider and cloud SDKs
  outside the application core.

Binding detail: `docs/02-security/security-baseline-policy.md`,
`docs/05-privacy-gateway/privacy-gateway-contract.md`,
`docs/06-human-review/human-review-policy.md`,
`docs/15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md`,
`docs/15-decisions/adr/adr-004-select-reference-cloud.md`.

## German prose

German prose uses standard UTF-8 orthography with `ä`, `ö`, `ü`, and `ß`.
Do not replace umlauts with `ae`, `oe`, or `ue`. Do not use `ss` as a
substitute for `ß`. Legitimate German `ss` such as in `dass`, `muss`, or
`wissen` remains correct. ASCII forms remain allowed only where technically
required, for example identifiers, filenames, regexes, commands, or external
literal values. Do not bulk-normalize historical documents.

## Validation

After changes:

```bash
git status --short
git diff --check
git diff --stat
git diff
```

Read new untracked files directly. Before a pull request:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

## Required final output

Report branch name, commit hash, PR URL, changed files, verification results,
and that the pull request was not merged.
