---
name: aws-reference-demo-context
description: >-
  Routes repository context for the non-productive AWS reference demo,
  its current simplified deployment target, pre-live review, reference-demo
  CloudFormation and Guard, and explicitly requested legacy IAM v2.3 evidence.
  Use when the task is about the AWS reference demo, pre-live readiness,
  reference-demo CloudFormation/Guard, or explicitly names legacy v2.3,
  simulator SIM cases, or aws_reference_demo_iam_control_plane. Do not use for
  privacy gateway, RAG, evaluation, FastAPI, Docker, legal, or tax-advice work
  that is not an AWS reference-demo task.
---

# AWS reference-demo context

Instruction-only context router for the current AWS reference-demo target and
explicitly requested legacy IAM evidence. Portable Agent Skills `SKILL.md` for
Codex and Cursor.

This skill lists paths, load stages, and task-based selection rules only.
Do not copy summaries of existing policies, SIM tables, or runbook steps.

## Bounds

Context routing only.
Does not authorize AWS writes.
Does not grant an AWS live-test Go.
Does not turn a legacy runbook into an executable current path.
Does not override AGENTS.md, roadmap, ADRs, implementation or tests.

`AGENTS.md` remains the general context router. This skill only adds the
AWS reference-demo load order.

## When to use

Apply when the user or files concern any of:

- current AWS reference demo / reference-cloud demo
- simplified portfolio deployment evidence
- pre-live review or AWS live-test readiness (routing only; no Go)
- `infra/cloudformation/reference-demo.yaml` or
  `infra/cloudformation/guards/reference-demo.guard`
- `infra/cloudformation/reference-demo-static-roles.yaml` or
  `infra/cloudformation/guards/reference-demo-static-roles.guard`
- explicitly named legacy or historical IAM lifecycle v2.3 work
- explicitly named IAM Policy Simulator evidence or a `SIM-*` case
- explicitly named `tools/aws_reference_demo_iam_control_plane.py`

Do not infer a legacy IAM task merely because a current AWS deployment needs
an execution role, infrastructure role, deployer boundary, or IAM discussion.

## When not to use

Do not apply for work that is only about:

- privacy gateway
- RAG, retrieval, grounding, or evaluation suites
- FastAPI or Docker smoke outside the AWS reference demo
- legal, tax advice, or Human Review of tax drafts

If an AWS reference-demo task later needs one of those areas, follow
`AGENTS.md` for that need. Do not load those sources from this skill.

## Load order

Read in this order. Stop when the task is covered. Do not read later stages
"just in case".

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

### 2. Current target by default

For normal new AWS reference-demo work, load:

- `docs/03-architecture/aws-reference-cloud-deployment.md`

Then select only the current implementation or operational files required by
the task. Do not automatically load the v2.3 IAM README, IAM JSON artifacts,
simulator protocol, control-plane tool, or the body of a runbook marked
Legacy/Superseded.

### 3. Task-dependent

Load only the rows that match the current task.

| When the task is about | Load |
| --- | --- |
| Current AWS architecture, deployment scope, roles, secrets, costs, cleanup, or evidence target | Current architecture. Add `docs/02-security/security-baseline-policy.md` when the task needs security-policy detail |
| Current CloudFormation template, Guard, stack shape, or template freeze | `infra/cloudformation/reference-demo.yaml`; `infra/cloudformation/guards/reference-demo.guard`; `tests/test_reference_cloudformation_template.py`; `tests/test_reference_demo_runbook.py` when runbook/template coupling is relevant. For the two static Express roles outside the ephemeral stack, add `infra/cloudformation/reference-demo-static-roles.yaml`; `infra/cloudformation/guards/reference-demo-static-roles.guard`; `tests/test_reference_demo_static_roles.py`. Treat any documented legacy mismatch explicitly; do not route to v2.3 IAM evidence by default |
| Current operations or a new executable runbook | Current architecture and the implemented template/tests. Load `docs/09-operations/aws-reference-demo-runbook.md` only when the task targets that file; if it is marked Legacy/Superseded, its commands are historical context and not a current execution path |
| Broad current pre-live review or live-test readiness | Current architecture, actual implementation, relevant tests, and current operational status. Do not load v2.3 IAM evidence or simulator results unless the task explicitly asks whether that historical path is relevant |
| Explicit legacy, v2.3, historical IAM, bootstrap-role, old operator-policy, or old CloudFormation-service-role task | `infra/iam/reference-demo/v2.3/README.md`; only the named JSON artifacts; relevant IAM tests |
| A named `SIM-*` case or explicit historical simulator finding | v2.3 IAM README as needed; that case's row and, if present, its correction section. Do not load the full protocol or unrelated current architecture unless the finding requires them |
| Explicit legacy control-plane tool, v2.3 apply/teardown, or dry-run | v2.3 IAM README; `tools/aws_reference_demo_iam_control_plane.py`; `tests/test_aws_reference_demo_iam_control_plane.py`. Load the legacy runbook only if the task also targets its historical operation |
| Current IAM, secrets, or security questions | Current architecture; `docs/02-security/security-baseline-policy.md`. Do not auto-load v2.3 README, JSON or simulator evidence |
| MCP, external tools, or research limits | `docs/04-mcp/agent-mcp-boundaries.md` |

## Legacy simulator protocol

Path: `docs/09-operations/aws-reference-demo-iam-simulator-test-protocol.md`

Load this file only for an explicitly requested legacy/v2.3/simulator task.
Do **not** load it in full.

For explicit status and gates, read only:

- `## Zweck und Status`
- `## Zählweise`
- `## Noch ausstehende Gates außerhalb dieses Simulatorprotokolls`

For a named `SIM-*` case, search for that ID and read only the matching table
row plus any `## Befund und Korrektur` section for that ID.

Do not load the full confirmed-case table, execution proofs, uncounted
attempts, or the sources appendix unless the user names that section.

## Do not auto-load

Do not load from this skill:

- `infra/iam/reference-demo/v2.3/README.md`
- JSON files under `infra/iam/reference-demo/v2.3/`
- `docs/09-operations/aws-reference-demo-iam-simulator-test-protocol.md`
- `tools/aws_reference_demo_iam_control_plane.py`
- the command body of a runbook marked Legacy/Superseded
- `docs/05-privacy-gateway/privacy-gateway-contract.md`
- RAG, retrieval, grounding, or evaluation documents
- FastAPI, Docker, or legal documents
- Gateway, Human Review, or tax-risk policies except via `AGENTS.md` when
  the task is actually about those topics

The first five exclusions become eligible only through the explicit legacy or
file-specific routing rows above.

Do not add scripts, bundled references, nested `AGENTS.md`,
`agents/openai.yaml`, or Cursor-only frontmatter (`paths`,
`disable-model-invocation`, `allowed-tools`).
