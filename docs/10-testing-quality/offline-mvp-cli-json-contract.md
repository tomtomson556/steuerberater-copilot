# Offline MVP CLI JSON Contract

## Purpose

This document describes the currently stabilized CLI JSON output contract for
the offline MVP.

It applies to the local, deterministic, synthetic, draft-only offline MVP. It
serves as a reference for tests and human review processes.

This is not a productive interface. It provides no tax advice, no tax
calculation logic, and no external integration.

## CLI Entry Points

The supported local CLI entry points are:

```bash
python -m steuerberater_copilot.offline_mvp --case CASE_001
python -m steuerberater_copilot.offline_mvp --case CASE_002
python -m steuerberater_copilot.offline_mvp --case CASE_003
python -m steuerberater_copilot.offline_mvp --case CASE_004
python -m steuerberater_copilot.offline_mvp --all
python -m steuerberater_copilot.offline_mvp --list-cases
```

`--case` returns one JSON object. `--all` returns a JSON array with all four
synthetic fixture cases. `--list-cases` returns the available synthetic case
IDs.

## Top-Level Contract

Each workflow JSON object contains these top-level fields:

- `case_id`
- `gateway`
- `risk`
- `review_gate`
- `draft`

Tests should rely on these field names, not on pretty-printing or object key
order.

## Workflow Object Contract

Each workflow JSON object currently contains exactly these nested objects and
fields. Tests should treat the field names and value semantics as the contract,
not the pretty-printing or object key order.

## Gateway Contract

`gateway` contains:

- `decision`
- `reasons`
- `block_reasons`
- `checks`

The field types are:

| Field | Type | Meaning |
| --- | --- | --- |
| `decision` | string | deterministic gateway result |
| `reasons` | array of strings | escalation reasons |
| `block_reasons` | array of strings | block reasons |
| `checks` | array of strings | request- and response-side check labels |

The current `decision` values are:

- `allow_draft`
- `escalate`
- `block`

`allow_draft` is only for synthetic, allowed, sufficiently checked cases.

`escalate` is used for unclear purpose, missing review path,
re-identification risk, or missing context.

`block` is used for prohibited data classes or problematic response signals.

`escalate` and `block` lead to `draft.available == false`.

## Risk Contract

`risk` contains:

- `level`
- `review_required`
- `basis`

The field types are:

| Field | Type | Meaning |
| --- | --- | --- |
| `level` | string | internal RiskLevel marker |
| `review_required` | boolean | whether Human Review is required before continuation |
| `basis` | array of strings | deterministic routing basis from synthetic signals and gateway results |

The current `level` values are `A`, `B`, `C`, and `D`.

RiskLevel `A` can continue only in the offline mock, and only when the Privacy
Gateway returns `allow_draft` and the Review Gate allows continuation.

RiskLevel `B`, `C`, and `D` stop before automatic continuation. They require
Human Review and lead to `draft.available == false`.

## Review Gate Contract

`review_gate` contains:

- `status`
- `decision`
- `allows_offline_mock_continuation`
- `reason`

The field types are:

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | string | deterministic Review Gate status |
| `decision` | string | current alias of `status` |
| `allows_offline_mock_continuation` | boolean | whether the offline mock may continue |
| `reason` | string | human-readable gate reason |

`review_gate.decision` is currently an alias of `review_gate.status`.

If a separate Review Gate decision meaning is introduced later, the JSON
contract and tests must be updated deliberately.

Human Review must not be bypassed, removed, or weakened.

## Draft Contract

`draft` contains:

- `available`
- `draft_only`
- `summary`
- `summary_points`
- `questions`
- `review_status`
- `handoff_notes`
- `disclaimers`

The field types are:

| Field | Type | Meaning |
| --- | --- | --- |
| `available` | boolean | whether draft material is exposed in the CLI output |
| `draft_only` | boolean | explicit draft-only marker |
| `summary` | array of strings | visible summary points when a draft is available |
| `summary_points` | array of strings | backward-compatible mirror of `summary` |
| `questions` | array of strings | visible question drafts when a draft is available |
| `review_status` | string | review status label for the draft package |
| `handoff_notes` | array of strings | manual handoff and review notes |
| `disclaimers` | array of strings | draft-only and review boundary notices |

`draft.summary` is currently an alias of `draft.summary_points`.
`summary_points` remains available for backward compatibility.

`draft_only` remains explicitly visible in the JSON output.

An available draft remains preparation and review material only. The Kanzlei
reviews, and the Steuerberater decides.

## Current Case Semantics

The current fixture semantics are:

| Case | Gateway | RiskLevel | Draft available | Questions |
| --- | --- | --- | --- | --- |
| `CASE_001` | `escalate` | `C` | `false` | `[]` |
| `CASE_002` | `allow_draft` | `A` | `true` | `[]` |
| `CASE_003` | `allow_draft` | `B` | `false` | `[]` |
| `CASE_004` | `allow_draft` | `D` | `false` | `[]` |

`CASE_002` is the only positive draft case.

`CASE_001` is explicitly not a positive draft case.

## Non-Goals

The CLI JSON contract does not introduce:

- productive API
- FastAPI
- UI
- cloud integration
- LLM integration
- DATEV, ELSTER, Agenda, banking, or email integration
- automatic filing, submission, or transmission
- real data
- tax advice
- tax calculation logic

## Relation to ADR 002

[ADR 002](../15-decisions/adr/adr-002-cli-first-api-second.md) documents the
CLI-first/API-second interface decision.

The CLI is the first supported entry point for the offline MVP. JSON output is
the primary machine-readable interface in this phase.
