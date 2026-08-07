# AWS-Referenzdemo: IAM-Policy-Simulator-Testprotokoll

Stand: 7. August 2026\
Repository: `tomtomson556/steuerberater-copilot`  
Geprüfter Ausgangsstand: `ef37f77a21b84be6d909bcd420a0cefcafa81b76`
Policy-Verzeichnis: `infra/iam/reference-demo/v2.3`  
Zielregion: `eu-central-1`  
Simulatorprofil: `administrator`

## Zweck und Status

Dieses Protokoll hält die bestätigten Ergebnisse der vorbereitenden
IAM-Policy-Simulator-Prüfung für die AWS-Referenzdemo fest. Es ist die
Fortsetzungsgrundlage für spätere Sitzungen und verhindert doppelte oder
vergessene Tests.

Bisher wurde ausschließlich `aws iam simulate-custom-policy` verwendet. Die
Simulationen haben keine AWS-Ressourcen erstellt, verändert, zurückgesetzt oder
gelöscht.

Der AWS-Live-Test bleibt **No-Go**, bis die vollständige Vorprüfung und die
weiteren V2.3-Gates abgeschlossen sind.

## Zählweise

- Bestätigte nummerierte Simulatorfälle: **72**
- Ergänzende bestätigte Gruppenmarker: **2**
- SIM-046: im Erstlauf fehlgeschlagen, nach Policy-Korrektur erfolgreich wiederholt

Nur vom Nutzer ausdrücklich gemeldete Entscheidungen oder bestandene
Gruppenmarker werden als bestätigt geführt. Erwartete Ergebnisse allein zählen
nicht.

## Bestätigte Simulatorfälle

