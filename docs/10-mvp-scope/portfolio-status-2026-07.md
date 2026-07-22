# Portfolio Status - July 2026 Experiment Branch

## Scope

This document summarizes work on `experiment/cursor-full-project` as of
22 July 2026. It is a branch status note, not a claim that items are merged to
`main`, productively verified, or portfolio-complete.

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Presence matrix

| Item | on `main` | on this experiment branch | maturity |
| --- | --- | --- | --- |
| Offline MVP CLI, gateway, Human Review, FakeModelProvider | yes | yes | implemented and tested |
| Semantic draft validation, prompt versioning, offline AI evaluation | yes | yes | implemented and tested |
| OpenAI Responses adapter | yes | yes | code present; live smoke not verified |
| Retrieval / grounding / abstention evaluation baseline | yes | yes | implemented and tested |
| Contradiction evaluation over natural synthetic passages | no | yes | experimental, deterministic closed-template extractor |
| Freshness evaluation via supersession / validity window | no | yes | experimental, metadata semantics only |
| Portfolio evaluation baseline CLI | no | yes | experimental aggregation |
| FastAPI synthetic demo boundary | no | yes | experimental demo |
| Docker demo runtime | no | yes | experimental local container path |
| Structured runtime logging / in-process metrics | no | yes | experimental helpers |
| Azure Bicep / reference-cloud guide | no | yes | prototype sketch only; cloud choice not accepted |
| ADR-004 final cloud selection | no | proposed/deferred only | not accepted |

## Implemented on the experiment branch only

- RAG contradiction detection and evaluation using closed-template extraction
  from natural synthetic sentences. This is **not** general semantic NLP.
- RAG freshness/outdated detection based on supersession and explicit
  `valid_to` windows. A past `valid_from` alone does not mark a document
  outdated.
- Portfolio evaluation baseline report and CLI.
- Synthetic FastAPI demo, Docker runtime, and observability helpers.
- Experimental Azure IaC sketch and deferred ADR-004 comparison note.

## Evaluation posture

The experiment-branch portfolio baseline currently aggregates the synthetic
suites available on this branch. Binary suites (workflow, abstention,
contradiction, freshness) are assessed with exact expected/observed
comparisons. Retrieval and grounding remain metric suites without invented
binary pass/fail thresholds.

After the hardening pass, the portfolio baseline contains 41 synthetic cases.
The binary suites contain 28 cases with 27 passing; the failed case is the
documented contradiction limitation for informal "decade" wording. A high
binary pass rate means the current deterministic fixtures and detectors agree
on most labeled cases. It is not proof of productive RAG quality, general
contradiction understanding, or End-to-End safety.

See also
[`experiment-hardening-assessment-2026-07.md`](experiment-hardening-assessment-2026-07.md).

## Decisions and non-decisions

- Safe default remains local, offline, deterministic, and synthetic.
- `FakeModelProvider` remains the default for tests and demos.
- FastAPI stays a system-boundary demo, not workflow logic.
- Docker is a local deployment baseline candidate, not a cloud decision.
- Reference-cloud selection remains open until 31 August 2026.
- Azure IaC on this branch is an experimental prototype only.
- Multi-Cloud support remains out of scope.

## Open items

- Final AWS vs Azure comparison and an accepted ADR-004.
- Opt-in OpenAI live smoke verification.
- Live non-productive container deployment with real image references and a
  secret store that never commits secrets.
- Broader adversarial evaluation beyond the current synthetic libraries.
- Demo video and final portfolio packaging.
- Any merge to `main` remains a separate human decision and should be sliced.

## Non-claims

This status does not claim:

- portfolio-ready production quality
- completed Phase 3/4/5 on `main`
- accepted Azure reference-cloud selection
- productive tax advice or tax actions
- general semantic contradiction NLP
- live provider verification
- compliance certification
