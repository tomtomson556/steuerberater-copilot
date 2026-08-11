# AWS-Referenzdemo: IAM-Policy-Simulator-Testprotokoll

Stand: 11. August 2026\
Repository: `tomtomson556/steuerberater-copilot`  
Zuletzt geprüfter Ausgangsstand: `cb2ac53787f8428f8e6bc42a7ac64d8d9012005f`
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

- Bestätigte nummerierte Simulatorfälle: **100**
- Ergänzende bestätigte Gruppenmarker: **2**
- SIM-046: im Erstlauf fehlgeschlagen, nach Policy-Korrektur erfolgreich wiederholt
- SIM-086: im Erstlauf fehlgeschlagen, nach atomarer SLR-Paarbindung erfolgreich wiederholt
- SIM-075: historischer Verifier-Inventarstand mit 13 Policies; durch die ACM-Ergänzung sind aktuell 14 exakt freigegeben, die erneute Inventarprüfung folgt als SIM-101/102

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
| SIM-073 | Operator / Verifier | `iam:GetRole`, `iam:GetRolePolicy`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies` und `iam:ListRoleTags` | sechs exakt freigegebene Rollen | `allowed` × 30 | bestanden |
| SIM-074 | Operator / Verifier | dieselben fünf IAM-Rollen-Leseaktionen | nicht freigegebene Rolle im Referenzpfad | `implicitDeny` × 5 | bestanden |
| SIM-075 | Operator / Verifier | `iam:GetPolicy` und `iam:GetPolicyVersion` | 13 exakt freigegebene verwaltete Policies | `allowed` × 26 | bestanden |
| SIM-076 | Operator / Verifier | dieselben zwei IAM-Policy-Leseaktionen | nicht freigegebene Policy im Control-Plane-Pfad | `implicitDeny` × 2 | bestanden |
| SIM-077 | Operator / Verifier | `sts:GetCallerIdentity` | globale Ressource `*` | `allowed` | bestanden |
| SIM-078 | Operator / Verifier | `sts:AssumeRole` auf die feste CloudFormation-Service-Rolle | Rollenübernahme durch den read-only Verifier | `implicitDeny` | bestanden |
| SIM-079 | Operator / Verifier | `cloudformation:DescribeStackEvents`, `DescribeStackResource`, `DescribeStackResourceDrifts`, `DescribeStackResources`, `DescribeStacks`, `DetectStackDrift`, `GetTemplate` und `ListStackResources` | genehmigter Referenz-Stack, richtige Region | `allowed` × 8 | bestanden |
| SIM-080 | Operator / Verifier | dieselben acht CloudFormation-Stack-Leseaktionen | nicht genehmigter Stack, richtige Region | `implicitDeny` × 8 | bestanden |
| SIM-081 | Operator / Verifier | 31 regionale globale Leseaktionen für ACM, Application Auto Scaling, CloudFormation, CloudTrail, CloudWatch, EC2, ECS, ELB, Logs und Service Quotas | globale Ressource `*`, richtige Region `eu-central-1` | `allowed` × 31 | bestanden |
| SIM-082 | Operator / Verifier | dieselben 31 regionalen globalen Leseaktionen | globale Ressource `*`, falsche Region `eu-west-1` | `implicitDeny` × 31 | bestanden |
| SIM-083 | Task Execution Role / Permissions Boundary | sieben erforderliche Laufzeitaktionen für ECR-Pull, CloudWatch-Logs-Schreibzugriff und Secret-Lesen | breite Identity-Policy; ausschließlich freigegebene Referenzressourcen und richtige Region | `allowed` × 7 | bestanden |
| SIM-084 | Task Execution Role / Permissions Boundary | zehn adversariale Aktionen: fremde ECR-, Logs- und Secret-Ressourcen sowie nicht freigegebene Lösch-, Schreib- und S3-Aktionen | breite Identity-Policy; richtige Region | `implicitDeny` × 10 | bestanden |
| SIM-085 | Express Infrastructure Role / Permissions Boundary | `iam:CreateServiceLinkedRole` für Application Auto Scaling und Elastic Load Balancing | breite Identity-Policy; je exakter Service-Linked-Role-ARN mit zugehörigem `iam:AWSServiceName` | `allowed` × 2 | bestanden |
| SIM-086 | Express Infrastructure Role / Permissions Boundary | sechs adversariale IAM-Fälle: zwei gekreuzte ARN/Service-Kombinationen, falscher Service, fremder Service-Linked-Role-ARN sowie `CreateRole` und `DeleteRole` | breite Identity-Policy | Erstlauf: `allowed` × 2 und `implicitDeny` × 4; Wiederholung nach Policy-Korrektur: `implicitDeny` × 6 | bestanden nach Korrektur |
| SIM-087 | Express Infrastructure Role / Permissions Boundary | zehn ELBv2-Mutationen: `AddListenerCertificates`, `DeleteListener`, `DeleteLoadBalancer`, `DeleteRule`, `DeleteTargetGroup`, `DeregisterTargets`, `ModifyListener`, `ModifyRule`, `RegisterTargets` und `RemoveListenerCertificates` | breite Identity-Policy; passende ELBv2-Ressourcen mit `aws:ResourceTag/AmazonECSManaged=true` | `allowed` × 10 | bestanden |
| SIM-088 | Express Infrastructure Role / Permissions Boundary | dieselben zehn ELBv2-Mutationen | breite Identity-Policy; gleiche Ressourcen mit `aws:ResourceTag/AmazonECSManaged=false` | `implicitDeny` × 10 | bestanden |
| SIM-089 | Express Infrastructure Role / Permissions Boundary | vier ELBv2-Create-Aktionen: `CreateListener`, `CreateLoadBalancer`, `CreateRule` und `CreateTargetGroup` | breite Identity-Policy; passende ELBv2-Ressourcen mit `aws:ResourceTag/AmazonECSManaged=true` | `allowed` × 4 | bestanden |
| SIM-090 | Express Infrastructure Role / Permissions Boundary | dieselben vier ELBv2-Create-Aktionen | breite Identity-Policy; gleiche Ressourcen mit `aws:ResourceTag/AmazonECSManaged=false` | `implicitDeny` × 4 | bestanden |
| SIM-091 | Express Infrastructure Role / Permissions Boundary | `elasticloadbalancing:AddTags` auf synthetischen Load-Balancer-ARN | breite Identity-Policy; `elasticloadbalancing:CreateAction=CreateLoadBalancer` | `allowed` | bestanden |
| SIM-092 | Express Infrastructure Role / Permissions Boundary | `elasticloadbalancing:AddTags` auf denselben Load-Balancer-ARN | breite Identity-Policy; nicht freigegebener `elasticloadbalancing:CreateAction=CreateTrustStore` | `implicitDeny` | bestanden |
| SIM-093 | Express Infrastructure Role / Permissions Boundary | fünf EC2-Security-Group-Mutationen: `AuthorizeSecurityGroupEgress`, `AuthorizeSecurityGroupIngress`, `DeleteSecurityGroup`, `RevokeSecurityGroupEgress` und `RevokeSecurityGroupIngress` | breite Identity-Policy; synthetische Security Group mit `aws:ResourceTag/AmazonECSManaged=true` | `allowed` × 5 | bestanden |
| SIM-094 | Express Infrastructure Role / Permissions Boundary | dieselben fünf EC2-Security-Group-Mutationen | breite Identity-Policy; dieselbe Security Group mit `aws:ResourceTag/AmazonECSManaged=false` | `implicitDeny` × 5 | bestanden |
| SIM-095 | Express Infrastructure Role / Permissions Boundary | `ec2:CreateSecurityGroup` auf synthetische Security Group und VPC | breite Identity-Policy; `aws:RequestTag/AmazonECSManaged=true`; beide Ressourcenentscheidungen `allowed`; keine fehlenden Kontextwerte | `allowed` | bestanden |
| SIM-096 | Express Infrastructure Role / Permissions Boundary | `ec2:CreateSecurityGroup` auf dieselben synthetischen Ressourcen | breite Identity-Policy; `aws:RequestTag/AmazonECSManaged=false`; Security Group `implicitDeny`, VPC `allowed`; keine fehlenden Kontextwerte | `implicitDeny` | bestanden |
| SIM-097 | Express Infrastructure Role / Permissions Boundary | `ec2:CreateTags` auf synthetische Security Group beziehungsweise Security-Group-Rule | breite Identity-Policy; freigegebene `ec2:CreateAction`-Werte `CreateSecurityGroup`, `AuthorizeSecurityGroupIngress` und `AuthorizeSecurityGroupEgress`; keine fehlenden Kontextwerte | `allowed` × 3 | bestanden |
| SIM-098 | Express Infrastructure Role / Permissions Boundary | `ec2:CreateTags` auf synthetische Security Group und Security-Group-Rule | breite Identity-Policy; nicht freigegebene `ec2:CreateAction=CreateNetworkInterface`; keine fehlenden Kontextwerte | `implicitDeny` × 2 | bestanden |
| SIM-099 | Express Infrastructure Role / effektiver Policy-Pfad | `acm:RequestCertificate` mit AWS-Managed-Policy v6, ergänzender ACM-Identity-Policy und Express-Boundary | `aws:RequestTag/AmazonECSManaged=true`, `aws:RequestedRegion=eu-central-1`; Boundary erlaubt | `allowed` | bestanden |
| SIM-100 | Express Infrastructure Role / effektiver Policy-Pfad | `acm:RequestCertificate` mit derselben Policy-Kombination | `aws:RequestTag/AmazonECSManaged=false`, `aws:RequestedRegion=eu-central-1`; Boundary verweigert | `implicitDeny` | bestanden |

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

## Befund und Korrektur zu SIM-083

Der erste Lauf von SIM-083 schlug für `logs:CreateLogStream` und
`logs:PutLogEvents` fehl, während die fünf ECR- und Secrets-Manager-Aktionen
bereits `allowed` waren. Die Detailausgabe des IAM-Simulators zeigte für die
beiden Logs-Aktionen keine passende Boundary-Anweisung.

Die Ursache war das zu enge Ressourcenmuster
`...:log-group:/steuerberater-copilot/reference-demo/application:log-stream:*`
in `task-execution-boundary.json`. Es wurde auf das weiterhin ausschließlich
dieselbe Referenz-Loggruppe begrenzende AWS-Muster
`...:log-group:/steuerberater-copilot/reference-demo/application:*`
korrigiert. Ein isolierter Diagnoselauf bestätigte danach beide Logs-Aktionen
als `allowed`; der vollständige Lauf von SIM-083/084 gegen Commit
`85dd456187b093dab3e3f863fa54bb15e7714ecb` war anschließend erfolgreich.

## Befund und Korrektur zu SIM-086

Der erste Lauf gegen Commit
`e9910a9c81b36cba5604164cd39254f4d30c0698` bestätigte SIM-085, zeigte aber
bei SIM-086, dass die beiden zugelassenen Service-Linked-Role-ARNs jeweils
auch mit dem Service-Namen des anderen zulässigen Dienstes kombiniert werden
konnten:

```text
EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES=allowed allowed
EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES_POSITIVE=passed
EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES=allowed allowed implicitDeny implicitDeny implicitDeny implicitDeny
EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES_NEGATIVE=failed
```

Die Ursache war ein gemeinsames Boundary-Statement mit zwei Ressourcen-ARNs
und zwei Werten für `iam:AWSServiceName`. Dadurch waren die Werte nicht
paarweise gebunden. Das Statement wurde in zwei atomare Statements aufgeteilt:
je ein exakter Service-Linked-Role-ARN mit genau dem zugehörigen
`iam:AWSServiceName`. Ein statischer Regressionstest sichert diese
Paarbindung.

Durch die Aufteilung überschritt die Policy zunächst das AWS-Größenlimit für
Managed Policies. Deshalb wurden ausschließlich 14 optionale `Sid`-Felder
entfernt; Aktionen, Ressourcen, Bedingungen und die 18 Statements blieben
unverändert. Die kompakte Policygröße sank von 6.344 auf 5.797 Zeichen. Der
anschließende CI-Lauf #279 war vollständig erfolgreich.

Die Wiederholung gegen Commit
`6f18395ae1e94d4d337ce25fe11bca19ab8267c6` bestätigte sowohl die beiden
zulässigen Paare als auch alle sechs adversarialen Verweigerungen:

```text
EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES=allowed allowed
EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES_POSITIVE=passed
EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES=implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny
EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES_NEGATIVE=passed
```

Damit ist die Kreuzkombinationslücke geschlossen und SIM-086 bestanden.

## Befund und Korrektur zu ACM `RequestCertificate`

Ein unnummerierter Diagnoselauf zeigte vor SIM-099/100, dass der für die
Express Infrastructure Role vorgesehene Pfad `acm:RequestCertificate` mit der
AWS-Managed-Policy `AmazonECSInfrastructureRoleforExpressGatewayServices` in
der bestätigten Default-Version `v6` und dem damaligen Boundary-Modell nicht
als `allowed` ausgewertet wurde. Auch die isolierte AWS-Managed-Policy v6
lieferte für den bisherigen Certificate-ARN-/Resource-Tag-Pfad
`implicitDeny`, ohne fehlende Kontextwerte.

Die isolierte Gegenprobe bestätigte das passende Create-Modell:
`Resource="*"` mit `aws:RequestTag/AmazonECSManaged=true` und
`aws:RequestedRegion=eu-central-1` ergibt `allowed`; ein falscher Request-Tag
ergibt `implicitDeny`.

Daraufhin wurde die enge ergänzende Identity-Policy
`express-infrastructure-acm-request-policy.json` eingeführt und das
`acm:RequestCertificate`-Statement der Express-Boundary auf dieselbe
Request-Tag- und Regionssemantik korrigiert. Die übrigen ACM-Aktionen bleiben
weiterhin auf Certificate-ARN und `aws:ResourceTag/AmazonECSManaged=true`
begrenzt.

SIM-099/100 prüfen den effektiven Pfad aus AWS-Managed-Policy v6, ergänzender
ACM-Identity-Policy und Express-Boundary. Der Positivfall ist `allowed` und
`AllowedByPermissionsBoundary=True`; der falsche Request-Tag führt zu
`implicitDeny` und `AllowedByPermissionsBoundary=False`.

Im Negativfall meldet der Simulator zusätzlich nicht bereitgestellte Context
Keys aus anderen Statements der vollständigen Policies. Die für
`acm:RequestCertificate` relevanten Keys `aws:RequestTag/AmazonECSManaged` und
`aws:RequestedRegion` wurden jedoch bereitgestellt. Deshalb bewertet der
Test-Harness nur diese beiden Keys als für SIM-100 relevant.

## Ergänzende bestätigte Gruppenmarker

Diese Marker stammen aus bestandenen Sammelprüfungen. Weil die einzelnen
`EvalDecision`-Zeilen nicht vollständig erhalten sind, werden sie nicht als
zusätzliche nummerierte Simulatorfälle gezählt.

| ID | Bestätigter Marker | Bedeutung | Status |
|---|---|---|---|
| GRP-001 | `OPERATOR_WRONG_SERVICE_NEGATIVE=passed` | Operator darf die feste CloudFormation-Service-Rolle nicht an einen falschen Service übergeben. | bestanden |
| GRP-002 | `OPERATOR_WRONG_ROLE_NEGATIVE=passed` | Operator darf keine andere Rolle an CloudFormation übergeben. | bestanden |

## Ausführungsnachweise SIM-031 bis SIM-100

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
SIM-073  OPERATOR_VERIFIER_IAM_ROLE_READS=allowed × 30
         VERIFIER_IAM_ROLE_READS_POSITIVE=passed
SIM-074  OPERATOR_VERIFIER_IAM_ROLE_READS_WRONG_ROLE=implicitDeny × 5
         VERIFIER_IAM_ROLE_READS_WRONG_ROLE_NEGATIVE=passed
SIM-075  OPERATOR_VERIFIER_IAM_POLICY_READS=allowed × 26
         VERIFIER_IAM_POLICY_READS_POSITIVE=passed
SIM-076  OPERATOR_VERIFIER_IAM_POLICY_READS_WRONG_POLICY=implicitDeny × 2
         VERIFIER_IAM_POLICY_READS_WRONG_POLICY_NEGATIVE=passed
SIM-077  OPERATOR_VERIFIER_STS_CALLER_IDENTITY=allowed
         VERIFIER_STS_CALLER_IDENTITY_POSITIVE=passed
SIM-078  OPERATOR_VERIFIER_STS_ASSUME_ROLE=implicitDeny
         VERIFIER_STS_ASSUME_ROLE_NEGATIVE=passed
SIM-079  OPERATOR_VERIFIER_CLOUDFORMATION_STACK_READS=allowed × 8
         VERIFIER_CLOUDFORMATION_STACK_READS_POSITIVE=passed
SIM-080  OPERATOR_VERIFIER_CLOUDFORMATION_STACK_READS_WRONG_STACK=implicitDeny × 8
         VERIFIER_CLOUDFORMATION_STACK_READS_WRONG_STACK_NEGATIVE=passed
SIM-081  OPERATOR_VERIFIER_REGIONAL_GLOBAL_READS=allowed × 31
         VERIFIER_REGIONAL_GLOBAL_READS_POSITIVE=passed
SIM-082  OPERATOR_VERIFIER_REGIONAL_GLOBAL_READS_WRONG_REGION=implicitDeny × 31
         VERIFIER_REGIONAL_GLOBAL_READS_WRONG_REGION_NEGATIVE=passed
SIM-083  TASK_EXECUTION_BOUNDARY_ALLOWED_ACTIONS=allowed × 7
         TASK_EXECUTION_BOUNDARY_ALLOWED_ACTIONS_POSITIVE=passed
SIM-084  TASK_EXECUTION_BOUNDARY_ADVERSARIAL_DENIES=implicitDeny × 10
         TASK_EXECUTION_BOUNDARY_ADVERSARIAL_DENIES_NEGATIVE=passed
SIM-085  EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES=allowed allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_SLR_CREATES_POSITIVE=passed
SIM-086  Erstlauf: EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES=allowed allowed implicitDeny implicitDeny implicitDeny implicitDeny
         Erstlauf: EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES_NEGATIVE=failed
         Wiederholung: EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES=implicitDeny × 6
         Wiederholung: EXPRESS_INFRASTRUCTURE_BOUNDARY_IAM_ADVERSARIAL_DENIES_NEGATIVE=passed
SIM-087  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_MUTATIONS=allowed × 10
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_MUTATIONS_POSITIVE=passed
SIM-088  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_MUTATIONS_WRONG_TAG=implicitDeny × 10
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_MUTATIONS_WRONG_TAG_NEGATIVE=passed
SIM-089  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_CREATES=allowed × 4
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_CREATES_POSITIVE=passed
SIM-090  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_CREATES_WRONG_TAG=implicitDeny × 4
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_CREATES_WRONG_TAG_NEGATIVE=passed
SIM-091  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_ADD_TAGS_CREATE_LOAD_BALANCER=allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_ADD_TAGS_CREATE_LOAD_BALANCER_POSITIVE=passed
SIM-092  EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_ADD_TAGS_WRONG_CREATE_ACTION=implicitDeny
         EXPRESS_INFRASTRUCTURE_BOUNDARY_ELB_ADD_TAGS_WRONG_CREATE_ACTION_NEGATIVE=passed
SIM-093  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_SG_MUTATIONS=allowed × 5
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_SG_MUTATIONS_POSITIVE=passed
SIM-094  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_SG_MUTATIONS_WRONG_TAG=implicitDeny × 5
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_SG_MUTATIONS_WRONG_TAG_NEGATIVE=passed
SIM-095  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG=allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_RESOURCES=security-group=allowed vpc=allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_MISSING_CONTEXT=none
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_POSITIVE=passed
SIM-096  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_WRONG_TAG=implicitDeny
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_WRONG_TAG_RESOURCES=security-group=implicitDeny vpc=allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_WRONG_TAG_MISSING_CONTEXT=none
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_SG_WRONG_TAG_NEGATIVE=passed
SIM-097  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS=allowed allowed allowed
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS_MISSING_CONTEXT=none|none|none
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS_POSITIVE=passed
SIM-098  EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS_WRONG_CREATE_ACTION=implicitDeny implicitDeny
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS_WRONG_CREATE_ACTION_MISSING_CONTEXT=none|none
         EXPRESS_INFRASTRUCTURE_BOUNDARY_EC2_CREATE_TAGS_WRONG_CREATE_ACTION_NEGATIVE=passed
SIM-099  AWS_MANAGED_POLICY_VERSION=v6
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE=allowed
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_BOUNDARY=True
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_MISSING_CONTEXT=none
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_POSITIVE=passed
SIM-100  EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_WRONG_TAG=implicitDeny
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_WRONG_TAG_BOUNDARY=False
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_WRONG_TAG_MISSING_CONTEXT=iam:AWSServiceName|application-autoscaling:service-namespace|aws:ResourceTag/AmazonECSManaged|elasticloadbalancing:CreateAction|ec2:CreateAction
         EXPRESS_INFRASTRUCTURE_ACM_REQUEST_CERTIFICATE_WRONG_TAG_NEGATIVE=passed
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
- Der erste Entwurf für SIM-091/092 prüfte `elasticloadbalancing:AddTags` auf
  Load Balancer, Listener, Listener Rule und Target Group. Nur der Load-
  Balancer-Pfad wurde als `allowed` ausgewertet. Ein nachgeschalteter
  Minimaltest ohne Permissions Boundary bestätigte dasselbe Simulatorverhalten:
  Load Balancer `allowed`, Listener, Listener Rule und Target Group jeweils
  `implicitDeny`, ohne fehlende Kontextwerte. Dieser Diagnoselauf wurde nicht
  als SIM-091/092 gewertet; der bestätigte Test beschränkt sich auf den vom
  Simulator auswertbaren Load-Balancer-Pfad und prüft dort gezielt
  `elasticloadbalancing:CreateAction`.
- Der erste Start von SIM-093/094 brach vor einer verwertbaren
  Simulatorentscheidung mit einem `ValidationError` für
  `permissionsBoundaryPolicyInputList` ab. Ursache war die Übergabe der
  Boundary über einen für diesen Listenparameter ungeeigneten `file://`-Wert.
  Dieser Lauf wurde nicht als SIM-Fall gewertet; die erfolgreiche Wiederholung
  übergab Policy und Boundary jeweils als vollständigen JSON-String.
