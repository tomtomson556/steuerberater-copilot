# ADR 004: Select Azure as the single reference cloud

## Status

Accepted

## Context

ADR 003 keeps the application core local-first and cloud-neutral, but allows one
reference cloud at the system boundary for the 2026 portfolio. The project needs
a small deployment proof for the synthetic FastAPI and Docker demo without
turning the offline MVP into a productive Kanzlei system.

The reference cloud must support an EU region, container execution, managed
secret storage, observable runtime signals, and a simple cost off switch. It must
not require real Mandanten-, Kanzlei-, Beleg-, Steuer-, or productive metadata.

## Decision

Azure is accepted as the single reference cloud for the portfolio deployment
track.

The reference deployment targets an EU Azure region and uses container runtime
infrastructure at the system boundary. Azure Key Vault is the placeholder for
future secret integration. No secrets are committed to the repository, and the
current synthetic demo does not require a real provider secret.

The initial Infrastructure as Code skeleton uses Azure Bicep under
`infra/azure/`. It is intentionally small and demonstrates:

- containerized FastAPI demo deployment
- Azure Key Vault resource placeholder
- EU-region parameterization
- scale-to-zero or equivalent cost off switch
- no productive data paths

This is explicitly not a Multi-Cloud decision. AWS, GCP, hybrid operation, and
general cloud adapter abstractions remain out of scope for the 2026 portfolio
baseline unless the roadmap is changed by a later ADR.

## Consequences

Positive consequences:

- one concrete cloud target reduces portfolio ambiguity
- the application core can remain cloud-neutral
- Bicep artifacts can stay isolated under `infra/azure/`
- Key Vault can be documented without committing secrets
- a cost off switch is part of the deployment baseline

Accepted trade-offs:

- cloud depth is limited to one provider
- Azure-specific IaC exists at the repository boundary
- no portability layer is built for hypothetical future clouds

This decision does not introduce productive tax advice, productive tax actions,
real client data, productive external integrations, or live provider
verification.

## Revisit conditions

Revisit this ADR if:

- Azure access becomes unavailable for the portfolio demonstration
- the portfolio target changes materially
- real data or productive operation is proposed
- another cloud becomes mandatory for a concrete employment or review context
