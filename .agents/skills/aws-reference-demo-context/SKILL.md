---
name: aws-reference-demo-context
description: >-
  Routes repository context for the non-productive AWS reference demo,
  pre-live review, IAM lifecycle v2.3, IAM simulator evidence,
  reference-demo CloudFormation and Guard, and the local IAM control-plane
  tool. Use when the task is about the AWS reference demo, pre-live, IAM
  lifecycle, simulator SIM cases, reference-demo CloudFormation/Guard, or
  aws_reference_demo_iam_control_plane. Do not use for privacy gateway, RAG,
  evaluation, FastAPI, Docker, legal, or tax-advice work that is not an AWS
  reference-demo task.
---

# AWS reference-demo context

Instruction-only context router for AWS reference-demo, pre-live, and
IAM-lifecycle tasks. Portable Agent Skills `SKILL.md` for Codex and Cursor.

This skill lists paths, load stages, and task-based selection rules only.
Do not copy summaries of existing policies, SIM tables, or runbook steps.

## Bounds

Context routing only.
Does not authorize AWS writes.
Does not grant an AWS live-test Go.
Does not override AGENTS.md, roadmap, ADRs, implementation or tests.

`AGENTS.md` remains the general context router. This skill only adds the
AWS reference-demo load order.

## When to use

Apply when the user or files concern any of:

- AWS reference demo / reference-cloud demo
- pre-live review or AWS live-test readiness (routing only; no Go)
- IAM lifecycle v2.3, bootstrap role, operator or CloudFormation service role
- IAM Policy Simulator evidence or named `SIM-*` cases
- `infra/cloudformation/reference-demo.yaml` or
  `infra/cloudformation/guards/reference-demo.guard`
- `tools/aws_reference_demo_iam_control_plane.py`

## When not to use

Do not apply for work that is only about:

- privacy gateway
- RAG, retrieval, grounding, or evaluation suites
- FastAPI or Docker smoke
- legal, tax advice, or Human Review of tax drafts

If an AWS reference-demo task later needs one of those areas, follow
`AGENTS.md` for that need. Do not load those sources from this skill.

## Load order

Read in this order. Stop when the task is covered. Do not read later
stages "just in case".

Paths are repository-relative from the repo root.

### 1. Always / base

1. `AGENTS.md`
2. `docs/00-project/current-state.md` as an inventory index only; not a
   source of truth
3. Phase 5 only in `docs/10-mvp-scope/ai-engineering-roadmap-2026.md`:
   from `### Phase 5 - Referenz-Cloud und Observability` up to
   `### Phase 6 - Hardening und Portfolio-Release`. Do not load the rest
   of the roadmap unless the task names another phase.
4. `docs/15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md`
5. `docs/15-decisions/adr/adr-004-select-reference-cloud.md`

### 2. AWS core

After base, do **not** load architecture, runbook, and IAM README as a
universal package. Select each of them only when the current task needs
it. A broad AWS pre-live review may load all three together.

- Architecture: `docs/03-architecture/aws-reference-cloud-deployment.md`
- Runbook: `docs/09-operations/aws-reference-demo-runbook.md`
- IAM README: `infra/iam/reference-demo/v2.3/README.md`

Load a JSON file under `infra/iam/reference-demo/v2.3/` only when the
task names that artifact.

### 3. Task-dependent

Load only the rows that match the current task.

| When the task is about | Load |
| --- | --- |
| Broad AWS pre-live review or live-test readiness across architecture, operations, and IAM | Architecture; runbook; IAM README; simulator protocol **status and gates only** (see below) |
| A named `SIM-*` case or a specific simulator finding | IAM README as needed; that case's row and, if present, its correction section. Not architecture or the full runbook unless the finding requires them. Not the rest of the protocol |
| CloudFormation template, Guard, stack shape, or template freeze | `infra/cloudformation/reference-demo.yaml`; `infra/cloudformation/guards/reference-demo.guard`; `tests/test_reference_cloudformation_template.py`; `tests/test_reference_demo_runbook.py`. Architecture and/or runbook only as the concrete issue needs them |
| IAM JSON artifacts, bootstrap role, or policy text | IAM README; the named files under `infra/iam/reference-demo/v2.3/`; `tests/test_reference_demo_iam_policies.py` |
| Control-plane tool, apply, teardown, or dry-run | IAM README; `tools/aws_reference_demo_iam_control_plane.py`; `tests/test_aws_reference_demo_iam_control_plane.py`. Not the full runbook unless the task is about a runbook-owned operation |
| IAM, secrets, or security questions | `docs/02-security/security-baseline-policy.md` |
| MCP, external tools, or research limits | `docs/04-mcp/agent-mcp-boundaries.md` |

## Simulator protocol

Path: `docs/09-operations/aws-reference-demo-iam-simulator-test-protocol.md`

Do **not** load this file in full.

For status and gates, read only:

- `## Zweck und Status`
- `## Zählweise`
- `## Noch ausstehende Gates außerhalb dieses Simulatorprotokolls`

For a named `SIM-*` case, search for that ID and read only the matching
table row plus any `## Befund und Korrektur` section for that ID.

Do not load the full confirmed-case table, execution proofs, uncounted
attempts, or the sources appendix unless the user names that section.

## Do not auto-load

Do not load from this skill:

- `docs/05-privacy-gateway/privacy-gateway-contract.md`
- RAG, retrieval, grounding, or evaluation documents
- FastAPI, Docker, or legal documents
- Gateway, Human Review, or tax-risk policies except via `AGENTS.md` when
  the task is actually about those topics

Do not add scripts, bundled references, nested `AGENTS.md`,
`agents/openai.yaml`, or Cursor-only frontmatter (`paths`,
`disable-model-invocation`, `allowed-tools`).
