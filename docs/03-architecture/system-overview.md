# Offline MVP System Overview

## Scope

The current offline MVP is a local, deterministic preparation workflow. It uses
synthetic fixtures only and produces draft output for internal review.

It does not connect to productive systems, external services, real client data,
or filing channels.

The interface baseline remains CLI-first/API-second as documented in
[ADR 002](../15-decisions/adr/adr-002-cli-first-api-second.md). The current
implemented interface is the local CLI and its stable JSON output.

Future GoBD-oriented storage considerations are documented as a baseline in
[gobd-storage-baseline.md](../08-gobd-storage/gobd-storage-baseline.md). The
current offline MVP does not implement productive document storage.

## Current Flow

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
   `DraftPackage`.
4. `workflow_to_json()` in
   `src/steuerberater_copilot/offline_mvp/serialization.py` serializes the
   workflow result into the stable CLI JSON contract.
5. The CLI prints the serializer payload with deterministic JSON formatting.
6. The Human Review boundary remains binding for all draft material.

## Components

| Component | Current role |
| --- | --- |
| CLI entrypoint | Local command-line interface in `offline_mvp/__main__.py`; no API or UI surface. |
| Synthetic fixtures | Local examples without original documents, real personal data, or productive system data. |
| Mock workflow | Deterministic offline orchestration for local validation only. |
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

The current synthetic case semantics are:

| Case | Current behavior |
| --- | --- |
| `CASE_001` | `gateway=escalate`, `RiskLevel C`, `draft.available=false`, `review_gate.allows_offline_mock_continuation=false`. `draft.questions` may still be visible as internal, review-bound preparation from synthetic missing items. |
| `CASE_002` | The only positive draft case; `draft.available=true`. |
| `CASE_003` | Restrictive case; no available draft. |
| `CASE_004` | Restrictive case; no available draft. |
| `CASE_005` | Privacy Gateway block case; `gateway=block`, `RiskLevel D`, no available draft, and Human Review remains required. |

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

The offline MVP does not provide or introduce:

- API
- UI
- real data
- tax advice
- tax calculation logic
- LLM integration
- productive communication
- productive client communication
- external productive integrations
- automated filing, submission, or transmission
- Agenda, DATEV, ELSTER, banking, email, or cloud integration

These boundaries preserve the current compliance-first scope: local fixtures,
deterministic offline behavior, review-first routing, and draft-only output.
