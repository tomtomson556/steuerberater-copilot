# Reference Cloud Deployment Guide (Experimental Prototype)

## Scope

This guide describes an **experimental** Azure IaC prototype path for a
synthetic FastAPI demo container. It is not an accepted architecture decision
and not a productive Kanzlei operations manual.

ADR-004 on this branch remains `Proposed / Deferred`. AWS and Azure must still
be compared by 31 August 2026 before any final reference-cloud acceptance.

Allowed input remains synthetic fixture data only. The deployment must not use
real Mandanten-, Kanzlei-, Beleg-, Steuer-, banking, email, DATEV, Agenda, or
ELSTER data.

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Prototype status

- `infra/azure/` is a disposable experiment-branch sketch
- Azure is not finally selected
- no live deployment is claimed by this repository state
- no secrets are committed
- Multi-Cloud support remains out of scope

## Prerequisites for a later non-productive trial

- a non-productive cloud account chosen only after ADR-004 acceptance
- container image built from the repository `Dockerfile`
- image pushed to a non-productive registry
- local parameter file outside version control

The current demo uses `FakeModelProvider` by default. A real model provider is
not required for exercising the local Docker path.

## Prototype deploy command (not verified live here)

```bash
az deployment group create \
  --resource-group <resource-group> \
  --template-file infra/azure/main.bicep \
  --parameters @infra/azure/parameters.example.json
```

Replace the container image placeholder before any real trial. Do not commit
filled parameter files that contain account-specific values or secrets.

## Runtime checks for a later trial

- `/health` returns `{"status":"ok"}`
- `/version` reports `FakeModelProvider` as the default provider
- demo endpoints only accept synthetic fixture case IDs such as `CASE_002`
- responses do not include full prompt text
- runtime logs contain structured metadata only

## Cost off switch

The Bicep skeleton exposes `minReplicas` and defaults it to `0`. Keep
`maxReplicas` small for portfolio testing. Deleting the resource group remains
the cleanest stop operation for disposable experiments.

## Boundaries

This prototype guide does not add:

- accepted Azure selection
- productive tax advice or tax actions
- real client data
- DATEV, Agenda, ELSTER, banking, or email integration
- Multi-Cloud support
- live provider verification
- productive operations guarantees

Human Review remains mandatory for any tax-relevant draft material.
