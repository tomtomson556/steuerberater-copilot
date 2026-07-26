# AWS Reference Cloud Deployment Architecture

## Zweck und Status

Dieses Dokument legt die kleinstmögliche konkrete AWS-Referenzarchitektur für
die bestehende stateless FastAPI-/Docker-Demo fest. Es ist die verbindliche
Grundlage für den nächsten Produktionsbranch
`feat/add-reference-cloud-infrastructure`.

Dieser Branch enthält ausschließlich Dokumentation. Er erzeugt keine
AWS-Ressourcen, kein Infrastructure as Code, keine SDK-Integration und keine
Anwendungscode-Änderung.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Leitentscheidungen bleiben ADR-003 und ADR-004:

- [adr-003-local-first-cloud-neutral-single-reference-cloud.md](../15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md)
- [adr-004-select-reference-cloud.md](../15-decisions/adr/adr-004-select-reference-cloud.md)

## Scope und Non-Goals

In Scope:

- ein Containerdienst
- ein Secret Store (AWS Secrets Manager) als verbindlicher IaC-Bestandteil mit
  konditionalem Opt-in
- Health Check
- Logging-Senke
- EU-Region sowie Kosten- und Abschaltkontrolle
- Daten-, Secret-, Netzwerk- und Vertrauensgrenzen
- Abgrenzung cloud-neutraler Kern versus AWS-Systemrand
- konkrete CloudFormation-Vorgabe inklusive zweistufigem Bootstrap für den
  IaC-Branch

Nicht in Scope (dieser und der unmittelbare Folge-Branch):

- Infrastructure as Code oder AWS-Ressourcen in diesem Dokumentationsbranch
- AWS-SDK im Anwendungskern
- Multi-Cloud
- Kubernetes
- Datenbank oder Persistenz
- Authentifizierung
- eigene VPC- oder ALB-Architektur
- erweitertes Monitoring oder Dashboards
- echte Secret-Werte im Repository

## Bestehende lokale Baseline

Die Cloud-Referenz bildet die vorhandene lokale Demo ab, ändert sie aber nicht:

| Lokal | Cloud-Mapping |
| --- | --- |
| Dockerfile, Port `8000` | Express-Mode-`containerPort` `8000` |
| `GET /health` | ALB-Health-Check-Pfad `/health` |
| `FakeModelProvider` als sicherer Standard | bleibt Default; keine Secret-Injection |
| synthetische Fixtures | ausschließlich synthetische Daten |
| kein Secret im Image | weiterhin keine Secrets im Image |

## Festgelegte Architektur

Region: `eu-central-1` (ADR-004).

| Baustein | Entscheidung |
| --- | --- |
| Containerdienst | Amazon ECS Express Mode |
| Image-Quelle | Amazon ECR (privat) |
| Image-Referenz | unveränderlicher Digest; nicht `latest` |
| Secret Store | AWS Secrets Manager als verbindlicher Template-Bestandteil; Default ohne Injection |
| Health Check | ALB-Pfad `/health`, Container-Port `8000` |
| Logging | Stackverwaltete `AWS::Logs::LogGroup` mit `RetentionInDays: 14`, referenziert in `PrimaryContainer.AwsLogsConfiguration` inkl. `LogStreamPrefix` |
| Skalierung | `MinTaskCount: 1`, `MaxTaskCount: 1` (höchstens `2`) |
| Netzwerk-Voraussetzung | Default-VPC mit mindestens zwei öffentlichen Subnetzen in mindestens zwei Availability Zones und mindestens acht freien IP-Adressen je Subnetz |
| ECR-Löschung | `EmptyOnDelete: true` am stackverwalteten Repository (nur kurzlebige Portfolio-Demo) |
| Bootstrap | Zweistufig im selben Stack: zuerst ECR/IAM/Log Group, danach Express Service mit Image-Digest |
| IaC | AWS CloudFormation mit `AWS::ECS::ExpressGatewayService` |

### Warum ECS Express Mode

AWS App Runner ist für Neukunden geschlossen. AWS empfiehlt Amazon ECS Express
Mode als Nachfolger. Offizielle AWS-Seiten nennen unterschiedliche Stichtage;
dieses Dokument hält deshalb keinen konkreten Schließungsstichtag fest.

ECS Express Mode: Image plus zwei IAM-Rollen reichen für einen
Fargate-basierten Web-/API-Dienst mit HTTPS-URL, Load Balancer, Scaling und
Networking. Express Mode automatisiert die unterstützenden Ressourcen; sie
entstehen im eigenen Account und bleiben einsehbar.

Quellen:

