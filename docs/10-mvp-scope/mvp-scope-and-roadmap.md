# MVP Scope and Roadmap

## Zweck und Reichweite

Dieses Dokument definiert den verbindlichen MVP-Rahmen fuer den
**Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Der MVP fuehrt keine produktive Integration ein und trifft keine steuerlichen
Entscheidungen. Er beschreibt Vorbereitung, Grenzen, Module und Reviewpflichten
fuer einen spaeteren, kontrollierten Entwicklungsstand.

Dieses Dokument bleibt verbindlich fuer den fachlichen MVP-Scope und die
Sicherheitsgrenzen. Die zeitliche AI-Engineering- und Portfolio-Planung bis Ende
2026 steht in
[ai-engineering-roadmap-2026.md](ai-engineering-roadmap-2026.md).

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## MVP-Ziel

Der MVP soll Kanzlei-Arbeit intern vorbereiten, strukturieren und pruefbar
machen. Er soll Unterlagen, Rueckfragen, Zusammenfassungen und Handoff-Material
als Entwurf bereitstellen, damit berechtigte Kanzlei-Rollen diese Inhalte
fachlich, organisatorisch und datenschutzbezogen pruefen koennen.

Der MVP ist erfolgreich, wenn er einen eng begrenzten Vorbereitungsworkflow mit
synthetischen oder freigegebenen, nicht vertraulichen Inhalten abbildet und
alle steuerlich relevanten Ergebnisse klar als Entwurf kennzeichnet.

## Erlaubte MVP-Funktionen

Im MVP erlaubt sind ausschliesslich vorbereitende und interne Funktionen ohne
produktive Wirkung:

- strukturierte Mandantenaufnahme als Entwurf mit synthetischen oder
  freigegebenen, nicht vertraulichen Beispieldaten
- Dokumenten- und Belegvorbereitung ohne echte Mandanten-, Beleg-, Steuer-,
  Kanzlei- oder Metadaten
- Erzeugung interner Rueckfragenlisten als Entwurf
- interne Kanzlei-Zusammenfassungen mit Quellen-, Zeitraum- und
  Unsicherheitsmarkierung
- Vorbereitung von Handoff-, Export- oder Staging-Informationen ohne
  produktive Uebergabe
- statische Policy-, Privacy- und Claim-Checks fuer Repository-Inhalte
- Nutzung synthetischer Testdaten fuer lokale Validierung
- Anzeige von Review-Status wie `Draft`, `In review`, `Rejected` oder
  `Escalated`, sofern Statuswechsel keine Modellentscheidung sind
- Protokollierung technischer Kontrollstatus ohne Original-PII, Secrets,
  Token-Maps oder vertrauliche Originalinhalte

Alle erlaubten Funktionen muessen durch das Policy- und Privacy-Gateway
gedacht werden. Modellkontexte duerfen nur zulaessige, minimierte und
pseudonymisierte Inhalte enthalten.

## Verbotene MVP-Funktionen

Im MVP verboten bleiben insbesondere:

- individuelle Steuerberatung durch das Modell
- autonome steuerliche Entscheidungen, Freigaben oder Empfehlungen mit
  Verbindlichkeitswirkung
- Erstellung, Freigabe, Uebermittlung, Signatur oder Einreichung steuerlich
  wirksamer Erklaerungen durch das System
- produktive ELSTER-, Agenda-, DATEV-, DMS-, Cloud-, Datenbank-, Storage- oder
  Mandantensystem-Integrationen
- direkte Schreibzugriffe auf Agenda, DATEV, ELSTER, DMS oder
  Mandantensysteme
- Nutzung echter Mandanten-, Steuer-, Beleg-, Kanzlei-, Bank-, Lohn-,
  Vertrags- oder Metadaten in Entwicklung, Tests, Dokumentation oder
  Public-LLM-Kontexten
- Nutzung abgeleiteter vertraulicher Inhalte aus echten Vorgaengen
- Speicherung oder Weitergabe von Secrets, Tokens, Zugangsdaten, Zertifikaten,
  privaten Schluesseln oder produktiven Konfigurationen
- direkter LLM-Zugriff auf Dateisysteme, Datenbanken, Object Storage, Agenda,
  DATEV, ELSTER, Audit-Logs, Token-Maps oder Secrets
- produktive MCP-Server, produktive MCP-Konfigurationen oder MCP-Werkzeuge mit
  Schreibzugriff auf produktive Systeme