| ID | Identität / Bereich | Aktion und Gegenstand | Kontext / Gegenfall | Entscheidung | Status |
|---|---|---|---|---|---|
| SIM-001 | CloudFormation-Service-Rolle | `ec2:DescribeVpcs` | `eu-central-1` | `allowed` | bestanden |
| SIM-002 | CloudFormation-Service-Rolle | `ec2:DescribeVpcs` | falsche Region `eu-west-1` | `implicitDeny` | bestanden |
| SIM-003 | Boundary-Kontrollfall | hypothetisches `s3:ListAllMyBuckets` | breite Inline-Policy ohne Service-Role-Boundary | `allowed` | bestanden |
| SIM-004 | Boundary-Wirksamkeit | hypothetisches `s3:ListAllMyBuckets` | breite Inline-Policy mit Service-Role-Boundary | `implicitDeny` | bestanden |
| SIM-005 | CloudFormation-Service-Rolle | `iam:PassRole` auf Task Execution Role | `iam:PassedToService=ecs-tasks.amazonaws.com` | `allowed` | bestanden |
| SIM-006 | CloudFormation-Service-Rolle | `iam:PassRole` auf Task Execution Role | falscher Service `lambda.amazonaws.com` | `implicitDeny` | bestanden |
| SIM-007 | CloudFormation-Service-Rolle | `iam:PassRole` auf Express Infrastructure Role | `iam:PassedToService=ecs.amazonaws.com` | `allowed` | bestanden |
| SIM-008 | Operator | `iam:PassRole` auf feste CloudFormation-Service-Rolle | `iam:PassedToService=cloudformation.amazonaws.com` | `allowed` | bestanden |
| SIM-009 | CloudFormation-Service-Rolle | Übergabe der CloudFormation-Service-Rolle an ECS | falsche Rollen-/Service-Kombination | `implicitDeny` | bestanden |
| SIM-010 | Express Infrastructure Role | Übergabe an CloudFormation | falscher Trust-/Service-Pfad | `implicitDeny` | bestanden |
| SIM-011 | Operator | `cloudformation:CreateStack` | direkte Stack-Erstellung | `implicitDeny` | bestanden |
| SIM-012 | Operator | `cloudformation:CreateChangeSet` | korrekter Stack, Name, Region, Service-Rolle und fünf Pflicht-Tags | `allowed` | bestanden |
| SIM-013 | Operator | `cloudformation:CreateChangeSet` | Pflicht-Tag `Lifecycle` fehlt | `implicitDeny` | bestanden |
| SIM-014 | Operator | `cloudformation:CreateChangeSet` | unzulässiger Change-Set-Name | `implicitDeny` | bestanden |
| SIM-015 | Operator | `cloudformation:CreateChangeSet` | unzulässiger Stackname | `implicitDeny` | bestanden |
| SIM-016 | Operator | `cloudformation:UpdateStack` | direkte Stack-Aktualisierung | `implicitDeny` | bestanden |
| SIM-017 | Operator | `cloudformation:ExecuteChangeSet` | zulässiger Change-Set-Name | `allowed` | bestanden |
| SIM-018 | Operator | `cloudformation:ExecuteChangeSet` | unzulässiger Change-Set-Name | `implicitDeny` | bestanden |
| SIM-019 | Operator | `cloudformation:DeleteStack` | genehmigter Stack und korrekte Service-Rolle | `allowed` | bestanden |
| SIM-020 | Operator | `cloudformation:DeleteStack` | falsche Service-Rolle | `implicitDeny` | bestanden |
| SIM-021 | Operator | `cloudformation:RollbackStack` | korrekte Service-Rolle | `allowed` | bestanden |
| SIM-022 | Operator | `cloudformation:RollbackStack` | falsche Service-Rolle | `implicitDeny` | bestanden |
| SIM-023 | Operator | `cloudformation:ContinueUpdateRollback` | korrekte Service-Rolle | `allowed` | bestanden |
| SIM-024 | Operator | `cloudformation:ContinueUpdateRollback` | falsche Service-Rolle | `implicitDeny` | bestanden |
| SIM-025 | Operator | `cloudformation:CancelUpdateStack` | genehmigter Stack und richtige Region; ohne `RoleArn`-Bedingung | `allowed` | bestanden |
| SIM-026 | Operator | `cloudformation:CancelUpdateStack` | unzulässiger Stackname | `implicitDeny` | bestanden |
| SIM-027 | Operator | `cloudformation:DescribeStacks` | genehmigter Stack und richtige Region | `allowed` | bestanden |
| SIM-028 | Operator | `cloudformation:DescribeStacks` | unzulässiger Stackname | `implicitDeny` | bestanden |
| SIM-029 | Operator | `cloudformation:ValidateTemplate` | richtige Region; globale Ressource `*` | `allowed` | bestanden |
| SIM-030 | Operator | `cloudformation:ValidateTemplate` | falsche Region `eu-west-1`; globale Ressource `*` | `implicitDeny` | bestanden |
| SIM-031 | Operator / ECR-Publisher | neun freigegebene ECR-Push- und Leseberechtigungen | genehmigtes Referenz-Repository, richtige Region | `allowed` × 9 | bestanden |
| SIM-032 | Operator / ECR-Publisher | neun ECR-Push- und Leseberechtigungen | fremdes Repository, richtige Region | `implicitDeny` × 9 | bestanden |
| SIM-033 | Operator / ECR-Publisher | neun ECR-Push- und Leseberechtigungen | genehmigtes Referenz-Repository, falsche Region | `implicitDeny` × 9 | bestanden |
| SIM-034 | Operator / ECR-Publisher | `ecr:GetAuthorizationToken` | richtige Region | `allowed` | bestanden |
| SIM-035 | Operator / ECR-Publisher | `ecr:GetAuthorizationToken` | falsche Region | `implicitDeny` | bestanden |
| SIM-036 | Operator / ECR-Publisher | nicht freigegebene Aktion `ecr:DeleteRepository` | genehmigtes Referenz-Repository, richtige Region | `implicitDeny` | bestanden |
| SIM-037 | Operator / Secret-Initializer | drei freigegebene Aktionen zum Setzen und Lesen von Secret-Metadaten | synthetisches Referenz-Secret, richtige Region | `allowed` × 3 | bestanden |
| SIM-038 | Operator / Secret-Initializer | `secretsmanager:GetSecretValue` | synthetisches Referenz-Secret, richtige Region | `implicitDeny` | bestanden |
| SIM-039 | Operator / Secret-Initializer | drei freigegebene Secret-Aktionen | fremdes Secret, richtige Region | `implicitDeny` × 3 | bestanden |
| SIM-040 | Operator / Secret-Initializer | drei freigegebene Secret-Aktionen | synthetisches Referenz-Secret, falsche Region | `implicitDeny` × 3 | bestanden |
| SIM-041 | Operator / Secret-Initializer | nicht freigegebene Aktionen `CreateSecret`, `DeleteSecret` und `UpdateSecret` | synthetisches Referenz-Secret, richtige Region | `implicitDeny` × 3 | bestanden |
| SIM-042 | Operator / Permissions Boundary | hypothetisch zu breite Identity-Policy erlaubt `secretsmanager:GetSecretValue` | synthetisches Referenz-Secret, richtige Region | `implicitDeny` | bestanden |
| SIM-043 | Operator / Verifier | `DescribeSecret` und `ListSecretVersionIds` | synthetisches Referenz-Secret, richtige Region | `allowed` × 2 | bestanden |
| SIM-044 | Operator / Verifier | `secretsmanager:GetSecretValue` | synthetisches Referenz-Secret, richtige Region | `implicitDeny` | bestanden |
| SIM-045 | Operator / Verifier | `DescribeSecret` und `ListSecretVersionIds` | fremdes Secret, richtige Region | `implicitDeny` × 2 | bestanden |
| SIM-046 | Operator / Verifier | `DescribeSecret` und `ListSecretVersionIds` | synthetisches Referenz-Secret, falsche Region | Erstlauf: `allowed` × 2; Wiederholung nach Policy-Korrektur: `implicitDeny` × 2 | bestanden nach Korrektur |
| SIM-047 | Operator / Verifier | `ecs:DescribeExpressGatewayService` | exakter Referenzservice, richtige Region | `allowed` | bestanden |
| SIM-048 | Operator / Verifier | `ecs:DescribeExpressGatewayService` | fremder Service, richtige Region | `implicitDeny` | bestanden |
| SIM-049 | Operator / Verifier | `ecs:DescribeServices` | exakter Referenzservice, richtige Region | `allowed` | bestanden |
| SIM-050 | Operator / Verifier | `ecs:DescribeServices` | fremder Service, richtige Region | `implicitDeny` | bestanden |
| SIM-051 | Operator / Verifier | `ecs:ListServiceDeployments` | exakter Referenzservice, richtige Region | `allowed` | bestanden |
| SIM-052 | Operator / Verifier | `ecs:ListServiceDeployments` | fremder Service, richtige Region | `implicitDeny` | bestanden |
| SIM-053 | Operator / Verifier | `ecs:DescribeServiceDeployments` | synthetische Deployment-ARN des exakten Referenzservices, richtige Region | `allowed` | bestanden |
| SIM-054 | Operator / Verifier | `ecs:DescribeServiceDeployments` | synthetische Deployment-ARN eines fremden Services, richtige Region | `implicitDeny` | bestanden |
| SIM-055 | Operator / Verifier | `ecs:DescribeServiceRevisions` | synthetische Revisions-ARN des exakten Referenzservices, richtige Region | `allowed` | bestanden |
| SIM-056 | Operator / Verifier | `ecs:DescribeServiceRevisions` | synthetische Revisions-ARN eines fremden Services, richtige Region | `implicitDeny` | bestanden |
| SIM-057 | Operator / Verifier | `ecs:DescribeTasks` | synthetische Task-ARN im Default-Cluster, korrekter Cluster-Kontext und richtige Region | `allowed` | bestanden |
| SIM-058 | Operator / Verifier | `ecs:DescribeTasks` | synthetische Task-ARN im Default-Cluster, falscher Cluster-Kontext und richtige Region | `implicitDeny` | bestanden |
| SIM-059 | Operator / Verifier | `ecs:ListTasks` | Default-Cluster-Kontext und richtige Region | `allowed` | bestanden |
| SIM-060 | Operator / Verifier | `ecs:ListTasks` | falscher Cluster-Kontext und richtige Region | `implicitDeny` | bestanden |
| SIM-061 | Operator / Verifier | `ecs:DescribeClusters` | Default-Cluster und richtige Region | `allowed` | bestanden |
| SIM-062 | Operator / Verifier | `ecs:DescribeClusters` | falscher Cluster und richtige Region | `implicitDeny` | bestanden |
| SIM-063 | Operator / Verifier | `ecs:ListTagsForResource` | exakter Referenzservice, richtige Region | `allowed` | bestanden |
| SIM-064 | Operator / Verifier | `ecs:ListTagsForResource` | fremder Service, richtige Region | `implicitDeny` | bestanden |
| SIM-065 | Operator / Verifier | `ecs:DescribeTaskDefinition` und `ecs:ListTaskDefinitions` | globale Ressource `*`, richtige Region | `allowed` × 2 | bestanden |
| SIM-066 | Operator / Verifier | `ecs:DescribeTaskDefinition` und `ecs:ListTaskDefinitions` | globale Ressource `*`, falsche Region `eu-west-1` | `implicitDeny` × 2 | bestanden |
| SIM-067 | Operator / Verifier | `ecr:DescribeImages`, `ecr:DescribeRepositories`, `ecr:ListImages` und `ecr:ListTagsForResource` | exaktes Referenz-Repository, richtige Region | `allowed` × 4 | bestanden |
| SIM-068 | Operator / Verifier | `ecr:DescribeImages`, `ecr:DescribeRepositories`, `ecr:ListImages` und `ecr:ListTagsForResource` | fremdes Repository, richtige Region | `implicitDeny` × 4 | bestanden |
| SIM-069 | Operator / Verifier | `logs:FilterLogEvents`, `logs:GetLogEvents` und `logs:ListTagsForResource` | exakte Referenz-Loggruppe, richtige Region | `allowed` × 3 | bestanden |
| SIM-070 | Operator / Verifier | `logs:FilterLogEvents`, `logs:GetLogEvents` und `logs:ListTagsForResource` | fremde Loggruppe, richtige Region | `implicitDeny` × 3 | bestanden |
| SIM-071 | Operator / Verifier | `logs:DescribeLogGroups` und `logs:DescribeLogStreams` | globale Ressource `*`, richtige Region | `allowed` × 2 | bestanden |
| SIM-072 | Operator / Verifier | `logs:DescribeLogGroups` und `logs:DescribeLogStreams` | globale Ressource `*`, falsche Region `eu-west-1` | `implicitDeny` × 2 | bestanden |

