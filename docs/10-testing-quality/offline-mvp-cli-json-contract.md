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
steuerberater-copilot-offline-mvp --case CASE_001
python -m steuerberater_copilot.offline_mvp --case CASE_002
python -m steuerberater_copilot.offline_mvp --case CASE_003
python -m steuerberater_copilot.offline_mvp --case CASE_004
python -m steuerberater_copilot.offline_mvp --case CASE_005
python -m steuerberater_copilot.offline_mvp --all
python -m steuerberater_copilot.offline_mvp --list-cases
python -m steuerberater_copilot.offline_mvp --review-worklist
python -m steuerberater_copilot.offline_mvp --review-summary
```

The console script `steuerberater-copilot-offline-mvp` uses the same JSON
contracts as `python -m steuerberater_copilot.offline_mvp` for JSON-emitting
modes. This PR adds no JSON fields.

`--case` returns one JSON object. `--all` returns a JSON array with all five
synthetic fixture cases. `--list-cases` returns the available synthetic case
IDs.

`--review-worklist` returns a compact JSON array for local review preparation.
It aggregates existing workflow results from all synthetic fixture cases and
does not change the `--case` or `--all` workflow object contract.

The unfiltered `--review-worklist` output remains the stable worklist contract.
Optional worklist filters such as `--review-limit`, `--review-min-risk`,
`--review-gateway`, and `--review-open-questions-only` only change the subset of
entries emitted to stdout. Each emitted item keeps the same structure; no JSON
fields are added, removed, renamed, or reinterpreted, and no priority logic is
changed.

`--review-summary` returns a compact JSON object for local review preparation.
It aggregates existing workflow and review worklist results from all synthetic
fixture cases. It does not change the workflow object contract or the review
worklist contract.

The unfiltered `--review-summary` output remains the stable summary contract.
The same optional review filters supported by `--review-worklist` may be used
with `--review-summary`. In filtered summary mode, the counts and
`highest_priority_cases` are computed only from the cases that remain after
applying the filters, and the output adds `summary_scope` and
`applied_filters`.

The optional `--review-handoff path/to/review-handoff.md` argument may write a
local Markdown review handoff in addition to stdout JSON for `--case` or
`--all`. It does not add, remove, rename, or reinterpret any JSON fields.

`--version` is a local CLI information mode. It prints a short text line and is
not a JSON contract.

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
| `available` | boolean | whether a complete draft is exposed in the CLI output |
| `draft_only` | boolean | explicit draft-only marker |
| `summary` | array of strings | visible summary points when a draft is available |
| `summary_points` | array of strings | backward-compatible mirror of `summary` |
| `questions` | array of strings | internal, review-bound question drafts derived from synthetic missing items |
| `review_status` | string | review status label for the draft package |
| `handoff_notes` | array of strings | manual handoff and review notes |
| `disclaimers` | array of strings | draft-only and review boundary notices |

`draft.summary` is currently an alias of `draft.summary_points`.
`summary_points` remains available for backward compatibility.

`draft.available == false` means no complete, substantively usable draft is
available. `draft.questions` may still contain internal, review-bound question
drafts when synthetic missing items can be surfaced for Kanzlei review.

Visible `draft.questions` do not allow offline mock continuation. They are not
client communication, not tax advice, not a productive handoff, and not an
approval to continue automatically. Human Review remains mandatory whenever the
Review Gate requires it.

`draft_only` remains explicitly visible in the JSON output.

An available draft remains preparation and review material only. The Kanzlei
reviews, and the Steuerberater decides.

## Review Worklist Contract

`--review-worklist` returns a JSON array. Each item contains these top-level
fields:

- `case_id`
- `priority`
- `gateway`
- `risk`
- `review_gate`
- `draft`
- `open_questions_count`
- `open_questions`

The worklist is local, deterministic, synthetic, and review-oriented. It is not
a workspace, not a persistent queue, and not a human review decision.

`gateway` contains:

- `decision`
- `reasons`
- `block_reasons`

`risk` contains:

- `level`
- `review_required`
- `basis`

`review_gate` contains:

- `status`
- `allows_offline_mock_continuation`
- `reason`

`draft` contains:

- `available`
- `review_status`

`open_questions_count` is the number of entries in `open_questions`.

### Review Worklist Priority

The worklist uses existing workflow markers only. It does not reclassify cases
or decide review outcomes.

Priority is calculated as follows:

- `gateway.decision == "block"` receives priority `100`
- otherwise RiskLevel `D` receives `80`, `C` receives `60`, `B` receives `40`,
  and `A` receives `20`
- cases with `risk.review_required == true` receive a `5` point bonus
- items are sorted by descending `priority`, then ascending `case_id`

## Review Summary Contract

`--review-summary` returns a JSON object. It is a local stdout-only aggregation
for synthetic fixture results. It is not productive reporting, not a dashboard,
not persistent storage, and not a fachliche or human review decision.

The top-level fields are:

- `total_cases`
- `gateway`
- `risk`
- `review_gate`
- `draft_availability`
- `open_questions`
- `highest_priority_cases`

`gateway` always contains the current gateway decision keys:

- `allow_draft`
- `escalate`
- `block`

These values must not be normalized to new names such as `allow`.

`risk` always contains:

- `A`
- `B`
- `C`
- `D`

`review_gate` always contains:

- `allowed_offline_mock_continuation`
- `requires_human_review`

`draft_availability` always contains:

- `available`
- `unavailable`

`open_questions` contains:

- `total`
- `cases_with_open_questions`

`highest_priority_cases` contains the first three cases from the existing
review worklist priority order, using only these compact fields:

- `case_id`
- `priority`
- `gateway_decision`
- `risk_level`
- `review_gate_status`
- `draft_available`
- `open_questions_count`

The summary uses existing workflow and review worklist markers only. It does
not reclassify cases, decide review outcomes, change draft availability, or
weaken Human Review.

Optional review filters may be used with `--review-summary`:

```bash
python -m steuerberater_copilot.offline_mvp --review-summary --review-limit 3
python -m steuerberater_copilot.offline_mvp --review-summary --review-min-risk C
python -m steuerberater_copilot.offline_mvp --review-summary --review-gateway block
python -m steuerberater_copilot.offline_mvp --review-summary --review-open-questions-only
```

In filtered mode, all aggregation fields refer only to the filtered case set:

- `total_cases`
- `gateway`
- `risk`
- `review_gate`
- `draft_availability`
- `open_questions`
- `highest_priority_cases`

Filtered summaries add these top-level fields:

- `summary_scope`
- `applied_filters`

`summary_scope` is `filtered`. `applied_filters` contains only filters that
were actually set, using these canonical keys and value types:

- `review_limit`: number
- `review_min_risk`: string such as `C`
- `review_gateway`: string such as `block`
- `review_open_questions_only`: boolean `true`

These two fields are not present in unfiltered `--review-summary` output.

## Current Case Semantics

The current fixture semantics are:

| Case | Gateway | RiskLevel | Draft available | Questions |
| --- | --- | --- | --- | --- |
| `CASE_001` | `escalate` | `C` | `false` | review-bound internal question drafts |
| `CASE_002` | `allow_draft` | `A` | `true` | `[]` |
| `CASE_003` | `allow_draft` | `B` | `false` | `[]` |
| `CASE_004` | `allow_draft` | `D` | `false` | `[]` |
| `CASE_005` | `block` | `D` | `false` | `[]` |

`CASE_002` is the only positive draft case.

`CASE_001` is explicitly not a positive draft case. Its visible questions are
only internal, review-bound preparation from synthetic missing items and do not
change the Review Gate result.

`CASE_005` is a synthetic Privacy Gateway block case. It exists only to secure
the end-to-end `block`/RiskLevel-D path through fixture loading, workflow,
CLI, and JSON output.

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
