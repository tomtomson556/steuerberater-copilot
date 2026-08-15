# AWS-Referenzdemo: IAM-Policy-Simulator-Testprotokoll

Stand: 15. August 2026\
Repository: `tomtomson556/steuerberater-copilot`  
Zuletzt geprüfter Ausgangsstand: `ccbe59333c30cffbbc32ddd7fc0ad654c4fc08be`
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

- Bestätigte nummerierte Simulatorfälle: **120**
- Ergänzende bestätigte Gruppenmarker: **2**
- SIM-046: im Erstlauf fehlgeschlagen, nach Policy-Korrektur erfolgreich wiederholt
- SIM-086: im Erstlauf fehlgeschlagen, nach atomarer SLR-Paarbindung erfolgreich wiederholt
- SIM-075: historischer Verifier-Inventarstand mit 13 Policies; durch die ACM-Ergänzung sind aktuell 14 exakt freigegeben und mit SIM-101/102 erneut bestätigt

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
| SIM-101 | Operator / Verifier | `iam:GetPolicy` und `iam:GetPolicyVersion` | alle aktuell 14 exakt freigegebenen verwalteten Policies; 28 `ResourceSpecificResults`, keine fehlenden Kontextwerte | `allowed` × 28 | bestanden |
| SIM-102 | Operator / Verifier | dieselben zwei IAM-Policy-Leseaktionen | nicht freigegebene Policy im Control-Plane-Pfad | `implicitDeny` × 2 | bestanden |
| SIM-103 | CloudFormation-Service-Rolle | `iam:CreateRole` für Task Execution Role und Express Infrastructure Role | je exakte Zielrolle mit der jeweils vorgeschriebenen Permissions Boundary und allen fünf Pflicht-Tags; keine fehlenden Kontextwerte | `allowed` × 2 | bestanden |
| SIM-104 | CloudFormation-Service-Rolle | dieselben beiden `iam:CreateRole`-Pfade | Permissions Boundaries absichtlich zwischen den beiden Rollen gekreuzt; keine fehlenden Kontextwerte | `implicitDeny` × 2 | bestanden |
| SIM-105 | CloudFormation-Service-Rolle | `iam:GetRole` und `iam:DeleteRole` | Task Execution Role und Express Infrastructure Role; vier `ResourceSpecificResults`, keine fehlenden Kontextwerte, keine Trunkierung | `allowed` × 4 | bestanden |
| SIM-106 | CloudFormation-Service-Rolle | `iam:PutRolePermissionsBoundary`, `iam:DeleteRolePermissionsBoundary`, `iam:UpdateAssumeRolePolicy`, `iam:UpdateRole` und `iam:UpdateRoleDescription` | beide Rollen; statisch keine passenden Statements oder Allow-Wildcards; zehn `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; keine passenden Statements, keine Trunkierung | `implicitDeny` × 10 | bestanden |
| SIM-107 | CloudFormation-Service-Rolle | `iam:AttachRolePolicy` und `iam:DetachRolePolicy` | drei exakt genehmigte Rollen-/Policy-Bindungen: Task Execution Role mit AWS Task-Execution-Policy sowie Express Infrastructure Role mit AWS Express-Policy und kundenverwalteter ACM-Request-Policy; sechs `ResourceSpecificResults`, keine fehlenden Kontextwerte, keine Trunkierung | `allowed` × 6 | bestanden |
| SIM-108 | CloudFormation-Service-Rolle | dieselben beiden Aktionen | drei gekreuzte und zwei fremde Rollen-/Policy-Bindungen; zehn `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; keine passenden Statements, keine Trunkierung | `implicitDeny` × 10 | bestanden |
| SIM-109 | CloudFormation-Service-Rolle | `iam:PutRolePolicy` und `iam:DeleteRolePolicy` | ausschließlich Task Execution Role; statisch je genau eine Ressourcenfreigabe in Lifecycle-Policy und Boundary, keine Action-Wildcards; zwei `ResourceSpecificResults`, keine fehlenden Kontextwerte, keine Trunkierung; Policy-Name und -Inhalt bleiben außerhalb der Simulatoraussage durch Template, Guard und Hash gebunden | `allowed` × 2 | bestanden |
| SIM-110 | CloudFormation-Service-Rolle | dieselben beiden Inline-Policy-Aktionen | Express Infrastructure Role und synthetische fremde Rolle; vier `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; keine passenden Statements, keine Trunkierung | `implicitDeny` × 4 | bestanden |
| SIM-111 | CloudFormation-Service-Rolle | `iam:GetRolePolicy`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies` und `iam:ListRoleTags` | Task Execution Role und Express Infrastructure Role; vier vollständige Policy-Dokumente, acht `ResourceSpecificResults`, keine fehlenden Kontextwerte, Boundary achtmal freigebend, keine Trunkierung | `allowed` × 8 | bestanden |
| SIM-112 | CloudFormation-Service-Rolle | vollständiger unbedingter Rollen-Read/Delete-Block mit `iam:DeleteRole`, `iam:GetRole` und den vier Metadaten-Leseaktionen aus SIM-111 | synthetische fremde Rolle im Referenzpfad; sechs `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte, keine passenden Statements, Boundary niemals freigebend, keine Trunkierung | `implicitDeny` × 6 | bestanden |
| SIM-113 | CloudFormation-Service-Rolle | `iam:TagRole` und `iam:UntagRole` | Task Execution Role und Express Infrastructure Role; vollständige effektive Policies, exakte fünf Request-Tag-Werte, exakt fünf zulässige Tag-Schlüssel und passender `iam:ResourceTag/Project`-Wert; vier `ResourceSpecificResults`, keine fehlenden Kontextwerte, Boundary viermal freigebend, keine Trunkierung | `allowed` × 4 | bestanden |
| SIM-114 | CloudFormation-Service-Rolle | dieselben beiden Rollen-Tag-Aktionen | unzulässiger Tag-Schlüssel `Owner` auf beiden Rollen, falscher Project-Wert auf beiden Rollen sowie synthetische fremde Rolle; zehn `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte, keine passenden Statements, relevante Kontextwerte vollständig, keine Trunkierung; Boundary bei den acht Tag-Guard-Gegenfällen freigebend und bei der fremden Rolle niemals freigebend | `implicitDeny` × 10 | bestanden |
| SIM-115 | CloudFormation-Service-Rolle | `ecr:CreateRepository`, `ecr:TagResource`, `logs:CreateLogGroup` und `logs:TagResource` | jeweils aktionsgerechte Referenzressource; vollständige effektive Policies, fünf feste Request-Tags, exakt fünf zulässige Tag-Schlüssel und richtige Region; vier einzeln simulierte `ResourceSpecificResults`, keine fehlenden Kontextwerte, Boundary viermal freigebend, keine Trunkierung | `allowed` × 4 | bestanden |
| SIM-116 | CloudFormation-Service-Rolle | dieselben vier ECR-/Logs-Create-/Tag-Aktionen | unzulässiger Tag-Schlüssel `Owner`, falscher Project-Wert und falsche Region jeweils auf den vier korrekten Action-/Ressourcen-Paaren sowie vier fremde ECR-/Log-Group-Ressourcen; 16 `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte, relevante Kontextwerte vollständig, keine passenden Statements, keine Trunkierung; Boundary bei den zwölf Condition-Gegenfällen freigebend und bei den vier fremden Ressourcen niemals freigebend | `implicitDeny` × 16 | bestanden |
| SIM-117 | CloudFormation-Service-Rolle | `ecr:DescribeRepositories`, `ecr:ListTagsForResource`, `ecr:PutImageTagMutability`, `ecr:UntagResource` und `ecr:DeleteRepository` | festes Referenz-Repository; vollständige effektive Policies; fünf einzeln simulierte `ResourceSpecificResults`; keine fehlenden Kontextwerte; fünf passende Statements; Boundary fünfmal freigebend; keine Trunkierung | `allowed` × 5 | bestanden |
| SIM-118 | CloudFormation-Service-Rolle | dieselben fünf ECR-Read-/Update-/Delete-Aktionen | fremdes Repository in `eu-central-1` und fest benanntes Repository in `eu-west-1`; zehn einzeln simulierte `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; relevante Kontextwerte vollständig; keine passenden Statements; Boundary niemals freigebend; keine Trunkierung | `implicitDeny` × 10 | bestanden |
| SIM-119 | CloudFormation-Service-Rolle | `logs:DescribeLogGroups`, `logs:ListTagsForResource`, `logs:PutRetentionPolicy`, `logs:DeleteRetentionPolicy`, `logs:UntagResource` und `logs:DeleteLogGroup` | `DescribeLogGroups` mit globaler Ressource `*` und richtiger Region; die übrigen fünf Aktionen auf der festen Application Log Group; vier vollständige Policy-Dokumente, sechs atomare Evaluationen und fünf `ResourceSpecificResults`; keine fehlenden Kontextwerte; sechs passende Statements; Boundary sechsmal freigebend; keine Trunkierung | `allowed` × 6 | bestanden |
| SIM-120 | CloudFormation-Service-Rolle | dieselben sechs CloudWatch-Logs-Read-/Update-/Delete-Aktionen | fremde Log Group in `eu-central-1` für die fünf ressourcengebundenen Aktionen, `DescribeLogGroups` mit globaler Ressource `*` in `eu-west-1` sowie die feste Log Group in `eu-west-1` für die fünf ressourcengebundenen Aktionen; elf atomare Evaluationen und zehn `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; relevante Kontextwerte vollständig; keine passenden Statements; Boundary niemals freigebend; keine Trunkierung | `implicitDeny` × 11 | bestanden |

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

## Ausführungsnachweise SIM-031 bis SIM-120

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
SIM-101  OPERATOR_VERIFIER_IAM_POLICY_INVENTORY=14
         OPERATOR_VERIFIER_IAM_POLICY_READS_TOP_LEVEL=2
         OPERATOR_VERIFIER_IAM_POLICY_READ_ACTIONS=iam:GetPolicy iam:GetPolicyVersion
         OPERATOR_VERIFIER_IAM_POLICY_READS=allowed × 28
         OPERATOR_VERIFIER_IAM_POLICY_READS_TOTAL=28
         OPERATOR_VERIFIER_IAM_POLICY_READS_MISSING_CONTEXT=none
         VERIFIER_IAM_POLICY_READS_POSITIVE=passed
SIM-102  OPERATOR_VERIFIER_IAM_POLICY_READS_WRONG_POLICY=implicitDeny implicitDeny
         VERIFIER_IAM_POLICY_READS_WRONG_POLICY_NEGATIVE=passed
SIM-103  CFN_SERVICE_ROLE_CREATE_ROLES=allowed allowed
         CFN_SERVICE_ROLE_CREATE_ROLES_MISSING_CONTEXT=none|none
         CFN_SERVICE_ROLE_CREATE_ROLES_POSITIVE=passed
SIM-104  CFN_SERVICE_ROLE_CREATE_ROLES_WRONG_BOUNDARY=implicitDeny implicitDeny
         CFN_SERVICE_ROLE_CREATE_ROLES_WRONG_BOUNDARY_MISSING_CONTEXT=none|none
         CFN_SERVICE_ROLE_CREATE_ROLES_WRONG_BOUNDARY_NEGATIVE=passed
SIM-105  CFN_SERVICE_ROLE_ROLE_LIFECYCLE_READ_DELETE=allowed allowed allowed allowed
         CFN_SERVICE_ROLE_ROLE_LIFECYCLE_READ_DELETE_TOTAL=4
         CFN_SERVICE_ROLE_ROLE_LIFECYCLE_READ_DELETE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_LIFECYCLE_READ_DELETE_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_LIFECYCLE_READ_DELETE_POSITIVE=passed
SIM-106  CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_STATIC_ACTIONS=5
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_STATIC_MATCHING_STATEMENTS=0
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_STATIC_ALLOW_MATCHES=0
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS=implicitDeny × 10
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_TOTAL=10
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_MISSING_CONTEXT=aws:RequestTag/Component|aws:RequestTag/Environment|aws:RequestTag/Lifecycle|aws:RequestTag/ManagedBy|aws:RequestTag/Project|aws:RequestedRegion|aws:TagKeys|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_TRUNCATED=false
         CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_NEGATIVE=passed
SIM-107  CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_ACTIONS=2
         CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_LIFECYCLE_BINDINGS=3
         CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_BOUNDARY_BINDINGS=3
         CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_MANAGED_POLICY_BINDINGS_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH=allowed × 6
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_TOTAL=6
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_BINDINGS=3
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_TRUNCATED=false
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_POSITIVE=passed
SIM-108  CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS=implicitDeny × 10
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_TOTAL=10
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_CASES=5
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_MISSING_CONTEXT=aws:RequestTag/Component|aws:RequestTag/Environment|aws:RequestTag/Lifecycle|aws:RequestTag/ManagedBy|aws:RequestTag/Project|aws:RequestedRegion|aws:TagKeys|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_TRUNCATED=false
         CFN_SERVICE_ROLE_MANAGED_POLICY_ATTACH_DETACH_WRONG_BINDINGS_NEGATIVE=passed
SIM-109  CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_ACTIONS=2
         CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_LIFECYCLE_RESOURCES=1
         CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_BOUNDARY_RESOURCES=1
         CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_INLINE_POLICY_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE=allowed allowed
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_TOTAL=2
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_TRUNCATED=false
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_POSITIVE=passed
SIM-110  CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES=implicitDeny × 4
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_TOTAL=4
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_MISSING_CONTEXT=aws:RequestTag/Component|aws:RequestTag/Environment|aws:RequestTag/Lifecycle|aws:RequestTag/ManagedBy|aws:RequestTag/Project|aws:RequestedRegion|aws:TagKeys|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_TRUNCATED=false
         CFN_SERVICE_ROLE_INLINE_POLICY_LIFECYCLE_WRONG_ROLES_NEGATIVE=passed
SIM-111  CFN_SERVICE_ROLE_ROLE_READS_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_POSITIVE_ACTIONS=4
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_STATEMENT_ACTIONS=6
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_ACTION_DOCUMENT_PAIRS=12
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_LIFECYCLE_RESOURCES=2
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_BOUNDARY_RESOURCES=2
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_CONDITIONED_STATEMENTS=0
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_ROLE_READS_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_ROLE_METADATA_READS=allowed × 8
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_TOTAL=8
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_BOUNDARY_ALLOWED=8
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_METADATA_READS_POSITIVE=passed
SIM-112  CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE=implicitDeny × 6
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_TOTAL=6
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_MISSING_CONTEXT=aws:RequestTag/Component|aws:RequestTag/Environment|aws:RequestTag/Lifecycle|aws:RequestTag/ManagedBy|aws:RequestTag/Project|aws:RequestedRegion|aws:TagKeys|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_READ_DELETE_WRONG_ROLE_NEGATIVE=passed
SIM-113  CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_ACTIONS=2
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_LIFECYCLE_RESOURCES=2
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_BOUNDARY_RESOURCES=2
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_REQUEST_TAGS=5
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_ALLOWED_TAG_KEYS=5
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_ROLE_TAGS_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE=allowed × 4
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_TOTAL=4
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_MATCHED_STATEMENTS=4
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_TAG_LIFECYCLE_POSITIVE=passed
SIM-114  CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY=implicitDeny × 4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_TOTAL=4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_MISSING_CONTEXT=aws:RequestedRegion|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_KEY_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT=implicitDeny × 4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_TOTAL=4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_MISSING_CONTEXT=aws:RequestedRegion|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_PROJECT_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE=implicitDeny × 2
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_TOTAL=2
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_MISSING_CONTEXT=aws:RequestedRegion|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_ROLE_TAGS_WRONG_ROLE_TRUNCATED=false
         CFN_SERVICE_ROLE_ROLE_TAG_GUARDS_NEGATIVE_TOTAL=10
         CFN_SERVICE_ROLE_ROLE_TAG_GUARDS_NEGATIVE=passed
SIM-115  AWS_REGION_CHECK=passed
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_ACTIONS=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_ACTION_DOCUMENT_PAIRS=8
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_FOUNDATION_RESOURCES=6
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_BOUNDARY_RESOURCES=2
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_REQUEST_TAGS=5
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_ALLOWED_TAG_KEYS=5
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE=allowed × 4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_TOTAL=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_MATCHED_STATEMENTS=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_LIFECYCLE_POSITIVE=passed
SIM-116  CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY=implicitDeny × 4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_TOTAL=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_MISSING_CONTEXT=ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_KEY_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT=implicitDeny × 4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_TOTAL=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_MISSING_CONTEXT=ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_PROJECT_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION=implicitDeny × 4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_TOTAL=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_MISSING_CONTEXT=ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_BOUNDARY_ALLOWED=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_REGION_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES=implicitDeny × 4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_TOTAL=4
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_MISSING_CONTEXT=ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_WRONG_RESOURCES_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_GUARDS_NEGATIVE_TOTAL=16
         CFN_SERVICE_ROLE_ECR_LOG_CREATE_GUARDS_NEGATIVE=passed
SIM-117  CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_ACTIONS=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_ACTION_DOCUMENT_PAIRS=10
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_FOUNDATION_RESOURCES=2
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_BOUNDARY_RESOURCES=2
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_CONDITIONED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_ECR_LIFECYCLE=allowed × 5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_TOTAL=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_MATCHED_STATEMENTS=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_BOUNDARY_ALLOWED=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_POSITIVE=passed
SIM-118  CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY=implicitDeny × 5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_TOTAL=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REPOSITORY_NEGATIVE=passed
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION=implicitDeny × 5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_TOTAL=5
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_TRUNCATED=false
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_WRONG_REGION_NEGATIVE=passed
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_NEGATIVE_TOTAL=10
         CFN_SERVICE_ROLE_ECR_LIFECYCLE_NEGATIVE=passed
SIM-119  CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_DOCUMENTS=4
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_ACTIONS=6
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_ACTION_DOCUMENT_PAIRS=12
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_DESCRIBE_FOUNDATION_RESOURCES=1
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_DESCRIBE_BOUNDARY_RESOURCES=1
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_FOUNDATION_RESOURCES=2
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_BOUNDARY_RESOURCES=2
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_DESCRIBE_CONDITIONED_STATEMENTS=2
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_CONDITIONED_STATEMENTS=0
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_ACTION_WILDCARDS=0
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_STATIC_CHECK=passed
         CFN_SERVICE_ROLE_LOG_LIFECYCLE=allowed × 6
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_TOTAL=6
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_RESOURCE_SPECIFIC_RESULTS=5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_MATCHED_STATEMENTS=6
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_BOUNDARY_ALLOWED=6
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_TRUNCATED=false
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_POSITIVE=passed
SIM-120  CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_LOG_GROUP=implicitDeny × 5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_LOG_GROUP_TOTAL=5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_LOG_GROUP_RESOURCE_SPECIFIC_RESULTS=5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_DESCRIBE_WRONG_REGION=implicitDeny
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_DESCRIBE_WRONG_REGION_TOTAL=1
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_DESCRIBE_WRONG_REGION_RESOURCE_SPECIFIC_RESULTS=0
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_REGION=implicitDeny × 5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_REGION_TOTAL=5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_WRONG_REGION_RESOURCE_SPECIFIC_RESULTS=5
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_TOTAL=11
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_RESOURCE_SPECIFIC_RESULTS=10
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_MISSING_CONTEXT=aws:RequestTag/Component|aws:RequestTag/Environment|aws:RequestTag/Lifecycle|aws:RequestTag/ManagedBy|aws:RequestTag/Project|aws:TagKeys|ec2:CreateAction|ec2:ResourceTag/Project|ecs:ResourceTag/Project|iam:PassedToService|iam:PermissionsBoundary|iam:PolicyARN|iam:ResourceTag/Project|secretsmanager:ForceDeleteWithoutRecovery
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_RELEVANT_MISSING_CONTEXT=none
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_MATCHED_STATEMENTS=0
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_BOUNDARY_ALLOWED=0
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE_TRUNCATED=false
         CFN_SERVICE_ROLE_LOG_LIFECYCLE_NEGATIVE=passed
```