- [AWS App Runner availability change](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)
- [Amazon ECS Express Mode overview](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
- [Resources created by Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html)
- [Delete Express Mode services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-delete-task.html)
- [Express Mode best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-best-practices.html)

### Warum nicht die Alternativen

| Alternative | Ablehnung |
| --- | --- |
| AWS App Runner | Für Neukunden geschlossen; AWS empfiehlt ECS Express Mode |
| Handgerolltes ECS Fargate mit eigener VPC/ALB | Unnötig komplex; Express Mode deckt denselben Portfolio-Nachweis ab |
| Kubernetes / EKS | Explizites Roadmap-Non-Goal |
| Multi-Cloud | Explizites ADR-/Roadmap-Non-Goal |

## Systemgrenzen

```text
HTTPS Client
  -> internet-facing ALB (Service Security Group ingress path)
    -> ECS Express Mode / Fargate task (public IP in public default subnet)
      -> FastAPI-Container (cloud-neutraler Kern, FakeModelProvider default)
        -> stdout/stderr
          -> stackverwaltete CloudWatch Log Group
             (RetentionInDays: 14, LogStreamPrefix)

ECR (Image by digest, EmptyOnDelete: true)
  -> Express Mode pull via Task Execution Role
Secrets Manager (template-owned, conditional opt-in)
  -> optional Env-Injection via Task Execution Role
CloudFormation Stack owns Express Mode, ECR, Log Group,
Secrets Manager wiring, and IAM edge resources
```

### Cloud-neutraler Anwendungskern

Im Kern bleiben:

- FastAPI-Demo und Offline-MVP-Workflow
- Gateway, Human Review und Risk-Grenzen
- `FakeModelProvider` als sicherer Standard
- keine AWS-SDKs und keine Cloud-API-Aufrufe der Anwendung

### AWS-Systemrand

Am Systemrand liegen ausschließlich:

- Amazon ECR (stackverwaltet, inkl. `EmptyOnDelete: true`)
- Amazon ECS Express Mode (darunter Fargate-Tasks und von Express Mode
  verwaltete ALB-/Netzwerkressourcen)
- stackverwaltete Amazon CloudWatch Log Group
- AWS Secrets Manager als verbindlicher Template-Bestandteil mit
  konditionalem Opt-in
- IAM-Rollen für Express Mode
- AWS CloudFormation

## Daten-, Secret-, Netzwerk- und Vertrauensgrenzen

### Daten

- ausschließlich synthetische Daten und Fixtures
- keine echten Mandanten-, Kanzlei-, Beleg- oder Steuerdaten
- keine produktiven Schnittstellen

### Secrets

- keine Secrets im Image, Repository, Log oder Prompt
- keine echten Secret-Werte im Repository
- Standardbetrieb: `FakeModelProvider` ohne Secret-Injection
- AWS Secrets Manager ist verbindlicher Bestandteil des IaC-Templates und der
  Roadmap-Vorgabe "ein Secret Store"
- derselbe Stack enthält einen expliziten, konditionalen Opt-in-Pfad für:
  - eine Secrets-Manager-Ressource und/oder
  - eine vorhandene Secret-ARN
  - sowie die zugehörige Container-Injection
- Default-Parameter lassen Secret-Ressource und Injection deaktiviert
- Secret-Injection in den Container benötigt Berechtigungen in der
  **Task Execution Role**
- eine **Task Role** ist nur erforderlich, wenn die Anwendung selbst
  AWS-APIs aufruft; die Standard-Demo tut das nicht

### Netzwerk

- bewusste Voraussetzung: Default-VPC in `eu-central-1` mit mindestens zwei
  öffentlichen Subnetzen in mindestens zwei Availability Zones und mindestens
  acht freien IP-Adressen je Subnetz
- bei öffentlichen Default-Subnetzen aktiviert Express Mode öffentliche IPs
  für die Fargate-Tasks
- die automatisch erzeugte Service Security Group erlaubt standardmäßig
  Internet-Egress
- eingehender Anwendungsverkehr bleibt über den internet-facing ALB und dessen
  Security-Group-Pfad begrenzt
- in diesem Architektur- und dem unmittelbaren IaC-Branch wird keine eigene
  VPC- oder ALB-Architektur entworfen oder als Hand-Template gepflegt

### Vertrauen

- Task Execution Role: Image-Pull aus ECR, Schreibrechte für CloudWatch Logs;
  bei aktiviertem Opt-in zusätzlich Leserechte für Secrets-Manager-Injection
- Infrastructure Role für Express Mode (`ecsInfrastructureRoleForExpressServices`)
- keine AWS-Credentials in Image oder Anwendungskern
- Modellprovider-Wahl und Laufzeit-Cloud bleiben getrennte Entscheidungen

## Kosten- und Abschaltkontrolle

Stack-Delete ist der verlässliche vollständige Abschaltpfad nur dann, wenn
auch die Log Group und das befüllte ECR-Repository tatsächlich
stackverwaltet und löschbar sind. Dafür muss der IaC-Branch:

- eine stackverwaltete `AWS::Logs::LogGroup` mit `RetentionInDays: 14`
  erzeugen und in `PrimaryContainer.AwsLogsConfiguration` referenzieren
- am ECR-Repository `EmptyOnDelete: true` setzen, damit ein befülltes
  Repository den Stack-Delete nicht blockiert

Die von Express Mode automatisch erzeugte Log Group läuft standardmäßig nicht
ab und kann nach dem Löschen des Services erhalten bleiben. Deshalb ist sie
kein ausreichender Abschalt- oder Retention-Pfad für diese Demo.

Bloßes Verringern der Task-Anzahl entfernt Application Load Balancer und
weitere Express-Mode-Randressourcen nicht und gilt nicht als vollständige
Abschaltung.

`EmptyOnDelete: true` ist destruktiv und nur für die kurzlebige synthetische
Portfolio-Demo zulässig.

Zusätzliche Betriebsregeln für den IaC-Branch:

- kleine Skalierungsgrenze: `MinTaskCount: 1`, `MaxTaskCount: 1`
  (höchstens `2`)
- Billing-Budget oder Kostenalarm im Account als organisatorische Kontrolle
- Demo nur bei Bedarf deployen; nach dem Nachweis Stack löschen

## IaC-Vorgabe für `feat/add-reference-cloud-infrastructure`

Der nächste Produktionsbranch setzt einen minimalen CloudFormation-Stack um.
Vorgabe:

### Zweistufiger Bootstrap im selben Stack

Kein Express Service darf vor einem verfügbaren Image-Digest erstellt werden.
Der Ablauf ist verbindlich zweistufig im selben Template:

1. Stack mit ECR, IAM, Log Group und Secrets-Manager-Verdrahtung erstellen,
   jedoch **ohne** Express Service (`DeployService=false`).
2. Image in ECR pushen, unveränderlichen Digest bestimmen und den Stack mit
   aktiviertem Express Service aktualisieren
   (`DeployService=true`, `ImageUri=<repo>@<digest>`).

Dafür sind klare Conditions und Parameter vorzusehen, mindestens:

- Parameter `DeployService` (Boolean; Default `false`)
- Parameter `ImageUri` (Digest-URI; nur bei Service-Deploy erforderlich)
- Condition, die `AWS::ECS::ExpressGatewayService` nur bei
  `DeployService=true` und gesetztem Digest-`ImageUri` erzeugt

### Ressourcen und Konfiguration

1. Amazon ECR Repository in `eu-central-1` mit `EmptyOnDelete: true`
2. IAM: Task Execution Role und Express-Mode Infrastructure Role
3. stackverwaltete `AWS::Logs::LogGroup` mit `RetentionInDays: 14`
4. AWS Secrets Manager als Template-Bestandteil mit konditionalem Opt-in:
   - Default: keine Secret-Injection; `FakeModelProvider` bleibt aktiv
   - Opt-in: Secret-Ressource und/oder vorhandene Secret-ARN plus
     Container-Injection über die Task Execution Role
   - keine echten Secret-Werte im Repository oder Template
5. konditional `AWS::ECS::ExpressGatewayService` mit:
   - `ImageUri` per unveränderlichem Digest
   - `containerPort: 8000`
   - Health-Check-Pfad `/health`
   - `MinTaskCount: 1`, `MaxTaskCount: 1` (höchstens `2`)
   - `PrimaryContainer.AwsLogsConfiguration` auf die stackverwaltete Log Group
     inkl. `LogStreamPrefix`
6. Default-VPC als Voraussetzung mit mindestens zwei öffentlichen Subnetzen
   in mindestens zwei Availability Zones und mindestens acht freien
   IP-Adressen je Subnetz; kein eigenes VPC-/Subnet-/ALB-Template
7. Stack-Delete als Abschaltpfad dokumentieren und manuell verifizieren,
   einschließlich Löschung von Log Group und geleertem ECR-Repository

Nicht Teil des Standard-Stacks:

- echte Secret-Werte
- Datenbank
- Authentifizierung
- Custom-Domain-Pflicht
- Multi-Region
- erweiterte Dashboards oder Alarmflut
- Verlass auf die automatisch von Express Mode erzeugte Log Group
- Express Service vor verfügbarem Image-Digest

## Spätere Observability-Branches

Dieses Dokument legt nur die Log-Senke und die Aufbewahrung fest.
Strukturierte Log-Metadaten folgen in
`feat/add-structured-runtime-logging`. Basis-Metriken folgen in
`feat/add-basic-runtime-metrics`.

## Revisit

Diese Architektur wird neu bewertet bei:

- Wegfall oder regionaler Nichtverfügbarkeit von ECS Express Mode in
  `eu-central-1`
- verbindlicher Anforderung an eine eigene VPC
- Einführung echter Daten oder produktiver Integrationen
- wesentlicher Änderung des Portfolioziels
