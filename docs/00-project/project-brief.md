# Projektbrief

## Projektname

**Steuerberater-Copilot / Steuer-Vorbereitungsassistent**

## Zielbild

KI-gestütztes Vorbereitungssystem für deutsche Steuerkanzleien. Das System strukturiert, dokumentiert und bereitet fachliche Arbeit vor. Entscheidungen, Freigaben und steuerlich wirksame Handlungen verbleiben bei der Kanzlei.

## Unterstützte Tätigkeiten

- Mandantenaufnahme
- Unterlagenprüfung
- Belegvorbereitung
- Rückfragenlisten
- Kanzlei-Zusammenfassungen
- Quellenrecherche mit Rechtsstand und Zeitraum
- GoBD-orientierte Ablagekonzepte
- Agenda-Handoff über Export, Staging oder manuelle Übergabe

Alle genannten Tätigkeiten liefern Vorbereitungs- und Entwurfsmaterial; sie ersetzen keine fachliche Prüfung.

## Nutzergruppen

- Steuerberater
- Kanzlei-Mitarbeiter
- fachliche Reviewer
- Kanzlei-Administratoren
- Mandanten im Mandantenportal, soweit von der Kanzlei freigegeben

## Nicht-Ziele

- kein autonomer Steuerberater
- keine individuelle Steuerberatung durch das Modell
- keine steuerlich wirksamen Entscheidungen
- keine direkte produktive Schreibintegration in Agenda, ELSTER oder Mandantensysteme
- keine Original-PII im Modellkontext
- keine echten vertraulichen Daten in Public-LLMs

## Architekturprinzip

Kontrollpunkte liegen **nicht im Modell**, sondern **vor und neben dem Modell**. Eingaben, Ausgaben und Übergaben werden über definierte Schichten geführt und geprüft.

## Kontrollschichten

1. **Mandantenportal und Kanzlei-Workspace** — getrennte Arbeitsbereiche, rollenbasierte Sichtbarkeit
2. **Policy- und Privacy-Gateway** — Filterung, Pseudonymisierung, Freigabe vor Modellaufruf
3. **Orchestrierung** — Ablaufsteuerung, keine direkten Modell-Zugriffe auf produktive Systeme
4. **Local- oder isolierte EU-/On-Prem-LLM-Runtime** — Modellausführung in kontrollierter Umgebung
5. **MCP-Services** — strukturierte, begrenzte Werkzeugzugriffe statt offener Systemrechte
6. **Human-Review-Layer** — Pflichtprüfung steuerlich relevanter Entwürfe vor Weiterverwendung
7. **Audit-, Release- und Compliance-Governance** — Nachvollziehbarkeit, Freigaben, Betriebsgrenzen

## MVP-Leitplanken

- pgvector als Standard-Vektorstore
- Qdrant nur bei begründetem Skalierungsbedarf
- Agenda nur über Handoff, Export oder Staging
- keine direkte ELSTER-Integration
- keine produktiven Datenpfade
- keine Original-PII im Modellkontext
- kein produktiver Betrieb ohne Release-Gates

## Rollen (grob)

| Bereich | Verantwortung |
| --- | --- |
| Fachliche Verantwortung | Kanzlei beziehungsweise Steuerberater |
| Technische Architektur | Entwicklungsteam |
| Compliance, Datenschutz, Release-Freigaben | vor produktionsnaher Nutzung prüfen und freigeben |

## Hinweis zur Rechtsauslegung

Dieser Projektbrief beschreibt Zielbild, Grenzen und Architekturprinzipien. Detaillierte rechtliche Auslegungen (z. B. StBerG, AI Act, Datenschutz) werden in späteren Pull Requests und Dokumenten ergänzt.