## Nicht gewertete Versuche

- Die ersten vier Harness-Ausführungen für das spätere SIM-117/118-Paar
  wurden nicht gewertet: zunächst wechselte ein `jq`-Ausdruck innerhalb
  der Action-Prüfung versehentlich auf das Action-Array; danach beendete
  `set -e` eine Arithmetik mit dem korrekten Ergebnis null; ein erster
  Korrekturblock verwendete anschließend eine fehlerhafte
  Command-Substitution; zuletzt wurde ein von AWS nicht ausgegebenes
  `IsTruncated`-Feld als `null` statt als `false` interpretiert. Keine
  dieser Ausführungen ergab einen Policybefund oder erhielt SIM-Nummern. Erst
  die vollständig bestandene Wiederholung wurde als SIM-117/118 gewertet.

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
- Der erste vorgesehene SIM-101-Lauf auf Commit
  `d97551c78abd8d3607d1290da902c3735e67796b` bestätigte den statischen
  Verifier-Inventarwert von 14 Policies, wurde aber nicht als SIM-101 gewertet.
  Der Harness zählte fälschlich nur die zwei Top-Level-`EvaluationResults`
  für `iam:GetPolicy` und `iam:GetPolicyVersion` und erwartete dort 28
  Ergebnisse. Bei einer Simulation mit mehreren Ressourcen liegen die
  Einzelentscheidungen je Aktion in `ResourceSpecificResults`; deshalb meldete
  der Harness `allowed x 2`, `TOTAL=2` und
  `VERIFIER_IAM_POLICY_READS_POSITIVE=failed`. SIM-102 wurde wegen `set -e`
  anschließend nicht ausgeführt. Policy-Änderungen wurden daraus nicht
  abgeleitet.
