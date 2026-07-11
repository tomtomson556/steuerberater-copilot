# AI-Engineering-Roadmap 2026

## Status

- Status: Active
- Ausgangsstand: `main` auf `4fc8e2e`
- Startdatum der Roadmap: 9. Juli 2026
- Portfolio-Zieltermin: 31. Dezember 2026
- Interner Release-Termin: spaetestens 20. Dezember 2026
- Aktuelle Phase: Evaluation und echter Provider

## Zweck

Diese Roadmap ist die strategische Quelle der Wahrheit fuer die
AI-Engineering-Weiterentwicklung des `steuerberater-copilot` bis Ende 2026.
Der `steuerberater-copilot` soll spaetestens bis zum 31. Dezember 2026 als
funktionierendes und vorzeigbares AI-Engineering-Portfolio einsetzbar sein und
bei der Suche nach einer guten neuen Anstellung unterstuetzen.

Der interne Zieltermin fuer den Portfolio-Release ist der 20. Dezember 2026. Der
Zeitraum vom 21. bis 31. Dezember 2026 ist ausschliesslich Release- und
Fehlerpuffer.

Das Projekt soll bis Ende 2026 praktische Kompetenz in diesen Bereichen
nachweisen:

- kontrollierte LLM-Integration
- strukturierte Modelloutputs
- semantische Validierung
- Prompt-Versionierung
- systematische Evaluation
- RAG mit nachvollziehbaren Quellen
- Abstention bei unzureichender Evidenz
- Gateway- und Human-Review-Grenzen
- FastAPI
- Docker
- minimale Cloud-Bereitstellung
- strukturierte Logs
- grundlegende Betriebs- und Qualitaetsmetriken
- reproduzierbare Demo

Portfolio und praktische Nachweise haben Vorrang vor Zertifikaten,
Infrastrukturbreite und produktionsnaher Betriebsarchitektur.

## Vorhandener Ist-Zustand

Der aktuelle Stand ist ein lokaler Offline-MVP mit synthetischen Daten. Der
Stand enthaelt eine CLI, deterministische Fixtures, Gateway-Logik,
Risikoklassifikation, Human Review Gate, kontrollierte Model Invocation, einen
providerneutralen `ModelProvider`, einen deterministischen `FakeModelProvider`,
synthetischen Prompt-Aufbau mit versionierter Promptdefinition sowie Prompt-ID
und Prompt-Version im `ModelRequest`, `StructuredDraftOutput`, einen strengen
strukturellen JSON-Parser und eine getrennte semantische Validierung. Die
semantische Validierung ist in den kontrollierten AI-Workflow integriert. Ein
`EvaluationCase`-Vertrag und ein deterministischer Einzel-Fall-Offline-
Evaluation-Runner sowie ein getrennter deterministischer Einzel-Fall-
Erwartungsvergleich sind ebenfalls vorhanden.

Der vorhandene Kontrollfluss ist:

```text
IntakeCase
-> Gateway
-> Risikoklassifikation
-> Human Review Gate
-> Prompt Builder
-> Model Invocation Boundary
-> Structured Output Parser
-> Structured Draft Semantic Validator
```

Die vorhandene Architekturgrenze bleibt:

```text
offline_mvp -> ai
```

Verboten bleibt:

```text
ai -> offline_mvp
```

Noch nicht vorhanden sind insbesondere Evaluationsfallbibliothek, messbare
Evaluationsmetriken, Evaluationsreport, echter Modellprovider, RAG, FastAPI,
Docker, Persistenz, Authentifizierung, Cloud-Deployment, Infrastructure as Code
und Monitoring. Die Offline-Evaluation ist damit noch nicht abgeschlossen.
Eine Prompt Registry ist bewusst aufgeschoben und aktuell nicht benoetigt.

## Pflichtumfang bis Ende 2026

Der verbindlich geplante Pflichtumfang bis zum Portfolio-Release umfasst:

