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
- Do not add productive integrations or productive external services.
- Do not use real or confidential data, or repository-stored secrets.
- Do not implement individual tax advice, autonomous tax decisions, productive
  tax actions, or tax calculation logic.
- Do not bypass the Gateway or Human Review.
- Do not add productive Agenda, DATEV, ELSTER, banking, email, API, cloud, or
  MCP integrations.
- Do not add unplanned external, provider, API, or cloud integrations.
- Do not add Multi-Cloud support.
- Do not give models direct access to databases, file systems, object storage,
  secrets, or productive systems.
- Keep standard tests deterministic and network-free.
- Do not weaken Human Review or existing policies.
- Preserve the local-first architecture and its safe offline default with
  synthetic data and the `FakeModelProvider`.

External, provider, API, or cloud work is allowed only when the current binding
roadmap explicitly provides for it, applicable accepted ADRs are followed, and
the current branch scope expressly authorizes it. Keep provider and cloud SDKs,
HTTP transport, the planned FastAPI and Docker surfaces, the single reference
cloud, secret integration, Cloud Logging, Cloud Metrics, and Infrastructure as
Code at clear system boundaries. A real-provider live smoke must be explicit
opt-in and use synthetic data only. These exceptions do not permit productive
integrations, network access in standard tests, or Multi-Cloud support.

Required local checks before a pull request:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```
