# Portfolio Status - July 2026 Experiment Branch

## Scope

This document summarizes the work present on
`experiment/cursor-full-project` as of 22 July 2026. It is a branch status note,
not a claim that every item is merged to `main`.

The project principle remains:

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Implemented on the experiment branch

- RAG contradiction and freshness evaluation contracts, libraries, runners,
  assessments, and aggregate metrics.
- Portfolio evaluation baseline report across workflow, retrieval, grounding,
  abstention, contradiction, and freshness suites.
- Evaluation CLI entry point:
  `python -m steuerberater_copilot.evaluation --portfolio-baseline`.
- Structured runtime observability helpers for JSON event lines, request IDs,
  timers, and in-process metrics snapshots.
- Synthetic FastAPI demo boundary with health, version, draft, RAG, and metrics
  endpoints.
- Dockerfile, Docker Compose file, and `.dockerignore` for local container
  demonstration.
- Minimal Azure reference-cloud ADR, deployment guide, and Bicep skeleton.

## Current portfolio baseline

The branch-level portfolio baseline contains 32 synthetic evaluation cases. The
binary suites report a pass rate of `1.0` with the current deterministic
fixtures and `FakeModelProvider` setup.

Retrieval and grounding remain metric suites without invented binary pass/fail
thresholds. Their metrics support regression review, not a productive
steuerliche Qualitaetsaussage.

## Decisions recorded

- The safe default remains local, offline, deterministic, and synthetic.
- `FakeModelProvider` remains the default for tests and demos.
- FastAPI is a system-boundary demo, not workflow logic.
- Docker is the local deployment baseline for the portfolio.
- Azure is the single reference cloud for the portfolio track.
- Multi-Cloud support remains explicitly out of scope.
- Secrets are placeholders only and are not committed.

## Open items

- Merge readiness for the experiment branch still depends on full local checks
  and review.
- A real provider live smoke remains opt-in and is not verified by this branch
  status.
- The Azure skeleton still needs a real non-productive image reference before a
  live deployment attempt.
- Authentication, persistence, productive monitoring, DATEV, Agenda, ELSTER,
  banking, and email integrations remain out of scope.
- Demo video and final portfolio packaging remain later portfolio work.

## Non-claims

This status does not claim productive tax advice, productive tax actions,
productive Kanzlei operation, real client data handling, live provider
verification, or compliance certification.
