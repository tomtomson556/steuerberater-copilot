# AWS Reference Cloud Deployment Architecture

## Zweck und Status

Dieses Dokument legt das aktuelle, vereinfachte Zielbild für den
kleinstmöglichen überzeugenden AWS-Deployment-Nachweis der vorhandenen
stateless FastAPI-/Docker-Demo fest. Es ersetzt für diesen ersten Nachweis den
früher in diesem Dokument beschriebenen stackeigenen IAM- und
Secrets-Manager-Pfad des IAM-/Lifecycle-Modells v2.3.

Die v2.3-Artefakte bleiben historische Engineering- und IAM-Evidenz. Sie sind
keine Voraussetzung und keine Zielarchitektur für neue normale
AWS-Referenzdemo-Arbeit.

CloudFormation-Template und Guard-Regeln auf `main` implementieren diesen
vereinfachten Stack mit externen Rollen-ARNs:

- `infra/cloudformation/reference-demo.yaml` und
  `infra/cloudformation/guards/reference-demo.guard` bilden den vereinfachten
  Stack ab, nicht den alten v2.3-IAM-/Secret-Pfad.
- `docs/09-operations/aws-reference-demo-runbook.md` bleibt Legacy v2.3. Seine
  Kommandos sind kein ausführbarer Pfad für den aktuellen Stack.
- Ein neues ausführbares Runbook für den vereinfachten Stack steht noch aus.
- Dieses Dokument erzeugt keine AWS-Ressourcen, erteilt keinen AWS-Schreibzugriff
  und gibt keinen AWS-Live-Test frei.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

Leitentscheidungen bleiben ADR-003 und ADR-004:

- [adr-003-local-first-cloud-neutral-single-reference-cloud.md](../15-decisions/adr/adr-003-local-first-cloud-neutral-single-reference-cloud.md)
- [adr-004-select-reference-cloud.md](../15-decisions/adr/adr-004-select-reference-cloud.md)

## Verbindliches Minimalziel

AWS bleibt die einzige Referenz-Cloud, die Region ist `eu-central-1`, und
Amazon ECS Express Mode bleibt die Referenzlaufzeit. Der erste reale Nachweis
ist genau auf diese Kette begrenzt:

1. das vorhandene Docker-Image reproduzierbar bauen und per unveränderlichem
   Digest aus einem privaten Amazon-ECR-Repository referenzieren
2. die FastAPI-Anwendung als kurzlebigen ECS-Express-Mode-Dienst bereitstellen
3. `GET /health` über den von Express Mode bereitgestellten HTTPS-Endpunkt
   nachweisen
4. einen ausschließlich synthetischen `POST /ai/draft` mit dem
   `FakeModelProvider` nachweisen
5. die vorhandenen strukturierten Runtime-Logs und CloudWatch-EMF-Metriken für
   diesen Aufruf in CloudWatch nachweisen
6. Stack, Express-Mode-Randressourcen und alle weiteren kurzlebig erzeugten
   Demo-Ressourcen vollständig bereinigen und die Bereinigung prüfen

Mehr Infrastrukturbreite ist für den Portfolio-Nachweis kein Erfolgskriterium.

## Scope und Non-Goals

In Scope für den vereinfachten Nachweis:

- Amazon ECS Express Mode mit `AWS::ECS::ExpressGatewayService`
- privates Amazon ECR
- stackverwaltete CloudWatch Log Group mit begrenzter Aufbewahrung
- kleine, reproduzierbare öffentliche VPC-Netzwerkbasis
- CloudFormation als minimale Infrastructure as Code
- zwei statische Express-Mode-Rollen außerhalb des kurzlebigen Stacks
- eine kurzlebige, vor einem Live-Test gesondert freizugebende
  Deployer-Identität
- Kostenkontrolle und verifizierter Cleanup

Nicht in Scope für den ersten Nachweis:

- echter Modellprovider oder externer Modellaufruf
- Runtime-Secret, Secret-Injection oder AWS Secrets Manager
- Task Role oder AWS-API-Aufrufe aus dem Anwendungscode
- IAM-Rollen im kurzlebigen Demo-Stack
- v2.3-Policies, Permissions Boundaries, Bootstrap-Rolle,
  IAM-Control-Plane-Werkzeug oder Simulatorprotokoll als Voraussetzung
