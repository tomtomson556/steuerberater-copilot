# GitHub Copilot Instructions

These are repository development instructions for GitHub Copilot and coding
assistants only.

They are not runtime instructions for the future steuerberater-copilot
application or any tax advisory AI.

Follow `AGENTS.md` as the central source for repository development agent
behavior.

Project principle:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Required behavior:

- Do not push directly to `main`.
- Do not merge pull requests.
- Prepare only small, reviewable pull requests.
- Do not add productive integrations.
- Do not use real data.
- Do not implement tax advice.
- Do not implement tax calculation logic.
- Do not add external services or APIs.
- Do not add Agenda, DATEV, ELSTER, banking, email, cloud, or API integrations.
- Do not weaken Human Review or existing policies.
- Preserve offline-only and deterministic project boundaries.

Required local checks before a pull request:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```
