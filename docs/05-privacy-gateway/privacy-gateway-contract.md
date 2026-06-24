# Privacy Gateway Contract

## Zweck und Reichweite

Dieses Dokument beschreibt den ersten verbindlichen Architektur- und Sicherheitsvertrag fuer das **Policy- und Privacy-Gateway** des **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es definiert Mindestgrenzen fuer Daten, Modellkontexte, Pruefschritte und Eskalationen vor jeder spaeteren Implementierung. Es fuehrt keine technische Integration ein und ersetzt keine spaetere Datenschutz-, Rechts-, Sicherheits- oder Betriebspruefung.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Grundsatz

Jeder Modellaufruf muss zwingend durch das **Policy- und Privacy-Gateway** gefuehrt werden.

Das Gateway ist eine Kontrollschicht vor und neben dem Modell. Das Modell selbst ist nicht der Ort fuer Datenschutz-, Geheimnis- oder Freigabeentscheidungen.

Ohne erfolgreich durchlaufene Gateway-Pruefung darf kein Prompt, kein Kontext, kein Retrieval-Ergebnis, kein Tool-Ergebnis und kein sonstiger Eingabebestandteil an ein Modell uebergeben werden.

## Verbindliche Modellgrenzen

Fuer Modellkontexte gelten mindestens diese Grenzen:

- keine Original-PII im Modellkontext
- keine vertraulichen Mandanten-, Beleg-, Steuer-, Buchhaltungs- oder Kanzleidaten in Public-LLM-Kontexten
- keine Secrets, Tokens, Zugangsdaten, Zertifikate oder privaten Schluessel im Modellkontext
- kein direkter LLM-Zugriff auf Datenbanken, Dateisysteme, Object Storage, Agenda, ELSTER, DMS, Audit-Logs oder Token-Maps
- keine Umgehung des Policy- und Privacy-Gateway durch Orchestrierung, Agenten, MCP-Services, RAG, UI oder Tests
- keine produktiven Datenpfade in Entwicklungs-, Test- oder Demo-Kontexten

## Datenklassen

### Erlaubte Datenklassen

Erlaubt sind nur Daten, die keine Identifikation echter Personen, Mandanten, Kanzleien oder Vorgaenge erlauben und keine vertraulichen Inhalte enthalten.

Dazu koennen gehoeren:

- oeffentliche oder ausdruecklich freigegebene Projektdokumentation
- abstrakte Architektur-, Policy- und Prozessbeschreibungen
- synthetische Beispieldaten ohne Bezug zu realen Personen, Mandanten, Kanzleien oder Vorgaengen
- generische Kategorien, Checklisten und Textbausteine ohne vertrauliche Einzelfalldaten
- freigegebene steuerliche oder technische Quellen, soweit sie spaeter separat geprueft und versioniert werden

### Nur pseudonymisiert erlaubte Datenklassen

Die folgenden Datenklassen duerfen nur in pseudonymisierter, minimierter und fuer den Modellzweck notwendiger Form in einen Modellkontext gelangen:

- Rollen oder Beteiligte eines Vorgangs
- interne Fall-, Vorgangs- oder Dokumentreferenzen
- Zeitraeume, Fristen oder Sachverhaltsmerkmale, soweit sie fuer die Vorbereitung erforderlich sind
- kategorisierte Beleg- oder Dokumentmerkmale
- strukturierte Rueckfragen oder Pruefpunkte
- fachliche Arbeitsnotizen ohne Original-PII und ohne vertrauliche Originalinhalte

Pseudonyme muessen als Platzhalter gestaltet sein, zum Beispiel `CLIENT_001`, `PERSON_001`, `DOCUMENT_001` oder `CASE_001`. Sie duerfen selbst keine rueckschliessbaren Bestandteile aus Originaldaten enthalten.

### Verbotene Datenklassen

Nicht in Modellkontexte aufgenommen werden duerfen:

- Namen, Adressen, Geburtsdaten, Steuer-IDs, Identifikationsnummern oder Kontaktdaten echter Personen
- echte Mandanten-, Kanzlei-, Beleg-, Steuer-, Buchhaltungs-, Bank-, Lohn- oder Vertragsdaten
- Originaldokumente, OCR-Rohtexte, E-Mail-Inhalte, Chat-Inhalte oder Metadaten mit vertraulichem Bezug
- Kontoverbindungen, Zahlungsdaten, Rechnungsnummern, Kundennummern oder vergleichbare Identifikatoren
- Zugangsdaten, API-Keys, Tokens, Zertifikate, private Schluessel oder sonstige Secrets
- produktive Systempfade, Datenbankverbindungen, Storage-Konfigurationen oder Cloud-Konfigurationen
- Token-Maps, Detokenisierungsdaten oder Zuordnungen zwischen Pseudonymen und Originalwerten
- Inhalte, die durch Kombination mit anderem Kontext eine Re-Identifikation naheliegend machen

## Token- und Pseudonym-Map

Die Token-Map bleibt ausserhalb des Modells.

Das LLM darf keinen Zugriff auf Token-Maps, Detokenisierungsfunktionen oder Originalwerte erhalten. Detokenisierung ist ausschliesslich ausserhalb des Modellkontexts in kontrollierten Schichten zulaessig, insbesondere im Policy- und Privacy-Gateway oder im Kanzlei-Workspace.

