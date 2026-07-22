# ADR 004: Reference cloud selection (comparison pending)

## Status

Proposed / Deferred

This ADR is **not** an accepted architecture decision on
`experiment/cursor-full-project`. It records the open comparison only.

## Context

ADR 003 keeps the application core local-first and cloud-neutral and allows
exactly one later reference cloud at the system boundary. The binding roadmap
requires AWS and Azure to be compared by 31 August 2026 before a final choice.

Current preference signals exist for Azure in the German B2B context, but
account access, cost, EU-region readiness, container operations, secret
management, monitoring effort, and employment-market fit are not yet finally
weighed.

An experimental Azure Bicep skeleton may exist under `infra/azure/` on this
experiment branch. That skeleton is a disposable prototype for exploring IaC
shape. It is not a binding selection of Azure and must not be read as portfolio
completion of Phase 5.

## Non-decision

No reference cloud is accepted by this ADR at this time.

Until the comparison is complete and this ADR is rewritten with status
`Accepted`:

- Azure is not the final reference cloud
- AWS remains an open alternative
- Multi-Cloud support remains out of scope
- any `infra/azure/` artifacts are experimental prototypes only

## Comparison criteria (binding)

- target roles and labour market signal
- available account and service access
- cost and reliable shut-off
- EU region
- model access boundaries remain separate from cloud choice
- container runtime
- secret management without repository secrets
- monitoring baseline
- IaC effort

## Consequences

Positive consequences of deferring:

- avoids locking the portfolio to an unverified cloud choice
- keeps the application core cloud-neutral
- allows experimental IaC exploration without overstating readiness

Accepted temporary trade-offs:

- no live reference-cloud deployment claim
- documentation must distinguish prototype IaC from accepted architecture

## Revisit deadline

Revisit and either accept a single cloud or explicitly re-scope by
31 August 2026, consistent with
`docs/10-mvp-scope/ai-engineering-roadmap-2026.md` and ADR 003.