- Ein weiterer vorgesehener SIM-101/102-Lauf auf Commit
  `c6fc4b6cc64dc588f6d597607602dbd974c278c2` brach bereits beim
  `SimulateCustomPolicy`-Request mit `ValidationError` ab. Die vollständige
  Verifier-Policy beziehungsweise Operator-Boundary überschritten in dieser
  Aufrufform die vom Request akzeptierten Dokumentgrößen. Es fand keine
  verwertbare Simulatorentscheidung statt. Der Harness wurde deshalb auf die
  unverändert einschlägigen `iam:GetPolicy`-/`iam:GetPolicyVersion`-Statements
  der beiden Repository-Policies fokussiert; es erfolgte keine Policy-Änderung.
- Der anschließende fokussierte Lauf auf demselben Commit lieferte für den
  Positivpfad bereits `allowed` × 28, `TOTAL=28` und
  `MISSING_CONTEXT=none`; der lokale Positivmarker blieb jedoch wegen eines
  zusätzlichen spröden Struktur-/Vergleichschecks auf `failed`. Der
  Negativpfad lieferte gleichzeitig `implicitDeny` × 2 und `passed`. Auch
  dieser Zwischenlauf wurde nicht nummeriert. Der abschließende Harness prüfte
  stattdessen strukturiert genau zwei Aktionen, je 14 erwartete
  `ResourceSpecificResults`, die exakten 14 Ressourcen, ausschließlich
  `allowed` und keine fehlenden Kontextwerte. Erst dessen vollständig
  bestandener Lauf wurde als SIM-101/102 gewertet.