- eigene CloudFormation-Service-Rolle
- Datenbank oder Persistenz
- Authentifizierung, Custom Domain oder WAF
- private Subnetze, NAT Gateway, Elastic IP oder VPC Endpoints
- eigene ALB-, Target-Group- oder Security-Group-Ressourcen im Template
- Kubernetes, Multi-Region oder Multi-Cloud
- produktive Daten, produktive Integrationen oder Dauerbetrieb
- verwaltetes Dashboard oder Alarmarchitektur

## Bestehende Repository-Baseline

Die Zielarchitektur bildet vorhandene, lokal verifizierbare Funktionen ab und
ändert den Anwendungskern nicht:

| Repository-Stand | AWS-Nachweis |
| --- | --- |
| `Dockerfile`, Port `8000`, nicht privilegierter User `10001` | dasselbe Image in ECS Express Mode |
| `GET /health` | Express-Mode-Health-Check und HTTPS-Smoke |
| synthetisches `POST /ai/draft` | genau ein synthetischer Cloud-Smoke |
| `FakeModelProvider` als fest verdrahteter HTTP-Demo-Provider | unveränderter AWS-Default ohne Secret |
| ein EMF-JSON-Event je `POST /ai/draft` auf stdout | Aufnahme in CloudWatch Logs und reale EMF-Extraktion |
| keine AWS-SDK-Nutzung im Anwendungscode | keine AWS-Credentials im Container |

CloudFormation-Template und Guard-Regeln gehören zu dieser Baseline: Sie
implementieren den vereinfachten Stack mit externen Rollen-ARNs. Das vorhandene
ausführbare Runbook gehört nicht dazu; es bleibt Legacy v2.3. Ein neues
ausführbares Runbook steht noch aus.

## Zielarchitektur

| Baustein | Verbindliche Entscheidung |
| --- | --- |
| Referenz-Cloud | ausschließlich AWS |
| Region | `eu-central-1` |
| Containerlaufzeit | Amazon ECS Express Mode |
| IaC-Ressource | `AWS::ECS::ExpressGatewayService` |
| Image | privates ECR, Referenz per `repository@sha256:<digest>` |
| Anwendung | vorhandenes FastAPI-/Docker-Artefakt, Port `8000` |
| Health Check | `/health` |
| Provider | ausschließlich `FakeModelProvider` |
| Logs/Metriken | stackverwaltete CloudWatch Log Group, vorhandenes EMF auf stdout |
| Netzwerk | stackeigene IPv4-VPC, zwei öffentliche Subnetze in zwei AZs, IGW und öffentliche Route |
| Skalierung | `MinTaskCount: 1`, `MaxTaskCount: 1` |
| Statische Rollen | Task Execution Role und Express Infrastructure Role außerhalb des Stacks |
| Task Role | keine |
| Secrets Manager | nicht Teil dieses Nachweises |
| Deployer | kurzlebige Identität, keine eigene CloudFormation-Service-Rolle |
| Abschaltung | Stack-Delete plus Post-Delete-Inventur |

AWS beschreibt Express Mode als vereinfachten Fargate-basierten Dienst für
stateless Webanwendungen und APIs. Für den Einstieg sind Container-Image,
Task Execution Role und Infrastructure Role erforderlich; Express Mode
verwaltet unter anderem HTTPS-Endpunkt, Load Balancer, Auto Scaling und
Netzwerkkomponenten. Die CloudFormation-Ressource verlangt die
Infrastructure Role und bietet eigene Felder für Execution Role,
Health-Check-Pfad, Netzwerk, Container und eine optionale Task Role.

Offizielle Grundlagen:

- [Amazon ECS Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
- [Resources created by Amazon ECS Express Mode services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html)
- [Create an Express Mode service using the AWS CLI](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-getting-started.html)
- [`AWS::ECS::ExpressGatewayService`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecs-expressgatewayservice.html)

## System- und Vertrauensgrenzen

```text
kurzlebige Deployer-Session
  -> CloudFormation ohne eigene Service-Rolle
    -> kurzlebiger Demo-Stack
       -> ECR + Log Group + öffentliche VPC-Netzwerkbasis
       -> ECS Express Mode (mit zwei externen statischen Rollen)
          -> Express-verwalteter HTTPS-/ALB-Pfad
             -> FastAPI-Container, FakeModelProvider, keine AWS-Credentials
                -> stdout/stderr
                   -> stackverwaltete CloudWatch Log Group
                      -> EMF-Extraktion
```

### Cloud-neutraler Anwendungskern

Im Container bleiben:

- FastAPI-Demo und bestehender synthetischer RAG-/Draft-Workflow
- Gateway-, Risk- und Human-Review-Grenzen
- `FakeModelProvider` als sicherer Standard
- keine AWS-SDKs und keine Cloud-API-Aufrufe
- keine Secrets und keine produktiven Daten

### AWS-Systemrand

Am Systemrand liegen:

- Amazon ECR
- Amazon ECS Express Mode und seine verwalteten Randressourcen
- eine kleine stackeigene öffentliche Netzwerkbasis
- eine stackverwaltete Amazon CloudWatch Log Group
- AWS CloudFormation
- die beiden ausdrücklich abgegrenzten statischen Rollen

Modellprovider-Wahl und Laufzeit-Cloud bleiben getrennte Entscheidungen.

### Statische Task Execution Role

Die Task Execution Role liegt außerhalb des kurzlebigen Demo-Stacks und wird
von `ecs-tasks.amazonaws.com` angenommen. Sie dient dem ECS-/Fargate-Agenten,
nicht dem Anwendungscode. Für diesen Nachweis ist sie auf die für den Pull
aus privatem ECR und den `awslogs`-Pfad benötigten Berechtigungen begrenzt;
AWS dokumentiert dafür `AmazonECSTaskExecutionRolePolicy` oder äquivalente
Berechtigungen.

Die Rolle erhält insbesondere keine Secret-Leserechte, weil die
Task-Definition kein Secret referenziert. AWS verlangt zusätzliche
Secrets-Manager-Berechtigungen erst, wenn eine Task-Definition entsprechende
sensitive Daten referenziert.

Quelle:
[Amazon ECS task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html).

### Statische Express Infrastructure Role

Die Express Infrastructure Role liegt ebenfalls außerhalb des kurzlebigen
Stacks und wird von `ecs.amazonaws.com` angenommen. ECS verwendet sie für die
von Express Mode verwalteten Infrastrukturkomponenten wie Load Balancing,
Security Groups und Auto Scaling. Der vereinfachte Pfad orientiert sich am
aktuellen AWS-Vertrag mit
`AmazonECSInfrastructureRoleforExpressGatewayServices` oder nachweislich
äquivalenten Berechtigungen.

Die Rolle wird nicht dem Container bereitgestellt. Die alte v2.3-Boundary- und
Zusatzpolicy-Architektur wird nicht als Voraussetzung übernommen.

Quellen:

- [Express Mode IAM role defaults](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html#express-service-iam-role-defaults)
- [`AmazonECSInfrastructureRoleforExpressGatewayServices`](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonECSInfrastructureRoleforExpressGatewayServices.html)

### Keine Task Role

Eine Task Role stellt dem Container Berechtigungen für eigene AWS-API-Aufrufe
bereit. Der vorhandene Anwendungscode ruft keine AWS-APIs auf; Image-Pull und
Logtransport gehören zur Task Execution Role. Deshalb wird `TaskRoleArn` im
ersten Nachweis nicht gesetzt.

Quelle:
[Amazon ECS task IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html).

### Deployer-Grenze ohne CloudFormation-Service-Rolle

Der erste vereinfachte Pfad führt keine eigene
CloudFormation-Service-Rolle ein. AWS CloudFormation verwendet ohne angegebene
Service-Rolle eine temporäre Session aus den Caller-Credentials. Deshalb muss
die spätere Deployer-Identität selbst auf die tatsächlich vom vereinfachten
Template benötigten Aktionen und auf das Referenzprojekt begrenzt sein.

Der konkrete Least-Privilege-Vertrag wird aus dem vorhandenen vereinfachten Template,
seinen Stack-Operationen, dem ECR-Push und dem kontrollierten Referenzieren der
beiden statischen Rollen hergeleitet. Er wird vor jedem AWS-Live-Go separat
reviewt. Dieser Dokumentationsstand behauptet weder eine fertige Policy noch
übernimmt er die v2.3-Operator-, Bootstrap- oder Service-Rollen-Policies.

AWS weist darauf hin, dass eine einmal an einen Stack gebundene
CloudFormation-Service-Rolle für spätere Operationen weiterverwendet wird.
Das Weglassen dieser zusätzlichen langlebigen Rolle ist für den ersten
Minimalpfad bewusst; es ersetzt nicht die noch ausstehende
Least-Privilege-Begrenzung der Deployer-Session.

Quellen:

- [CloudFormation service role](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)
- [`CreateStack` `RoleARN`](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html#API_CreateStack_RequestParameters)

## Daten- und Secret-Grenze

- ausschließlich synthetische Fixtures und synthetische Requests
- keine echten Mandanten-, Kanzlei-, Beleg- oder Steuerdaten
- keine produktiven Schnittstellen
- keine Secrets im Image, Repository, Log, Prompt oder Stack
- kein Runtime-Secret und keine Container-Secret-Injection
- kein echter Modellprovider
- AWS Secrets Manager ist kein Bestandteil und keine Pflicht dieses
  FakeProvider-Nachweises

Der Verzicht auf Secrets Manager gilt nur für diesen genau abgegrenzten
Nachweis. Ein späterer echter Provider wäre eine neue Entscheidung mit
eigenem Secret-, Egress-, Modell- und Kostenvertrag.

## Netzwerkgrenze

Die reproduzierbare Minimalbasis darf im kurzlebigen Stack bleiben:

- eine IPv4-VPC mit DNS-Support und DNS-Hostnames
- zwei öffentliche Subnetze mit nicht überlappenden CIDRs in zwei
  Availability Zones und Public-IP-Zuweisung
- Internet Gateway, Attachment, öffentliche Route Table, Route `0.0.0.0/0`
  und beide Subnetz-Assoziationen
- explizite Übergabe beider Subnetze an
  `ExpressGatewayService.NetworkConfiguration`
- keine eigenen Security Groups im Template; Express Mode verwaltet die
  benötigten Service- und Load-Balancer-Gruppen

AWS dokumentiert, dass Express Mode bei öffentlichen Subnetzen standardmäßig
Public IPs für Tasks aktiviert und bei nicht angegebenen Security Groups
geeignete Gruppen verwaltet. Die öffentliche Erreichbarkeit ist nur für den
kurzlebigen synthetischen HTTPS-Smoke akzeptiert; sie ist keine
Produktionsarchitektur.

Quelle:
[Express Mode network defaults](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html#express-service-network-configuration-defaults).

## Infrastructure as Code und Image-Digest-Ablauf

Der vereinfachte CloudFormation-Stack enthält nur folgende projektbezogene
Ressourcen:

1. privates ECR-Repository mit `EmptyOnDelete: true`
2. CloudWatch Log Group mit `RetentionInDays: 14`
3. die kleine öffentliche VPC-Netzwerkbasis
4. konditional den `AWS::ECS::ExpressGatewayService`

Nicht in den Stack gehören IAM-Rollen, Permissions Boundaries, IAM-Policies
oder Secrets-Manager-Ressourcen. Die statischen Rollen werden dem Service nur
per ARN referenziert.

Weil das vom Stack erzeugte ECR-Repository vor dem Image-Push existieren muss,
bleibt der Ablauf zweistufig im selben Stack:

1. Foundation-Stand mit ECR, Log Group und Netzwerkbasis, aber ohne Express
   Service erstellen.
2. Image für die vereinbarte Containerarchitektur bauen, nach ECR pushen und
   den von ECR bestätigten Digest bestimmen.
3. Den Stack mit aktiviertem Express Service und
   `ImageUri=<repository>@<digest>` aktualisieren.

Template, Guard-Regeln und ihre Offline-Tests bilden diese Ressourcenmenge
bereits ab. Ein neues Runbook muss die tatsächlich ausführbaren Parameter und
Befehle dokumentieren. Die alten v2.3-Kommandos sind keine Vorlage, die
ungeprüft übernommen werden darf.

Quellen:

- [`AWS::ECR::Repository` `EmptyOnDelete`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecr-repository.html)
- [`AWS::Logs::LogGroup`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-logs-loggroup.html)
- [Updating CloudFormation stacks](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks.html)

## Observability-Nachweis

Die Anwendung schreibt für jeden `POST /ai/draft` genau ein einzeiliges
JSON-Event nach stdout und setzt eine serverseitige `X-Request-ID`. Das Event
enthält CloudWatch Embedded Metric Format im Namespace
`SteuerberaterCopilot/Runtime` mit den statischen Dimensionen
`service=steuerberater-copilot` und `operation=POST /ai/draft`.

Der AWS-Nachweis muss belegen:

- das Runtime-Event erscheint in der stackverwalteten Log Group
- Request-ID, Workflowstatus, Gatewayentscheidung, technischer
  Review-Gate-Status, Provider-/Modellname, Promptversion, Laufzeit, Parse- und
  Validierungsstatus sowie Fehlerklasse bleiben sichtbar
- CloudWatch extrahiert mindestens `request_count`, Erfolgs-/Fehlerzähler,
  `duration_ms`, Fehlerzähler und `abstention_count` als EMF-Metriken
- Request-/Response-Bodys, Prompts, Modellantworten, Exception-Texte, Secrets
  und personenbezogene Daten erscheinen nicht im Event

`review_gate_status` bleibt ein technischer Status und keine menschliche
Reviewentscheidung. Die reale EMF-Extraktion ist erst nach einem gesondert
freigegebenen Live-Test bestätigt. Ein Dashboard und Alarme sind dafür keine
Pflicht.

Quellen:

- [Embedding metrics within logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
- [CloudWatch Embedded Metric Format specification](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)

## Kosten- und Cleanup-Vertrag

Vor einem späteren Live-Test müssen ein enges Zeitfenster und eine
accountweite Kostenkontrolle, etwa Budget oder Kostenalarm, bestätigt sein.
Für den Stack gelten:

- `MinTaskCount: 1`, `MaxTaskCount: 1`
- Log-Aufbewahrung 14 Tage während der Existenz des Stacks
- ECR `EmptyOnDelete: true` ausschließlich für diese kurzlebige synthetische
  Demo
- kein NAT Gateway, keine Datenbank und kein Dauerbetrieb
- Stack unmittelbar nach dem Nachweis löschen

Express Mode verursacht keine eigene Zusatzgebühr, aber die darunterliegenden
Ressourcen wie Fargate, Load Balancer, CloudWatch und Datentransfer können
Kosten verursachen. Benutzerdefinierte EMF-Metriken können ebenfalls Kosten
verursachen.

Vollständiger Cleanup bedeutet für diesen Nachweis:

1. Stack löschen und `DELETE_COMPLETE` abwarten.
2. ECR-Repository, stackverwaltete Log Group und VPC-Netzwerkbasis auf
   Abwesenheit prüfen.
3. den Express Service sowie die ihm zurechenbaren Tasks, Task Definitions,
   Target Groups, Service Security Groups, Auto-Scaling-Ressourcen und
   sonstigen Express-Randressourcen inventarisieren und auf Abwesenheit
   prüfen.
4. von Express Mode möglicherweise behaltene oder geteilte Ressourcen vor
   jeder manuellen Bereinigung eindeutig attribuieren; geteilte Ressourcen
   niemals blind löschen.
5. die beiden vorab deklarierten statischen Rollen gesondert ausweisen. Sie
   gehören bewusst nicht zum kurzlebigen Stack und sind daher kein
   unerkannter Stack-Rest.

AWS dokumentiert, dass beim Löschen eines Express-Mode-Diensts die eindeutig
dienstbezogenen Ressourcen entfernt werden, geteilte Ressourcen aber erhalten
bleiben können. Deshalb ist Stack-Delete allein noch kein ausreichender
Cleanup-Nachweis.

Quellen:

- [Delete Amazon ECS Express Mode services](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-delete-task.html)
- [Amazon ECS Express Mode pricing](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html#express-service-pricing)
- [Amazon CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/)

## Abnahmekriterien für den späteren Portfolio-Nachweis

Der Nachweis ist erst erbracht, wenn eine separat freigegebene Ausführung
folgende Evidenz liefert:

- finaler Review-Commit und geprüfte IaC-Artefakte
- erfolgreicher zweistufiger Stack-Ablauf mit Digest-Image
- erfolgreicher HTTPS-Aufruf von `/health`
- erfolgreicher synthetischer `POST /ai/draft` mit `FakeModelProvider` und
  unveränderten Human-Review-/Gateway-Grenzen
- zugehöriges Runtime-Event in CloudWatch Logs und bestätigte EMF-Extraktion
- dokumentiertes Kostenfenster
- `DELETE_COMPLETE` und bestandene Post-Delete-Inventur

Template und Tests für den vereinfachten Stack sind vorhanden. Bis das neue
ausführbare Runbook vorliegt, besteht kein AWS-Live-Test-Go.

## Revisit

Diese Architektur wird neu bewertet bei:

- Wegfall oder regionaler Nichtverfügbarkeit von ECS Express Mode in
  `eu-central-1`
- Einführung eines echten Modellproviders oder Runtime-Secrets
- verbindlicher Anforderung an Authentifizierung, private Netzwerke oder
  produktive Daten
- wesentlicher Änderung des Portfolioziels
