# AWS Documentation MCP Setup and Verification

## Zweck und Abgrenzung

Der AWS-Dokumentations-MCP unter
`https://aws-mcp.eu-central-1.api.aws/mcp` dient Entwicklungsagenten
ausschließlich zur read-only Recherche in öffentlicher offizieller
AWS-Dokumentation und öffentlichen regionalen Serviceinformationen.

Er ist keine Anwendungskomponente. Die vorliegende Freigabe umfasst
ausschließlich die unauthentifizierte read-only Dokumentationsnutzung. In
dieser freigegebenen Nutzung wird keine Verbindung zu einem AWS-Konto
hergestellt. Authentifizierte AWS-API-, Skript- oder Kontofunktionen des
Servers sind nicht freigegeben und dürfen nicht verwendet werden.
Resource-Discovery, Infrastructure as Code und Schreiboperationen bleiben
ebenfalls ausgeschlossen.

Die verbindlichen Nutzungsgrenzen stehen in
[agent-mcp-boundaries.md](agent-mcp-boundaries.md).

## Persönliche Clientkonfiguration

Der Endpoint wird als entfernter HTTP-MCP-Server ausschließlich in der
persönlichen Benutzerkonfiguration des jeweiligen Clients eingetragen:

| Client oder Erweiterung | Persönlicher Konfigurationsort |
| --- | --- |
| VS Code mit GitHub Copilot Chat und DeepSeek-Copilot-Erweiterung | globale VS-Code-MCP-Benutzerkonfiguration |
| Codex-VS-Code-Erweiterung | persönliche Codex-Konfiguration; Codex-IDE und Codex-CLI teilen die benutzerbezogene `config.toml` |
| Cursor-Terminalagent | persönliche Cursor-MCP-Konfiguration |

Für Codex beschreibt die
[offizielle MCP-Dokumentation](https://learn.chatgpt.com/docs/extend/mcp), dass
IDE-Erweiterung und CLI dieselbe persönliche Konfiguration verwenden.

Für alle Clients gelten dieselben Einrichtungsgrenzen:

- keine AWS-Authentifizierung konfigurieren
- keine AWS-Profile, Access Keys, Tokens oder OAuth-Anmeldung hinterlegen
- keine automatischen Toolfreigaben aktivieren
- nur die read-only Werkzeuge für Dokumentationssuche, Lesen und regionale
  Serviceverfügbarkeit verwenden
- weitere angezeigte Werkzeuge weder freigeben noch verwenden

Dieser Branch legt keine Workspace-Konfiguration an. Insbesondere werden keine
`.vscode/mcp.json`, `.cursor/mcp.json`, Codex-Konfigurationsdateien,
persönlichen Home-Verzeichnisdateien oder Credentials in das Repository
aufgenommen.

## Codespaces

Die Benutzerkonfigurationen liegen außerhalb des Repositories. Nach einem
Codespace-Rebuild oder in einem neuen Codespace können die persönliche
Konfiguration und eine erneute manuelle Verifikation erforderlich sein.

Eine fehlende oder verlorene Benutzerkonfiguration darf nicht durch eine
eingecheckte Workspace-Konfiguration ersetzt werden.

## Manuelle Verifikation

Nach der persönlichen Einrichtung wird für jeden verwendeten Agenten manuell
geprüft:

1. Der Endpoint ist erreichbar.
2. Werkzeuge für Dokumentationssuche, Lesen und regionale Verfügbarkeit
   werden erkannt.
3. Eine ausschließlich öffentliche AWS-Dokumentationsfrage liefert eine
   offizielle AWS-Quelle.
4. Die regionale Abfrage benötigt weder AWS-Anmeldung noch AWS-API-Aufruf.
5. Es wird kein nicht freigegebenes Werkzeug verwendet oder automatisch
   freigegeben.

Diese Verifikation ist kein Standardtest, kein CI-Test und keine Zusicherung
der dauerhaften Verfügbarkeit des externen MCP-Servers.

## Manueller Smoke-Test vom 25. Juli 2026

Ergebnis des bereits manuell ausgeführten Entwicklungsnachweises:

- Alle drei verwendeten Entwicklungsagenten konnten den
  AWS-Dokumentationszugang nutzen.
- Mindestens die Werkzeuge für Dokumentationssuche, Lesen und regionale
  Serviceverfügbarkeit wurden erkannt.
- Amazon ECS Express Mode und seine Verfügbarkeit in `eu-central-1` wurden
  anhand offizieller AWS-Dokumentation und regionaler Serviceinformationen
  geprüft.
- Es wurden keine AWS-Credentials und keine AWS-API-Aufrufe verwendet.

Verwendete offizielle AWS-Quellen:

- [Amazon ECS Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
- [Amazon ECS endpoints and quotas](https://docs.aws.amazon.com/general/latest/gr/ecs-service.html)
- [Supported Regions for Amazon ECS on AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate-Regions.html)
- [AWS Services by Region](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/)

Die ECS-Dokumentation beschreibt Express Mode als in den AWS-Regionen
verfügbar, in denen Amazon ECS und AWS Fargate unterstützt werden. Die
regionale read-only Abfrage meldete Amazon ECS und AWS Fargate am Testdatum
für `eu-central-1` als verfügbar.

Der Nachweis belegt nur das manuelle Ergebnis vom 25. Juli 2026. Er behauptet
weder automatisierte noch dauerhafte Verfügbarkeit des externen MCP-Servers
und trifft keine Architekturentscheidung für ECS Express Mode, Fargate,
CloudFormation oder einen anderen Deploymentdienst.