1. getrennte semantische Validierung strukturierter Modelloutputs
2. versionierte Promptdefinitionen
3. Offline-Evaluationsfaelle und messbare Metriken
4. genau einen echten Modellprovider
5. Timeout-, Groessen- und Fehlergrenzen
6. RAG ueber einen kontrollierten Dokumentbestand
7. sichtbare Quellenreferenzen
8. getestetes Abstention-Verhalten
9. kleine FastAPI-Demo
10. Docker-Laufzeit
11. genau eine Referenz-Cloud
12. minimale Infrastructure as Code
13. strukturierte Logs
14. grundlegende Laufzeit- und Qualitaetsmetriken
15. README, Architekturdiagramm, Evaluationsuebersicht und Demo-Video

Dieser Pflichtumfang ist keine Aussage, dass die genannten Funktionen bereits
implementiert sind. Er beschreibt die verbindliche Zielrichtung bis Ende 2026.

## Stretch Goals

Stretch Goals werden nur bearbeitet, wenn der Pflichtumfang spaetestens am
30. November 2026 stabil ist:

- einfacher persistenter Reviewstatus
- ein ungefaehrliches synthetisches Tool mit Human Approval
- kleine Authentifizierungsdemo
- erweitertes Cloud-Monitoring
- kleines zweites AI-Mini-Projekt

### Einfacher persistenter Reviewstatus

Ein einfacher persistenter Reviewstatus darf als In-Memory Repository oder
optional mit SQLite umgesetzt werden. Managed PostgreSQL und ein produktives
Auditarchiv sind dafuer nicht erforderlich.

### Kontrolliertes synthetisches Tool Calling

Ein optionales Tool-Calling-Beispiel darf nur ein ungefaehrliches synthetisches
Tool enthalten. Der erlaubte Kontrollfluss ist:

```text
Modell schlaegt Tool Call vor
-> Allowlist-Pruefung
-> Human Approval
-> Ausfuehrung
-> technisches Event
```

Produktive DATEV-, ELSTER- oder Agenda-Integrationen bleiben ausgeschlossen.

### Kleines zweites AI-Projekt

Ein kleines zweites AI-Projekt ist nur bei ausreichender Zeitreserve sinnvoll.
Ein moegliches Beispiel ist eine kleine IT-Runbook-RAG-Demo. Es darf kein
zweites Grossprojekt entstehen.

## Nicht-Ziele bis Ende 2026

Bis Ende 2026 sind ausdruecklich keine Ziele:

- keine echten Mandanten- oder Kanzleidaten
- kein produktiver Steuerberatungseinsatz
- keine GoBD-Konformitaetsbehauptung
- keine DATEV-, ELSTER- oder Agenda-Integration
- kein vollstaendiges Rollen- und Berechtigungssystem
- kein produktionsreifes Audit-Archiv
- keine Multi-Cloud-Unterstuetzung
- kein Hybridbetrieb
- kein Kubernetes
- keine Microservices
- keine mehreren echten Modellprovider
- keine frei laufenden Agenten
- keine komplexe asynchrone Job-Infrastruktur
- kein Fine-Tuning
- keine vollstaendige Weboberflaeche

Keine Phase dieser Roadmap hebt die bestehenden fachlichen, rechtlichen,
datenschutzbezogenen, sicherheitsbezogenen oder Human-Review-Grenzen auf.

## Architekturstrategie

### Cloud-neutraler Kern

Der Anwendungskern bleibt unabhaengig von AWS, Azure und Cloud-SDKs. Im Kern
sind verboten:

- AWS-SDKs
- Azure-SDKs
- FastAPI-Typen
- SQLAlchemy
- Cloud Secret Stores
- Cloud Logging APIs
- Deployment-Konfiguration

Plattformspezifische Komponenten sind nur an den Systemraendern zulaessig:

- echter `ModelProvider`
- HTTP-Transport
- Secrets
- Deployment
- Cloud Logging
- Cloud Metrics
- Infrastructure as Code

### Bestehende Abhaengigkeitsrichtung

Die bestehende Abhaengigkeitsrichtung bleibt verbindlich:

```text
offline_mvp -> ai
```

Die Gegenrichtung bleibt verboten:

```text
ai -> offline_mvp
```

### Abstraktionsregel

Ein neues Interface oder Protocol wird nur eingefuehrt, wenn mindestens eine
reale Anforderung vorliegt:

