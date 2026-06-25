# Security Baseline Policy

## Zweck und Reichweite

Dieses Dokument beschreibt die erste interne Security-Baseline fuer den **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es definiert Mindestgrenzen fuer Entwicklung, Tests, Dokumentation, Modellkontexte und spaetere kontrollierte Workflows. Es fuehrt keine technische Integration, keinen Produktivbetrieb und keine Verbindung zu produktiven Systemen ein.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Sicherheitsgrundsaetze

Die Security-Baseline folgt diesen Grundsaetzen:

- Datenminimierung vor jeder Verarbeitung
- keine echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten in Entwicklungs-, Test- oder Dokumentationsbeispielen
- keine Secrets, Tokens, Zugangsdaten, Zertifikate oder privaten Schluessel im Repository
- keine produktiven Systemzugriffe aus Entwicklungs-, Test- oder Dokumentationskontexten
- keine Umgehung des **Policy- und Privacy-Gateway**
- Human Review vor fachlicher Nutzung steuerlich relevanter Ergebnisse
- klare Stop- und Eskalationsfaelle statt automatischer Freigabe

Kontrollpunkte liegen vor und neben dem Modell. Das Modell selbst ist nicht der Ort fuer Datenschutz-, Geheimnis-, Freigabe- oder Sicherheitsentscheidungen.

## Datenminimierung

Eingaben, Beispiele, Testdaten und Dokumentationsinhalte muessen auf das notwendige Minimum beschraenkt bleiben.

Erlaubt sind nur abstrakte, synthetische oder oeffentliche Inhalte, die keinen Rueckschluss auf echte Personen, Mandanten, Kanzleien, Belege, Steuerfaelle oder Vorgaenge zulassen.

Nicht erlaubt sind:

- echte Namen, Adressen, Steuer-IDs, Identifikationsnummern, Kontaktdaten oder vergleichbare Identifikatoren
- echte Mandanten-, Beleg-, Steuer-, Buchhaltungs-, Bank-, Lohn-, Vertrags- oder Kanzleidaten
- realistische Fallbeispiele, die wie echte Mandanten- oder Steuerunterlagen wirken
- abgeleitete vertrauliche Inhalte, Zusammenfassungen oder Metadaten aus echten Vorgaengen
- Token-Maps, Detokenisierungsdaten oder Zuordnungen zwischen Pseudonymen und Originalwerten

Synthetische Beispiele muessen eindeutig als abstrakte Beispiele erkennbar sein und duerfen keine realen Einzelfaelle nachbilden.

## Secrets und Zugangsdaten

Secrets duerfen nicht im Repository abgelegt, dokumentiert oder in Tests verwendet werden.

Dazu gehoeren insbesondere:

- API-Keys, Tokens, Passwoerter und Zugangsdaten
- Zertifikate, private Schluessel und Signaturmaterial
- produktive Konfigurationen, Verbindungszeichenfolgen oder Systempfade
- Cloud-, Storage-, Datenbank-, Agenda-, ELSTER-, DMS- oder Mandantensystem-Zugangsdaten

Platzhalter muessen klar synthetisch sein, zum Beispiel `EXAMPLE_TOKEN_DO_NOT_USE` oder `CLIENT_001`. Platzhalter duerfen keine rueckschliessbaren Bestandteile aus echten Daten enthalten.

## Produktive Systemgrenzen

Entwicklung, Tests und Dokumentation duerfen keine produktiven Systemzugriffe einrichten oder verwenden.

Nicht erlaubt sind:

- produktive Datenbank-, Storage-, Cloud-, Agenda-, ELSTER-, DMS- oder Mandantensystem-Verbindungen
- direkte produktive Schreibzugriffe
- produktive MCP-Server oder produktive MCP-Konfigurationen
- automatische Uebermittlung, Einreichung, Signatur, Freigabe oder Mandantenkommunikation

Agenda, ELSTER, DMS und andere produktive Systeme bleiben im Projektkontext auf Handoff, Export, Staging oder manuelle Uebernahme beschraenkt, soweit spaetere Architektur- und Freigabedokumente nichts anderes ausdruecklich erlauben.

## Modell- und LLM-Grenzen

Das LLM erhaelt keinen direkten Zugriff auf:

- Datenbanken
- Dateisysteme
- Object Storage
- Agenda
- ELSTER
- DMS
- Token-Maps oder Detokenisierungsfunktionen
- Audit-Logs
- Secrets oder produktive Konfigurationen

Modellkontexte duerfen keine Original-PII, vertraulichen Originaldaten, Secrets oder produktiven Systeminformationen enthalten.

Alle Modelloutputs bleiben Entwuerfe. Steuerlich relevante Outputs benoetigen Human Review und Kanzlei-Freigabe vor fachlicher Nutzung, Weitergabe oder Uebernahme in nachgelagerte Arbeitsprozesse.

## Policy- und Privacy-Gateway

Jeder spaetere Modellaufruf muss durch das **Policy- und Privacy-Gateway** gefuehrt werden.

Das Gateway prueft vor und nach Modellnutzung mindestens Datenklassen, Zweckbindung, Datenminimierung, Pseudonymisierung, Secret-Freiheit, Modellgrenzen und Eskalationspflichten.

Ein fehlgeschlagener Gateway-Check darf nicht durch UI, Tests, Agenten, MCP, Orchestrierung oder manuelle Workarounds umgangen werden.

## Human Review

