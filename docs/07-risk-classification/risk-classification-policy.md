# Risk Classification Policy

## Zweck und Reichweite

Dieses Dokument beschreibt die erste interne **Risk Classification Policy** fuer den **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es definiert ein vorlaeufiges, von Menschen gefuehrtes Klassifikations- und Triage-Rahmenwerk fuer KI-gestuetzte Ausgaben und Workflows. Es dient der Entscheidung, wie Ergebnisse geprueft, eskaliert und kontrolliert werden sollen.

Dieses Dokument ist:

- keine abschliessende rechtliche, regulatorische oder AI-Act-Risikoeinordnung
- kein automatisiertes Modell-Risk-Scoring
- kein Ersatz fuer fachliche, datenschutzrechtliche, sicherheitsbezogene oder betriebliche Freigaben

Das Modell darf keine Steuerentscheidungen, Compliance-Entscheidungen oder abschliessenden Risikoentscheidungen treffen.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Grundsatz

Risikoklassifikation ist eine **menschliche, kanzleiseitige Triage-Entscheidung**.

Sie wird von berechtigten Kanzlei-Rollen vorgenommen, dokumentiert und bei Bedarf angepasst. Das Modell darf Klassifikationen weder final setzen noch Freigaben, Eskalationen oder Stop-Entscheidungen ersetzen.

Alle steuerlich relevanten KI-Ausgaben bleiben **Entwuerfe**. Human Review bleibt verpflichtend, soweit steuerliche Relevanz, Mandantenkommunikation, sensible Daten oder produktive Uebergabe betroffen sind.

## Klassifikationszweck

Die Klassifikation unterstuetzt die Kanzlei dabei:

- den erforderlichen Kontrollaufwand vor fachlicher Nutzung zu bestimmen
- Review-, Eskalations- und Gateway-Pflichten sichtbar zu machen
- Unsicherheit, fehlenden Kontext und sensible Effekte frueh zu erkennen
- produktive Handlungen, Mandantenkommunikation und steuerlich relevante Uebernahmen zu kontrollieren

Die Klassifikation ist ein internes Steuerungsinstrument, kein Nachweis rechtlicher oder regulatorischer Konformitaet.

## Klassifikationsdimensionen

Jeder zu pruefende KI-Workflow oder jede KI-Ausgabe soll entlang mindestens dieser Dimensionen bewertet werden. Die Bewertung erfolgt durch Menschen in berechtigten Kanzlei-Rollen.

| Dimension | Fragestellung | typische Auspraegungen |
| --- | --- | --- |
| Steuerliche Relevanz | Enthaelt der Output steuerliche Einordnung, Hinweise, Zahlen, Fristen oder entscheidungsnahe Bewertungen? | keine / gering / mittel / hoch |
| Datensensitivitaet | Sind vertrauliche, personenbezogene, mandantenbezogene oder geheimhaltungsrelevante Inhalte betroffen? | oeffentlich / intern / vertraulich / besonders sensibel |
| Externe Wirkung | Kann die Nutzung Mandanten, Behoerden, Dritte oder externe Systeme betreffen? | rein intern / intern mit spaeterer Weitergabe / extern wirksam |
| Mandantenkommunikation | Ist die Ausgabe fuer Rueckfragen, Hinweise, E-Mails, Portalinhalte oder sonstige Mandantenkommunikation bestimmt? | nein / Entwurf intern / mandantenbezogen |
| Produktivsystem-Naehe | Beruehrt der Workflow Agenda, ELSTER, DMS, Mandantensysteme oder andere produktive Systeme? | keine / Vorbereitung / Handoff oder Staging / produktive Aktion |
| Automatisierungsgrad | Wie weitgehend soll KI den Ablauf vorbereiten oder strukturieren? | manuell unterstuetzt / teilautomatisiert / weitgehend automatisiert |
| Unsicherheit oder fehlender Quellenkontext | Fehlen Belege, Zeitraeume, Rechtsstand, Mandantenangaben oder sind Angaben widerspruechlich? | klar / teilweise unklar / wesentlich unklar / widerspruechlich |

Einzelne Dimensionen koennen die Gesamtklassifikation anheben. Die hoechste relevante Dimension bestimmt mindestens die erforderliche Kontrollstufe.

## Handlungsklassen

Die folgenden Handlungsklassen sind interne Kontrollstufen. Sie sind keine abschliessende rechtliche oder regulatorische Risikoeinordnung.

