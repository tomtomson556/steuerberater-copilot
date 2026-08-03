# AWS-Referenzdemo: IAM-Policy-Simulator-Testprotokoll

Stand: 3. August 2026  
Repository: `tomtomson556/steuerberater-copilot`  
Geprüfter Referenzstand: `d615f335b0bf1063e3f7129b71eee168f1115db2`  
Policy-Verzeichnis: `infra/iam/reference-demo/v2.3`  
Zielregion: `eu-central-1`  
Simulatorprofil: `administrator`

## Zweck und Status

Dieses Protokoll hält die einzeln bestätigten Ergebnisse der vorbereitenden
IAM-Policy-Simulator-Prüfung für die AWS-Referenzdemo fest. Es ist die
Fortsetzungsgrundlage für spätere Sitzungen und verhindert doppelte oder
vergessene Tests.

Bisher wurde ausschließlich `aws iam simulate-custom-policy` verwendet. Die
Simulationen haben keine AWS-Ressourcen erstellt, verändert, zurückgesetzt oder
gelöscht.

Der AWS-Live-Test bleibt **No-Go**, bis die vollständige Vorprüfung und die
weiteren V2.3-Gates abgeschlossen sind.

## Zählweise

- Bestätigte atomare Simulatorentscheidungen: **29**
- Ergänzende bestätigte Gruppenmarker: **2**
- Bestätigte Nachweise insgesamt: **31**
- Noch offene Simulatorfälle nach dem zuletzt bestandenen Test: **20**
  (manueller Arbeitsstand; V2.3 definiert Kategorien, aber keine atomar
  nummerierte Gesamtmatrix)

Nur vom Nutzer ausdrücklich gemeldete Entscheidungen oder bestandene
Gruppenmarker werden als bestätigt geführt. Erwartete Ergebnisse allein zählen
nicht.

## Bestätigte atomare Entscheidungen

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

## Ergänzende bestätigte Gruppenmarker

Diese Marker stammen aus bestandenen Sammelprüfungen. Weil die einzelnen
`EvalDecision`-Zeilen nicht vollständig erhalten sind, werden sie nicht als
zusätzliche atomare Entscheidungen gezählt.

| ID | Bestätigter Marker | Bedeutung | Status |
|---|---|---|---|
| GRP-001 | `OPERATOR_WRONG_SERVICE_NEGATIVE=passed` | Operator darf die feste CloudFormation-Service-Rolle nicht an einen falschen Service übergeben. | bestanden |
| GRP-002 | `OPERATOR_WRONG_ROLE_NEGATIVE=passed` | Operator darf keine andere Rolle an CloudFormation übergeben. | bestanden |

## Nicht gewertete Versuche

- Ein früher Test nutzte durch eine unscharfe Dateisuche die falsche
  Policy-Datei. Daraus wurde kein Policybefund abgeleitet.
- Ein eingefügter Shell-/Python-Block wurde beschädigt; außerdem war ein
  `file://`-Aufruf für Listenparameter ungeeignet. Der Versuch wurde nicht
  ausgeführt beziehungsweise nicht als Simulatorentscheidung gewertet.
- Erwartungswerte aus vorgeschlagenen, aber noch nicht ausgeführten Blöcken
  werden nicht als Ergebnis protokolliert.

## Nächster offener Einzelfall

| ID | Identität / Bereich | Aktion und Gegenstand | Gegenfall | Soll | Status |
|---|---|---|---|---|---|
| SIM-030 | Operator | `cloudformation:ValidateTemplate` | falsche Region `eu-west-1` | `implicitDeny` | offen |

## Fortsetzungsregel

1. Immer genau einen Simulatorfall ausführen.
2. Das tatsächliche Terminalergebnis prüfen.
3. Nur bei Übereinstimmung mit dem Soll den Fall als `bestanden` markieren.
4. Entscheidung und ausgegebenen Pass-Marker unmittelbar in diesem Dokument
   ergänzen.
5. Den nächsten offenen Fall eindeutig benennen.
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