## Befund und Korrektur zu SIM-046

Der erste Lauf von SIM-046 schlug fehl:

```text
OPERATOR_VERIFIER_SECRET_WRONG_REGION=allowed allowed
VERIFIER_SECRET_WRONG_REGION_NEGATIVE=failed
```

Die Untersuchung bestätigte eine fehlende Regionsbedingung in den
Secrets-Manager-Statements beider Dateien:

- `infra/iam/reference-demo/v2.3/operator-verifier-policy.json`
- `infra/iam/reference-demo/v2.3/operator-boundary.json`

In beiden Statements wurde die Bedingung
`aws:RequestedRegion = eu-central-1` ergänzt. Die Wiederholung war erfolgreich:

```text
OPERATOR_VERIFIER_SECRET_WRONG_REGION=implicitDeny implicitDeny
VERIFIER_SECRET_WRONG_REGION_NEGATIVE=passed
```

Damit ist die im Erstlauf entdeckte Regionslücke geschlossen und SIM-046
bestanden.

## Ergänzende bestätigte Gruppenmarker

Diese Marker stammen aus bestandenen Sammelprüfungen. Weil die einzelnen
`EvalDecision`-Zeilen nicht vollständig erhalten sind, werden sie nicht als
zusätzliche nummerierte Simulatorfälle gezählt.

