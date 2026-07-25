# ADR 004: Select AWS as the single reference cloud

## Status

Accepted

## Context

ADR 003 legt fest, dass genau eine Referenz-Cloud umgesetzt wird, der
Anwendungskern cloud-neutral bleibt und die konkrete Plattform spaetestens am
31. August 2026 in einem eigenen ADR ausgewaehlt wird. Die fruehere Praeferenz
war Azure; das war keine endgueltige Entscheidung.

Phase 4 liefert die lokale FastAPI- und Docker-Demo. Der naechste Schritt ist
der minimale Cloud-Deployment-Nachweis fuer das Portfolio 2026. Dafuer muss die
Plattform verbindlich feststehen, bevor Architektur, Infrastructure as Code und
Observability an Systemraendern geplant werden.

Der Projektinhaber absolviert laufend eine AWS-Ausbildung. Eine zweite parallele
Azure-Einarbeitung wuerde den begrenzten Portfolio-Zeitraum splitten, ohne den
AI-Engineering-Nachweis zu staerken. Modellprovider und Laufzeit-Cloud bleiben
getrennte Entscheidungen; die bestehende OpenAI-Adaptergrenze aendert diese
Cloudwahl nicht.

## Decision

AWS ist die einzige Referenz-Cloud fuer den Portfolio-Release 2026.

Verbindliche Leitplanken:

- genau eine Referenz-Cloud: AWS
- keine Multi-Cloud-Unterstuetzung
- cloud-neutraler Anwendungskern; keine AWS-SDKs im Kern
- AWS-Komponenten nur an Systemraendern (Deployment, Secrets, Cloud Logging,
  Cloud Metrics, Infrastructure as Code)
- Wahl des Modellproviders und Wahl der Laufzeit-Cloud bleiben getrennte
  Entscheidungen
- ausschliesslich synthetische Daten; keine echten Mandanten-, Kanzlei- oder
  Steuerdaten
- EU-Region ist Pflicht; vorgesehene Referenzregion ist `eu-central-1`
- Kostenkontrolle und zuverlaessige Abschaltbarkeit sind Pflicht
- lokale Docker-Demo und offline deterministische Standardtests bleiben der
  sichere Standard

Diese Entscheidung waehlt nur die Cloudplattform und die Leitplanken. Die
konkrete Auswahl zwischen App Runner, ECS Fargate oder anderen AWS-
Laufzeitdiensten gehoert in den spaeteren Architekturbranch und ist hier nicht
entschieden.

## Reasons

AWS wird ausgewaehlt, weil:

1. der Projektinhaber laufend eine AWS-Ausbildung absolviert
2. Ausbildung und praktischer Portfolio-Nachweis damit direkt verbunden bleiben
3. der Kompetenzaufbau konsistent auf einer Plattform liegt statt paralleler
   Azure-Einarbeitung
4. AWS fuer einen kleinen containerisierten Portfolio-Deployment-Nachweis
   technisch geeignet ist

## Alternatives considered

Azure: Technisch tragfaehig und fuer das deutsche B2B-/Microsoft-Umfeld
relevant. Fuer den Portfolio-Release 2026 bewusst nicht gewaehlt, weil die
laufende AWS-Ausbildung den groesseren praktischen Nutzen liefert und eine
zweite Cloud-Einarbeitung den Fokus und die Zeitreserve unnoetig belasten
wuerde. Azure bleibt eine spaeter erneut bewertbare Alternative, nicht der
Referenzpfad 2026.

Rein lokaler Betrieb ohne Referenz-Cloud: Behaelt maximale Einfachheit, liefert
aber keinen ausreichenden Deployment-Nachweis fuer das Portfolio.

Multi-Cloud: Unverhaeltnismaessig aufwendig fuer eine einzelne entwickelnde
Person und laut ADR 003 sowie Roadmap explizit kein Ziel.

## Consequences

Positive Folgen:

- klare Plattformbasis fuer Phase 5
- Ausbildung und Portfolio-Nachweis laufen auf derselben Cloud
- Anwendungskern bleibt cloud-neutral
- lokale Offline- und Docker-Standards bleiben erhalten

Bewusst akzeptierte Nachteile:

- nur AWS wird praktisch demonstriert
- Azure-Tiefe wird im Portfolio 2026 nicht aufgebaut
- spaetere Architektur- und IaC-Arbeit muss die konkreten AWS-Dienste noch
  festlegen

Diese Entscheidung erzeugt keine AWS-Ressourcen, keine Credentials, kein SDK,
kein IaC und keine Aenderung an Produktionscode, Dockerfile, CI oder Tests.

## Non-goals

Diese Entscheidung entscheidet nicht:

- App Runner versus ECS Fargate oder andere konkrete Laufzeitdienste
- Secret-Store-, Logging- oder Metrics-Implementierung
- Infrastructure as Code
- Modellprovider-Wahl
- Multi-Cloud-Abstraktionen

## Revisit conditions

Diese Entscheidung wird neu bewertet bei:

- Wegfall des AWS-Zugangs oder der Ausbildungspraxis
- technischer oder wirtschaftlicher Nichtverfuegbarkeit von AWS fuer den
  geplanten Minimalumfang
- neuen Anforderungen mit echten Daten
- wesentlicher Aenderung des Portfolioziels
- Verzug des Cloud-Meilensteins um mehr als zwei Wochen
