# Human Review Policy

## Zweck und Reichweite

Dieses Dokument beschreibt die erste Human-Review-Leitlinie fuer den **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es operationalisiert den Human-Review-Layer als verpflichtende Kontrollschicht nach KI-Ausgaben und vor fachlicher Nutzung durch die Kanzlei.

Es fuehrt keine technische Integration, kein Produktivsystem und keine automatisierte Freigabe ein.

## Leitprinzip

```text
KI bereitet vor.
Die Kanzlei prueft.
Der Steuerberater entscheidet.
```

## Grundsatz

Alle steuerlich relevanten KI-Ausgaben sind **Entwuerfe**.

Human Review ist die verpflichtende operative Kontrolle nach der KI-gestuetzten Vorbereitung und vor jeder fachlichen Kanzlei-Nutzung, Weitergabe oder Uebernahme in nachgelagerte Arbeitsprozesse.

Das Modell darf steuerlich relevante Arbeit niemals:

- freigeben
- einreichen
- uebermitteln
- unterschreiben
- versenden
- kommunizieren
- finalisieren

Die fachliche Verantwortung, Freigabe und Entscheidung verbleiben bei der Kanzlei beziehungsweise beim verantwortlichen Steuerberater.

## Rollen

| Rolle | Aufgabe |
| --- | --- |
| Preparer | Erstellt oder sammelt Vorbereitungsmaterial, prueft Vollstaendigkeit im Arbeitskontext und markiert offene Punkte. |
| Reviewer | Prueft KI-Ausgaben, Quellenkontext, Plausibilitaet, Kennzeichnung als Entwurf und Einhaltung der Reviewpflicht. |
| Verantwortlicher Steuerberater | Traegt die fachliche Verantwortung fuer steuerlich relevante Freigaben, Entscheidungen und externe Verwendung. |
| Optionaler Admin | Verwaltet Rollen, Workflows, Statuswerte und technische Berechtigungen, ohne steuerliche Freigaben zu ersetzen. |

Rollen koennen organisatorisch zusammenfallen, soweit Kanzlei-Regeln, fachliche Qualifikation und spaetere Betriebsfreigaben dies zulassen. Die Verantwortung des Steuerberaters wird dadurch nicht auf das Modell uebertragen.

## Review-Level

| Level | Inhalt | Mindestkontrolle |
| --- | --- | --- |
| Nicht-steuerliche administrative Ausgaben | Interne Organisationsnotizen, neutrale Listen oder formale Vorbereitung ohne steuerliche Aussage. | Plausibilitaetspruefung und Daten-/Geheimnisschutzpruefung vor Nutzung. |
| Dokumenten- und Belegvorbereitung | Strukturierung, Kategorisierung, Rueckfragenlisten und Vorbereitung von Unterlagen. | Pruefung auf Quellenbezug, Vollstaendigkeit, Datenminimierung und offene Rueckfragen. |
| Steuerlich relevante Zusammenfassungen | Entwuerfe mit steuerlichem Bezug, fachlichen Einordnungen oder entscheidungsnahen Hinweisen. | Fachlicher Review durch qualifizierte Kanzlei-Rolle; Freigabe durch verantwortlichen Steuerberater, soweit erforderlich. |
| Mandantenfrage-Entwuerfe | Entwuerfe fuer Rueckfragen, Hinweise oder sonstige Mandantenkommunikation. | Menschliche Freigabe vor jeder Verwendung; steuerlich relevante Inhalte muessen fachlich geprueft werden. |
| Agenda-, ELSTER-, DMS-, Handoff- oder Exportvorbereitung | Vorbereitung von Uebergaben, Exportpaketen, Staging-Inhalten oder manuellen Uebernahmen. | Review vor Uebergabe; keine direkte produktive Schreib- oder Uebermittlungswirkung durch das Modell. |

## Review-Status