- Der erste vorgesehene SIM-105/106-Lauf auf Commit
  `2970b3ac88c0cbf4bcc16a8ac261049233ba439a` bestätigte für den Positivpfad
  bereits `allowed` × 4 und `MISSING_CONTEXT=none`. Der Negativpfad lieferte
  ebenfalls bereits die erwarteten zehn `implicitDeny`-Entscheidungen, endete
  aber mit `CFN_SERVICE_ROLE_FORBIDDEN_ROLE_MUTATIONS_NEGATIVE=failed`, weil
  der Harness pauschal `MISSING_CONTEXT=none` verlangte. Die gemeldeten Keys
  stammten ausschließlich aus fachlich unbeteiligten Statements der vier
  vollständig eingereichten Policy-Dokumente. Dieser Lauf wurde nicht
  nummeriert; es erfolgte keine Policy-Änderung.
- Ein weiterer Start des korrigierten SIM-105/106-Harnesses auf demselben
  Commit bestand den statischen Abgleich aller vier Policy-Dokumente, brach
  danach aber wegen fehlender AWS-Anmeldedaten mit `NoCredentials` vor beiden
  `SimulateCustomPolicy`-Aufrufen ab. Es fand keine Simulatorentscheidung
  statt; der Lauf wurde nicht gewertet.