1. Es gibt zwei sinnvolle Implementierungen.
2. Eine externe Systemgrenze muss isoliert werden.
3. Tests benoetigen einen Ersatzadapter.
4. Eine konkrete Infrastrukturabhaengigkeit wuerde sonst in den Anwendungskern
   gelangen.

Vorsorgliche Ports fuer hypothetische spaetere Anforderungen werden nicht
eingefuehrt.

### FakeModelProvider

Der `FakeModelProvider` bleibt vorerst an seinem bestehenden Ort.

- Es gibt keinen eigenstaendigen Architekturhygiene-Branch nur zur
  Verschiebung.
- Die Paketposition wird beim ersten echten Provideradapter erneut geprueft.
- Eine Verschiebung erfolgt nur, wenn sie dann eine tatsaechlich genutzte
  Port-/Adapter-Grenze klarer macht.
- Eine solche Verschiebung darf nicht mit fachfremden Aenderungen vermischt
  werden.

## Betriebsstrategie

### Lokaler Standard

Der sichere Standardbetrieb bleibt:

```text
lokal
synthetische Daten
deterministische Tests
FakeModelProvider
kein Netzwerk in Standardtests
keine Secrets
```

### Lokale Demo

Der spaetere lokale Demo-Stack soll diese Eigenschaften haben:

- FastAPI
- Docker
- `FakeModelProvider` als sicherer Standard
- optional bewusst aktivierter echter Provider
- kontrollierter lokaler Dokumentbestand
- keine produktiven Daten

### Referenz-Cloud

Es wird genau eine Referenz-Cloud umgesetzt. Multi-Cloud ist kein Ziel.

Die aktuelle Praeferenz ist Azure. Azure ist jedoch noch keine endgueltige
Architekturentscheidung. AWS und Azure werden spaetestens bis zum
31. August 2026 verbindlich verglichen. Die konkrete Auswahl wird in einem
spaeteren eigenen ADR dokumentiert:

```text
docs/15-decisions/adr/adr-004-select-reference-cloud.md
```

Entscheidungskriterien sind:

- Zielstellen und Arbeitsmarkt
- verfuegbarer Account und Dienstzugang
- Kosten
- EU-Region
- Modellzugang
- Containerbetrieb
- Secret Management
- Monitoring
- IaC-Aufwand
- zuverlaessige Abschaltmoeglichkeit

Defaultregel: Falls keine deutliche AWS-Dominanz im relevanten Stellenmarkt
besteht und Azure technisch sowie wirtschaftlich zugaenglich ist, wird Azure
als Referenzplattform gewaehlt.

Die Wahl des Modellproviders und die Wahl der Laufzeit-Cloud sind getrennte
Entscheidungen.

## Zeitlich verbindliche Roadmap

Die genannten Branches sind Planungsvorschlaege und keine Behauptung ueber
bereits vorhandene Arbeit.

### Phase 0 - Roadmap verbindlich machen

Zeitraum: 9. bis 13. Juli 2026

Branch:

```text
docs/add-ai-engineering-roadmap-2026
```

Exit-Kriterium: Roadmap und ADR sind auf `main` gemerged und im README
auffindbar.

### Phase 1 - Semantische Qualitaet und Prompt-Reproduzierbarkeit

Zeitraum: 14. Juli bis 9. August 2026

Status: Abgeschlossen am 10. Juli 2026.

Geplante Branches:

```text
feat/add-structured-draft-semantic-validator
feat/integrate-semantic-validation-into-ai-workflow
feat/add-versioned-prompt-definition
feat/add-prompt-metadata-to-model-request
```

Verbindliche Entscheidungen:

- Der JSON-Parser bleibt fuer strukturelle Pruefung zustaendig.
- Semantische Validierung erfolgt in einer getrennten Komponente.
- Parser- und Validierungsfehler bleiben unterscheidbar.
- `ModelRequest` traegt die verwendete Prompt-ID und Prompt-Version.
- Eine Prompt Registry wird erst eingefuehrt, wenn mehrere Promptversionen
  aufgeloest werden muessen oder ein realer Auswahl-Consumer existiert.

