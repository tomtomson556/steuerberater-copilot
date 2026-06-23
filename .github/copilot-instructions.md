# GitHub Copilot Instructions

Dieses Repository gehört zum **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

**Zentrale Agentenregeln:** `AGENTS.md` — dort stehen Pflichtworkflows, verbotene Aktionen, PR-Regeln und Verweise auf MCP-Grenzen.

Leitbild:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Arbeite compliance-first: erst prüfen, dann ändern. Lies vorhandene Dateien und prüfe den Git-Zustand, bevor du Änderungen vorschlägst oder umsetzt.

Harte Grenzen (Auszug — vollständig in `AGENTS.md`):

- keine echten Daten, Secrets oder produktiven Integrationen
- keine produktiven MCP-Server; MCP-Grenzen siehe `docs/04-mcp/agent-mcp-boundaries.md`
- keine autonomen steuerlichen Entscheidungen oder individuelle Steuerberatung durch KI
- steuerlich relevante Ergebnisse bleiben Entwürfe und benötigen Human Review
- keine alten PR-Inhalte duplizieren; kleine, reviewbare Pull Requests