Human Review ist Pflichtkontrolle nach KI-Ausgaben und vor fachlicher Nutzung.

Das Modell darf steuerlich relevante Arbeit nicht freigeben, einreichen, uebermitteln, unterschreiben, versenden, kommunizieren oder finalisieren.

Mandantenkommunikation mit steuerlich relevanten Inhalten erfordert menschliche Pruefung und Freigabe vor Verwendung.

## Logging und Nachvollziehbarkeit

Logging darf keine vertraulichen Originaldaten, Original-PII, Secrets, Token-Maps oder produktiven Systeminformationen enthalten.

Sichere Logs sollen, soweit spaeter technisch umgesetzt:

- nur notwendige technische Ereignisse und Kontrollstatus enthalten
- Pseudonyme statt Originalwerte verwenden
- Fehler und Blockfaelle nachvollziehbar machen, ohne sensible Inhalte offenzulegen
- keine Prompt-, OCR-, Dokument-, E-Mail- oder Chat-Rohinhalte mit vertraulichem Bezug speichern
- keine Freigabe oder fachliche Pruefung durch das Modell suggerieren

Konkrete Logging-, Audit- und Aufbewahrungsanforderungen folgen in separaten Architektur-, Datenschutz- oder Betriebsdokumenten.

## Lokale Entwicklungsgrenzen

Lokale Entwicklung bleibt auf abstrakte Dokumentation, synthetische Testdaten und lokale Validierung beschraenkt.

Lokale Checks duerfen:

- Markdown- und Repository-Inhalte statisch pruefen
- synthetische Testfaelle verwenden
- ohne Netzwerk, Secrets und produktive Systeme laufen

Lokale Checks duerfen nicht:

- externe Dienste aufrufen
- produktive Systeme kontaktieren
- echte oder abgeleitete vertrauliche Inhalte verarbeiten
- produktive Konfigurationen benoetigen

## Testdatenregeln

Tests duerfen nur synthetische, minimale und nicht rueckschliessbare Daten verwenden.

Testdaten muessen vermeiden:

- realistische Steuerfaelle mit echtem Einzelfallcharakter
- echte Namen, Adressen, Steuer-IDs, Belegnummern, Kontoverbindungen oder Kanzleidaten
- produktive Pfade, Zugangsdaten oder Verbindungszeichenfolgen
- Inhalte, die als fachlich gepruefte steuerliche Aussage erscheinen

Tests duerfen Policy-Grenzen pruefen, aber keine steuerlichen Entscheidungen, produktiven Integrationen oder Freigabelogik implementieren.

## Incident-, Stop- und Eskalationsfaelle

Ein Vorgang muss gestoppt oder eskaliert werden, wenn:

- echte oder realistisch wirkende Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten im Repository, Testkontext oder Modellkontext erscheinen
- Secrets, Zugangsdaten, Zertifikate, private Schluessel oder produktive Konfigurationen erkannt werden
- produktive Systemzugriffe eingerichtet oder angesprochen werden sollen
- ein LLM direkten Zugriff auf verbotene Systeme oder Daten erhalten wuerde
- das Policy- und Privacy-Gateway umgangen werden soll
- Modelloutputs als freigegeben, fachlich abschliessend oder steuerlich wirksam dargestellt werden
- Mandantenkommunikation ohne menschliche Freigabe vorbereitet oder verwendet werden soll
- Unsicherheit, fehlender Quellenkontext, widerspruechliche Informationen oder moegliche Datenabfluesse vorliegen

Eskalation bedeutet keine Freigabe. Sie fuehrt zu zusaetzlicher fachlicher, technischer, Datenschutz-, Sicherheits- oder Kanzlei-Pruefung.

## Nicht-Zusicherungen

Diese Policy enthaelt keine Zusage zu:

- rechtlicher Sicherheit
- Datenschutz-Compliance
- GoBD-Compliance
- AI-Act-Compliance
- produktiver Betriebs- oder Release-Freigabe

Sie ersetzt keine spaetere Rechts-, Datenschutz-, Sicherheits-, GoBD-, AI-Act-, Architektur- oder Betriebspruefung.

## Verhaeltnis zu anderen Dokumenten

| Dokument | Bezug |
| --- | --- |
| [README.md](../../README.md) | Projektleitbild, Grundabgrenzung und Systemgrenzen |
| [project-brief.md](../00-project/project-brief.md) | Projektziel, Kontrollschichten und Nicht-Ziele |
| [glossary.md](../00-project/glossary.md) | Begriffe wie Original-PII, Token-Map, Entwurf und Human Review |
| [legal-boundaries.md](../01-legal-compliance/legal-boundaries.md) | rechtliche Systemgrenzen und Entwurfscharakter |
| [stberg-safety-policy.md](../01-legal-compliance/stberg-safety-policy.md) | berufsrechtliche Sicherheitsleitplanken |
| [ai-act-readiness.md](../01-legal-compliance/ai-act-readiness.md) | interne AI-Act-Readiness-Orientierung |
| [privacy-gateway-contract.md](../05-privacy-gateway/privacy-gateway-contract.md) | Gateway-Pruefungen, Datenklassen und Eskalationsfaelle |
| [human-review-policy.md](../06-human-review/human-review-policy.md) | Review-Level, Status und Stop-Faelle vor fachlicher Nutzung |
| [risk-classification-policy.md](../07-risk-classification/risk-classification-policy.md) | menschliche Triage und interne Handlungsklassen |
