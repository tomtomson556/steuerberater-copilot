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

Dieses Dokument gibt genau einen read-only AWS-Dokumentationszugang fuer
Entwicklungsagenten frei. Es konfiguriert keinen MCP-Server im Repository und
aktiviert keine produktive Schnittstelle.

Der MCP ist ausschliesslich eine Recherchehilfe fuer Entwicklungsarbeit. Er ist
keine Anwendungskomponente und kein Bestandteil der Runtime. Die vorliegende
Freigabe umfasst ausschliesslich die unauthentifizierte read-only
Dokumentationsnutzung. In dieser freigegebenen Nutzung wird keine Verbindung zu
einem AWS-Konto hergestellt. Authentifizierte AWS-API-, Skript- oder
Kontofunktionen des Servers sind nicht freigegeben und duerfen nicht verwendet
werden.

MCP-Tools duerfen das **Policy- und Privacy-Gateway** nicht umgehen und keine
vertraulichen oder abgeleiteten vertraulichen Inhalte an Public-LLMs
weitergeben.

## Freigegebener AWS-Dokumentationszugang

Freigegeben ist ausschliesslich:

- Zweck: read-only Recherche in aktueller oeffentlicher offizieller
  AWS-Dokumentation und regionalen AWS-Serviceinformationen
- Endpoint: `https://aws-mcp.eu-central-1.api.aws/mcp`
- Fragen: ausschliesslich oeffentliche Dokumentationsfragen ohne vertraulichen
  Projekt-, Mandanten-, Kanzlei-, Steuer- oder Betriebsinhalt
- Werkzeuge: ausschliesslich read-only Dokumentationssuche, Lesen von
  Dokumentationsseiten und Abfrage oeffentlicher regionaler
  Serviceverfuegbarkeit

Die Freigabe ist zweck- und werkzeuggebunden. Weitere von einem Client oder
Server angezeigte Werkzeuge sind dadurch nicht freigegeben und duerfen nicht
verwendet werden.

## Verbindliche Nutzungsgrenzen

Der Zugang erfolgt ohne AWS-Authentifizierung. Nicht erlaubt sind:

- AWS-Profile, Access Keys, Tokens, Secrets oder Zertifikate
- OAuth-Anmeldung oder eine andere AWS-Anmeldung
- AWS-API-Aufrufe
- Konto-, Organisations- oder Resource-Discovery
- Skriptausfuehrung
- Ausfuehrung von Infrastructure as Code
- Schreibwerkzeuge oder zustandsaendernde Werkzeuge
- automatische Toolfreigaben
- vertrauliche oder abgeleitete vertrauliche Inhalte in Fragen,
  Toolargumenten oder Ergebnissen
- Fragen ausserhalb oeffentlicher offizieller AWS-Dokumentation und
  oeffentlicher regionaler Serviceinformationen

Lokale Clientkonfigurationen bleiben persoenliche Benutzerkonfigurationen
ausserhalb des Repositories. Es werden insbesondere keine Workspace-MCP-
Konfigurationen, Credentials oder Toolfreigaben eingecheckt.

## Recherche und Architekturentscheidungen

Zeitabhaengige oder servicespezifische AWS-Architekturbehauptungen muessen
gegen aktuelle offizielle AWS-Quellen geprueft werden. Architektur- und
Entscheidungsdokumente muessen die verwendeten Quellen nachvollziehbar nennen.

MCP-Ergebnisse sind nur Recherchegrundlage. Sie treffen keine automatische
Architekturentscheidung und geben keinen AWS-Dienst, kein Deploymentmodell und
keine Infrastructure-as-Code-Technologie fuer das Projekt frei.

## Verboten

Nicht erlaubt sind:

- produktive Agenda-MCPs
- produktive ELSTER-MCPs
- produktive Datenbank-, Storage- oder Cloud-MCPs
- MCPs mit echten Mandanten-, Beleg-, Steuer-, Kanzlei- oder Metadaten
- MCPs mit abgeleiteten vertraulichen Inhalten
- MCPs mit Secrets, Tokens, Zugangsdaten oder Zertifikaten im Repository
- Schreibtools auf produktive Systeme
- MCP-Tools, die steuerlich wirksame Handlungen ohne Kanzlei-Freigabe ausloesen
  koennen
- MCP-Tools, die Public-LLMs mit vertraulichen oder abgeleiteten vertraulichen
  Inhalten versorgen

## Später separat möglich

Spaeter koennen in separaten PRs geprueft werden:

- Policy-MCP mit freigegebenen, versionierten Policies
- Tax-Source-MCP mit freigegebenen, versionierten Quellen

Solche Erweiterungen duerfen nur nach eigener PR, Human Review, dokumentierten
Tests und expliziter Sicherheitsbewertung eingefuehrt werden.

## Human Review

MCP darf keine steuerlichen Entscheidungen automatisieren. Steuerlich
relevante Ergebnisse bleiben Entwuerfe und benoetigen Human Review durch die
Kanzlei.

## Verwandte Dokumentation

Die persoenliche Einrichtung und der manuelle Entwicklungsnachweis sind in
[aws-documentation-mcp-setup.md](aws-documentation-mcp-setup.md) dokumentiert.
