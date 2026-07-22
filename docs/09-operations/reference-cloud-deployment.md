# Reference Cloud Deployment Guide

## Scope

This guide describes the minimal Azure reference-cloud path for the synthetic
FastAPI demo. It is a portfolio deployment guide, not a productive Kanzlei
operations manual.

Allowed input remains synthetic fixture data only. The deployment must not use
real Mandanten-, Kanzlei-, Beleg-, Steuer-, banking, email, DATEV, Agenda, or
ELSTER data.

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Prerequisites

- Azure subscription selected for portfolio experiments
- Azure CLI installed locally
- Docker image built from the repository `Dockerfile`
- Container image pushed to a non-productive registry
- No secrets committed to Git

The current demo uses `FakeModelProvider` by default. A real model provider is
not required for this reference deployment guide.

## Deploy the skeleton

The Bicep entry point is:

```bash
az deployment group create \
  --resource-group <resource-group> \
  --template-file infra/azure/main.bicep \
  --parameters @infra/azure/parameters.example.json
```

Before running the command, copy `infra/azure/parameters.example.json` to a local
file outside version control or pass explicit parameter values. Replace the
container image placeholder with an image from a non-productive registry.

## Runtime checks

After deployment, inspect:

- `/health` returns `{"status":"ok"}`
- `/version` reports `FakeModelProvider` as the default provider
- demo endpoints only accept synthetic fixture case IDs such as `CASE_002`
- responses do not include full prompt text
- runtime logs contain structured metadata only, not prompts, model payloads, or
  secrets

## Cost off switch

The Bicep skeleton exposes `minReplicas` and defaults it to `0`. Keep
`maxReplicas` small for portfolio testing.

To stop the demo after review, scale the Container App to zero or remove the
resource group:

```bash
az containerapp update \
  --name <container-app-name> \
  --resource-group <resource-group> \
  --min-replicas 0
```

For a disposable portfolio run, deleting the resource group is the cleanest stop
operation.

## Boundaries

This reference deployment does not add:

- productive tax advice
- productive tax actions
- real client data
- DATEV, Agenda, ELSTER, banking, or email integration
- Multi-Cloud support
- live provider verification
- productive operations guarantees

Human Review remains mandatory for any tax-relevant draft material.