- Der erste Negativlauf für SIM-096 lieferte bereits `implicitDeny`, meldete
  jedoch mehrere nicht bereitgestellte Context Keys aus anderen Statements der
  vollständigen Express-Boundary und endete deshalb mit dem lokalen
  `...WRONG_TAG_NEGATIVE=failed`-Marker. Dieser Lauf wurde nicht gewertet. Die
  Wiederholung stellte alle gemeldeten Context Keys explizit bereit und
  bestätigte bei `MISSING_CONTEXT=none` erneut Security Group `implicitDeny`,
  VPC `allowed` und die Gesamtentscheidung `implicitDeny`.
- Vor SIM-099/100 zeigte ein unnummerierter ACM-Diagnoselauf, dass
  `acm:RequestCertificate` mit der AWS-Managed-Policy v6 und dem damaligen
  Certificate-ARN-/Resource-Tag-Modell nicht `allowed` wurde. Dieser Lauf
  diente zur Ursachenanalyse und wurde nicht als nummerierter SIM-Fall gewertet.
- Der erste vorgesehene SIM-100-Lauf lieferte bereits `implicitDeny` und
  `AllowedByPermissionsBoundary=False`, endete aber mit dem lokalen
  `...WRONG_TAG_NEGATIVE=failed`-Marker, weil der Harness pauschal
  `MISSING_CONTEXT=none` verlangte. Die zusätzlich gemeldeten Keys stammten aus
  anderen Statements; die für `RequestCertificate` relevanten Context Keys
  waren vorhanden. Der Harness wurde ohne Policy-Änderung präzisiert und die
  erfolgreiche Wiederholung erst danach als SIM-100 gewertet.