Moegliche semantische Pruefungen:

- keine leeren oder whitespace-only Eintraege
- maximale Eintragsanzahl
- maximale Eintragslaenge
- keine exakten Duplikate
- keine unzulaessigen Freigabe- oder Finalitaetsclaims
- Unsicherheit benoetigt passende Review-Frage
- keine Behauptung automatischer fachlicher Pruefung

Es erfolgt keine steuerliche Richtigkeitspruefung.

### Phase 2 - Evaluation und echter Provider

Zeitraum: 10. August bis 6. September 2026

Status: In Arbeit seit 10. Juli 2026.

Geplante Branches:

```text
feat/add-evaluation-case-contract
feat/add-offline-evaluation-runner
feat/add-evaluation-case-assessment
feat/add-synthetic-evaluation-case-library
feat/add-evaluation-metrics-report
feat/add-model-invocation-policy
feat/add-real-model-provider
```

Erste Evaluationsmetriken:

- korrekte Gateway-Entscheidung
- korrekte Review-Gate-Entscheidung
- unerlaubte Provideraufrufe
- Parse-Erfolg
- semantische Validierung
- Erhalt von Unsicherheiten
- Erhalt notwendiger Review-Fragen
- verbotene Finalitaetsclaims
- Laufzeit
- Fehlerklasse

Anforderungen an den echten Provider:

- genau ein Provider
- bestehenden `ModelProvider`-Vertrag implementieren
- Provider-SDK nur im Adapter
- Standardtests ohne Netzwerk
- SDK in Tests mocken
- Live-Smoke-Test nur opt-in
- Secrets ausschliesslich ausserhalb des Repositorys
- nur synthetische Daten

Die Cloudentscheidung erfolgt spaetestens am 31. August 2026.

### Phase 3 - RAG mit nachvollziehbaren Quellen

Zeitraum: 7. September bis 11. Oktober 2026

Geplante Branches:

```text
feat/add-source-document-contract
feat/add-local-document-retriever
feat/add-grounded-draft-contract
feat/add-rag-workflow
feat/add-retrieval-evaluation
```

Bewusste Vereinfachungen:

- zunaechst kein pgvector
- keine Managed Vector Database
- keine OCR-Pipeline
- kein Object Storage
- keine komplexe Ingestion-Plattform

Zuerst wird eine deterministische lokale Retrieval-Baseline umgesetzt.

Pflichtmetriken:

- Recall@k
- richtige Quelle
- richtige Fundstelle
- Citation Coverage
- unbelegte Aussagen
- Abstention bei fehlender Quelle
- Widerspruchserkennung
- veraltete Dokumentversion

Exit-Kriterium: Mindestens 30 hochwertige synthetische Evaluationsfaelle.

### Phase 4 - API und Docker-Demo

Zeitraum: 12. Oktober bis 8. November 2026

Geplante Branches:

```text
feat/add-fastapi-application
feat/add-ai-draft-endpoint
feat/add-evaluation-command
feat/add-docker-runtime
```

API-Basis:

- App Factory
- `/health`
- `/version`
- keine Fachlogik in FastAPI
- keine Authentifizierung als Pflicht

AI-Draft-Endpunkt:

- nur synthetische Demo-Daten
- kontrollierten AI-Workflow aufrufen
- strukturierten Output liefern
- Reviewstatus anzeigen
- Quellen anzeigen
- keine Secrets
- keine vollstaendigen internen Prompts

Docker-Anforderungen:

- reproduzierbarer Build
- nicht privilegierter Benutzer
- Health Check
- keine Secrets im Image
- `FakeModelProvider` als sicherer Standard
- echter Provider nur per expliziter Konfiguration

Die bestehende CLI bleibt funktionsfaehig. Stabile CLI-JSON-Vertraege duerfen
nicht stillschweigend veraendert werden.

### Phase 5 - Referenz-Cloud und Observability

Zeitraum: 9. bis 30. November 2026

Minimaler Cloud-Scope:

- ein Containerdienst
- ein Secret Store
- Health Check
- strukturierte Logs
- minimale Infrastructure as Code
- Kosten- und Abschaltkontrolle

