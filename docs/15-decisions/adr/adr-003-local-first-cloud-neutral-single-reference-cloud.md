# ADR 003: Local-first development with a cloud-neutral core and one reference cloud

## Status

Accepted

## Context

Der `steuerberater-copilot` ist ein AI-Engineering-Portfolio. Das Projekt soll
bis Ende 2026 praktische Kompetenz in kontrollierter LLM-Nutzung, Evaluation,
Gateway-Grenzen, Human Review, lokaler Reproduzierbarkeit und einem kleinen
Deployment-Nachweis zeigen.

Aktuell existiert ein lokaler Offline-MVP. Er verwendet ausschliesslich
synthetische Daten, laeuft deterministisch und stellt eine CLI mit stabilem
JSON-Output bereit. API, Persistenz und Cloud-Infrastruktur existieren noch
nicht. Die konkrete Cloud-Plattform ist noch offen.

Eine zu fruehe Cloud-Festlegung wuerde aktuell unnoetige Komplexitaet erzeugen
und den AI-Engineering-Fokus schwaechen. Ein zu spaetes Deployment koennte
umgekehrt den Portfolio-Nachweis gefaehrden, weil die lokale Demo allein nicht
zeigt, dass das System kontrolliert ausgeliefert werden kann.

## Decision

Lokale und reproduzierbare Entwicklung bleibt Pflicht.

Standardtests bleiben offline und deterministisch. Sie duerfen keine Secrets,
keine produktiven Systeme, keine echten Daten und keine verpflichtenden
Netzwerkzugriffe benoetigen.

Der Anwendungskern bleibt cloud-neutral. Cloud- und Provider-SDKs bleiben
ausserhalb des Kerns. Plattformspezifische Komponenten duerfen nur an den
Systemraendern liegen, insbesondere bei echtem ModelProvider, HTTP-Transport,
Secrets, Deployment, Cloud Logging, Cloud Metrics und Infrastructure as Code.

Docker wird die lokale Deployment-Baseline. Es wird genau eine Referenz-Cloud
umgesetzt. Echte Multi-Cloud-Unterstuetzung wird nicht gebaut.

Die konkrete Cloud wird spaetestens am 31. August 2026 durch einen eigenen ADR
ausgewaehlt:

```text
docs/15-decisions/adr/adr-004-select-reference-cloud.md
```

Die aktuelle Praeferenz ist Azure. Das ist noch keine endgueltige Entscheidung.
EU-Region, Secret Management, Kostenkontrolle und Abschaltbarkeit sind
Pflichtkriterien fuer die spaetere Auswahl.

Managed PostgreSQL ist fuer den Portfolio-Release kein Pflichtbestandteil.
Infrastructure as Code wird erst mit dem konkreten Cloud-Deployment eingefuehrt.
AI-Funktionalitaet und Evaluation haben Vorrang vor Infrastrukturbreite.

## Alternatives considered

Rein lokaler Betrieb: Diese Variante ist einfach, kostenguenstig und sehr gut
reproduzierbar. Sie ist fuer Datenschutz und Tests attraktiv, liefert aber
einen schwaecheren Deployment-Nachweis fuer das Portfolio.

Azure sofort festlegen: Diese Variante passt potenziell gut zum deutschen
B2B- und Microsoft-Umfeld. Sie ist aktuell trotzdem verfrueht, weil Account,
Dienstzugang, Kosten, Modellzugang und Zielstellenprofil noch verbindlich
verglichen werden muessen.

AWS sofort festlegen: Diese Variante waere technisch tragfaehig und auf dem
Arbeitsmarkt relevant. Sie ist aktuell ebenfalls verfrueht, solange nicht klar
ist, dass AWS fuer die Zielstellen und den verfuegbaren Zugang die bessere
Referenzplattform ist.

Echte Multi-Cloud-Unterstuetzung: Diese Variante wuerde Lock-in formal
reduzieren, waere fuer eine einzelne entwickelnde Person aber
unverhaeltnismaessig aufwendig. Sie wuerde den Fokus von AI-Qualitaet,
Evaluation und Human-Review-Grenzen auf Infrastrukturabstraktionen verschieben.

Hybridbetrieb: Diese Variante kann fuer reale Kanzlei- oder
On-Premises-Szenarien spaeter interessant sein. Fuer den Portfolio-Release 2026
ist sie unnoetig komplex.

Eine spaetere Referenz-Cloud: Diese Variante bietet die beste Balance aus
lokaler Reproduzierbarkeit, geringer Cloud-Kopplung, spaeterem
Deployment-Nachweis und sichtbarem AI-Engineering-Fokus.

## Consequences

Positive Folgen:

- lokale Reproduzierbarkeit bleibt erhalten
- geringe Cloud-Kopplung im Anwendungskern
- klare Systemgrenzen fuer Provider, Secrets, Deployment und Observability
- spaetere echte Deployment-Demo bleibt moeglich
- AI-Fokus bleibt sichtbar

Bewusst akzeptierte Nachteile:

- nur eine Cloud wird praktisch demonstriert
- Cloud-spezifische Tiefe kommt erst spaeter
- ein spaeterer Cloudadapter und IaC-Stack bleiben notwendig

Diese Entscheidung fuehrt keine produktiven Daten, keine produktiven
Integrationen, keine Steuerberatung durch das Modell und keine produktive
Cloud-Nutzung ein.

## Revisit conditions

Diese Entscheidung wird neu bewertet bei:

- deutlicher AWS-Dominanz im relevanten Stellenmarkt
- technischer oder wirtschaftlicher Nichtverfuegbarkeit von Azure
- neuen Anforderungen mit echten Daten
- wesentlicher Aenderung des Portfolioziels
- Verzug des Cloud-Meilensteins um mehr als zwei Wochen
