# Experiment Branch Hardening Assessment

Date: 22 July 2026  
Branch: `experiment/cursor-full-project`  
Scope: red-team / hardening pass on the existing experiment implementation

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## What this assessment is

An honest post-red-team status for the experiment branch. It is not a
portfolio-complete claim, not a `main` completion claim, and not productive
verification.

## Belastbar demonstrierte Faehigkeiten

- Offline synthetic AI workflow with gateway, risk class, Human Review Gate,
  invocation policy, structured parse/validation, and response gateway controls
- Deterministic offline evaluation suites with FakeModelProvider
- Local retrieval and grounding metric suites
- Missing-evidence abstention evaluation
- Closed-template contradiction detection for a **small** set of natural
  synthetic sentence forms, including:
  - unscoped retention conflicts
  - retention affirmation vs negation
  - archive required vs not required
  - subject separation for `Client <Name> ...`
  - temporal-hedge suppression for unscoped extraction
- Freshness outdatedness via supersession and inclusive `valid_to` closure,
  including overlap, highest-expired-lower-current, exact boundary, and version
  gaps
- FastAPI synthetic demo endpoints under pytest TestClient
- Evaluation CLI aggregation

## Nur teilweise demonstrierte Faehigkeiten

- Contradiction detection beyond the published closed templates
- Independence of evaluation: document-id assessment is less coupled than exact
  sentence matching, but fixtures remain synthetic and detector-aware
- Docker demo path exists in repository files, but was **not** executed in this
  hardening environment because Docker was unavailable
- Azure IaC exists only as an experimental prototype; cloud choice remains open

## Nicht verifizierte Faehigkeiten

- Live OpenAI smoke
- Real container runtime smoke in this environment
- Any cloud deployment
- General semantic contradiction NLP
- Productive tax quality, compliance certification, or Kanzlei readiness

## Bekannte Schwaechen gefunden in dieser Runde

| Weakness | Status after hardening |
| --- | --- |
| False positive: different client subjects collided on unscoped retention | Corrected with subject-scoped keys and anchored patterns |
| False positive: temporally hedged retention sentences collided | Corrected by skipping temporally hedged unscoped extractions |
| False negative: `is 10 years` vs `is not 10 years` | Corrected with polarity-aware retention templates |
| Risk: `archive is not required` misread by alternation order | Hardened; `not required` normalizes to optional before positive form |
| Exact supporting-text assessment rewarded detector-string copying | Pass criteria now use presence + implicated document IDs |
| Duplicate family/version numbers were silently ambiguous | Rejected as invalid metadata |
| Informal wording such as "kept for a decade" remains invisible | Left as intentional failing known-limitation case |
| Docker build/smoke | Not verifiable here; documented as unverified |

## Evaluation after red-team

- Contradiction suite: 9 cases; pass rate intentionally below 1.0 because of
  `EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE`
- Freshness suite: 8 edge-focused cases; binary pass rate 1.0 under the stated
  metadata semantics
- Portfolio baseline: 41 synthetic cases; binary suite currently 27/28
- Perfect pass rate is no longer treated as a goal

## Suitable later small production-branch candidates

- FastAPI factory/demo boundary pattern
- Evaluation CLI / portfolio aggregation idea
- Freshness metadata semantics once further reviewed
- Observability event shape
- Docker packaging approach

## Do not take over wholesale to `main`

- The whole experiment branch as one bulk merge
- Closed-template contradiction detector as if it were semantic RAG quality
- Azure Bicep / ADR-004 as an accepted cloud decision
- Any claim of portfolio-ready completion from this branch alone
- Known-limitation-aware fixtures without documenting the limitation

## Practical verification notes

- `ruff`, `pytest`, and `policy_claim_check` are the verified local gates
- FastAPI behavior is covered by automated TestClient tests
- `docker` was not available in the hardening environment; no container success
  is claimed