| ID | Bestätigter Marker | Bedeutung | Status |
|---|---|---|---|
| GRP-001 | `OPERATOR_WRONG_SERVICE_NEGATIVE=passed` | Operator darf die feste CloudFormation-Service-Rolle nicht an einen falschen Service übergeben. | bestanden |
| GRP-002 | `OPERATOR_WRONG_ROLE_NEGATIVE=passed` | Operator darf keine andere Rolle an CloudFormation übergeben. | bestanden |

## Ausführungsnachweise SIM-031 bis SIM-072

```text
SIM-031  OPERATOR_ECR_PUSH=allowed × 9
         ECR_PUSH_POSITIVE=passed
SIM-032  OPERATOR_ECR_WRONG_REPOSITORY=implicitDeny × 9
         ECR_WRONG_REPOSITORY_NEGATIVE=passed
SIM-033  OPERATOR_ECR_WRONG_REGION=implicitDeny × 9
         ECR_WRONG_REGION_NEGATIVE=passed
SIM-034  OPERATOR_ECR_AUTH_TOKEN=allowed
         ECR_AUTH_TOKEN_POSITIVE=passed
SIM-035  OPERATOR_ECR_AUTH_TOKEN_WRONG_REGION=implicitDeny
         ECR_AUTH_TOKEN_WRONG_REGION_NEGATIVE=passed
SIM-036  OPERATOR_ECR_DELETE_REPOSITORY=implicitDeny
         ECR_DELETE_REPOSITORY_NEGATIVE=passed
SIM-037  OPERATOR_SECRET_INITIALIZER=allowed × 3
         SECRET_INITIALIZER_POSITIVE=passed
SIM-038  OPERATOR_SECRET_VALUE_READ=implicitDeny
         SECRET_VALUE_READ_NEGATIVE=passed
SIM-039  OPERATOR_SECRET_WRONG_RESOURCE=implicitDeny × 3
         SECRET_WRONG_RESOURCE_NEGATIVE=passed
SIM-040  OPERATOR_SECRET_WRONG_REGION=implicitDeny × 3
         SECRET_WRONG_REGION_NEGATIVE=passed
SIM-041  OPERATOR_SECRET_UNAPPROVED_ACTIONS=implicitDeny × 3
         SECRET_UNAPPROVED_ACTIONS_NEGATIVE=passed
SIM-042  OPERATOR_BOUNDARY_SECRET_VALUE_READ=implicitDeny
         BOUNDARY_SECRET_VALUE_READ_NEGATIVE=passed
SIM-043  OPERATOR_VERIFIER_SECRET_METADATA=allowed × 2
         VERIFIER_SECRET_METADATA_POSITIVE=passed
SIM-044  OPERATOR_VERIFIER_SECRET_VALUE_READ=implicitDeny
         VERIFIER_SECRET_VALUE_READ_NEGATIVE=passed
SIM-045  OPERATOR_VERIFIER_WRONG_SECRET=implicitDeny × 2
         VERIFIER_WRONG_SECRET_NEGATIVE=passed
SIM-046  Erstlauf: OPERATOR_VERIFIER_SECRET_WRONG_REGION=allowed × 2
         Erstlauf: VERIFIER_SECRET_WRONG_REGION_NEGATIVE=failed
         Wiederholung: OPERATOR_VERIFIER_SECRET_WRONG_REGION=implicitDeny × 2
         Wiederholung: VERIFIER_SECRET_WRONG_REGION_NEGATIVE=passed
SIM-047  OPERATOR_VERIFIER_DESCRIBE_EXPRESS_SERVICE=allowed
         VERIFIER_DESCRIBE_EXPRESS_SERVICE_POSITIVE=passed
SIM-048  OPERATOR_VERIFIER_DESCRIBE_WRONG_SERVICE=implicitDeny
         VERIFIER_DESCRIBE_WRONG_SERVICE_NEGATIVE=passed
SIM-049  OPERATOR_VERIFIER_DESCRIBE_SERVICES=allowed
         VERIFIER_DESCRIBE_SERVICES_POSITIVE=passed
SIM-050  OPERATOR_VERIFIER_DESCRIBE_SERVICES_WRONG_SERVICE=implicitDeny
         VERIFIER_DESCRIBE_SERVICES_WRONG_SERVICE_NEGATIVE=passed
SIM-051  OPERATOR_VERIFIER_LIST_SERVICE_DEPLOYMENTS=allowed
         VERIFIER_LIST_SERVICE_DEPLOYMENTS_POSITIVE=passed
SIM-052  OPERATOR_VERIFIER_LIST_SERVICE_DEPLOYMENTS_WRONG_SERVICE=implicitDeny
         VERIFIER_LIST_SERVICE_DEPLOYMENTS_WRONG_SERVICE_NEGATIVE=passed
SIM-053  OPERATOR_VERIFIER_DESCRIBE_SERVICE_DEPLOYMENTS=allowed
         VERIFIER_DESCRIBE_SERVICE_DEPLOYMENTS_POSITIVE=passed
SIM-054  OPERATOR_VERIFIER_DESCRIBE_SERVICE_DEPLOYMENTS_WRONG_SERVICE=implicitDeny
         VERIFIER_DESCRIBE_SERVICE_DEPLOYMENTS_WRONG_SERVICE_NEGATIVE=passed
SIM-055  OPERATOR_VERIFIER_DESCRIBE_SERVICE_REVISIONS=allowed
         VERIFIER_DESCRIBE_SERVICE_REVISIONS_POSITIVE=passed
SIM-056  OPERATOR_VERIFIER_DESCRIBE_SERVICE_REVISIONS_WRONG_SERVICE=implicitDeny
         VERIFIER_DESCRIBE_SERVICE_REVISIONS_WRONG_SERVICE_NEGATIVE=passed
SIM-057  OPERATOR_VERIFIER_DESCRIBE_TASKS=allowed
         VERIFIER_DESCRIBE_TASKS_POSITIVE=passed
SIM-058  OPERATOR_VERIFIER_DESCRIBE_TASKS_WRONG_CLUSTER=implicitDeny
         VERIFIER_DESCRIBE_TASKS_WRONG_CLUSTER_NEGATIVE=passed
SIM-059  OPERATOR_VERIFIER_LIST_TASKS=allowed
         VERIFIER_LIST_TASKS_POSITIVE=passed
SIM-060  OPERATOR_VERIFIER_LIST_TASKS_WRONG_CLUSTER=implicitDeny
         VERIFIER_LIST_TASKS_WRONG_CLUSTER_NEGATIVE=passed
SIM-061  OPERATOR_VERIFIER_DESCRIBE_CLUSTERS=allowed
         VERIFIER_DESCRIBE_CLUSTERS_POSITIVE=passed
SIM-062  OPERATOR_VERIFIER_DESCRIBE_CLUSTERS_WRONG_CLUSTER=implicitDeny
         VERIFIER_DESCRIBE_CLUSTERS_WRONG_CLUSTER_NEGATIVE=passed
SIM-063  OPERATOR_VERIFIER_LIST_TAGS_FOR_RESOURCE=allowed
         VERIFIER_LIST_TAGS_FOR_RESOURCE_POSITIVE=passed
SIM-064  OPERATOR_VERIFIER_LIST_TAGS_FOR_RESOURCE_WRONG_SERVICE=implicitDeny
         VERIFIER_LIST_TAGS_FOR_RESOURCE_WRONG_SERVICE_NEGATIVE=passed
SIM-065  OPERATOR_VERIFIER_TASK_DEFINITION_READS=allowed allowed
         VERIFIER_TASK_DEFINITION_READS_POSITIVE=passed
SIM-066  OPERATOR_VERIFIER_TASK_DEFINITION_READS_WRONG_REGION=implicitDeny implicitDeny
         VERIFIER_TASK_DEFINITION_READS_WRONG_REGION_NEGATIVE=passed
SIM-067  OPERATOR_VERIFIER_ECR_READS=allowed allowed allowed allowed
         VERIFIER_ECR_READS_POSITIVE=passed
SIM-068  OPERATOR_VERIFIER_ECR_READS_WRONG_REPOSITORY=implicitDeny implicitDeny implicitDeny implicitDeny
         VERIFIER_ECR_READS_WRONG_REPOSITORY_NEGATIVE=passed
SIM-069  OPERATOR_VERIFIER_LOG_RESOURCE_READS=allowed allowed allowed
         VERIFIER_LOG_RESOURCE_READS_POSITIVE=passed
SIM-070  OPERATOR_VERIFIER_LOG_RESOURCE_READS_WRONG_LOG_GROUP=implicitDeny implicitDeny implicitDeny
         VERIFIER_LOG_RESOURCE_READS_WRONG_LOG_GROUP_NEGATIVE=passed
SIM-071  OPERATOR_VERIFIER_LOG_DESCRIBE_READS=allowed allowed
         VERIFIER_LOG_DESCRIBE_READS_POSITIVE=passed
SIM-072  OPERATOR_VERIFIER_LOG_DESCRIBE_READS_WRONG_REGION=implicitDeny implicitDeny
         VERIFIER_LOG_DESCRIBE_READS_WRONG_REGION_NEGATIVE=passed
```