| Klasse | Kurzbezeichnung | Mindestanforderung |
| --- | --- | --- |
| A | geringer Kontrollbedarf | Plausibilitaets- und Datenschutzpruefung vor interner Nutzung; kein produktiver oder mandantenbezogener Effekt |
| B | mittlerer Kontrollbedarf | strukturierte Human Review, Quellen- und Vollstaendigkeitspruefung; Freigabe durch berechtigte Kanzlei-Rolle |
| C | hoher Kontrollbedarf | fachliche Pruefung durch qualifizierte Kanzlei-Rolle; Freigabe durch verantwortlichen Steuerberater, soweit erforderlich |
| D | Stop oder Eskalation | keine fachliche Nutzung ohne Klaerung; zusaetzliche fachliche, technische, Datenschutz-, Sicherheits- oder Kanzlei-Pruefung |

Eine Handlungsklasse ist keine Modellentscheidung. Sie muss von Menschen gesetzt, begruendet und bei Aenderung des Sachverhalts neu bewertet werden.

## Beispiele

### Geringer Kontrollbedarf (Klasse A)

- interne Projekt- oder Prozessnotizen ohne steuerliche Aussage
- neutrale Checklisten oder Organisationslisten ohne Mandantenbezug
- Strukturierung nicht-steuerlicher Metadaten ohne vertrauliche Originalinhalte
- allgemeine Architektur- oder Policy-Diskussionen ohne Fallbezug

### Mittlerer Kontrollbedarf (Klasse B)

- Beleg- oder Dokumentvorbereitung mit Rueckfragenlisten
- Kategorisierung oder Strukturierung von Unterlagen mit begrenztem steuerlichem Bezug
- interne Zusammenfassungen mit offenen Punkten und erkennbarem Quellenbedarf
- Vorbereitung von Handoff- oder Exportpaketen ohne unmittelbare produktive Wirkung

### Hoher Kontrollbedarf (Klasse C)

- steuerlich relevante Zusammenfassungen, Einordnungen oder entscheidungsnahe Hinweise
- Mandantenfrage-Entwuerfe oder sonstige mandantenbezogene Kommunikationsentwuerfe
- Vorbereitung fuer Agenda-, ELSTER-, DMS- oder Mandantensystem-Uebergabe
- Inhalte mit hoher Datensensitivitaet, externer Wirkung oder wesentlicher Unsicherheit

## Eskalationstrigger

Ein Vorgang muss mindestens auf Klasse C angehoben oder nach Klasse D eskaliert werden, wenn:

- steuerliche Relevanz hoch ist oder eine fachliche Freigabe naheliegt
- Mandantenkommunikation vorgesehen oder wahrscheinlich ist
- vertrauliche, personenbezogene oder geheimhaltungsrelevante Daten betroffen sind
- externe Wirkung auf Mandanten, Behoerden oder Dritte moeglich ist
- produktive Systeme ueber Vorbereitung, Handoff, Export oder Staging hinaus beruehrt werden sollen
- Quellen, Belege, Zeitraeume oder Rechtsstand fehlen oder unklar sind
- Informationen widerspruechlich oder nicht belastbar sind
- das Modell eine Freigabe, abschliessende Bewertung oder steuerlich wirksame Handlung suggeriert
- das Policy- und Privacy-Gateway blockiert, filtert oder eine Datenschutz-/Sicherheitspruefung ausloest

Eskalation bedeutet keine Freigabe. Sie fuehrt zu zusaetzlicher Pruefung durch die passende fachliche, technische, Datenschutz-, Sicherheits- oder Kanzlei-Rolle.

## Stop-Faelle

Ein Vorgang muss gestoppt werden, bis eine berechtigte Kanzlei-Rolle den Fall neu bewertet hat, wenn mindestens einer der folgenden Stop-Faelle vorliegt:

