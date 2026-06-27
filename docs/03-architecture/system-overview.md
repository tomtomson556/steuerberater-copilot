# Offline MVP System Overview

## Scope

The current offline MVP is a local, deterministic preparation workflow. It uses
synthetic fixtures only and produces draft output for internal review.

It does not connect to productive systems, external services, real client data,
or filing channels.

## Current Flow

```text
synthetic fixture -> workflow -> risk classification -> human review gate -> draft output
```

1. Synthetic fixture cases are loaded from `fixtures/offline_mvp/cases.json`.
2. The offline mock workflow runs deterministic gateway checks.
3. The workflow assigns an internal `RiskLevel` A, B, C, or D.
4. The Human Review Gate decides whether the offline mock may continue.
5. The workflow returns a `DraftPackage` and exposes the `review_gate` decision.

## Components

| Component | Current role |
| --- | --- |
| Synthetic fixtures | Local examples without original documents, real personal data, or productive system data. |
| Mock workflow | Deterministic offline orchestration for local validation only. |
| Risk classification | Internal routing marker using `RiskLevel.CLASS_A` through `RiskLevel.CLASS_D`. |
| Human Review Gate | Mandatory gate derived from the internal risk class. |
| Draft output | Internal preparation material only, without external effect. |

## Review Behavior

`RiskLevel A` may continue only as an offline mock workflow without productive
effect.

`RiskLevel B`, `RiskLevel C`, and `RiskLevel D` stop before automatic
continuation. Their workflow output keeps Human Review visible and avoids
substantive draft continuation before review.

Human Review is a mandatory project rule. The Kanzlei reviews, and the
responsible Steuerberater decides where fachliche responsibility is required.

## Current Non-Goals

The offline MVP does not provide or introduce:

- productive integrations
- real personal data
- tax advice
- tax calculation logic
- external service calls
- automated filing or submission
- Agenda, DATEV, ELSTER, banking, email, or cloud integration

These boundaries preserve the current compliance-first scope: local fixtures,
deterministic offline behavior, review-first routing, and draft-only output.
