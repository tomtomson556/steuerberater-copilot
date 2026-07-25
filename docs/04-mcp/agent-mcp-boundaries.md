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

Dieses Dokument gibt genau einen read-only AWS-Dokumentationszugang für
Entwicklungsagenten frei. Es konfiguriert keinen MCP-Server im Repository und
aktiviert keine produktive Schnittstelle.

Der MCP ist ausschließlich eine Recherchehilfe für Entwicklungsarbeit. Er ist
keine Anwendungskomponente und kein Bestandteil der Runtime. Die vorliegende
Freigabe umfasst ausschließlich die unauthentifizierte read-only
Dokumentationsnutzung. In dieser freigegebenen Nutzung wird keine Verbindung zu
einem AWS-Konto hergestellt. Authentifizierte AWS-API-, Skript- oder
Kontofunktionen des Servers sind nicht freigegeben und dürfen nicht verwendet
werden.

MCP-Tools dürfen das **Policy- und Privacy-Gateway** nicht umgehen und keine
vertraulichen oder abgeleiteten vertraulichen Inhalte an Public-LLMs
weitergeben.

## Freigegebener AWS-Dokumentationszugang

Freigegeben ist ausschließlich:

- Zweck: read-only Recherche in aktueller öffentlicher offizieller
  AWS-Dokumentation und regionalen AWS-Serviceinformationen
- Endpoint: `https://aws-mcp.eu-central-1.api.aws/mcp`
- Fragen: ausschließlich öffentliche Dokumentationsfragen ohne vertraulichen
  Projekt-, Mandanten-, Kanzlei-, Steuer- oder Betriebsinhalt
- Werkzeuge: ausschließlich read-only Dokumentationssuche, Lesen von
  Dokumentationsseiten und Abfrage öffentlicher regionaler
  Serviceverfügbarkeit

Die Freigabe ist zweck- und werkzeuggebunden. Weitere von einem Client oder
Server angezeigte Werkzeuge sind dadurch nicht freigegeben und dürfen nicht
verwendet werden.

## Verbindliche Nutzungsgrenzen

Der Zugang erfolgt ohne AWS-Authentifizierung. Nicht erlaubt sind:

- AWS-Profile, Access Keys, Tokens, Secrets oder Zertifikate
- OAuth-Anmeldung oder eine andere AWS-Anmeldung
- AWS-API-Aufrufe
- Konto-, Organisations- oder Resource-Discovery
- Skriptausführung
- Ausführung von Infrastructure as Code
- Schreibwerkzeuge oder zustandsändernde Werkzeuge
- automatische Toolfreigaben
- vertrauliche oder abgeleitete vertrauliche Inhalte in Fragen,
  Toolargumenten oder Ergebnissen
- Fragen außerhalb öffentlicher offizieller AWS-Dokumentation und
  öffentlicher regionaler Serviceinformationen

Lokale Clientkonfigurationen bleiben persönliche Benutzerkonfigurationen
außerhalb des Repositories. Es werden insbesondere keine Workspace-MCP-
Konfigurationen, Credentials oder Toolfreigaben eingecheckt.

## Recherche und Architekturentscheidungen

Zeitabhängige oder servicespezifische AWS-Architekturbehauptungen müssen
gegen aktuelle offizielle AWS-Quellen geprüft werden. Architektur- und
Entscheidungsdokumente müssen die verwendeten Quellen nachvollziehbar nennen.

MCP-Ergebnisse sind nur Recherchegrundlage. Sie treffen keine automatische
Architekturentscheidung und geben keinen AWS-Dienst, kein Deploymentmodell und
keine Infrastructure-as-Code-Technologie für das Projekt frei.

## Verboten

Nicht erlaubt sind:

- produktive Agenda-MCPs
- produktive ELSTER-MCPs
- produktive Datenbank-, Storage- oder Cloud-MCPs
- MCPs mit echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten
- MCPs mit abgeleiteten vertraulichen Inhalten
- MCPs mit Secrets, Tokens, Zugangsdaten oder Zertifikaten im Repository
- Schreibtools auf produktive Systeme
- MCP-Tools, die steuerlich wirksame Handlungen ohne Kanzlei-Freigabe auslösen
  können
- MCP-Tools, die Public-LLMs mit vertraulichen oder abgeleiteten vertraulichen
  Inhalten versorgen

## Später separat möglich

Später können in separaten PRs geprüft werden:

- Policy-MCP mit freigegebenen, versionierten Policies
- Tax-Source-MCP mit freigegebenen, versionierten Quellen

Solche Erweiterungen dürfen nur nach eigener PR, Human Review, dokumentierten
Tests und expliziter Sicherheitsbewertung eingeführt werden.

## Human Review

MCP darf keine steuerlichen Entscheidungen automatisieren. Steuerlich
relevante Ergebnisse bleiben Entwürfe und benötigen Human Review durch die
Kanzlei.

## Verwandte Dokumentation

Die persönliche Einrichtung und der manuelle Entwicklungsnachweis sind in
[aws-documentation-mcp-setup.md](aws-documentation-mcp-setup.md) dokumentiert.
