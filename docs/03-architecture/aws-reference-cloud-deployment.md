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
- private VPC mit NAT, VPC Endpoints oder privaten Subnetzen
- eigene ALB- oder Target-Group-Ressource im Template
- eigene Security Groups im Template
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
| Netzwerk | Stackeigene IPv4-VPC mit zwei öffentlichen Subnetzen in zwei AZs, Internet Gateway und öffentlicher Route `0.0.0.0/0`; Subnets explizit in `NetworkConfiguration`; keine Default-VPC-Abhängigkeit |
| ECR-Löschung | `EmptyOnDelete: true` am stackverwalteten Repository (nur kurzlebige Portfolio-Demo) |
| Bootstrap | Zweistufig im selben Stack: zuerst ECR/IAM/Log Group/VPC, danach Express Service mit Image-Digest |
| IaC | AWS CloudFormation mit `AWS::ECS::ExpressGatewayService` |

### Warum ECS Express Mode

AWS App Runner ist für Neukunden geschlossen. AWS empfiehlt Amazon ECS Express
Mode als Nachfolger.

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
- [CloudFormation Parameters](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html)
- [CloudFormation Conditions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/conditions-section-structure.html)
- [AWS::ECS::ExpressGatewayService](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecs-expressgatewayservice.html)
- [ExpressGatewayService NetworkConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-ecs-expressgatewayservice-expressgatewayservicenetworkconfiguration.html)
- [PrimaryContainer.AwsLogsConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-ecs-expressgatewayservice-expressgatewayserviceawslogsconfiguration.html)
- [AWS::Logs::LogGroup](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-logs-loggroup.html)
- [AWS::ECR::Repository](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecr-repository.html) (`EmptyOnDelete`)
- [AWS::SecretsManager::Secret](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-secretsmanager-secret.html)
- [Updating stacks](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks.html)
- [Embedding metrics within logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
- [Specification: Embedded metric format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)
- [Amazon CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/)

### Warum nicht die Alternativen

| Alternative | Ablehnung |
| --- | --- |
| AWS App Runner | Für Neukunden geschlossen; AWS empfiehlt ECS Express Mode |
| Handgerolltes ECS Fargate mit privater VPC/NAT/eigener ALB | Unnötig komplex; Express Mode plus minimale öffentliche stackeigene VPC deckt denselben Portfolio-Nachweis ab |
| Kubernetes / EKS | Explizites Roadmap-Non-Goal |
| Multi-Cloud | Explizites ADR-/Roadmap-Non-Goal |

## Systemgrenzen

```text
HTTPS Client
  -> internet-facing ALB (Express-managed Service Security Group ingress path)
    -> ECS Express Mode / Fargate task
       (public IP in stack-owned public subnet, MapPublicIpOnLaunch)
      -> FastAPI-Container (cloud-neutraler Kern, FakeModelProvider default)
        -> stdout/stderr
          -> stackverwaltete CloudWatch Log Group
             (RetentionInDays: 14, LogStreamPrefix)

Stack-owned VPC (IPv4) + 2 public subnets + IGW + public route
  -> ExpressGatewayService.NetworkConfiguration.Subnets
ECR (Image by digest, EmptyOnDelete: true)
  -> Express Mode pull via Task Execution Role
Secrets Manager (template-owned, conditional opt-in)
  -> optional Env-Injection via Task Execution Role
CloudFormation Stack owns Express Mode, ECR, Log Group,
stack VPC networking, Secrets Manager wiring, and IAM edge resources
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
  verwaltete ALB-/Security-Group-Ressourcen)
- stackeigene öffentliche IPv4-VPC mit zwei öffentlichen Subnetzen,
  Internet Gateway und öffentlicher Route Table
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

- keine Abhängigkeit von einer accountweiten Default-VPC
- der Stack stellt in `eu-central-1` eine eigene IPv4-VPC mit DNS-Support und
  DNS-Hostnames sowie zwei öffentlichen Subnetzen in zwei Availability Zones
  bereit (`MapPublicIpOnLaunch: true`, nicht überlappende CIDRs)
- Internet Gateway, VPC-Attachment, öffentliche Route Table mit Route
  `0.0.0.0/0` und Subnetz-Assoziationen sind stackverwaltet und beim
  Stack-Delete vollständig entfernbar
- `ExpressGatewayService.NetworkConfiguration.Subnets` übergibt beide
  öffentlichen Subnetze ausdrücklich; ohne eigene Security Groups im Template,
  damit Express Mode Service- und Load-Balancer-Security-Groups weiter selbst
  verwaltet
- laut AWS Express-Mode-Defaults: öffentliche Custom-Subnetze führen zu einem
  internet-facing ALB und `assignPublicIp` für die Tasks; fehlende eigene
  Security Groups lassen Express Mode die erforderlichen Gruppen erzeugen
- kein NAT Gateway, keine Elastic IP, keine privaten Subnetze, keine VPC
  Endpoints und keine eigene ALB-/Target-Group-Ressource im Template

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

1. Stack mit ECR, IAM, Log Group, stackeigener öffentlicher VPC-Netzwerkbasis
   und Secrets-Manager-Verdrahtung erstellen, jedoch **ohne** Express Service
   (`DeployService="false"`).
2. Image in ECR pushen, unveränderlichen Digest bestimmen und den Stack mit
   aktiviertem Express Service aktualisieren
   (`DeployService="true"`, `ImageUri=<repo>@<digest>`).

Parameter (CloudFormation kennt keinen `Boolean`-Parametertyp; Strings mit
`AllowedValues` verwenden):

```yaml
DeployService:
  Type: String
  Default: "false"
  AllowedValues:
    - "true"
    - "false"

ImageUri:
  Type: String
  Default: ""
```

Conditions so definieren, dass `AWS::ECS::ExpressGatewayService` nur erstellt
wird, wenn `DeployService` gleich `"true"` ist und `ImageUri` nicht leer ist,
beispielsweise:

```yaml
Conditions:
  DeployExpressService:
    Fn::And:
      - Fn::Equals:
          - Ref: DeployService
          - "true"
      - Fn::Not:
          - Fn::Equals:
              - Ref: ImageUri
              - ""
```

Die Express-Service-Ressource trägt `Condition: DeployExpressService`.

### Ressourcen und Konfiguration

1. Amazon ECR Repository in `eu-central-1` mit `EmptyOnDelete: true`
2. IAM: Task Execution Role und Express-Mode Infrastructure Role
3. stackverwaltete `AWS::Logs::LogGroup` mit `RetentionInDays: 14`
4. AWS Secrets Manager als Template-Bestandteil mit konditionalem Opt-in:
   - Default: keine Secret-Injection; `FakeModelProvider` bleibt aktiv
   - Opt-in: Secret-Ressource und/oder vorhandene Secret-ARN plus
     Container-Injection über die Task Execution Role
   - keine echten Secret-Werte im Repository oder Template
5. stackeigene öffentliche Netzwerkbasis (immer im Stack, auch ohne Service):
   - eine IPv4-VPC mit `EnableDnsSupport` und `EnableDnsHostnames`
   - zwei öffentliche Subnetze mit nicht überlappenden CIDRs in zwei AZs und
     `MapPublicIpOnLaunch: true`
   - Internet Gateway, VPC-Attachment, öffentliche Route Table, Route
     `0.0.0.0/0` und beide Subnetz-Assoziationen
6. konditional `AWS::ECS::ExpressGatewayService` mit:
   - `ImageUri` per unveränderlichem Digest
   - `containerPort: 8000`
   - Health-Check-Pfad `/health`
   - `MinTaskCount: 1`, `MaxTaskCount: 1` (höchstens `2`)
   - `PrimaryContainer.AwsLogsConfiguration` auf die stackverwaltete Log Group
     inkl. `LogStreamPrefix`
   - `NetworkConfiguration.Subnets` auf beide stackeigenen öffentlichen
     Subnetze; ohne `NetworkConfiguration.SecurityGroups`
7. Stack-Delete als Abschaltpfad dokumentieren und manuell verifizieren,
   einschließlich Löschung von Log Group, geleertem ECR-Repository und der
   stackeigenen VPC-Netzwerkbasis

Nicht Teil des Standard-Stacks:

- echte Secret-Werte
- Datenbank
- Authentifizierung
- Custom-Domain-Pflicht
- Multi-Region
- erweiterte Dashboards oder Alarmflut
- Default-VPC-Abhängigkeit
- NAT Gateway, Elastic IP, private Subnetze oder VPC Endpoints
- eigene ALB-, Target-Group- oder Security-Group-Ressourcen
- Verlass auf die automatisch von Express Mode erzeugte Log Group
- Express Service vor verfügbarem Image-Digest

## Observability

Die Log-Senke und die Aufbewahrung bleiben die stackverwaltete CloudWatch Log
Group mit `RetentionInDays: 14` und `PrimaryContainer.AwsLogsConfiguration`.
Strukturierte Runtime-Logs sind am HTTP-Systemrand vorhanden: jeder
`POST /ai/draft`-Aufruf schreibt genau ein einzeiliges JSON-Event nach stdout
und setzt eine serverseitige `X-Request-ID`. Das Event ist ein gültiges
[CloudWatch Embedded Metric Format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)-Dokument
laut
[EMF-Spezifikation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html).
Die Anwendung verwendet dafür die Python-Standardbibliothek; es gibt kein
AWS-SDK, keine CloudWatch-API, keinen `PutMetricData`-Aufruf und keine neue
Dependency. `logs:PutLogEvents` über den bestehenden awslogs-Pfad bleibt
ausreichend.

Namespace `SteuerberaterCopilot/Runtime`. Nur die statischen Dimensionen
`service=steuerberater-copilot` und `operation=POST /ai/draft`.
`request_id`, `provider_name`, `model_name` und `prompt_version` sind keine
CloudWatch-Dimensionen. `/health` und `/version` erzeugen keine
Runtime-Metriken.

Technische HTTP-Quoten, keine fachliche Bewertung:

- Erfolgsquote: `SUM(success_count) / SUM(request_count)`
- Fehlerquote: `SUM(error_count) / SUM(request_count)`
- Abstention Rate: `SUM(abstention_count) / SUM(request_count)`
- P95-Latenz: p95-Statistik von `duration_ms`
- Fehlerzähler jeweils als Sum
- Modellkosten nur über vorhandene numerische `model_cost_usd`-Werte

Kontrollierter Block und Abstention mit HTTP 200 zählen technisch als
erfolgreicher HTTP-Aufruf; die fachliche Bedeutung bleibt in
`workflow_status`. Geschätzte Modellkosten sind nicht implementiert;
`model_cost_usd` ist `0.0` oder `null`. Ist der Wert `null`, wird er nicht
als EMF-MetricDefinition referenziert.

EMF stellt mindestens-einmal-Verarbeitung sicher; gelegentliche doppelte
Metrikwerte sind möglich. Benutzerdefinierte CloudWatch-Metriken können
Kosten verursachen; siehe
[Amazon CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/).
Die niedrig-kardinalen Dimensionen begrenzen die Zahl der Zeitreihen. Es gibt
kein verwaltetes Dashboard und keine Alarme in diesem Stand. Die reale
EMF-Extraktion in CloudWatch bleibt bis zu einer bewussten AWS-Verifikation
unbestätigt. Ein AWS-Live-Test ist nicht Teil dieses Stands.

`review_gate_status` ist der technische Review-Gate-Status, keine menschliche
Reviewentscheidung. Request-/Response-Bodys, Prompts, Modellantworten,
Exception-Texte, Secrets und personenbezogene Daten gehören nicht ins Event.

## Revisit

Diese Architektur wird neu bewertet bei:

- Wegfall oder regionaler Nichtverfügbarkeit von ECS Express Mode in
  `eu-central-1`
- verbindlicher Anforderung an private Subnetze, NAT oder VPC Endpoints
- Einführung echter Daten oder produktiver Integrationen
- wesentlicher Änderung des Portfolioziels
