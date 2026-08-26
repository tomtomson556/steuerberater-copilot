# Current State

Agent-context inventory snapshot of a dated `main` commit. This file is not
strategy, architecture decision, security policy, or a source of truth. Those
remain in live Git state, the roadmap, accepted ADRs, implementation, and
existing control documents.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Snapshot

| Field | Value |
| --- | --- |
| Date | 22 August 2026 |
| `main` commit | `0f2d98e` (`feat: add reference-demo bootstrap role IAM contract (#142)`) |
| Productive use | No. Local-first, non-productive, synthetic data only. |
| Roadmap phase | Phase 5, Referenz-Cloud und Observability |

Code and infra below are taken from that `main` commit. The agent-context
layout in this file belongs with the router `AGENTS.md`: load detail documents
only when the task needs them. At this snapshot commit, nested `AGENTS.md`
files, agent skills, and multi-agent exec plans were not in use.

Refresh this inventory from live `main` when the implemented surface changes.
The binding strategy remains
[ai-engineering-roadmap-2026.md](../10-mvp-scope/ai-engineering-roadmap-2026.md).

## Operating mode

Safe default:

```text
local
synthetic data
deterministic, network-free standard tests
FakeModelProvider
no secrets in the repository
```

Architecture direction:

```text
offline_mvp -> ai
```

Forbidden:

```text
ai -> offline_mvp
```

Exactly one reference cloud (AWS). No Multi-Cloud.

## Implemented on `main`

### Offline MVP

- CLI entrypoint `python -m steuerberater_copilot.offline_mvp` and console
  script `steuerberater-copilot-offline-mvp`
- Synthetic fixtures in `fixtures/offline_mvp/cases.json`
- Gateway, internal `RiskLevel`, Human Review Gate, draft packages
- Stable CLI JSON contract

### Controlled AI path

- Provider-neutral `ModelProvider` in `src/steuerberater_copilot/ai/`
- Offline `FakeModelProvider` as the safe default
- One OpenAI Responses API adapter (`openai==2.45.0`), isolated at the provider
  boundary; live smoke is explicit opt-in and not verified
- Versioned synthetic prompt, structured draft parser, separate semantic
  validator, Model Invocation Policy, response-gateway marker check

### Local RAG baseline

- `SourceDocument`, `LocalDocumentRetriever`, grounded draft, synthetic RAG
  workflow
- Retrieval, grounding, abstention, contradiction, and freshness evaluation

### Offline evaluation

Six synthetic suites, 38 cases, aggregated by
`python -m steuerberater_copilot.evaluation` /
`steuerberater-copilot-evaluate`:

| Suite | Cases |
| --- | --- |
| AI workflow | 7 |
| Retrieval | 4 |
| Grounding | 9 |
| RAG abstention | 4 |
| RAG contradiction | 9 |
| RAG freshness | 5 |

### HTTP and Docker demo

FastAPI at `src/steuerberater_copilot/api/` is present:

- `GET /health`
- `GET /version`
- `POST /ai/draft` (synthetic `case_id` only; `FakeModelProvider` default)

Each `POST /ai/draft` emits one CloudWatch Embedded Metric Format JSON line on
stdout and a server-side `X-Request-ID`. Local Docker runtime is present
(`Dockerfile`, image user `10001`, no secrets in the image).

### Reference-cloud artefacts (not live)

Present in the repository, not a live AWS deployment:

- Architecture: `docs/03-architecture/aws-reference-cloud-deployment.md`
- CloudFormation: `infra/cloudformation/reference-demo.yaml`
- IAM control plane v2.3, including bootstrap-role contract:
  `infra/iam/reference-demo/v2.3/`
- Runbook: `docs/09-operations/aws-reference-demo-runbook.md`
- Local IAM control-plane tool: `tools/aws_reference_demo_iam_control_plane.py`

Chosen runtime in the architecture document: Amazon ECS Express Mode in
`eu-central-1`.

## Control flow

```text
IntakeCase
-> Gateway
-> Risikoklassifikation
-> Human Review Gate
-> Prompt Builder
-> Model Invocation Boundary
-> Structured Output Parser
-> Structured Draft Semantic Validator
-> Response Gateway
```

HTTP `POST /ai/draft` calls the existing synthetic RAG workflow at the system
boundary. FastAPI must not own fachliche logic.

## Not present / not claimed

- No AWS live test, no managed CloudWatch dashboard, no alarms
- No confirmed real CloudWatch EMF extraction
- No verified OpenAI live connection
- No retry policy, rate limiting, cost control, tokenizer, or provider allowlist
- No persistence, authentication, or Prompt Registry
- No productive data, Agenda/DATEV/ELSTER, or Multi-Cloud
- Estimated model cost is not implemented (`model_cost_usd` is `0.0` or `null`)

## Known documentation drift

These documents still describe an earlier slice of `main`. Prefer live Git, the
roadmap, accepted ADRs, and this snapshot over stale component lists:

| Document | Stale claim on `main` `0f2d98e` |
| --- | --- |
| [system-overview.md](../03-architecture/system-overview.md) | Treats CLI as the only implemented interface, API as absent, and LLM integration as a non-goal. FastAPI, Docker, the OpenAI adapter, RAG, evaluation, runtime logs, and metrics exist. |
| [adr-002-cli-first-api-second.md](../15-decisions/adr/adr-002-cli-first-api-second.md) | Decision text still says FastAPI is deferred and that no API server exists. CLI-first remains the offline-MVP interface decision; the HTTP demo is a later system boundary. |
| [adr-003-local-first-cloud-neutral-single-reference-cloud.md](../15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md) | Context still says API, persistence, and cloud infrastructure do not exist. Persistence still does not. FastAPI/Docker and reference-cloud artefacts do. ADR-004 selects AWS. |

Do not "fix" that drift by copying architecture or security text into new root
files. Update the owning document when that document is in scope.

## Where to read next

Load only what the task needs:

- Strategy: [ai-engineering-roadmap-2026.md](../10-mvp-scope/ai-engineering-roadmap-2026.md)
- Security: [security-baseline-policy.md](../02-security/security-baseline-policy.md)
- Gateway: [privacy-gateway-contract.md](../05-privacy-gateway/privacy-gateway-contract.md)
- Human Review: [human-review-policy.md](../06-human-review/human-review-policy.md)
- ADRs: `docs/15-decisions/adr/`
- AWS IAM / operations: [aws-reference-demo-runbook.md](../09-operations/aws-reference-demo-runbook.md)
- Agent MCP: [agent-mcp-boundaries.md](../04-mcp/agent-mcp-boundaries.md)