- Erwartungswerte aus vorgeschlagenen, aber noch nicht ausgeführten Blöcken
  werden nicht als Ergebnis protokolliert.

## Nächstes offenes Testpaar

Das nächste noch nicht protokollierte Testpaar ist `SIM-101/102`:

- SIM-101: `iam:GetPolicy` und `iam:GetPolicyVersion` auf allen aktuell 14 exakt
  freigegebenen verwalteten Policies des Operator-Verifiers; erwartet
  `allowed` × 28.
- SIM-102: dieselben beiden Leseaktionen auf einer nicht freigegebenen Policy im
  Control-Plane-Pfad; erwartet `implicitDeny` × 2.

Damit wird der historische 13-Policy-Inventarstand aus SIM-075 nach der
ACM-Ergänzung ausdrücklich neu bestätigt.

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


Quelle für SIM-073 und SIM-074: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `4f650374c2944828f20aed6929052f46feaa81e3`.
Quelle für SIM-075 und SIM-076: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `fb5f6e6f444207981e91df6c091cb16ba15a38c9`.
Der dort geprüfte Bestand von 13 verwalteten Policies ist historisch korrekt;
die später ergänzte ACM-Request-Policy wird separat mit SIM-101/102 erneut
geprüft.

Quelle für SIM-077 und SIM-078: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `4f18310a547b99b16f34b6fb98dcb0e625893141`.