- automatische Mandantenkommunikation ohne menschliche Pruefung und Freigabe
- Darstellung von Modelloutputs als abschliessend, fachlich freigegeben oder
  steuerlich wirksam

Diese Verbote gelten auch fuer Demos, Tests, Agentenarbeit, MCP-Ueberlegungen,
RAG-Kontexte, Orchestrierung und UI-Prototypen.

## Geplante MVP-Module

| Modul | MVP-Aufgabe | Grenze |
| --- | --- | --- |
| Kanzlei-Workspace | Interne Sicht auf Entwuerfe, Rueckfragen, Status und Review-Hinweise | keine fachliche Freigabe durch das Modell |
| Mandantenaufnahme-Entwurf | Strukturierte Erfassung synthetischer oder freigegebener Eingaben | keine echten Mandantendaten in Entwicklungs- oder Testkontexten |
| Dokumenten- und Belegvorbereitung | Kategorisierung, Vollstaendigkeits- und Rueckfragenentwuerfe | keine Originalbelege, OCR-Rohtexte oder vertraulichen Originalinhalte im Modellkontext |
| Policy- und Privacy-Gateway | Vor- und Nachpruefung von Modellkontexten und Outputs | keine Umgehung durch UI, Agenten, MCP, Tests oder Orchestrierung |
| Human-Review-Layer | Review-Status, Stop-Faelle und Eskalationshinweise sichtbar machen | keine automatische Freigabe oder steuerliche Entscheidung |
| Risk Classification | Menschlich gefuehrte Triage entlang vorhandener Handlungsklassen | keine finale Klassifikation durch das Modell |
| Handoff-Vorbereitung | Interne Export- oder Staging-Entwuerfe fuer spaetere manuelle Uebernahme | keine produktive ELSTER-, Agenda- oder DATEV-Uebertragung |
| Lokale Validierung | Statische Checks und Tests mit synthetischen Inhalten | keine Netzwerk-, Secret- oder Produktivsystem-Abhaengigkeit |

## Roadmap in Phasen

### Phase 0: Dokumentations- und Policy-Fundament

- Projektgrenzen, Rechtsgrenzen, Security Baseline, Privacy Gateway, Human
  Review und Risk Classification dokumentieren
- verbotene Claims und Autonomieaussagen statisch pruefen
- MVP-Scope als verbindliche Umsetzungsgrenze festlegen

### Phase 1: Lokaler Entwurfsworkflow

- lokale UI- oder API-Prototypen mit synthetischen Daten vorbereiten
- Rueckfragenlisten, Zusammenfassungen und Statuswerte als Entwurf abbilden
- Gateway- und Reviewpflichten in Workflow-Texten und Statusmodellen sichtbar
  machen

### Phase 2: Kontrollierte Vorbereitungsmodule

- Dokumenten- und Belegvorbereitung mit synthetischen oder ausdruecklich
  freigegebenen, nicht vertraulichen Inhalten testen
- Quellen-, Zeitraum-, Unsicherheits- und Stop-Hinweise strukturieren
- menschliche Triage und Eskalationspfade dokumentiert fuehren

### Phase 3: Handoff- und Exportentwuerfe

- Handoff-Material fuer manuelle Kanzlei-Uebernahme vorbereiten
- Export- oder Staging-Strukturen ohne produktive Verbindung beschreiben
- Review vor jeder Uebernahme erzwingen und als Kontrollpunkt sichtbar machen

### Phase 4: Vor produktionsnaher Nutzung

- separate Architektur-, Datenschutz-, Sicherheits-, Betriebs- und
  Kanzlei-Freigaben einholen
- technische Integrationen nur nach gesonderter Dokumentation und Review
  betrachten
- produktionsnahe Datenpfade erst nach ausdruecklicher Freigabe und Isolation
  pruefen

Keine Phase hebt die MVP-Verbote automatisch auf.

## Akzeptanzkriterien

Der MVP darf erst als fachlich vorbereiteter Entwicklungsstand betrachtet
werden, wenn mindestens diese Kriterien erfuellt sind:

- alle steuerlich relevanten Outputs sind als Entwurf gekennzeichnet
- Human Review ist vor fachlicher Nutzung, Mandantenkommunikation und
  Handoff-Uebergabe sichtbar verpflichtend
