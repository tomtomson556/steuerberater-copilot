# Projektbrief

## Projektname

**Steuerberater-Copilot / Steuer-Vorbereitungsassistent**

## Zweck

Der Steuerberater-Copilot ist ein nicht-produktives AI-Engineering-Portfolio
im Themenfeld steuerlicher Vorbereitung. Er zeigt kontrollierte LLM-Nutzung,
strukturierte Entwürfe, semantische Validierung, lokale RAG-Baseline,
deterministische Evaluation, Gateway- und Human-Review-Grenzen sowie eine
kleine FastAPI-/Docker-Demo.

Der fachliche Rahmen bleibt Vorbereitung, nicht Entscheidung. Der aktuelle
Stand ist **kein** fertiges Kanzleiprodukt, **kein** Mandantenportal und
**keine** produktive Steuerberatung.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Entscheidungen, Freigaben und steuerlich wirksame Handlungen verbleiben bei
der Kanzlei. Alle steuerlich relevanten Ergebnisse sind Entwürfe und
benötigen Human Review.

## Aktuell vorhandener Umfang

Implementiert auf dem aktuellen `main` ist ein modularer Monolith mit
synthetischen Daten:

- deterministischer Offline-MVP-Workflow mit CLI und stabilem JSON-Vertrag
- Policy- und Privacy-Gateway, interne Risikoklassifikation und Human Review Gate
- providerneutraler `ModelProvider` und `FakeModelProvider` als sicherer Default
- ein kontrollierter OpenAI-Responses-Adapter; der Live-Smoke ist opt-in und
  operativ noch nicht verifiziert
- versionierte synthetische Promptdefinition, strukturierter JSON-Parser und
  getrennte semantische Validierung
- lokale deterministische RAG-Baseline mit Quellen, Grounding und Abstention
- Offline-Evaluation über 38 synthetische Fälle in sechs Suites
- FastAPI-Demo mit `GET /health`, `GET /version` und `POST /ai/draft`
- lokale Docker-Laufzeit für diese Demo
- AWS als einzige Referenz-Cloud, vorgesehene Region `eu-central-1`

Die Evaluation ist ein deterministischer Engineering-Nachweis gegen
synthetische Fixtures. Sie ist keine produktive Modellqualitätsbehauptung.

Die aktuelle Roadmap-Phase ist Phase 5 (Referenz-Cloud und Observability).
Strukturierte Runtime-Logs und CloudWatch-EMF-Events für `POST /ai/draft`
sind im Anwendungscode vorhanden. Phase 5 ist nicht abgeschlossen: Ein
AWS-Live-Test, eine bestätigte EMF-Extraktion, ein verwaltetes Dashboard und
Alarme fehlen.

## Architekturprinzip

Kontrollpunkte liegen **nicht im Modell**, sondern **vor und neben dem
Modell**. Der Anwendungskern bleibt cloud-neutral. Die
Abhängigkeitsrichtung ist `offline_mvp -> ai`; `ai -> offline_mvp` ist
verboten.

Die Anwendung ist ein modularer Monolith, keine Microservice-Landschaft.
Provider-, HTTP- und Cloud-Komponenten liegen an den Systemrändern.

## Kontrollschichten

1. **Policy- und Privacy-Gateway** - deterministische Prüfungen vor dem
   Modellaufruf sowie Markerprüfung des Modelloutputs
2. **Risikoklassifikation und Human Review Gate** - interne Routing-Marker
   und Pflichtstopp vor automatischer Fortsetzung
3. **Model Invocation Policy** - erlaubte Prompt-ID/Version und
   Größengrenzen vor dem Provider
4. **Modellgrenze** - `FakeModelProvider` als Default; optional genau ein
   OpenAI-Adapter
5. **Strukturierter Output und semantische Validierung** - JSON-Parser und
   getrennte semantische Checks ohne steuerliche Richtigkeitsprüfung
6. **Human Review** - steuerlich relevante Entwürfe bleiben Entwürfe
7. **Systemränder** - CLI, FastAPI/Docker-Demo und geplante AWS-Referenzdemo;
   keine Fachlogik in FastAPI

MCP ist ausschließlich eine Recherchehilfe für Entwicklungsagenten. MCP ist
keine Anwendungskomponente und keine Runtime-Schicht.

Nicht aktuelle Portfolio-Pfade sind insbesondere:

- Mandantenportal oder Kanzlei-Workspace
- Local- oder On-Prem-LLM-Runtime
- PostgreSQL/pgvector oder eine andere Managed Vector Database
- Next.js oder eine vollständige Weboberfläche

Die lokale RAG-Baseline nutzt einen deterministischen Token-Overlap-Retriever
über synthetische `SourceDocument`-Objekte. Nach erfolgreichem Retrieval prüft
das Policy- und Privacy-Gateway den abgerufenen Retrieval-Kontext
deterministisch über Datenklassen- und Identitätsregeln, bevor Prompt Builder
oder Provider aufgerufen werden. Leeres Retrieval bleibt ohne Provider-Aufruf
eine Abstention.

## Nicht-Ziele

- kein autonomer Steuerberater
- keine individuelle Steuerberatung durch das Modell
- keine steuerlich wirksamen Entscheidungen
- keine direkten produktiven Schreibintegrationen in Agenda, ELSTER oder
  Mandantensysteme
- keine Original-PII im Modellkontext
- keine echten vertraulichen Daten in Public-LLMs
- keine Multi-Cloud
- keine frei laufenden Agenten
- kein GoBD-konformer Produktivspeicher im aktuellen Stand

## Rollen (grob)

| Bereich | Verantwortung |
| --- | --- |
| Fachliche Verantwortung | Kanzlei beziehungsweise Steuerberater |
| Technische Architektur | Entwicklungsteam |
| Compliance, Datenschutz, Release-Freigaben | vor produktionsnaher Nutzung prüfen und freigeben |

Dieses Portfolio trifft keine fachliche Entscheidung und ersetzt keine
menschliche Prüfung.

## Hinweis zur Rechtsauslegung

Dieser Projektbrief beschreibt den aktuellen Portfolio-Zweck, die
implementierten Grenzen und die Architekturprinzipien. Detaillierte
rechtliche Auslegungen (z. B. StBerG, AI Act, Datenschutz) werden in
gesonderten Dokumenten geführt. Dieser Brief enthält keine Zusage zu
Konformität oder produktiver Nutzbarkeit.
