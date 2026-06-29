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