| Stop-Fall | Beschreibung |
| --- | --- |
| Fehlender Quellenkontext | Belege, Zeitraeume, Mandantenangaben, Rechtsstand oder sonstiger fachlicher Kontext fehlen wesentlich. |
| Widerspruechliche Informationen | Angaben, Belege oder Modelloutputs widersprechen sich oder sind nicht aufloesbar. |
| Sensible Daten im falschen Kontext | Vertrauliche, personenbezogene oder geheimhaltungsrelevante Inhalte erscheinen in unzulaessigem Kontext. |
| Moegliche Re-Identifikation | Pseudonyme, Kontextkombinationen oder abgeleitete Inhalte ermoeglichen einen Rueckschluss auf echte Personen, Mandanten oder Vorgaenge. |
| Suggerierte abschliessende Steuerberatung | Der Output wirkt wie eine finale steuerliche Empfehlung, Bewertung oder Handlungsanweisung ohne Kanzlei-Freigabe. |
| Mandantenkommunikation ohne menschliche Freigabe | Mandantenbezogene Inhalte sollen verwendet, versendet oder extern dargestellt werden, ohne vorherige menschliche Pruefung und Freigabe. |
| Produktive Aktion ueber Handoff hinaus | Agenda-, ELSTER-, DMS- oder sonstige produktive Aktionen sollen ueber Handoff, Export, Staging oder manuelle Uebernahme hinaus ausgeloest werden. |

Stop bedeutet keine automatische Ablehnung des gesamten Projekts. Es bedeutet, dass die betroffene Ausgabe oder der Workflow nicht weiterverwendet werden darf, bis Menschen den Fall geklaert, neu klassifiziert oder verworfen haben.

## Rollen

| Rolle | Aufgabe in der Klassifikation |
| --- | --- |
| Preparer | markiert Unsicherheit, fehlenden Kontext und vorgeschlagene Handlungsklasse als Entwurf |
| Reviewer | prueft Dimensionen, Quellenbezug und Einhaltung von Review- und Gateway-Pflichten |
| Verantwortlicher Steuerberater | traegt die fachliche Verantwortung fuer Klassifikation und Freigabe bei hoher steuerlicher Relevanz |
| Optionaler Admin | unterstuetzt Workflow-, Status- und Berechtigungsfragen ohne steuerliche Entscheidungen zu ersetzen |

Rollen koennen organisatorisch zusammenfallen, soweit Kanzlei-Regeln, fachliche Qualifikation und spaetere Betriebsfreigaben dies zulassen. Die Verantwortung bleibt bei Menschen, nicht beim Modell.

## Verhaeltnis zu Kontrollschichten

Die Klassifikation verknuepft sich mit bestehenden Kontrollschichten, ersetzt sie aber nicht:

- **Policy- und Privacy-Gateway** - blockiert oder filtert unzulaessige Kontexte und Outputs unabhaengig von einer spaeteren Klassifikation
- **Human Review** - verpflichtende Pruefung vor fachlicher Nutzung, Mandantenkommunikation und produktiver Uebergabe
- **Kanzlei-Freigabe** - fachliche Entscheidung und Verantwortung durch den Steuerberater beziehungsweise berechtigte Kanzlei-Rollen

Eine niedrigere Handlungsklasse hebt keine Gateway-, Review- oder Freigabepflicht auf, wenn eine andere Policy oder ein anderer Kontrollpunkt eine hoehere Pflicht ausloest.

## Nicht-Zusicherungen

Diese Policy enthaelt keine Zusage zu:

- rechtlicher Sicherheit
- Datenschutz-Compliance
- GoBD-Compliance
- AI-Act-Compliance
- abschliessender Risikoeinordnung
- fachlicher Kanzlei-Pruefung einzelner KI-Ausgaben
- produktivem Release oder Betriebsfreigabe

Sie sagt nicht aus, dass KI-Ausgaben bereits fachlich geprueft oder fuer den produktiven Einsatz freigegeben sind.

## Verhaeltnis zu anderen Dokumenten

| Dokument | Bezug |
| --- | --- |
| [README.md](../../README.md) | Projektleitbild, Grundabgrenzung und Systemgrenzen |
| [project-brief.md](../00-project/project-brief.md) | Projektziel, Kontrollschichten und Nicht-Ziele |
| [legal-boundaries.md](../01-legal-compliance/legal-boundaries.md) | rechtliche Systemgrenzen und Entwurfscharakter |
| [stberg-safety-policy.md](../01-legal-compliance/stberg-safety-policy.md) | berufsrechtliche Sicherheitsleitplanken |
| [ai-act-readiness.md](../01-legal-compliance/ai-act-readiness.md) | interne AI-Act-Readiness-Orientierung |
| [privacy-gateway-contract.md](../05-privacy-gateway/privacy-gateway-contract.md) | Gateway-Pruefungen, Datenklassen und Eskalationsfaelle |
| [human-review-policy.md](../06-human-review/human-review-policy.md) | Review-Level, Status und Stop-Faelle vor fachlicher Nutzung |
