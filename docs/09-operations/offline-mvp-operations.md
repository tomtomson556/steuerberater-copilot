# Offline MVP Operations Guide

## Operating Mode

The current offline MVP may be operated only as a local, deterministic mock
workflow with synthetic fixtures.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Allowed operation is limited to:

- local/offline execution only
- synthetic fixtures only
- deterministic mock workflow only
- draft-only output
- Human Review as a mandatory project rule
- no automatic continuation for `RiskLevel B`, `RiskLevel C`, or `RiskLevel D`

Production operations are explicitly out of scope at the current stage.

## Operators and Developers May

- run the local verification commands from `README.md`
- inspect synthetic fixtures in `fixtures/offline_mvp/cases.json`
- run the local JSON CLI against synthetic fixtures only
- run tests for the offline MVP
- review draft outputs as internal preparation material
- open small pull requests for documented, reviewed changes

## Operators and Developers Must Not

- use real client data
- connect Agenda, DATEV, ELSTER, banking, email, cloud, or external APIs
- add tax advice
- add tax calculation logic
- treat outputs as final professional decisions
- bypass Human Review
- merge through agents

## Local Verification

Use the README developer verification commands before opening or updating a pull
request:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
python tools/policy_claim_check.py
```

## Local JSON CLI

After installing the project locally, the offline MVP can emit structured JSON
for synthetic fixtures:

```bash
python -m steuerberater_copilot.offline_mvp --case CASE_001
python -m steuerberater_copilot.offline_mvp --all
python -m steuerberater_copilot.offline_mvp --list-cases
```

The CLI is local-only and reads only the repository's synthetic fixture cases.

The stabilized CLI JSON output contract is documented in
[offline-mvp-cli-json-contract.md](../10-testing-quality/offline-mvp-cli-json-contract.md).

An optional local Markdown review handoff can be written in addition to the
unchanged stdout JSON output:

```bash
python -m steuerberater_copilot.offline_mvp --case CASE_001 --review-handoff .tmp/review-handoff.md
```

The review handoff is a local Draft-/Review artifact for human inspection. It
is not a final document, retained record, productive storage artifact, or
productive export package. The option does not change the CLI JSON contract and
does not create a default workspace.

### Draft and question semantics

The CLI JSON object includes a `draft` section. Operators and developers should
interpret it as follows:

- `draft.available == false` means no complete, substantively usable draft is
  exposed. It does not mean the `draft` object is empty.
- `draft.questions` may contain internal, review-bound question drafts derived
  from synthetic missing items, even when `draft.available` remains `false`.
- Visible `draft.questions` are preparation for Kanzlei review only. They are not
  client communication, not tax advice, not a productive handoff, and not
  permission to continue automatically.
- `review_gate.allows_offline_mock_continuation` and `draft.available` remain
  the binding continuation signals. Visible questions do not weaken or bypass
  Human Review.

For example, `CASE_001` may surface review-bound `draft.questions` while
`draft.available` stays `false` and `review_gate.allows_offline_mock_continuation`
stays `false`. The Kanzlei reviews; the Steuerberater decides.