- Der erste vorgesehene SIM-111/112-Lauf auf Commit
  `fbcb1bc1e1144794c2a1c5cf5c08bbf99b7333c5` bestand den vollständigen
  statischen Vorcheck, wurde aber vor einer Simulatorentscheidung mit einem
  `ValidationError` für `permissionsBoundaryPolicyInputList` abgelehnt.
  Ursache war erneut die für diesen Listenparameter ungeeignete Übergabe der
  Boundary über `file://`. Der Lauf wurde nicht nummeriert; die erfolgreiche
  Wiederholung übergab alle drei Identity-Policies und die Boundary jeweils
  als kompakten vollständigen JSON-String. Es erfolgte keine Policy-Änderung.
- Der erste Start des SIM-113/114-Harnesses stoppte vor statischem Vorcheck
  und AWS-Simulation beim Head-Abgleich: Der lokale Branch stand noch auf
  `fbcb1bc1e1144794c2a1c5cf5c08bbf99b7333c5`, der Remote-Branch und der
  erwartete Stand bereits auf `d5d4c711be85855faf5ce669855d3ff58d7b4542`.
  Nach dem reinen Fast-Forward wurde derselbe Harness vollständig erfolgreich
  ausgeführt. Der abgebrochene Start wurde nicht nummeriert.
