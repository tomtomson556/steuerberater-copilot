# Steuerberater-Copilot

Alternativbezeichnung: **Steuer-Vorbereitungsassistent**

Nicht-produktives AI-Engineering-Portfolio im Themenfeld steuerlicher
Vorbereitung. Der aktuelle Stand ist ein lokaler, deterministischer
modularer Monolith mit synthetischen Daten. Er ist **kein** fertiges
Kanzleiprodukt und **keine** produktive Steuerberatung.

Das System unterstützt interne Vorbereitung; es ersetzt weder Steuerberater
noch fachliche Prüfung.

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
- Mandantenportal, Kanzlei-Workspace oder fertige Weboberfläche

Alle steuerlich relevanten Ergebnisse sind **Entwürfe** und benötigen
**Human Review**, bevor sie fachlich verwendet oder weitergegeben werden.

## Aktueller Portfolio-Stand

Die folgende Tabelle beschreibt den implementierten Stand auf `main`, nicht
eine spätere Produktarchitektur.

| Bereich | Aktueller Stand |
| --- | --- |
| Form | Modularer Monolith in einem Python-Paket; keine Microservices |
| Daten | Ausschließlich synthetische Fixtures |
| Standardbetrieb | Lokal, offline, deterministisch; Standardtests ohne Netzwerk |
| Modellgrenze | Providerneutraler `ModelProvider`; `FakeModelProvider` als sicherer Default |
| Echter Provider | Ein kontrollierter OpenAI-Responses-Adapter (`openai==2.45.0`); Live-Smoke opt-in und noch nicht verifiziert |
| Schnittstellen | Offline-MVP-CLI, Evaluation-CLI und FastAPI-Demo |
| RAG | Lokale deterministische Baseline mit Token-Overlap-Retriever, Quellen und Evaluation; kein pgvector, keine Managed Vector Database |
| Evaluation | 38 synthetische Fälle in sechs Suites als deterministischer Engineering-Nachweis, keine produktive Modellqualitätsbehauptung |
| Docker | Lokale Demo der FastAPI-App mit `FakeModelProvider` |
| Referenz-Cloud | AWS als einzige Referenz-Cloud, vorgesehene Region `eu-central-1`; Live-Test nicht erfolgt |
| Frontend | Keine Web-UI; Next.js ist nicht die aktuelle Richtung |
| MCP | Nur Recherchehilfe für Entwicklungsagenten, keine Anwendungsschicht |

Die aktuelle Roadmap-Phase ist Phase 5 (Referenz-Cloud und Observability).
Strukturierte Runtime-Logs und CloudWatch-EMF-Events für `POST /ai/draft`
sind im Anwendungscode vorhanden. Phase 5 ist **nicht** abgeschlossen: Es
gibt keinen AWS-Live-Test, keine bestätigte EMF-Extraktion, kein
verwaltetes Dashboard und keine Alarme.

## Systemgrenzen

- Das LLM erhält **keinen direkten Zugriff** auf Datenbanken, Dateisysteme, Object Storage, Agenda, ELSTER, Audit-Logs, Token-Maps oder Secrets.
- **Keine** echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten und **keine** abgeleiteten vertraulichen Inhalte in Public-LLMs.
- **Keine** Secrets oder produktiven Zugangsdaten im Repository.
- **Keine** produktiven Steuer-, Agenda-, ELSTER-, Cloud- oder Mandantendaten in Entwicklungs- oder Testpfaden ohne explizite Freigabe und Isolation.
- Kontrollpunkte liegen vor und neben dem Modell, nicht im Modell selbst.

## Entwicklungsstandard

- Erst prüfen, dann ändern.
- Kleine Branches und kleine, reviewbare Pull Requests.
- Tests und Checks vor jedem Merge.
- `main` stabil halten.
- Nach jedem Merge `git status --short` prüfen.

## Dokumentation

- [Projektbrief](docs/00-project/project-brief.md)
- [Systemübersicht](docs/03-architecture/system-overview.md)
- [Testing Strategy](docs/10-testing-quality/testing-strategy.md)
- [Current State](docs/00-project/current-state.md)
- [Glossar](docs/00-project/glossary.md)
- [Security Baseline Policy](docs/02-security/security-baseline-policy.md)
- [AI-Engineering-Roadmap 2026](docs/10-mvp-scope/ai-engineering-roadmap-2026.md)
- [MVP Scope and Roadmap](docs/10-mvp-scope/mvp-scope-and-roadmap.md)
- [AWS Reference Cloud Deployment](docs/03-architecture/aws-reference-cloud-deployment.md)
- [Offline MVP Operations Guide](docs/09-operations/offline-mvp-operations.md)
- [Offline MVP CLI JSON Contract](docs/10-testing-quality/offline-mvp-cli-json-contract.md)
- [GoBD-Oriented Storage Baseline](docs/08-gobd-storage/gobd-storage-baseline.md)
- [Review-to-Final Artifact Boundary](docs/08-gobd-storage/review-to-final-artifact-boundary.md)

