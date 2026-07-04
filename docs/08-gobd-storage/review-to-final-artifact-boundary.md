# Review-to-Final Artifact Boundary

## Purpose

This document describes the conceptual boundary between offline MVP draft
material, Human Review, and a later final artifact after human approval.

It is an architecture and operations boundary only. It does not change runtime
behavior, the CLI JSON contract, tests, fixtures, storage behavior, or release
scope.

## Current Offline MVP Boundary

The offline MVP produces only draft and review artifacts from synthetic
fixtures. Its local CLI output is deterministic preparation material for
engineering validation and Kanzlei review.

The CLI JSON output is not a final tax document, not a productive handoff, and
not a stored business record. It remains governed by the current
[Offline MVP CLI JSON Contract](../10-testing-quality/offline-mvp-cli-json-contract.md).

Fixtures, test outputs, and CLI JSON examples are test artifacts. They are not
productive storage artifacts, retained records, or evidence of a productive
document lifecycle.

## Artifact Stages

| Stage | Meaning | Boundary |
| --- | --- | --- |
| Offline-MVP draft | Deterministic draft material produced from synthetic fixtures. | Internal preparation only; no productive effect and no final document status. |
| Human Review | Mandatory human control before fachliche use, communication, handoff, or later finalization. | The model does not approve, release, send, file, or finalize. |
| Final artifact after human approval | A later artifact may exist only after authorized human review and approval. | The offline MVP does not create, store, export, or retain this artifact. |

Human Review remains the binding gate between preparation material and any later
approved artifact. The Kanzlei reviews; the responsible Steuerberater decides
where fachliche responsibility is required.

## Relation to Storage Baseline

The [GoBD-Oriented Storage Baseline](gobd-storage-baseline.md) defines
orientation for future storage architecture. This boundary document narrows the
current artifact states so draft and review material cannot be mistaken for a
later approved artifact.

No productive storage, document management system, archive, WORM storage,
retention mechanism, or export function is introduced by this document. Any
future productive storage behavior requires a separate architecture decision,
implementation scope, and review.

This document does not state that the project satisfies GoBD requirements.

## Non-Goals

This document does not:

- provide tax advice or legal advice
- change the CLI JSON contract
- add runtime semantics
- add productive storage or retention behavior
- add a document management system, archive, WORM storage, or export function
- make fixtures, test outputs, or CLI JSON output productive records
- approve autonomous filing, sending, submission, communication, or handoff
- remove, weaken, or bypass the Human Review gate