| Status | Bedeutung |
| --- | --- |
| Draft | KI-gestuetztes oder manuell vorbereitetes Material ohne Freigabe. |
| In review | Material befindet sich in fachlicher, organisatorischer oder Datenschutz-/Sicherheitspruefung. |
| Approved for internal use | Fuer interne Kanzlei-Nutzung freigegeben, aber nicht automatisch fuer Mandantenkommunikation oder produktive Uebergabe bestimmt. |
| Approved for client communication | Nach menschlicher Pruefung fuer konkrete Mandantenkommunikation freigegeben. |
| Rejected | Ausgabe darf nicht verwendet werden und muss korrigiert, ersetzt oder verworfen werden. |
| Escalated | Vorgang benoetigt zusaetzliche fachliche, technische, Datenschutz-, Sicherheits- oder Kanzlei-Pruefung. |

Ein Status ist keine Modellentscheidung. Statuswechsel mit steuerlicher Relevanz muessen durch berechtigte Kanzlei-Rollen erfolgen.

## Mandantenkommunikation

Mandantenkommunikation mit steuerlich relevanten Inhalten erfordert vor Verwendung menschliche Pruefung und Freigabe.

KI-Ausgaben duerfen Mandanten gegenueber nicht als fachlich abschliessend bewertet, extern freigegeben oder durch das Modell entschieden dargestellt werden.

## Produktive Systeme

Agenda, ELSTER, DMS und andere produktive Systeme bleiben im Projektkontext auf Handoff, Export, Staging oder manuelle Uebernahme beschraenkt.

Direkte produktive Schreibzugriffe, Einreichungen, Uebermittlungen oder Freigaben sind ausgeschlossen, solange sie nicht in einem spaeteren Architektur- oder Freigabedokument ausdruecklich beschrieben und genehmigt werden.

## Stop- und Eskalationsfaelle

Ein Vorgang muss gestoppt oder eskaliert werden, wenn:

- fachliche Unsicherheit besteht
- Quellen, Belege, Kontext oder Zeitraum fehlen
- Informationen widerspruechlich sind
- sensible Daten im falschen Kontext erscheinen
- ein moeglicher Datenabfluss, eine Re-Identifikation oder eine Geheimnisschutzverletzung naheliegt
- steuerliche Relevanz vorliegt und keine passende Review- oder Freigabespur erkennbar ist
- das Modell eine Freigabe, abschliessende Bewertung, Uebermittlung oder steuerlich wirksame Handlung suggeriert
- Agenda-, ELSTER-, DMS- oder sonstige Produktivsysteme ueber Handoff, Export, Staging oder manuelle Uebernahme hinaus genutzt werden sollen

Eskalation bedeutet keine Freigabe. Sie fuehrt zu zusaetzlicher Pruefung durch die passende fachliche, technische, Datenschutz-, Sicherheits- oder Kanzlei-Rolle.

## Nicht-Zusicherungen

Diese Policy enthaelt keine Zusage zu:

- rechtlicher Sicherheit
- Datenschutz-Compliance
- GoBD-Compliance
- AI-Act-Compliance
- abschliessender Risikoklassifizierung
- fachlicher Kanzlei-Pruefung einzelner KI-Ausgaben

Sie sagt nicht aus, dass ein produktiver Einsatz bereits freigegeben ist.

## Verhaeltnis zu anderen Dokumenten

| Dokument | Bezug |
| --- | --- |
| [README.md](../../README.md) | Projektleitbild, Grundabgrenzung und Systemgrenzen |
| [legal-boundaries.md](../01-legal-compliance/legal-boundaries.md) | rechtliche Systemgrenzen und Entwurfscharakter |
| [stberg-safety-policy.md](../01-legal-compliance/stberg-safety-policy.md) | berufsrechtliche Sicherheitsleitplanken |
| [ai-transparency-policy.md](../01-legal-compliance/ai-transparency-policy.md) | Kennzeichnung, Transparenz und Mandantenkommunikation |
| [ai-act-readiness.md](../01-legal-compliance/ai-act-readiness.md) | interne AI-Act-Readiness-Orientierung |
| [privacy-gateway-contract.md](../05-privacy-gateway/privacy-gateway-contract.md) | Gateway-Pruefungen, Datenklassen und Eskalationsfaelle |