## Nicht gewertete Versuche

- Ein früher Test nutzte durch eine unscharfe Dateisuche die falsche
  Policy-Datei. Daraus wurde kein Policybefund abgeleitet.
- Ein eingefügter Shell-/Python-Block wurde beschädigt; außerdem war ein
  `file://`-Aufruf für Listenparameter ungeeignet. Der Versuch wurde nicht
  ausgeführt beziehungsweise nicht als Simulatorentscheidung gewertet.
- Der erste Start von SIM-063 wurde beim Einfügen sichtbar beschädigt und
  brach wegen der Kollision von `set -u` mit der RVM-Shell-Funktion
  `rvm_bash_nounset` vor der AWS-Simulation ab. Er wurde nicht gewertet.
- Ein erster Entwurf für SIM-069 simulierte `logs:GetLogEvents` mit einem
  Logstream-ARN. Der IAM-Simulator lieferte dafür selbst mit minimalen
  Test-Policies und `Resource: "*"` ein `implicitDeny`, wertete dieselbe
  Aktion mit dem Loggruppen-ARN aber als `allowed`. Dieser Diagnoselauf wurde
  nicht als SIM-069 gewertet; der bestätigte Test verwendet für alle drei
  CloudWatch-Logs-Aktionen den vom Simulator auswertbaren Loggruppen-ARN.
