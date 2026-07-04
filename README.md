# Steuerberater-Copilot

Alternativbezeichnung: **Steuer-Vorbereitungsassistent**

KI-gestütztes Vorbereitungssystem für deutsche Steuerkanzleien. Das System unterstützt interne Kanzlei-Prozesse; es ersetzt weder Steuerberater noch fachliche Prüfung.

## Leitprinzip

```
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Abgrenzung

Dieses Projekt ist ausdrücklich **kein**:

- autonomer Steuerberater
- „KI-Steuerberater“
- System für individuelle Steuerberatung durch das Modell
- Werkzeug für steuerlich wirksame Handlungen ohne Kanzlei-Freigabe

Alle steuerlich relevanten Ergebnisse sind **Entwürfe** und benötigen **Human Review** durch die Kanzlei, bevor sie fachlich verwendet oder weitergegeben werden.

## Systemgrenzen

- Das LLM erhält **keinen direkten Zugriff** auf Datenbanken, Dateisysteme, Object Storage, Agenda, ELSTER, Audit-Logs, Token-Maps oder Secrets.
- **Keine** echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten und **keine** abgeleiteten vertraulichen Inhalte in Public-LLMs.
- **Keine** Secrets oder produktiven Zugangsdaten im Repository.
- **Keine** produktiven Steuer-, Agenda-, ELSTER-, Cloud- oder Mandantendaten in Entwicklungs- oder Testpfaden ohne explizite Freigabe und Isolation.

Kontrollpunkte liegen vor und neben dem Modell, nicht im Modell selbst.

## Entwicklungsstandard

- Erst prüfen, dann ändern.
- Kleine Branches und kleine, reviewbare Pull Requests.
- Tests und Checks vor jedem Merge.
- `main` stabil halten.
- Nach jedem Merge `git status --short` prüfen.

## MVP-Stack (Leitplanke, nicht finale Architektur)

Die folgenden Angaben sind frühe Leitplanken für das MVP. Finale Entscheidungen werden später per ADR dokumentiert.

| Bereich | Voraussichtliche Richtung |
| --- | --- |
| Backend | Python, FastAPI, Pydantic |
| Frontend | TypeScript, Next.js |
| Vektorstore | PostgreSQL mit pgvector (Standard im MVP) |
| Skalierung Vektoren | Qdrant nur bei begründetem Skalierungsbedarf |
| Agenda | nur über Handoff, Export oder Staging |
| ELSTER | keine direkte Integration im MVP |

## Dokumentation

- [Projektbrief](docs/00-project/project-brief.md)
- [Glossar](docs/00-project/glossary.md)
- [Security Baseline Policy](docs/02-security/security-baseline-policy.md)
- [MVP Scope and Roadmap](docs/10-mvp-scope/mvp-scope-and-roadmap.md)
- [Offline MVP Operations Guide](docs/09-operations/offline-mvp-operations.md)
- [Offline MVP CLI JSON Contract](docs/10-testing-quality/offline-mvp-cli-json-contract.md)
- [GoBD-Oriented Storage Baseline](docs/08-gobd-storage/gobd-storage-baseline.md)
- [Review-to-Final Artifact Boundary](docs/08-gobd-storage/review-to-final-artifact-boundary.md)

## Lokale Entwickler-Validierung

Installiere das Projekt lokal mit den Entwicklungswerkzeugen:

```bash
python -m pip install -e ".[dev]"
```

Fuehre vor einem Pull Request die lokalen Checks aus:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

Lokale Offline-MVP-JSON-Ausgaben fuer synthetische Fixtures:

```bash
python -m steuerberater_copilot.offline_mvp --case CASE_001
python -m steuerberater_copilot.offline_mvp --all
python -m steuerberater_copilot.offline_mvp --list-cases
python -m steuerberater_copilot.offline_mvp --review-worklist
python -m steuerberater_copilot.offline_mvp --review-summary
```

Der editable install kann Python-Paketmetadaten wie `*.egg-info/` erzeugen. Diese
lokalen Artefakte werden durch `.gitignore` ignoriert.

Weitere Richtlinien (Recht, Sicherheit, Architektur, Human Review) folgen in separaten Dokumenten und Pull Requests.