- Der erste vorgesehene SIM-115/116-Lauf auf Commit
  `79d1df1cf5239fd0a0732bc1fef41cb901ac7206` lieferte bereits alle vier
  erwarteten `allowed`-Entscheidungen des Positivpfads sowie alle 16
  erwarteten `implicitDeny`-Entscheidungen der Gegenfälle. Der lokale
  Negativmarker blieb dennoch auf `failed`, weil der Harness pauschal
  `MISSING_CONTEXT=none` verlangte. Die gemeldeten Keys stammten
  ausschließlich aus fachlich unbeteiligten Statements; alle für die vier
  ECR-/Logs-Aktionen relevanten Kontextwerte waren vollständig. Dieser Lauf
  wurde nicht nummeriert. Der Harness wurde ohne Policy-Änderung auf
  `RELEVANT_MISSING_CONTEXT=none` präzisiert und anschließend vollständig
  erfolgreich wiederholt.
- Erwartungswerte aus vorgeschlagenen, aber noch nicht ausgeführten Blöcken
  werden nicht als Ergebnis protokolliert.

## Stand nach SIM-119/120

SIM-119 bestätigt den vollständigen noch offenen CloudWatch-Logs-Lifecycle der
CloudFormation-Service-Rolle: `logs:DescribeLogGroups` wurde aktionsgerecht
mit globaler Ressource `*` und Referenzregion simuliert; die fünf
ressourcengebundenen Read-/Update-/Delete-Aktionen wurden jeweils atomar gegen
die feste Application Log Group geprüft. Alle sechs Entscheidungen sind
`allowed`, die Boundary gab alle sechs frei, es fehlten keine Kontextwerte
und kein Ergebnis war trunkiert.

