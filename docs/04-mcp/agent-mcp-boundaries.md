# Agent MCP Boundaries

## Zweck

Dieses Dokument beschreibt MCP-Grenzen für Agentenarbeit im Codespace des **Steuerberater-Copilot** / **Steuer-Vorbereitungsassistent**.

Zentrale Agentenregeln und Pflichtworkflows stehen in `AGENTS.md`.

Verbindliches Leitbild:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Klarstellung

Diese PR konfiguriert keine MCP-Server und aktiviert keine produktiven Schnittstellen.

MCP ist in diesem Projekt zunächst nur dokumentativ oder read-only für öffentliche oder ausdrücklich freigegebene Dokumentationsquellen denkbar. Jede konkrete MCP-Nutzung benötigt eine eigene spätere PR mit Review, Tests und klarer Sicherheitsbewertung.

MCP-Tools dürfen das **Policy- und Privacy-Gateway** nicht umgehen und keine vertraulichen Inhalte an Public-LLMs weitergeben.

## Verboten

Nicht erlaubt sind:

- produktive Agenda-MCPs
- produktive ELSTER-MCPs
- produktive Datenbank-, Storage- oder Cloud-MCPs
- MCPs mit echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten
- MCPs mit abgeleiteten vertraulichen Inhalten
- MCPs mit Secrets, Tokens, Zugangsdaten oder Zertifikaten im Repository
- Schreibtools auf produktive Systeme
- MCP-Tools, die steuerlich wirksame Handlungen ohne Kanzlei-Freigabe auslösen können
- MCP-Tools, die Public-LLMs mit vertraulichen oder abgeleiteten vertraulichen Inhalten versorgen

## Später separat möglich

Später können in separaten PRs geprüft werden:

- Read-only-Dokumentations-MCPs
- Policy-MCP mit freigegebenen, versionierten Policies
- Tax-Source-MCP mit freigegebenen, versionierten Quellen

Solche Erweiterungen dürfen nur nach eigener PR, Human Review, dokumentierten Tests und expliziter Sicherheitsbewertung eingeführt werden.

## Human Review

MCP darf keine steuerlichen Entscheidungen automatisieren. Steuerlich relevante Ergebnisse bleiben Entwürfe und benötigen Human Review durch die Kanzlei.
