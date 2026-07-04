# GoBD-Oriented Storage Baseline

## Purpose

The current project is an offline MVP. It does not implement productive
document storage, a document management system, an archive, WORM storage, or
production retention.

This document defines a baseline for future architecture and operations work
around GoBD-oriented storage considerations. It is not a compliance
certification, a legal assessment, or a release approval for productive use.

The GoBD were changed by BMF letter dated 14 July 2025, titled as the second
change due to various statutory changes. The BMF letter is the reference for
this date and context:
[2025-07-14-GoBD-2-aenderung.pdf](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2025-07-14-GoBD-2-aenderung.pdf?__blob=publicationFile&v=3).
This baseline uses that current context only as orientation for future storage
design and avoids deriving legal conclusions from it.

## Offline MVP Boundary

The existing system remains CLI-first/API-second. The implemented surface is a
local CLI with deterministic JSON output based on synthetic offline fixtures.
The workflow is review-first and stops at a Human Review boundary before any
productive use.

The offline MVP does not perform autonomous filing, sending, submission, or
external communication. It does not connect to productive storage, client
systems, tax filing channels, email, banking, DATEV, Agenda, ELSTER, cloud
services, or archives.

Current CLI JSON output and fixtures are test artifacts. They support local
validation of deterministic workflow behavior and the CLI contract. They are
not a productive record archive and are not designed as retained business
records.

The current review-to-final artifact boundary is described in
[review-to-final-artifact-boundary.md](review-to-final-artifact-boundary.md).

## Target Principles

Future productive storage design should be evaluated against these principles:

- Traceability: record where documents and decisions came from, which workflow
  step handled them, and which user or system action changed state.
- Completeness: preserve all records required for the defined productive
  process, including relevant source material, derived artifacts, review
  decisions, and export metadata.
- Immutability and tamper resistance: protect finalized records from silent
  modification and make later corrections explicit and traceable.
- Reproducibility: keep enough inputs, versions, decisions, and metadata to
  explain how a stored artifact or review package was produced.
- Access control: restrict read, write, review, finalization, export, and
  deletion actions to defined roles and approved service paths.
- Retention and deletion boundaries: separate retention requirements,
  deletion holds, test data lifecycle, and productive record lifecycle.
- Export and audit support: provide reviewable export packages for authorized
  internal review, operational checks, or external audit workflows.
- State separation: distinguish draft, review, and final artifact states so
  incomplete preparation cannot be mistaken for a finalized record.

## Relation To Current Architecture

The current offline MVP architecture already establishes boundaries that future
storage work must preserve:

- CLI-first/API-second remains the interface baseline until changed by an ADR.
- The Human Review gate remains mandatory before any productive effect.
- Offline fixture behavior remains deterministic and synthetic.
- Draft output remains internal preparation material only.
- No autonomous filing, sending, tax submission, or productive communication is
  introduced by the offline MVP.

Any future storage implementation should make the transition from draft to
review to final artifact explicit. A final artifact should exist only after
human approval and should carry enough metadata to support later review without
changing the CLI JSON contract by accident.

## Non-Goals

This document does not:

- claim that the project satisfies GoBD requirements
- provide tax advice or legal advice
- implement a DMS, archive, WORM storage, or production retention
- change the CLI JSON contract
- change runtime behavior
- add productive document storage
- approve autonomous filing, sending, or tax submission

## Future Implementation Considerations

Future PRs may evaluate these design options before any productive storage
scope is introduced:

- Append-only event log or audit trail for document and review state changes.
- Content-addressed document storage or checksums for source and derived
  artifacts.
- Versioned review decisions with reviewer identity, timestamps, and rationale.
- Explicit finalization step after Human Review approval.
- Retention metadata that records retention class, legal hold state, deletion
  eligibility, and responsible process owner.
- Export package for audit or review, including source references, generated
  artifacts, review decisions, checksums, and operational metadata.

Each implementation step should remain separately reviewable and should state
which behavior is still mock-only, which behavior is productive, and which
claims remain intentionally out of scope.