Quelle für SIM-079 und SIM-080: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `02491a2ce7768580d3fb70559eca3eb2155ba9b7`.

Quelle für SIM-081 und SIM-082: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `11b35a03654a79a8787fbd1e4205c0f6c7d08e8e`.

Quelle für SIM-083 und SIM-084: vom Nutzer am 8. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem nach Korrektur der
Task-Execution-Boundary geprüften Ausgangsstand
`85dd456187b093dab3e3f863fa54bb15e7714ecb`.

Quelle für SIM-085 und SIM-086: vom Nutzer am 9. August 2026 ausdrücklich
gemeldete Terminalausgaben des Erstlaufs auf
`e9910a9c81b36cba5604164cd39254f4d30c0698` und der erfolgreichen Wiederholung
nach Korrektur der Express-Infrastructure-Boundary auf
`6f18395ae1e94d4d337ce25fe11bca19ab8267c6`.

Quelle für SIM-087 und SIM-088: vom Nutzer am 9. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `4e6ea71c9a117481a3d7fbb1f218b470be17a3b3`.

Quelle für SIM-089 und SIM-090: vom Nutzer am 9. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `919bb16bfeaf54bab04de151cfa72ebb2902195b`.

Quelle für SIM-091 und SIM-092: vom Nutzer am 11. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `b76a72a051eef9d762621804bdee69ceb26c2fc1`.

Quelle für SIM-093 und SIM-094: vom Nutzer am 11. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `d51ce00e898d1de983f813ca8961df4031954381`.

Quelle für SIM-095 und SIM-096: vom Nutzer am 11. August 2026 ausdrücklich
gemeldete Terminalausgaben der erfolgreichen Wiederholung auf dem geprüften
Ausgangsstand `3b5e8e3a9c95ce2cd75d1bf4bceb1d01e6590aba`.

Quelle für SIM-097 und SIM-098: vom Nutzer am 11. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften
Ausgangsstand `3599fd04bdc743e2e065a3b9be18ded4eeed4d7a`.

Quelle für SIM-099 und SIM-100: vom Nutzer am 11. August 2026 ausdrücklich
gemeldete Terminalausgaben der erfolgreichen Simulationen auf dem geprüften
Ausgangsstand `cb2ac53787f8428f8e6bc42a7ac64d8d9012005f`; bestätigte AWS-Managed-Policy-Version `v6`.