SIM-120 bestätigt elf `implicitDeny`-Entscheidungen: fünf Aktionen gegen eine
fremde Log Group in `eu-central-1`, `DescribeLogGroups` in `eu-west-1`
sowie fünf Aktionen gegen die fest benannte Log Group in `eu-west-1`. Für
`Resource: "*"` liefert AWS erwartungsgemäß kein `ResourceSpecificResults`-
Element; deshalb entsprechen sechs beziehungsweise elf atomare Evaluationen
fünf beziehungsweise zehn ressourcenspezifischen Einträgen. Die rohen
`MissingContextValues` stammen ausschließlich aus fachlich unbeteiligten
Statements; alle für die geprüften Aktionen relevanten Kontextwerte waren
vollständig. Es wurden keine Statements getroffen, die Boundary gab keinen
Gegenfall frei und kein Ergebnis war trunkiert.

Keine Policy-Änderung war erforderlich. Vor der Festlegung des nächsten
Testpaars werden der dann aktuelle PR-Head, die verbleibende
V2.3-Simulatorpflichtmatrix und die noch nicht abgedeckten
CloudFormation-Service-Role-Aktionen erneut live abgeglichen.

## Fortsetzungsregel

Für alle weiteren Testpaare wird dieselbe temporäre Datei
`/workspaces/exports/sim-065-066.sh` wiederverwendet. Vor jedem neuen Paar wird
ihr bisheriger Inhalt im Editor vollständig durch den neuen kontrollierten
Block ersetzt.

