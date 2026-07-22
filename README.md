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
- "KI-Steuerberater"
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
- [AI-Engineering-Roadmap 2026](docs/10-mvp-scope/ai-engineering-roadmap-2026.md)
- [Portfolio Status July 2026](docs/10-mvp-scope/portfolio-status-2026-07.md)
- [Offline MVP Operations Guide](docs/09-operations/offline-mvp-operations.md)
- [Offline MVP CLI JSON Contract](docs/10-testing-quality/offline-mvp-cli-json-contract.md)
- [Evaluation Guide](docs/10-testing-quality/evaluation-guide.md)
- [GoBD-Oriented Storage Baseline](docs/08-gobd-storage/gobd-storage-baseline.md)
- [Review-to-Final Artifact Boundary](docs/08-gobd-storage/review-to-final-artifact-boundary.md)

Die AI-Engineering-Roadmap 2026 dokumentiert das Portfolio-Ziel bis Ende 2026,
die geplanten Phasen, den Pflichtumfang und bewusste Nicht-Ziele. Sie ist kein
Versprechen produktiver Steuerberatung, produktiver Kanzleinutzung oder
Compliance-Konformitaet.

## License

This project is licensed under the PolyForm Noncommercial License 1.0.0.
Commercial use is not granted under this license. For commercial licensing,
contact the project owner.

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

### FastAPI demo quickstart

Die FastAPI-Demo ist ein synthetischer lokaler HTTP-Systemrand. Sie nutzt
standardmaessig `FakeModelProvider` und gibt keine vollstaendigen Prompts aus:

```bash
uvicorn steuerberater_copilot.api.main:app --reload
```

Beispielaufrufe:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
curl "http://127.0.0.1:8000/v1/demo/draft?case_id=CASE_002"
curl "http://127.0.0.1:8000/v1/demo/rag?case_id=CASE_002"
```

### Docker quickstart

Die Container-Demo bleibt synthetisch und nicht-produktiv:

```bash
docker compose up --build
```

Danach sind dieselben lokalen Demo-Endpunkte auf Port `8000` erreichbar. Stoppe
die lokale Demo mit `Ctrl+C`.

### Evaluation command

Die aggregierte Portfolio-Baseline laeuft lokal und deterministisch:

```bash
python -m steuerberater_copilot.evaluation --portfolio-baseline
steuerberater-copilot-evaluate --portfolio-baseline
```

Details zur Interpretation stehen im
[Evaluation Guide](docs/10-testing-quality/evaluation-guide.md). Der aktuelle
Branch-Status steht in
[Portfolio Status July 2026](docs/10-mvp-scope/portfolio-status-2026-07.md).

Lokale Offline-MVP-JSON-Ausgaben fuer synthetische Fixtures:

```bash
python -m steuerberater_copilot.offline_mvp --case CASE_001
steuerberater-copilot-offline-mvp --case CASE_001
python -m steuerberater_copilot.offline_mvp --all
python -m steuerberater_copilot.offline_mvp --list-cases
python -m steuerberater_copilot.offline_mvp --review-worklist
python -m steuerberater_copilot.offline_mvp --review-worklist --review-min-risk C --review-limit 2
steuerberater-copilot-offline-mvp --review-worklist --review-open-questions-only
python -m steuerberater_copilot.offline_mvp --review-summary
python -m steuerberater_copilot.offline_mvp --review-summary --review-min-risk C
```

Der Console Script Entry Point `steuerberater-copilot-offline-mvp` ruft dieselbe
Offline-MVP-CLI auf wie `python -m steuerberater_copilot.offline_mvp`.
`steuerberater-copilot-offline-mvp --version` gibt eine kurze lokale
CLI-Versionszeile aus und ist kein JSON-Contract.
Optionale Review-Filter schneiden nur die lokale `--review-worklist`-Ausgabe
oder die lokale `--review-summary`-Aggregation zu; sie aendern keine Workflow-,
Gateway-, Risk-, Review-Gate- oder Draft-Logik. Ohne Filter bleibt der
`--review-summary`-JSON-Contract unveraendert.

Der editable install kann Python-Paketmetadaten wie `*.egg-info/` erzeugen. Diese
lokalen Artefakte werden durch `.gitignore` ignoriert.

## Optionaler OpenAI-Live-Smoke-Test

Der sichere Standardbetrieb bleibt vollstaendig offline und verwendet den
`FakeModelProvider`. Ein echter OpenAI-Aufruf erfolgt niemals automatisch und
wird weder durch `pytest` noch durch die bestehende CLI gestartet.

Der konkrete Adapter ist gegen die exakt gepinnte Laufzeitabhaengigkeit
`openai==2.45.0` implementiert und getestet. Er verwendet in der Responses API
`text={"format": {"type": "json_object"}}`. Dieser `json_object`-Modus ist der
aeltere JSON-Modus ohne Schema-Garantie; der bestehende Prompt fordert deshalb
ausdruecklich genau ein gueltiges JSON-Objekt an. Die Kompatibilitaet ist nicht
fuer beliebige OpenAI-Modelle garantiert: Das ueber `OPENAI_MODEL` konfigurierte
Modell muss sowohl die Responses API als auch diesen JSON-Modus unterstuetzen.

Der getrennte Smoke-Test verwendet ausschliesslich ein vorhandenes synthetisches
Fixture und erfordert die bewusste Opt-in-Konfiguration
`RUN_OPENAI_LIVE_SMOKE=1`, `OPENAI_API_KEY` und `OPENAI_MODEL`. Optional koennen
`OPENAI_TIMEOUT_SECONDS` und `OPENAI_MAX_OUTPUT_TOKENS` gesetzt werden; die
Defaults sind 60 Sekunden und 2.000 Output-Tokens. Das Outputbudget von 2.000
Tokens ist eine kontrollierte Adaptergrenze, aber keine Garantie, dass es fuer
jedes Modell ausreicht.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
RUN_OPENAI_LIVE_SMOKE=1 python tools/openai_provider_smoke_test.py
```

Der Live-Aufruf kann API-Kosten verursachen. Die Ausgabe enthaelt nur knappe
Status- und Metadaten sowie Feldanzahlen, aber keine vollstaendigen Prompts,
Modellantworten oder strukturierten Entwuerfe. Echte Mandanten-, Kanzlei- oder
Steuerdaten sind fuer diesen Pfad nicht zulaessig.

Der opt-in Live-Smoke fuer das konkrete Zielmodell wurde noch nicht ausgefuehrt.
Modellkompatibilitaet, reales Response-Verhalten und die Eignung des
Outputbudgets muessen durch diesen spaeteren Live-Smoke bestaetigt werden.

Weitere Richtlinien (Recht, Sicherheit, Architektur, Human Review) folgen in separaten Dokumenten und Pull Requests.