- das Policy- und Privacy-Gateway ist als zwingender Kontrollpunkt vor und nach
  Modellnutzung beschrieben oder technisch abgebildet
- es werden keine echten Mandanten-, Beleg-, Steuer-, Kanzlei-, DATEV-,
  Agenda-, ELSTER- oder Secret-Daten verwendet
- Modellkontexte enthalten keine Original-PII, vertraulichen Originalinhalte,
  Secrets, Token-Maps oder produktiven Systeminformationen
- lokale Tests und statische Checks laufen ohne produktive Systeme,
  produktive Zugangsdaten und externe Pflichtdienste
- keine direkte produktive ELSTER-, Agenda-, DATEV-, DMS- oder
  Mandantensystem-Integration ist eingerichtet
- keine UI, kein API-Endpunkt, kein Agent und kein MCP-Werkzeug suggeriert eine
  autonome steuerliche Entscheidung oder Freigabe
- Stop- und Eskalationsfaelle aus Human Review, Privacy Gateway und Risk
  Classification sind konsistent referenziert
- verbotene Claims werden durch lokale Checks erkannt oder im Review
  blockiert

## Human-Review-Grenzen

Human Review ist nicht optional. Es ist die Pflichtkontrolle zwischen
KI-gestuetzter Vorbereitung und jeder fachlichen Nutzung.

Das Modell darf steuerlich relevante Arbeit nicht:

- freigeben
- finalisieren
- einreichen
- uebermitteln
- unterschreiben
- versenden
- als fachlich abschliessend bewerten
- in produktive Systeme schreiben
- gegenueber Mandanten oder Behoerden verbindlich kommunizieren

Statuswechsel mit fachlicher Bedeutung muessen durch berechtigte Kanzlei-Rollen
erfolgen. Der verantwortliche Steuerberater beziehungsweise die Kanzlei traegt
die fachliche Verantwortung fuer steuerlich relevante Entscheidungen,
Freigaben und externe Verwendung.

## Klare MVP-Ausschluesse

Der MVP leistet keine Steuerberatung durch das Modell. Er trifft keine
autonomen steuerlichen Entscheidungen. Er fuehrt keine steuerlich wirksamen
Handlungen aus.

Der MVP enthaelt keine produktive ELSTER-Integration, keine produktive
Agenda-Integration und keine produktive DATEV-Integration. Agenda, DATEV,
ELSTER, DMS und Mandantensysteme bleiben im MVP auf Handoff-, Export-,
Staging- oder manuelle Uebernahmeentwuerfe ohne produktive Schreib- oder
Uebermittlungswirkung beschraenkt.

## Nicht-Zusicherungen

Dieses Dokument enthaelt keine Zusage zu rechtlicher Sicherheit,
Datenschutz-Compliance, GoBD-Compliance, AI-Act-Compliance, produktiver
Betriebsfreigabe oder fachlicher Freigabe einzelner KI-Ausgaben.

Es sagt nicht aus, dass produktionsnahe Nutzung bereits freigegeben ist.
Solche Bewertungen benoetigen separate fachliche, technische, rechtliche,
datenschutzbezogene, sicherheitsbezogene und organisatorische Pruefung.

## Verhaeltnis zu anderen Dokumenten

| Dokument | Bezug |
| --- | --- |
| [README.md](../../README.md) | Projektleitbild, Grundabgrenzung und MVP-Stack |
| [project-brief.md](../00-project/project-brief.md) | Zielbild, Nicht-Ziele und Kontrollschichten |
| [legal-boundaries.md](../01-legal-compliance/legal-boundaries.md) | rechtliche Systemgrenzen und Entwurfscharakter |
| [security-baseline-policy.md](../02-security/security-baseline-policy.md) | Sicherheits-, Testdaten- und Produktivsystemgrenzen |
| [agent-mcp-boundaries.md](../04-mcp/agent-mcp-boundaries.md) | MCP-Grenzen fuer Agentenarbeit |
| [privacy-gateway-contract.md](../05-privacy-gateway/privacy-gateway-contract.md) | Gateway-Pruefungen, Datenklassen und Eskalationsfaelle |
| [human-review-policy.md](../06-human-review/human-review-policy.md) | Review-Level, Status und Stop-Faelle |
| [risk-classification-policy.md](../07-risk-classification/risk-classification-policy.md) | menschliche Triage und interne Handlungsklassen |
