# AWS Documentation MCP Setup and Verification

## Zweck und Abgrenzung

Der AWS-Dokumentations-MCP unter
`https://aws-mcp.eu-central-1.api.aws/mcp` dient Entwicklungsagenten
ausschliesslich zur read-only Recherche in oeffentlicher offizieller
AWS-Dokumentation und oeffentlichen regionalen Serviceinformationen.

Er ist keine Anwendungskomponente. Die vorliegende Freigabe umfasst
ausschliesslich die unauthentifizierte read-only Dokumentationsnutzung. In
dieser freigegebenen Nutzung wird keine Verbindung zu einem AWS-Konto
hergestellt. Authentifizierte AWS-API-, Skript- oder Kontofunktionen des
Servers sind nicht freigegeben und duerfen nicht verwendet werden.
Resource-Discovery, Infrastructure as Code und Schreiboperationen bleiben
ebenfalls ausgeschlossen.

Die verbindlichen Nutzungsgrenzen stehen in
[agent-mcp-boundaries.md](agent-mcp-boundaries.md).

## Persoenliche Clientkonfiguration

Der Endpoint wird als entfernter HTTP-MCP-Server ausschliesslich in der
persoenlichen Benutzerkonfiguration des jeweiligen Clients eingetragen:

| Client oder Erweiterung | Persoenlicher Konfigurationsort |
| --- | --- |
| VS Code mit GitHub Copilot Chat und DeepSeek-Copilot-Erweiterung | globale VS-Code-MCP-Benutzerkonfiguration |
| Codex-VS-Code-Erweiterung | persoenliche Codex-Konfiguration; Codex-IDE und Codex-CLI teilen die benutzerbezogene `config.toml` |
| Cursor-Terminalagent | persoenliche Cursor-MCP-Konfiguration |

Fuer Codex beschreibt die
[offizielle MCP-Dokumentation](https://learn.chatgpt.com/docs/extend/mcp), dass
IDE-Erweiterung und CLI dieselbe persoenliche Konfiguration verwenden.

Fuer alle Clients gelten dieselben Einrichtungsgrenzen:

- keine AWS-Authentifizierung konfigurieren
- keine AWS-Profile, Access Keys, Tokens oder OAuth-Anmeldung hinterlegen
- keine automatischen Toolfreigaben aktivieren
- nur die read-only Werkzeuge fuer Dokumentationssuche, Lesen und regionale
  Serviceverfuegbarkeit verwenden
- weitere angezeigte Werkzeuge weder freigeben noch verwenden

Dieser Branch legt keine Workspace-Konfiguration an. Insbesondere werden keine
`.vscode/mcp.json`, `.cursor/mcp.json`, Codex-Konfigurationsdateien,
persoenlichen Home-Verzeichnisdateien oder Credentials in das Repository
aufgenommen.

## Codespaces

Die Benutzerkonfigurationen liegen ausserhalb des Repositories. Nach einem
Codespace-Rebuild oder in einem neuen Codespace koennen die persoenliche
Konfiguration und eine erneute manuelle Verifikation erforderlich sein.

Eine fehlende oder verlorene Benutzerkonfiguration darf nicht durch eine
eingecheckte Workspace-Konfiguration ersetzt werden.

## Manuelle Verifikation

Nach der persoenlichen Einrichtung wird fuer jeden verwendeten Agenten manuell
geprueft:

1. Der Endpoint ist erreichbar.
2. Werkzeuge fuer Dokumentationssuche, Lesen und regionale Verfuegbarkeit
   werden erkannt.
3. Eine ausschliesslich oeffentliche AWS-Dokumentationsfrage liefert eine
   offizielle AWS-Quelle.
4. Die regionale Abfrage benoetigt weder AWS-Anmeldung noch AWS-API-Aufruf.
5. Es wird kein nicht freigegebenes Werkzeug verwendet oder automatisch
   freigegeben.

Diese Verifikation ist kein Standardtest, kein CI-Test und keine Zusicherung
der dauerhaften Verfuegbarkeit des externen MCP-Servers.

## Manueller Smoke-Test vom 25. Juli 2026

Ergebnis des bereits manuell ausgefuehrten Entwicklungsnachweises:

- Alle drei verwendeten Entwicklungsagenten konnten den
  AWS-Dokumentationszugang nutzen.
- Mindestens die Werkzeuge fuer Dokumentationssuche, Lesen und regionale
  Serviceverfuegbarkeit wurden erkannt.
- Amazon ECS Express Mode und seine Verfuegbarkeit in `eu-central-1` wurden
  anhand offizieller AWS-Dokumentation und regionaler Serviceinformationen
  geprueft.
- Es wurden keine AWS-Credentials und keine AWS-API-Aufrufe verwendet.

Verwendete offizielle AWS-Quellen:

- [Amazon ECS Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
- [Amazon ECS endpoints and quotas](https://docs.aws.amazon.com/general/latest/gr/ecs-service.html)
- [Supported Regions for Amazon ECS on AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate-Regions.html)
- [AWS Services by Region](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)

Die ECS-Dokumentation beschreibt Express Mode als in den AWS-Regionen
verfuegbar, in denen Amazon ECS und AWS Fargate unterstuetzt werden. Die
regionale read-only Abfrage meldete Amazon ECS und AWS Fargate am Testdatum
fuer `eu-central-1` als verfuegbar.

Der Nachweis belegt nur das manuelle Ergebnis vom 25. Juli 2026. Er behauptet
weder automatisierte noch dauerhafte Verfuegbarkeit des externen MCP-Servers
und trifft keine Architekturentscheidung fuer ECS Express Mode, Fargate,
CloudFormation oder einen anderen Deploymentdienst.
