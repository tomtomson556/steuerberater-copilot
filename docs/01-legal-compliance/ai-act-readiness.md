# AI Act Readiness

## Zweck und Reichweite

Dieses Dokument beschreibt den internen **AI Act readiness**-Vorbereitungsstand des **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Es ist keine Rechtsberatung, keine Konformitätszusage und keine abschließende Systemklassifizierung. Es dient der Orientierung für Entwicklung, Review und spätere Governance-Arbeit.

## Quellenstand

**Prüfdatum:** 2026-06-23

Die folgenden Hinweise dienen der Orientierung, nicht als Rechtsgutachten. Vor produktionsnaher Nutzung sind Quellenstand, Fristen und Einordnung erneut zu prüfen.

| Hinweis | Kurzbeschreibung |
| --- | --- |
| Regulation (EU) 2024/1689 | EU-KI-Verordnung (AI Act) |
| Inkrafttreten | 1. August 2024 |
| Vollständige Anwendbarkeit | grundsätzlich ab 2. August 2026, mit Ausnahmen für bestimmte Regelungsbereiche |
| AI Literacy | Pflichten für Anbieter und Betreiber der KI-Systeme seit 2. Februar 2025 |

Offizielle Referenz: [Regulation (EU) 2024/1689 (EUR-Lex)](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32024R1689)

Finale Bewertung, Rollenklärung und weitere Fristen sind vor produktionsnaher Nutzung erneut zu prüfen.

## Projektbezogene Ausgangsposition

Der Steuerberater-Copilot ist als **Steuer-Vorbereitungsassistent** und Vorbereitungssystem konzipiert:

- kein autonomes Entscheidungssystem
- keine individuelle Steuerberatung durch das Modell
- keine produktiven Schreibzugriffe in Agenda, ELSTER oder Mandantensysteme
- keine echten vertraulichen Inhalte in **Public-LLMs**
- Kontrolle vor und neben dem Modell, insbesondere über **Human Review** und das **Policy- und Privacy-Gateway**

## Vorläufige AI-Act-Readiness-Prinzipien

Im Projekt gelten vorläufig diese Readiness-Prinzipien:

| Prinzip | Kurzbeschreibung |
| --- | --- |
| Transparenz | KI-Unterstützung erkennbar machen; siehe `ai-transparency-policy.md` |
| Human Review | steuerlich relevante Ergebnisse bleiben Entwürfe mit Pflichtprüfung |
| Entwurfscharakter | keine steuerlich wirksame Handlung ohne Kanzlei-Freigabe |
| Dokumentation | Quellen, Policies und Modellversionen nachvollziehbar halten |
| Versionskontrolle | Policies und Freigaben versionieren |
| AI Literacy | für beteiligte Nutzer und Betreiber später operationalisieren |
| Release-Gates | keine produktive Nutzung ohne dokumentierte Freigaben |

Diese Prinzipien beschreiben den **Vorbereitungsstand**, nicht einen abgeschlossenen Compliance-Nachweis.

## Offene Punkte für spätere PRs

Folgende Themen sind bewusst nicht Gegenstand dieses Dokuments:

- finale Rollenklärung: Provider, Deployer, Betreiber, Kanzlei, technischer Dienstleister
- Risikoklassifizierung
- technische Dokumentation im Detail
- Logging und Auditierbarkeit im Detail
- Data Governance
- Human-Oversight-Prozess im Detail
- Post-Market- beziehungsweise Betriebsüberwachung, soweit einschlägig
- Incident- beziehungsweise Meldeprozesse, soweit einschlägig

## Nicht-Zusicherungen

Dieses Dokument sagt ausdrücklich nicht aus, dass:

- das System bereits den Anforderungen des AI Act vollständig genügt
- ein produktiver Einsatz zulässig ist
- eine abschließende rechtliche oder regulatorische Einordnung vorliegt

Verbindliche Bewertung obliegt der Kanzlei beziehungsweise beauftragten Fachstellen.

## Verhältnis zu späteren Dokumenten

| Thema | Ort |
| --- | --- |
| Risk Classification | separater PR / `docs/07-risk-classification/` |
| Data Governance | separater PR / `docs/12-data-governance/` |
| Release Governance | separater PR / `docs/11-release-governance/` |
| Architektur / ADR | separater PR / `docs/15-decisions/adr/` |
| AI-Transparenz | `ai-transparency-policy.md` |
| Rechtliche Systemgrenzen | `legal-boundaries.md` |