Pseudonymisierung ist kein Freibrief fuer beliebige Modellnutzung. Das Gateway muss weiterhin Datenminimierung, Zweckbindung, Kontextgrenzen und Eskalationsregeln pruefen.

## Request-seitige Pruefungen

Vor jedem Modellaufruf muss das Gateway mindestens pruefen:

- ob der Zweck des Modellaufrufs dokumentiert und zulaessig ist
- ob der Modellaufruf fuer Vorbereitung, Strukturierung, Rueckfragen oder Entwurfserstellung bestimmt ist
- ob alle Eingaben einer erlaubten oder pseudonymisiert erlaubten Datenklasse zugeordnet sind
- ob Original-PII, vertrauliche Originaldaten, Secrets oder produktive Systeminformationen entfernt oder blockiert wurden
- ob Pseudonyme keine rueckschliessbaren Originalbestandteile enthalten
- ob der Kontext auf das erforderliche Minimum reduziert wurde
- ob Retrieval-, Tool-, Agenten- oder MCP-Inhalte dieselben Grenzen einhalten
- ob steuerlich erhebliche oder rote Faelle vorliegen, die Human Review oder Eskalation erfordern

Schlaegt eine Pruefung fehl, darf kein Modellaufruf erfolgen.

## Response-seitige Pruefungen

Nach jedem Modelloutput muss das Gateway oder eine gleichwertige kontrollierte Schicht mindestens pruefen:

- ob der Output Original-PII, vertrauliche Inhalte, Secrets oder produktive Systeminformationen enthaelt
- ob der Output unzulaessige Rueckschluesse auf echte Personen, Mandanten, Kanzleien oder Vorgaenge ermoeglicht
- ob der Output als Entwurf erkennbar bleibt
- ob steuerlich relevante Aussagen Human Review und Kanzlei-Freigabe voraussetzen
- ob das Modell eine steuerliche Entscheidung, Freigabe, Rechtsgewissheit oder autonome Handlung suggeriert
- ob Unsicherheit, fehlende Informationen oder rote Faelle angemessen markiert wurden

Schlaegt eine Pruefung fehl, darf der Output nicht ungeprueft weiterverwendet werden.

## Block- und Eskalationsfaelle

Das Gateway muss blockieren oder eskalieren, wenn:

- Original-PII oder vertrauliche Originaldaten im Modellkontext erkannt werden
- Secrets, Zugangsdaten oder produktive Konfigurationen erkannt werden
- Token-Maps oder Detokenisierungsinformationen in den Modellkontext gelangen wuerden
- eine Re-Identifikation durch Kontextkombination naheliegt
- ein Public-LLM mit vertraulichen oder abgeleiteten vertraulichen Inhalten versorgt werden soll
- der Modellaufruf eine steuerliche Entscheidung, Freigabe oder steuerlich wirksame Handlung vorbereiten soll, ohne Human Review vorzusehen
- Agenda-, ELSTER-, DMS-, Datenbank-, Storage- oder Cloud-Integrationen produktiv oder schreibend angesprochen werden sollen
- die Datenklasse, der Zweck oder die Freigabe des Modellaufrufs unklar ist
- der Output als abschliessend, rechtssicher, steuerlich freigegeben oder verbindlich dargestellt wird

Eskalation bedeutet keine automatische Freigabe. Sie fuehrt zu fachlicher, technischer, Datenschutz-, Sicherheits- oder Kanzlei-Pruefung, je nach Fall.

## Entwurfs- und Reviewpflicht

Alle Modelloutputs bleiben Entwuerfe.

Steuerlich relevante Outputs duerfen erst nach Human Review und Kanzlei-Freigabe fachlich verwendet, weitergegeben oder in nachgelagerte Arbeitsprozesse uebernommen werden.

Das System darf keine autonome Steuerberaterrolle einnehmen, keine individuelle Steuerberatung durch das Modell leisten und keine steuerlich wirksamen Handlungen ohne Kanzlei-Freigabe ausloesen.

## Nicht-Zusicherungen

Dieses Dokument enthaelt keine Zusage von DSGVO-Konformitaet, rechtlicher Sicherheit, berufsrechtlicher Zulaessigkeit, GoBD-Konformitaet oder produktiver Betriebsfreigabe.

Es enthaelt keine finale AI-Act-Klassifizierung und keine Aussage, dass produktionsnahe Nutzung bereits freigegeben ist. Solche Bewertungen benoetigen separate Pruefung, Dokumentation und Human Review.

## Verhaeltnis zu anderen Dokumenten

| Dokument | Bezug |
| --- | --- |
| `docs/00-project/project-brief.md` | Projektziel, Kontrollschichten und Nicht-Ziele |
| `docs/00-project/glossary.md` | Begriffe wie Original-PII, Token-Map, Entwurf und Human Review |
| `docs/01-legal-compliance/legal-boundaries.md` | rechtliche Systemgrenzen und Entwurfscharakter |
| `docs/01-legal-compliance/stberg-safety-policy.md` | berufsrechtliche Sicherheitsleitplanken |
| `docs/04-mcp/agent-mcp-boundaries.md` | MCP-Grenzen und Gateway-Pflicht |
