# System Overview

## Scope

The current system is a local-first, non-productive AI-engineering portfolio.
It is a modular monolith that uses synthetic data only and produces draft
output for review.

It does not connect to productive systems, real client data, or filing
channels. It is not a finished Kanzlei product and does not provide
productive tax advice.

The safe default remains:

```text
local
synthetic data
deterministic, network-free standard tests
FakeModelProvider
no secrets in the repository
```

ADR-003 keeps a cloud-neutral application core and exactly one reference
cloud. ADR-004 selects AWS; the intended region is `eu-central-1`. ADR-002
established CLI-first JSON output for the offline MVP. The later FastAPI
demo is an HTTP system boundary around the existing workflow. It does not
replace the stable CLI JSON contract.

Future GoBD-oriented storage considerations are documented as a baseline in
[gobd-storage-baseline.md](../08-gobd-storage/gobd-storage-baseline.md). The
current system does not implement productive document storage.

## Modular monolith

The application is one Python package with internal modules. It is not a
microservice architecture and not a Next.js application.

| Module | Role |
| --- | --- |
| `steuerberater_copilot.offline_mvp` | Deterministic workflow, gateway, risk class, Human Review Gate, prompt building, structured output, RAG workflow |
| `steuerberater_copilot.ai` | Provider-neutral `ModelProvider`, `FakeModelProvider`, invocation policy, OpenAI Responses adapter |
| `steuerberater_copilot.rag` | `SourceDocument`, `LocalDocumentRetriever`, contradiction detector |
| `steuerberater_copilot.evaluation` | Synthetic suites, runners, assessments, aggregated reports, evaluation CLI |
| `steuerberater_copilot.api` | FastAPI HTTP boundary: `/health`, `/version`, `POST /ai/draft` |

Binding dependency direction:

```text
offline_mvp -> ai
```

Forbidden:

```text
ai -> offline_mvp
```

Cloud SDKs stay out of the application core. The OpenAI SDK is isolated at
the provider adapter. FastAPI types stay at the HTTP boundary.

MCP is a development-agent research aid only. It is not an application or
runtime layer.

## Control flow

The controlled AI path is:

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

The RAG path runs the same gateway and review controls first, then retrieves
local synthetic sources. Empty retrieval abstains without a provider call.
Retrieved `SourceDocument` content currently has no separate gateway check
before prompt construction; this known security gap remains an open
follow-up fix. Citations remain part of the grounded draft contract.

Semantic validation checks structured draft claims. It is not a tax
correctness check. Human Review remains mandatory for any tax-relevant
draft.

## Interfaces

### Offline MVP CLI

The first supported interface remains the local CLI and its stable JSON
output:

```text
CLI entrypoint
-> offline MVP workflow
-> workflow_to_json() serializer
-> stable CLI JSON output
-> Human Review boundary
```

1. `src/steuerberater_copilot/offline_mvp/__main__.py` accepts local CLI
   commands such as `--case`, `--all`, and `--list-cases`.
2. Synthetic fixture cases are loaded from `fixtures/offline_mvp/cases.json`.
3. The offline MVP workflow runs deterministic gateway checks, assigns an
   internal `RiskLevel`, applies the Human Review Gate, and prepares a
   `DraftPackage`. This CLI path does not call a model provider.
4. `workflow_to_json()` in
   `src/steuerberater_copilot/offline_mvp/serialization.py` serializes the
   workflow result into the stable CLI JSON contract.
5. The CLI prints the serializer payload with deterministic JSON formatting.
6. The Human Review boundary remains binding for all draft material.

### FastAPI demo

The HTTP demo lives under `steuerberater_copilot.api` and exposes:

- `GET /health`
- `GET /version`
- `POST /ai/draft`

`POST /ai/draft` accepts only known synthetic `case_id` values
(`CASE_002`, `CASE_005`, `CASE_006`). It calls the existing RAG workflow
with `FakeModelProvider` and local synthetic sources. Unknown IDs are
rejected. FastAPI must not own fachliche logic.

Each `POST /ai/draft` call emits one CloudWatch Embedded Metric Format JSON
line on stdout and a server-side `X-Request-ID`. The event does not contain
request or response bodies, prompts, model answers, exception text,
secrets, or personal data.

### Evaluation CLI

`python -m steuerberater_copilot.evaluation` and
`steuerberater-copilot-evaluate` run all six synthetic suites offline and
emit deterministic JSON. The current library has 38 cases. This is an
engineering record against fixtures, not a productive model-quality claim.

## Model providers

`FakeModelProvider` is the safe default for the AI workflow, RAG path, and
evaluation. The FastAPI and Docker demo paths are wired to
`FakeModelProvider` and do not call a live provider.