1. Immer genau zwei fachlich zusammengehörige Simulatorfälle (Positiv- und
   Negativfall) in einem kontrollierten Block ausführen.
2. Beide tatsächlichen Terminalergebnisse einzeln prüfen.
3. Nur bei Übereinstimmung mit dem jeweiligen Soll beide Fälle als `bestanden`
   markieren.
4. Nach jedem bestandenen Testpaar beide Entscheidungen und Pass-Marker
   gemeinsam in diesem Dokument ergänzen und auf den PR-Branch committen.
5. Das nächste offene Testpaar erst nach Abgleich mit dem aktuellen
   Repository-Stand und der verbleibenden Pflichtmatrix eindeutig benennen.
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
die später ergänzte ACM-Request-Policy wurde mit SIM-101/102 erneut geprüft.

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

Quelle für SIM-101 und SIM-102: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen fokussierten
Verifier-Inventarlaufs auf dem geprüften Ausgangsstand
`c6fc4b6cc64dc588f6d597607602dbd974c278c2`.

Quelle für SIM-103 und SIM-104: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben der Simulationen auf dem geprüften Ausgangsstand
`bbba509dbfd82437d0ff721c1806d3f5f1279724`.

Quelle für SIM-105 und SIM-106: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen korrigierten Harnesses
auf dem geprüften Ausgangsstand
`2970b3ac88c0cbf4bcc16a8ac261049233ba439a`.

Quelle für SIM-107 und SIM-108: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`06ab88abdab6e95c7be08358111af4df9804263a`.

Quelle für SIM-109 und SIM-110: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`ab0deacb9975d50a482de5d1a5e3468cc7ab7c4d`.

Quelle für SIM-111 und SIM-112: vom Nutzer am 13. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`fbcb1bc1e1144794c2a1c5cf5c08bbf99b7333c5`.

Quelle für SIM-113 und SIM-114: vom Nutzer am 15. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`d5d4c711be85855faf5ce669855d3ff58d7b4542`.

Quelle für SIM-115 und SIM-116: vom Nutzer am 15. August 2026 ausdrücklich
gemeldete Terminalausgaben der vollständig bestandenen korrigierten
Wiederholung auf dem geprüften Ausgangsstand
`79d1df1cf5239fd0a0732bc1fef41cb901ac7206`.

Quelle für SIM-117 und SIM-118: vom Nutzer am 15. August 2026 ausdrücklich
gemeldete Terminalausgaben der vollständig bestandenen Wiederholung auf dem
geprüften Ausgangsstand
`09f14e9ac9f1546883a591b0e275d73d61b08494`.

Quelle für SIM-119 und SIM-120: vom Nutzer am 15. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`ccbe59333c30cffbbc32ddd7fc0ad654c4fc08be`.
