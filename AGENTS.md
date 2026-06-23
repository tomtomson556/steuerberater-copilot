# Agenten-Guardrails

## Projekt

Dieses Repository gehört zum **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Verbindliches Leitbild:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Agenten unterstützen die Arbeit am Repository. Sie treffen keine steuerlichen Entscheidungen, geben keine individuelle Steuerberatung und führen keine steuerlich wirksamen Handlungen aus. Steuerlich relevante Ergebnisse bleiben Entwürfe und benötigen Human Review.

Kontrollpunkte liegen vor und neben dem Modell — insbesondere im **Policy- und Privacy-Gateway** — nicht im Modell selbst.

## Weitere Agenten-Dateien

| Datei | Zweck |
| --- | --- |
| `.github/copilot-instructions.md` | Kurzfassung für GitHub Copilot / VS Code |
| `.cursor/rules/steuerberater-copilot.mdc` | Cursor-Projektregel |
| `docs/04-mcp/agent-mcp-boundaries.md` | MCP-Grenzen für Agentenarbeit |

Diese Datei ist die zentrale Agenten-Anweisung für Codex und andere Agenten, soweit vom jeweiligen Werkzeug unterstützt.

## Pflichtworkflow zu Beginn eines Tasks

Zu Beginn jedes Tasks müssen Agenten den aktuellen Zustand prüfen:

```bash
pwd
git branch --show-current
git status --short
git checkout main
git pull --ff-only origin main
git log --oneline --max-count=5
```

Danach muss ein eigener, kleiner Arbeitsbranch verwendet werden. Relevante vorhandene Dateien müssen gelesen werden, bevor neue Inhalte erzeugt oder bestehende Inhalte geändert werden. Bereits gemergte PR-Inhalte dürfen nicht erneut erzeugt oder dupliziert werden.

## Pflichtworkflow nach Änderungen

Nach jeder Änderung müssen Agenten den Arbeitsstand prüfen:

```bash
git status --short
git diff --check
git diff --stat
git diff
```

Bei neuen untracked Dateien müssen die betroffenen Dateien zusätzlich direkt gelesen werden, weil `git diff` untracked Inhalte nicht vollständig zeigt.

## Verbotene Inhalte und Aktionen

Agenten dürfen nicht einführen, erzeugen, konfigurieren oder verwenden:

- echte Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten
- abgeleitete vertrauliche Inhalte in Public-LLMs
- Secrets, Tokens, Zugangsdaten, Zertifikate oder private Schlüssel
- produktive Agenda-, ELSTER-, Cloud-, Storage-, Datenbank- oder Mandantensystem-Anbindungen
- direkte Schreibzugriffe auf Agenda, ELSTER oder Mandantensysteme
- produktive MCP-Server oder produktive MCP-Konfigurationen
- autonome steuerliche Entscheidungen
- individuelle Steuerberatung durch ein Modell
- produktive Datenpfade in Entwicklungs- oder Testkontexten

Das LLM erhält keinen direkten Zugriff auf Datenbanken, Dateisysteme, Object Storage, Agenda, ELSTER, Audit-Logs, Token-Maps oder Secrets.

## MCP-Grenzen

MCP darf für Agentenarbeit in diesem Repository zunächst nur dokumentativ oder read-only für öffentliche oder ausdrücklich freigegebene Dokumentationsquellen gedacht werden.

Nicht erlaubt sind produktive MCP-Server, MCPs mit echten oder abgeleiteten vertraulichen Inhalten, MCPs mit Secrets im Repository und Schreibtools auf produktive Systeme. MCP darf das Policy- und Privacy-Gateway nicht umgehen. Details stehen in `docs/04-mcp/agent-mcp-boundaries.md`.

## PR-Regeln

- Kleine Branches verwenden.
- Kleine, reviewbare Pull Requests erstellen.
- Scope vor Änderungen klären und eng halten.
- Keine alten PR-Inhalte duplizieren.
- Keine produktiven Integrationen nebenbei aktivieren.
- Kein Merge ohne Human Review.
- Nach einem Merge `main` aktualisieren und `git status --short` prüfen.