Exactly one real adapter exists: `OpenAIResponsesProvider` for the OpenAI
Responses API, pinned to `openai==2.45.0`. It uses explicit model
configuration, a timeout, disabled SDK retries, `store=False`, and
`text={"format": {"type": "json_object"}}` without a schema guarantee. The
live smoke is explicit opt-in and has not been verified. Standard tests do
not call the network.

There is no local or on-prem LLM runtime in the current portfolio path.

## Local RAG baseline

Retrieval uses `LocalDocumentRetriever`: deterministic token overlap over
in-memory `SourceDocument` objects. There is no PostgreSQL, pgvector,
Qdrant, or managed vector store in the current MVP.

The baseline includes grounding, missing-evidence abstention, a closed
template contradiction check, and freshness evaluation over synthetic
documents.

## Docker and reference cloud

The local Docker runtime starts the FastAPI demo with
`FakeModelProvider`, a non-root user, and no secrets in the image.

AWS is the only reference cloud. The intended region is `eu-central-1`.
Repository artefacts for the simplified reference-demo stack exist. There
is no AWS live test and no confirmed CloudWatch EMF extraction. Roadmap
Phase 5 (reference cloud and observability) is the current section and is
not complete. Details live in
[aws-reference-cloud-deployment.md](aws-reference-cloud-deployment.md).

## Offline MVP components

| Component | Current role |
| --- | --- |
| CLI entrypoint | Local command-line interface in `offline_mvp/__main__.py`; stable JSON output. |
| Synthetic fixtures | Local examples without original documents, real personal data, or productive system data. |
| Mock workflow | Deterministic offline orchestration for local validation only; no model call. |
| Risk classification | Internal routing marker using `RiskLevel.CLASS_A` through `RiskLevel.CLASS_D`. |
| Human Review Gate | Mandatory gate derived from the internal risk class. |
| JSON serializer | `workflow_to_json()` converts `WorkflowOutput` into the stable CLI JSON shape. |
| Draft output | Internal preparation material only, without external effect or productive communication. |

## JSON Contract and Tests

The CLI JSON output is stabilized and documented in
[offline-mvp-cli-json-contract.md](../10-testing-quality/offline-mvp-cli-json-contract.md).
The same baseline is covered by automated tests:

- `tests/test_offline_mvp_cli.py` checks the CLI JSON contract and case
  semantics end to end.
- `tests/test_offline_mvp_serialization.py` directly checks
  `workflow_to_json()`, including top-level keys, nested keys, alias
  invariants, and CLI-vs-serializer equivalence.

The current alias invariants are:

- `review_gate.decision == review_gate.status`
- `draft.summary == draft.summary_points`

These aliases are part of the current contract and must be changed only through
an explicit contract update.

## Case Semantics

The current synthetic CLI case semantics are:

| Case | Current behavior |
| --- | --- |
| `CASE_001` | `gateway=escalate`, `RiskLevel C`, `draft.available=false`, `review_gate.allows_offline_mock_continuation=false`. `draft.questions` may still be visible as internal, review-bound preparation from synthetic missing items. |
| `CASE_002` | The only positive draft case; `draft.available=true`. |
| `CASE_003` | Restrictive case; no available draft. |
| `CASE_004` | Restrictive case; no available draft. |
| `CASE_005` | Privacy Gateway block case; `gateway=block`, `RiskLevel D`, no available draft, and Human Review remains required. |

The HTTP demo additionally uses `CASE_006` as a synthetic abstention fixture.
That case is not part of the offline MVP CLI fixture set.

Visible `draft.questions` while `draft.available=false` do not create a
productive draft, do not allow offline mock continuation, and do not permit
client communication. They are internal preparation for review only.

## Human Review Boundary

`RiskLevel A` may continue only as an offline mock workflow without productive
effect.

`RiskLevel B`, `RiskLevel C`, and `RiskLevel D` stop before automatic
continuation. Their workflow output keeps Human Review visible and avoids
substantive draft continuation before review.

Human Review is a mandatory project rule. The Kanzlei reviews, and the
responsible Steuerberater decides where fachliche responsibility is required.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Operational handling is documented in
[offline-mvp-operations.md](../09-operations/offline-mvp-operations.md). Current
test and quality gates are documented in
[testing-strategy.md](../10-testing-quality/testing-strategy.md).

## Current Non-Goals

The current portfolio does not provide or introduce:

- a finished Kanzlei product or Mandantenportal
- a UI or Next.js frontend
- real data
- tax advice
- tax calculation logic
- a local or on-prem LLM runtime
- MCP services as an application layer
- PostgreSQL, pgvector, or another managed vector store
- productive communication
- productive client communication
- external productive integrations
- automated filing, submission, or transmission
- Agenda, DATEV, ELSTER, banking, or email integration
- a verified OpenAI live connection
- a live AWS deployment, managed dashboard, or alarms

These boundaries preserve the current compliance-first scope: local fixtures,
deterministic offline behavior, review-first routing, and draft-only output.