Managed PostgreSQL ist kein Pflichtbestandteil. Die Demo arbeitet nur mit
synthetischen Daten. Ein stateless Betrieb ist schneller, guenstiger und
risikoaermer. Persistenz wird nur ergaenzt, wenn sie einen klaren
Portfolio-Mehrwert liefert.

Geplante Branches:

```text
docs/add-reference-cloud-deployment-architecture
feat/add-reference-cloud-infrastructure
feat/add-structured-runtime-logging
feat/add-basic-runtime-metrics
```

Pflichtmetadaten fuer strukturierte Logs:

- Request-ID
- Workflowstatus
- Gatewayentscheidung
- Reviewentscheidung
- Providername
- Modellname
- Promptversion
- Laufzeit
- Parse- und Validierungsstatus
- Fehlerklasse

Nicht geloggt werden:

- Secrets
- vollstaendige Rohprompts
- vollstaendige Modellantworten
- reale personenbezogene Daten

Grundlegende Metriken:

- Requestzahl
- Erfolgsquote
- Fehlerquote
- P95-Latenz
- Providerfehler
- Parsefehler
- Validierungsfehler
- Abstention Rate
- gemeldete oder geschaetzte Modellkosten

Keine Pflicht besteht fuer:

- Kubernetes
- Managed PostgreSQL
- Entra-ID-Integration
- komplexe private Netzarchitektur
- Multi-Cloud

### Phase 6 - Hardening und Portfolio-Release

Zeitraum: 1. bis 20. Dezember 2026

In dieser Phase werden keine neuen grossen Features begonnen.

Schwerpunkte:

- Regression Suite
- fester Evaluation-Baseline-Report
- Prompt-Injection-Testfaelle
- unbeantwortbare Fragen
- widerspruechliche Quellen
- Providerfehler
- Timeouts
- ungueltige JSON-Antworten
- semantisch ungueltige Antworten
- fehlende Quellen
- zu lange Antworten

Portfolio-Artefakte:

- Release-Tag `v1.0.0`
- README
- Architekturdiagramm
- Datenflussdiagramm
- Threat- und Failure-Boundaries
- lokaler Quickstart
- Docker Quickstart
- Cloud Deployment Guide
- Evaluation Guide
- Kostenhinweise
- bekannte Einschraenkungen
- drei- bis fuenfminuetiges Demo-Video
- Evaluationsuebersicht
- technische Fallstudie
- CV-taugliche Projektbeschreibung
- Lessons Learned

Code Freeze ist der 20. Dezember 2026. Der Zeitraum vom 21. bis
31. Dezember 2026 bleibt Puffer. Nach dem Code Freeze sind nur noch Blocker,
Sicherheitsprobleme, defekte Dokumentation, kaputte Demo und Releasekorrekturen
zulaessig.

## Prioritaets- und Kuerzungsregeln

Bei Zeitdruck gilt diese Reihenfolge:

1. semantische Validierung
2. Prompt-Versionierung
3. Offline-Evaluation und messbare Qualitaetsmetriken
4. genau ein kontrollierter echter Modellprovider
5. RAG mit Quellen und Retrieval-Evaluation
6. FastAPI-Demo
7. lokale Docker-Demo
8. genau eine Referenz-Cloud
9. grundlegende Laufzeitbeobachtung
10. Stretch Goals

Diese Reihenfolge bildet technische Abhaengigkeiten und die geplante
Ausfuehrungsreihenfolge ab. Semantische Validierung und versionierte Prompts
sind Voraussetzungen fuer reproduzierbare Evaluation. Die Evaluation muss
vorhanden sein, bevor ein echter Provider als Portfolio-Nachweis bewertet wird.
Unter Zeitdruck duerfen diese Voraussetzungen nicht uebersprungen werden.

Ein echter Provider ohne semantische Validierung, Prompt-Versionierung und
Evaluation gilt nicht als abgeschlossenes Portfolio-Ziel.

Cloud-Infrastruktur darf niemals auf Kosten von funktionierender AI und
Evaluation priorisiert werden.