- Erwartungswerte aus vorgeschlagenen, aber noch nicht ausgeführten Blöcken
  werden nicht als Ergebnis protokolliert.

## Nächster offener Einzelfall

Das nächste noch nicht protokollierte Testpaar beginnt mit `SIM-073`. Sein
genauer Prüfumfang wird vor der Ausführung anhand der aktuellen V2.3-Policies
festgelegt.

## Fortsetzungsregel

Für alle weiteren Testpaare wird dieselbe temporäre Datei
`/tmp/sim-065-066.sh` wiederverwendet. Vor jedem neuen Paar wird ihr bisheriger
Inhalt im Editor vollständig durch den neuen kontrollierten Block ersetzt.

1. Immer genau zwei fachlich zusammengehörige Simulatorfälle (Positiv- und
   Negativfall) in einem kontrollierten Block ausführen.
2. Beide tatsächlichen Terminalergebnisse einzeln prüfen.
3. Nur bei Übereinstimmung mit dem jeweiligen Soll beide Fälle als `bestanden`
   markieren.
4. Nach jedem bestandenen Testpaar beide Entscheidungen und Pass-Marker
   gemeinsam in diesem Dokument ergänzen und auf den PR-Branch committen.
5. Das nächste offene Testpaar eindeutig benennen.
6. Bei jeder Abweichung stoppen; während eines späteren Deployments niemals
   Berechtigungen reaktiv ergänzen.