Die AI-Engineering-Roadmap 2026 ist die strategische Quelle der Wahrheit für
das Portfolio-Ziel bis Ende 2026. Sie dokumentiert Phasen, Pflichtumfang und
bewusste Nicht-Ziele. Sie ist kein Versprechen produktiver Steuerberatung,
produktiver Kanzleinutzung oder Compliance-Konformität. ADR-003 und ADR-004
legen den local-first, cloud-neutralen Kern und AWS als einzige
Referenz-Cloud fest.

## License

This project is licensed under the PolyForm Noncommercial License 1.0.0.
Commercial use is not granted under this license. For commercial licensing,
contact the project owner.

## Lokale Entwickler-Validierung

Installiere das Projekt lokal mit den Entwicklungswerkzeugen:

```bash
python -m pip install -e ".[dev]"
```

Führe vor einem Pull Request die lokalen Checks aus:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

Standard-pytest bleibt docker- und netzwerkfrei. `FakeModelProvider` ist der
sichere Default für AI-Workflow, RAG-Demo und Evaluation.

Lokale Offline-MVP-JSON-Ausgaben für synthetische Fixtures:

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

Die Offline-MVP-CLI führt den deterministischen Mock-Workflow ohne
Modellaufruf aus. Der Evaluation-Command führt alle sechs synthetischen
Suites offline mit `FakeModelProvider` aus:

```bash
python -m steuerberater_copilot.evaluation
steuerberater-copilot-evaluate
```

## Lokale Docker-Demo

Die lokale Docker-Laufzeit startet die bestehende FastAPI-Demo mit
`FakeModelProvider` als sicherem Standard. Es gibt keine Secrets im Image und
keinen echten Provider im Default-Pfad.

```bash
docker build -t steuerberater-copilot:local .
docker run --rm -p 8000:8000 steuerberater-copilot:local
```

Beispielaufrufe:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/version
curl -sS -X POST http://127.0.0.1:8000/ai/draft \
  -H "Content-Type: application/json" \
  -d '{"case_id":"CASE_002"}'
```

`POST /ai/draft` akzeptiert nur bekannte synthetische `case_id`-Werte und
ruft den vorhandenen RAG-Workflow auf. Unbekannte IDs werden abgelehnt.

Der Console Script Entry Point `steuerberater-copilot-offline-mvp` ruft dieselbe
Offline-MVP-CLI auf wie `python -m steuerberater_copilot.offline_mvp`.
`steuerberater-copilot-offline-mvp --version` gibt eine kurze lokale
CLI-Versionszeile aus und ist kein JSON-Contract.
Optionale Review-Filter schneiden nur die lokale `--review-worklist`-Ausgabe
oder die lokale `--review-summary`-Aggregation zu; sie ändern keine Workflow-,
Gateway-, Risk-, Review-Gate- oder Draft-Logik. Ohne Filter bleibt der
`--review-summary`-JSON-Contract unverändert.

Der editable install kann Python-Paketmetadaten wie `*.egg-info/` erzeugen. Diese
lokalen Artefakte werden durch `.gitignore` ignoriert.

## Optionaler OpenAI-Live-Smoke-Test

Der sichere Standardbetrieb bleibt vollständig offline und verwendet den
`FakeModelProvider`. Ein echter OpenAI-Aufruf erfolgt niemals automatisch und
wird weder durch `pytest` noch durch die bestehende CLI gestartet.

Der konkrete Adapter ist gegen die exakt gepinnte Laufzeitabhängigkeit
`openai==2.45.0` implementiert und getestet. Er verwendet in der Responses API
`text={"format": {"type": "json_object"}}`. Dieser `json_object`-Modus ist der
ältere JSON-Modus ohne Schema-Garantie; der bestehende Prompt fordert deshalb
ausdrücklich genau ein gültiges JSON-Objekt an. Die Kompatibilität ist nicht
für beliebige OpenAI-Modelle garantiert: Das über `OPENAI_MODEL` konfigurierte
Modell muss sowohl die Responses API als auch diesen JSON-Modus unterstützen.

Der getrennte Smoke-Test verwendet ausschließlich ein vorhandenes synthetisches
Fixture und erfordert die bewusste Opt-in-Konfiguration
`RUN_OPENAI_LIVE_SMOKE=1`, `OPENAI_API_KEY` und `OPENAI_MODEL`. Optional können
`OPENAI_TIMEOUT_SECONDS` und `OPENAI_MAX_OUTPUT_TOKENS` gesetzt werden; die
Defaults sind 60 Sekunden und 2.000 Output-Tokens. Das Outputbudget von 2.000
Tokens ist eine kontrollierte Adaptergrenze, aber keine Garantie, dass es für
jedes Modell ausreicht.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
RUN_OPENAI_LIVE_SMOKE=1 python tools/openai_provider_smoke_test.py
```

Der Live-Aufruf kann API-Kosten verursachen. Die Ausgabe enthält nur knappe
Status- und Metadaten sowie Feldanzahlen, aber keine vollständigen Prompts,
Modellantworten oder strukturierten Entwürfe. Echte Mandanten-, Kanzlei- oder
Steuerdaten sind für diesen Pfad nicht zulässig.

Der opt-in Live-Smoke für das konkrete Zielmodell wurde noch nicht ausgeführt.
Modellkompatibilität, reales Response-Verhalten und die Eignung des
Outputbudgets müssen durch diesen späteren Live-Smoke bestätigt werden.