Die Referenz-Cloud ist kein Stretch Goal. Cloud-Funktionalitaet bleibt zeitlich
nach AI-Qualitaet, Evaluation, RAG, API und Docker eingeordnet. Bei Zeitdruck
wird zuerst der Cloud-Umfang reduziert, nicht die Referenz-Cloud vollstaendig
gestrichen. Eine lokale Docker-Demo ersetzt die Referenz-Cloud nicht.

Als minimaler reduzierter Cloud-Scope bleiben verbindlich:

- ein Containerdienst
- ein Secret Store
- Health Check
- strukturierte Logs
- minimale Infrastructure as Code
- Kosten- und Abschaltkontrolle

Falls ein Meilenstein mehr als zwei Wochen hinter dem Plan liegt, werden zuerst
gestrichen oder reduziert:

- Managed PostgreSQL
- Authentifizierung
- persistentes Audit
- private Netzwerkarchitektur
- erweitertes Monitoring
- zusaetzliche Cloud-Dienste
- Tool Calling
- zweites Projekt

Nicht gestrichen werden:

- semantische Validierung
- Prompt-Versionierung
- Offline-Evaluation
- genau ein kontrollierter echter Modellprovider
- RAG mit nachvollziehbaren Quellen
- lokale Docker-Demo
- genau eine per Infrastructure as Code reproduzierbar bereitgestellte
  Referenz-Cloud
- Portfolio-Dokumentation und Demo-Nachweise

## Roadmap-Pflege

Diese Roadmap ist die strategische Quelle der Wahrheit. Sie wird nicht nach
jedem kleinen Pull Request geaendert.

Am Ende jeder Phase wird aktiv geprueft:

- Sind die Exit-Kriterien tatsaechlich erfuellt?
- Ist die naechste Phase im verbleibenden Zeitraum realistisch?
- Besteht ein Verzug von mehr als zwei Wochen?
- Muessen optionale oder reduzierbare Ziele vor Beginn der naechsten Phase
  gestrichen werden?

Kuerzungsentscheidungen werden proaktiv an den Phasenuebergaengen getroffen und
nicht erst dann, wenn der Gesamttermin bereits gefaehrdet ist. Die Roadmap ist
ambitioniert, aber die geplanten Branches muessen nicht unabhaengig vom
tatsaechlichen Fortschritt unveraendert abgearbeitet werden.

Sie wird aktualisiert bei:

- abgeschlossenem Meilenstein
- wesentlicher Prioritaetsaenderung
- gestrichenem Ziel
- Terminverschiebung von mehr als zwei Wochen

Jede wesentliche Aktualisierung nennt Datum, Aenderung, Begruendung und
Auswirkung. GitHub Issues und Milestones verwalten konkrete Arbeitspakete,
ersetzen aber nicht die Roadmap. ADRs dokumentieren schwer umkehrbare
Architekturentscheidungen.

### Aktualisierung vom 10. Juli 2026

- Datum: 10. Juli 2026
- Aenderung: Der bisher kombinierte Evaluationsmetrik- und Report-Branch wird in
  `feat/add-evaluation-case-assessment`,
  `feat/add-synthetic-evaluation-case-library` und
  `feat/add-evaluation-metrics-report` aufgeteilt.
- Begruendung: Der Einzel-Fall-Erwartungsvergleich ist eine eigenstaendige
  Voraussetzung. Eine belastbare Aggregation benoetigt anschliessend eine echte
  Fallbibliothek. Metriken und Report werden nicht auf Unit-Test-Hilfsfaellen
  aufgebaut.
- Auswirkung: keine Aenderung am Portfolio-Zieltermin.

## Unmittelbar naechster Produktionsbranch

Der unmittelbar naechste Produktionsbranch ist:

```text
feat/add-synthetic-evaluation-case-library
```

Die synthetische Evaluationsfallbibliothek baut auf dem getrennten Einzel-Fall-
Erwartungsvergleich auf und schafft die belastbare Eingabe fuer den spaeteren
Metrik- und Report-Branch. In diesem Branch gibt es noch keinen echten Provider
und keine API-, CLI-, Docker-, Cloud- oder RAG-Arbeit.