7. Nach einem neuen Commit den geprüften Referenz-Commit in diesem Dokument
   aktualisieren oder eine neue klar abgegrenzte Prüfrunde beginnen.

## Noch ausstehende Gates außerhalb dieses Simulatorprotokolls

Dieses Dokument ersetzt nicht:

- Template- und Guard-Prüfungen
- Template-Hash- und Change-Set-Prüfungen
- AWS Access Analyzer
- unabhängige Reviews
- kontrollierte Live-Lifecycle-Tests
- Post-Delete-Restressourcenprüfung

Quelle für SIM-001 bis SIM-030: Repository-Datei aus Draft-PR #138,
Branch `agent/add-iam-simulator-test-protocol`, Blob
`d4a4dd753356154fde7d0e4d1ff1e0b2a1582667`.

Quelle für SIM-031 bis SIM-046: vollständiger exportierter Chatverlauf in
`Eingefügter Text(46).txt`. Es wurden ausschließlich darin belegte
Testergebnisse übernommen.

Quelle für SIM-047 und SIM-048: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-049 und SIM-050: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-051 und SIM-052: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-053 und SIM-054: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-055 und SIM-056: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-057 und SIM-058: vom Nutzer am 4. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem jeweils geprüften
Ausgangsstand.

Quelle für SIM-059 und SIM-060: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `35e25ffd927135eef9087102f13e2d53b2955c4d`.

Quelle für SIM-061 und SIM-062: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `12ce1ccc26b9f7375eb7ac6c983a2db08e1a1889`.

Quelle für SIM-063 und SIM-064: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `52095340ba3b37dba87bf65e46c8184c7606c957`.

Quelle für SIM-065 und SIM-066: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `b0083050893c06ee25b5e45ad6c3eb1f8231f0a9`.

Quelle für SIM-067 und SIM-068: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `7d27b310c4af876b4f1d8b9fa6dc49c7aac52be9`.

Quelle für SIM-069 und SIM-070: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `4c43c18cae02824257b7f01a70672ddcd76ea17c`.

Quelle für SIM-071 und SIM-072: vom Nutzer am 7. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `ef37f77a21b84be6d909bcd420a0cefcafa81b76`.
