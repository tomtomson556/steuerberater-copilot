# AWS Reference Demo Operations Runbook

Betriebs- und Deployment-Anleitung für den minimalen AWS-Referenz-Stack
(`infra/cloudformation/reference-demo.yaml`). Synthetische Portfolio-Demo
nur; keine echten Mandanten-, Kanzlei- oder Steuerdaten.

Das Runbook bindet Template, Guard-Regeln und Betrieb an das IAM-/Lifecycle-
Modell v2.3 und die Artefakte unter `infra/iam/reference-demo/v2.3/`. Create
und Update laufen ausschließlich über geprüfte Change Sets mit der festen
CloudFormation-Service-Rolle. Direkte `create-stack`- und `update-stack`-
Aufrufe sind nicht Teil dieses Pfads.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Voraussetzungen

- AWS-Konto und Zielregion `eu-central-1` (keine Default-VPC erforderlich; der
  Stack erzeugt seine eigene öffentliche IPv4-VPC mit zwei Subnetzen)
- IAM-Control-Plane v2.3 bereits gebootstrappt (Operator-Policies, Boundaries,
  Service-Rolle). Bootstrap und Teardown liegen bei
  `tools/aws_reference_demo_iam_control_plane.py` und sind kein Bestandteil
  dieses Stack-Laufs.
- lokale Docker-Build-Fähigkeit für `linux/amd64` und AWS-CLI als Operator
  mit den v2.3-Operator-Policies
- Billing-Budget oder Kostenalarm im Account
- keine Credentials, Secret-Werte oder Access Keys im Repository
- `cfn-guard` ist für den Offline-Freeze verbindlich; ein erfolgreicher Lauf
  gegen `infra/cloudformation/guards/reference-demo.guard` ist Voraussetzung
  für jedes Change Set. Die Offline-Tests rufen dieselbe Guard-CLI lokal auf
  und bleiben ohne AWS-Netzwerkzugriff

Dieses Runbook wird manuell ausgeführt. CI und Standardtests deployen keinen
Stack und benötigen kein AWS-Konto. Ein AWS-Live-Test bleibt ein separates
Go-/No-Go und ist durch dieses Runbook nicht freigegeben.

## Verbindliche Konstanten

| Größe | Wert |
|---|---|
| Region | `eu-central-1` |
| Stack | `steuerberater-copilot-reference-demo` |
| Change-Set-Präfix | `steuerberater-copilot-reference-demo-` |
| Capabilities | ausschließlich `CAPABILITY_NAMED_IAM` |
| Service-Rolle | `arn:aws:iam::<ACCOUNT_ID>:role/steuerberater-copilot/control-plane/reference-demo-cfn-service-role` |
| ECR | `steuerberater-copilot-reference-demo` |
| Log Group | `/steuerberater-copilot/reference-demo/application` |
| Express Service | Cluster `default`, Name `steuerberater-copilot-reference-demo` |
| Taskgröße | `Cpu=256`, `Memory=512` |
| Task Execution Role | Pfad `/steuerberater-copilot/reference-demo/`, Name `task-execution` |
| Express Infrastructure Role | Pfad `/steuerberater-copilot/reference-demo/`, Name `express-infrastructure` |
| optionales Secret | `steuerberater-copilot/reference-demo/synthetic` |

Feste Stack- und Ressource-Tags, bei jedem `CreateChangeSet` ausdrücklich
mitzusenden:

```text
Project=steuerberater-copilot
Component=reference-demo
Environment=portfolio-test
ManagedBy=cloudformation
Lifecycle=ephemeral
```

`cloudformation:ResourceTypes` wird nicht gesetzt. `CAPABILITY_NAMED_IAM` und
diese API-Option sind nicht gemeinsam verwendbar; die Ressourcentypgrenze
liegt bei Template-Hash, Guard-Allowlist, manuell geprüftem Change Set und
der Service-Rollen-Boundary.

## 0. Offline-Freeze vor jedem Change Set

Im Repository-Root, gegen den geprüften Review-Commit:

```bash
git rev-parse HEAD
sha256sum infra/cloudformation/reference-demo.yaml
sha256sum infra/cloudformation/guards/reference-demo.guard
```

Die Hashes müssen zum eingefrorenen Reviewstand passen. Abweichung ist ein
No-Go: kein Change Set erstellen oder ausführen.

Verbindlicher Guard-Lauf. Fehlschlag, Parser-Fehler oder Überspringen ist ein
No-Go. CloudFormation unterstützt keine YAML-Aliases, Anker oder Hash-Merges
([Template format](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-formats.html));
das Template wiederholt die fünf festen Tags deshalb ausdrücklich.

```bash
cfn-guard validate \
  --data infra/cloudformation/reference-demo.yaml \
  --rules infra/cloudformation/guards/reference-demo.guard
```

Exit-Status muss `0` sein.

Unabhängig davon gelten die Offline-Regressionstests:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
```

Guard und Tests müssen unter anderem sichern: feste Namen/Pfade/Boundaries,
statische Secret-Lesepolicy ab Stage 1, `Cpu=256`, `Memory=512`,
`DeletionPolicy`/`UpdateReplacePolicy=Delete` am Secret und die Abwesenheit
von `TaskRoleArn`.

Gemeinsame Operator-Variablen für die folgenden Schritte:

```bash
REGION=eu-central-1
STACK_NAME=steuerberater-copilot-reference-demo
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
SERVICE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/steuerberater-copilot/control-plane/reference-demo-cfn-service-role"
TEMPLATE="file://infra/cloudformation/reference-demo.yaml"
```

Read-only CloudFormation-Templatevalidierung vor dem ersten Change Set. Der
Aufruf `validate-template` erzeugt oder ändert keine Ressourcen; er prüft, ob
CloudFormation das YAML akzeptiert, und nennt die erforderlichen Capabilities
([validate-template](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/validate-template.html)).
Dieser Schritt gehört nicht zu den netzwerkfreien Standardtests und wird hier
nicht ausgeführt.

```bash
aws cloudformation validate-template \
  --region "$REGION" \
  --template-body "$TEMPLATE"
```

Erwartung: die Antwort enthält `CAPABILITY_NAMED_IAM`. Validierungsfehler,
YAML-Parserfehler oder unerwartete Capabilities sind ein No-Go. Der Aufruf
ist kein Change Set und kein `create-stack`/`update-stack`.

## 1. Stage-1-Change-Set ohne Service

Change-Set-Typ `CREATE`. Erwartung: genau die 13 Stage-1-Ressourcen (ECR, Log
Group, VPC-Netzwerkbasis, beide Runtime-Rollen). Kein Express Service, kein
Secret. Beide Rollen mit fester Boundary und statischer Secret-Lesepolicy.

```bash
CHANGE_SET_NAME=steuerberater-copilot-reference-demo-stage-1

aws cloudformation create-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME" \
  --change-set-type CREATE \
  --template-body "$TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --role-arn "$SERVICE_ROLE_ARN" \
  --tags \
    Key=Project,Value=steuerberater-copilot \
    Key=Component,Value=reference-demo \
    Key=Environment,Value=portfolio-test \
    Key=ManagedBy,Value=cloudformation \
    Key=Lifecycle,Value=ephemeral \
  --parameters \
    ParameterKey=DeployService,ParameterValue=false \
    ParameterKey=CreateManagedSecret,ParameterValue=false \
    ParameterKey=InjectManagedSecret,ParameterValue=false

aws cloudformation wait change-set-create-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation describe-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"
```

Change Set nicht ausführen, bis Resource Changes, Tags und Parameter gegen
die 13 Stage-1-Ressourcen und die Runtime-Role-Boundaries geprüft sind. Ein
CREATE-Change-Set kann einen leeren Stack im Status `REVIEW_IN_PROGRESS`
anlegen. Ein verworfenes Change Set und dieser leere Stack werden gelöscht:

```bash
aws cloudformation delete-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation delete-stack \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --role-arn "$SERVICE_ROLE_ARN"
```

Nach der Prüfung ausführen:

```bash
aws cloudformation execute-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation wait stack-create-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"

aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs'
```

Erwartete Outputs: `EcrRepositoryUri`, `LogGroupName`. Kein Service-Endpoint.
Stage 1 legt bereits die stackeigene öffentliche VPC-Netzwerkbasis an
(VPC, zwei öffentliche Subnetze, Internet Gateway, öffentliche Route) sowie
die unveränderlichen Runtime-Rollen.

## 2. Docker-Build und ECR-Push

Image ausdrücklich für `linux/amd64` bauen. Ein nur für ARM64 gebautes
Host-Image ist unzulässig.

```bash
ECR_URI="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)"
ECR_REPO_NAME=steuerberater-copilot-reference-demo

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

docker build --platform linux/amd64 -t steuerberater-copilot:reference .
docker image inspect steuerberater-copilot:reference \
  --format '{{.Os}}/{{.Architecture}}'
docker tag steuerberater-copilot:reference "${ECR_URI}:bootstrap"
docker push "${ECR_URI}:bootstrap"
```

Erwartung der Inspect-Ausgabe: `linux/amd64`.

## 3. Digest-Ermittlung

```bash
IMAGE_DIGEST="$(aws ecr describe-images \
  --region "$REGION" \
  --repository-name "$ECR_REPO_NAME" \
  --image-ids imageTag=bootstrap \
  --query 'imageDetails[0].imageDigest' \
  --output text)"

IMAGE_URI="${ECR_URI}@${IMAGE_DIGEST}"
echo "$IMAGE_URI"
```

Nur Digest-URIs (`…@sha256:…`) sind für `DeployService=true` zulässig.

## 4. Stage-2-Change-Set mit Service

Change-Set-Typ `UPDATE`. Dieselben fünf Stack-Tags erneut mitsenden.
`Task Execution Role` und `Express Infrastructure Role` dürfen weder als
`Modify` noch als `Replace` erscheinen. `ServiceName`,
`InfrastructureRoleArn` und Express-Tags sind create-only; eine
Tag-Änderung wäre Replacement und ist ein No-Go.

```bash
CHANGE_SET_NAME=steuerberater-copilot-reference-demo-stage-2

aws cloudformation create-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME" \
  --change-set-type UPDATE \
  --template-body "$TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --role-arn "$SERVICE_ROLE_ARN" \
  --tags \
    Key=Project,Value=steuerberater-copilot \
    Key=Component,Value=reference-demo \
    Key=Environment,Value=portfolio-test \
    Key=ManagedBy,Value=cloudformation \
    Key=Lifecycle,Value=ephemeral \
  --parameters \
    ParameterKey=DeployService,ParameterValue=true \
    ParameterKey=ImageUri,ParameterValue="$IMAGE_URI" \
    ParameterKey=CreateManagedSecret,ParameterValue=false \
    ParameterKey=InjectManagedSecret,ParameterValue=false

aws cloudformation wait change-set-create-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation describe-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"
```

Prüfen: Express Service mit `ServiceName`, `Cluster=default`, `Cpu=256`,
`Memory=512`, ohne `TaskRoleArn`. Bei unerwarteter Ressource, Replacement oder
Rollenänderung das Change Set nicht ausführen und stattdessen löschen:

```bash
aws cloudformation delete-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"
```

Nach der Prüfung:

```bash
aws cloudformation execute-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation wait stack-update-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"

ENDPOINT="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ServiceEndpoint'].OutputValue" \
  --output text)"
echo "$ENDPOINT"
```

## 5. HTTPS-Health- und synthetischer `/ai/draft`-Test

```bash
curl -fsS "https://${ENDPOINT}/health"
curl -fsS -X POST "https://${ENDPOINT}/ai/draft" \
  -H "Content-Type: application/json" \
  -d '{"case_id":"CASE_002"}'
```

Erwartung: `{"status":"ok"}` sowie ein Draft mit `review_status: "Draft"` für
den synthetischen Fall `CASE_002`. `FakeModelProvider` bleibt der sichere
Default ohne Secret-Injection.

## 6. Optionaler Secret-Nachweis (erst nach externem PutSecretValue)

Kein Secret-Wert gehört ins Repository, Template, Parameter, Output oder CI.
Im Runbook steht deshalb **kein** `--secret-string`-Literal und kein Shell-
Literal mit Secret-Inhalt.

Die Task Execution Role und ihre statische Secret-Lesepolicy bleiben in beiden
Secret-Change-Sets unverändert. `DeletionPolicy: Delete` und
`UpdateReplacePolicy: Delete` am Secret erzwingen den CloudFormation-Löschpfad
mit `secretsmanager:ForceDeleteWithoutRecovery=true`. Ein Delete mit Recovery
Window ist nicht Teil dieses Pfads.

1. UPDATE-Change-Set mit `CreateManagedSecret=true` und weiterhin
   `InjectManagedSecret=false` erstellen. Prüfen, dass ausschließlich das
   Secret und abhängige Outputs erscheinen; keine IAM-Rolle als `Modify` oder
   `Replace`.
2. Nach `UPDATE_COMPLETE` ARN aus Output `ManagedSecretArn` lesen.
3. **Außerhalb des Repositorys** einen synthetischen Demo-Wert über eine
   temporäre Datei in einer **Subshell** setzen. Sofort bereinigt werden nur die
   **lokale Variable** und die **temporäre Datei** - nicht der soeben in AWS
   Secrets Manager gesetzte Secret-Wert (der bleibt für den späteren
   Injection-Test erhalten). Trap und Variablen verbleiben nicht in der
   aufrufenden Shell. Ein fehlgeschlagenes `put-secret-value` behält einen
   Non-zero-Status.

```bash
CHANGE_SET_NAME=steuerberater-copilot-reference-demo-secret-create

aws cloudformation create-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME" \
  --change-set-type UPDATE \
  --template-body "$TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --role-arn "$SERVICE_ROLE_ARN" \
  --tags \
    Key=Project,Value=steuerberater-copilot \
    Key=Component,Value=reference-demo \
    Key=Environment,Value=portfolio-test \
    Key=ManagedBy,Value=cloudformation \
    Key=Lifecycle,Value=ephemeral \
  --parameters \
    ParameterKey=DeployService,ParameterValue=true \
    ParameterKey=ImageUri,ParameterValue="$IMAGE_URI" \
    ParameterKey=CreateManagedSecret,ParameterValue=true \
    ParameterKey=InjectManagedSecret,ParameterValue=false

aws cloudformation wait change-set-create-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation describe-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"
```

Rollen als `Modify`/`Replace` sind ein No-Go. Nach der Prüfung ausführen und
den Secret-Wert setzen:

```bash
aws cloudformation execute-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation wait stack-update-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"

MANAGED_SECRET_ARN="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ManagedSecretArn'].OutputValue" \
  --output text)"

(
  set -e
  SECRET_FILE="$(mktemp "${TMPDIR:-/tmp}/sbc-demo-secret.XXXXXX")"
  chmod 600 "$SECRET_FILE"

  cleanup() {
    rm -f "${SECRET_FILE:-}"
    unset SECRET_VALUE SECRET_FILE
  }
  trap cleanup EXIT INT TERM

  read -r -s -p "Synthetischen Demo-Secret-Wert eingeben (Eingabe wird nicht angezeigt): " SECRET_VALUE
  printf '\n'
  printf '%s' "$SECRET_VALUE" > "$SECRET_FILE"
  unset SECRET_VALUE

  aws secretsmanager put-secret-value \
    --region "$REGION" \
    --secret-id "$MANAGED_SECRET_ARN" \
    --secret-string "file://${SECRET_FILE}"
)
```

Der `trap` in der Subshell entfernt die temporäre Datei auch dann, wenn
`put-secret-value` fehlschlägt. Der AWS-Secret-Wert selbst bleibt bis zum
späteren Stack-Delete bzw. Secret-Lifecycle bestehen.

4. Erst danach UPDATE-Change-Set mit `InjectManagedSecret=true` und
   `DeployService=true` (Digest-`ImageUri` beibehalten). Prüfen, dass nur
   Express-Service-/Task-Definition-Konfiguration geändert wird und keine
   IAM-Rolle erscheint.
5. Injection anhand der Task-Definition / Container-Secret-Verdrahtung prüfen
   (`REFERENCE_DEMO_SECRET` → Managed-Secret-ARN). Secret-Werte nicht in Logs
   oder Tickets schreiben.

```bash
CHANGE_SET_NAME=steuerberater-copilot-reference-demo-secret-inject

aws cloudformation create-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME" \
  --change-set-type UPDATE \
  --template-body "$TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --role-arn "$SERVICE_ROLE_ARN" \
  --tags \
    Key=Project,Value=steuerberater-copilot \
    Key=Component,Value=reference-demo \
    Key=Environment,Value=portfolio-test \
    Key=ManagedBy,Value=cloudformation \
    Key=Lifecycle,Value=ephemeral \
  --parameters \
    ParameterKey=DeployService,ParameterValue=true \
    ParameterKey=ImageUri,ParameterValue="$IMAGE_URI" \
    ParameterKey=CreateManagedSecret,ParameterValue=true \
    ParameterKey=InjectManagedSecret,ParameterValue=true

aws cloudformation wait change-set-create-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation describe-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"
```

Rollenänderung oder Replacement ist ein No-Go. Nach der Prüfung:

```bash
aws cloudformation execute-change-set \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --change-set-name "$CHANGE_SET_NAME"

aws cloudformation wait stack-update-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"
```

Ungültige Kombinationen (Injection ohne Create, Injection ohne Deploy,
Deploy ohne Digest-URI) lehnt CloudFormation per Rules bzw. AllowedPattern ab.

## 7. Stack-Delete

Vor dem Delete Resource-IDs **außerhalb des Repositorys** sichern. Sonst sind
Express-ALB-, Target-Group-, Security-Group-, Rollen- und stackeigene
VPC-Prüfungen nach dem Löschen nicht reproduzierbar. Bloßes Verringern der
Task-Anzahl ist keine Abschaltung.

```bash
VERIFY_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sbc-reference-demo-verify.XXXXXX")"
chmod 700 "$VERIFY_DIR"
echo "Verify artifacts: $VERIFY_DIR"

# Stack-Outputs (ECR, Log Group, optional Managed Secret)
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs' \
  --output json > "$VERIFY_DIR/stack-outputs.json"

ECR_URI="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)"
LOG_GROUP_NAME="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='LogGroupName'].OutputValue" \
  --output text)"
MANAGED_SECRET_ARN="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ManagedSecretArn'].OutputValue" \
  --output text)"
printf '%s\n' "$ECR_URI" > "$VERIFY_DIR/ecr-uri.txt"
printf '%s\n' "$LOG_GROUP_NAME" > "$VERIFY_DIR/log-group-name.txt"
printf '%s\n' "$MANAGED_SECRET_ARN" > "$VERIFY_DIR/managed-secret-arn.txt"
ECR_REPO_NAME=steuerberater-copilot-reference-demo
printf '%s\n' "$ECR_REPO_NAME" > "$VERIFY_DIR/ecr-repository-name.txt"
printf '%s\n' "task-execution" > "$VERIFY_DIR/task-execution-role-name.txt"
printf '%s\n' "express-infrastructure" > "$VERIFY_DIR/express-infrastructure-role-name.txt"

# Stackeigene VPC-Netzwerkbasis (Physical Resource IDs)
VPC_ID="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id DemoVpc \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
printf '%s\n' "$VPC_ID" > "$VERIFY_DIR/vpc-id.txt"

PUBLIC_SUBNET_A_ID="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id PublicSubnetA \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
PUBLIC_SUBNET_B_ID="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id PublicSubnetB \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
printf '%s\n' "$PUBLIC_SUBNET_A_ID" > "$VERIFY_DIR/public-subnet-a-id.txt"
printf '%s\n' "$PUBLIC_SUBNET_B_ID" > "$VERIFY_DIR/public-subnet-b-id.txt"

IGW_ID="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id InternetGateway \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
printf '%s\n' "$IGW_ID" > "$VERIFY_DIR/internet-gateway-id.txt"

ROUTE_TABLE_ID="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id PublicRouteTable \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
printf '%s\n' "$ROUTE_TABLE_ID" > "$VERIFY_DIR/route-table-id.txt"

# Express Gateway Service Physical Resource ID (= Service-ARN)
EXPRESS_SERVICE_ARN="$(aws cloudformation describe-stack-resource \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --logical-resource-id ExpressGatewayService \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)"
printf '%s\n' "$EXPRESS_SERVICE_ARN" > "$VERIFY_DIR/express-service-arn.txt"

# Offizielle Express-Servicebeschreibung
aws ecs describe-express-gateway-service \
  --region "$REGION" \
  --service-arn "$EXPRESS_SERVICE_ARN" \
  --output json > "$VERIFY_DIR/express-service.json"

SERVICE_REVISION_ARN="$(aws ecs describe-express-gateway-service \
  --region "$REGION" \
  --service-arn "$EXPRESS_SERVICE_ARN" \
  --query 'service.activeConfigurations[0].serviceRevisionArn' \
  --output text)"
printf '%s\n' "$SERVICE_REVISION_ARN" > "$VERIFY_DIR/service-revision-arn.txt"

# Verwaltete ALB-, Target-Group-, Security-Group- und Log-Ressourcen
aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --output json > "$VERIFY_DIR/service-revision.json"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources' \
  --output json > "$VERIFY_DIR/ecs-managed-resources.json"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources.ingressPaths[0].loadBalancer.arn' \
  --output text > "$VERIFY_DIR/alb-arn.txt"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources.ingressPaths[0].targetGroups[].arn' \
  --output text > "$VERIFY_DIR/target-group-arns.txt"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources.ingressPaths[0].loadBalancerSecurityGroups[].arn' \
  --output text > "$VERIFY_DIR/alb-security-group-arns.txt"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources.serviceSecurityGroups[].arn' \
  --output text > "$VERIFY_DIR/service-security-group-arns.txt"

aws ecs describe-service-revisions \
  --region "$REGION" \
  --service-revision-arns "$SERVICE_REVISION_ARN" \
  --query 'serviceRevisions[0].ecsManagedResources.logGroups[].logGroupName' \
  --output text > "$VERIFY_DIR/express-log-group-names.txt"
```

Danach den Stack über dieselbe Service-Rolle löschen. CloudFormation löscht
das optionale Secret mit `ForceDeleteWithoutRecovery=true`.

```bash
aws cloudformation delete-stack \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --role-arn "$SERVICE_ROLE_ARN"

aws cloudformation wait stack-delete-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"
```

`EmptyOnDelete: true` leert das ECR-Repository beim Löschen. Die
stackverwaltete Log Group mit 14 Tagen Retention wird mit dem Stack entfernt.
Die Runtime-Rollen werden mit dem Stack entfernt; die IAM-Control-Plane
außerhalb des Stacks bleibt bis zum späteren Teardown bestehen.

## 8. Prüfung auf verbliebene Ressourcen

Nach `DELETE_COMPLETE` die zuvor gesicherten IDs in `eu-central-1` prüfen.

Harte Fehler (`FAIL`, Non-zero), wenn noch existieren:

- Express Gateway Service
- stackeigenes ECR
- stackeigene Log Group
- stackeigenes Managed Secret (falls zuvor angelegt) oder ein Secret in
  Löschwartestellung
- stackeigene Task Execution Role und Express Infrastructure Role
- stackeigene VPC, öffentliche Subnetze, Internet Gateway, Route Table und
  öffentliche Route
- eindeutig serviceeigene Target Groups
- `serviceSecurityGroups` dieser Demo

Nicht automatisch als harter Fehler behandeln (`WARN`):

- ein geteilter Application Load Balancer
- zugehörige `loadBalancerSecurityGroups`
- von Express Mode zurückbehaltene Log Groups
- der geteilte ECS-Cluster `default`
- accountweite Service-Linked Roles
- projektbezogene `STOPPED`-Tasks und Task Definitions in dokumentierten
  AWS-Löschfenstern

Vor manueller Löschung von ALB- oder ALB-Security-Group-Resten die Zuordnung zu
anderen Express-Services bzw. dem geteilten ALB prüfen. Nicht alle Einträge aus
`ecsManagedResources` müssen nach jedem Delete verschwunden sein.

Wichtig: Nicht jeder AWS-CLI-Fehler bedeutet "nicht vorhanden". Nur der jeweils
dokumentierte Not-found-Fall gilt als bestanden. AccessDenied, fehlende oder
abgelaufene Credentials, Netzwerkfehler, falsche Region und sonstige AWS-Fehler
beenden die Verifikation mit `FAIL`.

```bash
REGION=eu-central-1
# VERIFY_DIR aus Schritt 7 wiederverwenden
EXPRESS_SERVICE_ARN="$(cat "$VERIFY_DIR/express-service-arn.txt")"
ECR_REPO_NAME="$(cat "$VERIFY_DIR/ecr-repository-name.txt")"
LOG_GROUP_NAME="$(cat "$VERIFY_DIR/log-group-name.txt")"
MANAGED_SECRET_ARN="$(cat "$VERIFY_DIR/managed-secret-arn.txt")"
TASK_EXECUTION_ROLE_NAME="$(cat "$VERIFY_DIR/task-execution-role-name.txt")"
EXPRESS_INFRASTRUCTURE_ROLE_NAME="$(cat "$VERIFY_DIR/express-infrastructure-role-name.txt")"
VPC_ID="$(cat "$VERIFY_DIR/vpc-id.txt")"
PUBLIC_SUBNET_A_ID="$(cat "$VERIFY_DIR/public-subnet-a-id.txt")"
PUBLIC_SUBNET_B_ID="$(cat "$VERIFY_DIR/public-subnet-b-id.txt")"
IGW_ID="$(cat "$VERIFY_DIR/internet-gateway-id.txt")"
ROUTE_TABLE_ID="$(cat "$VERIFY_DIR/route-table-id.txt")"
ALB_ARN="$(cat "$VERIFY_DIR/alb-arn.txt")"
TARGET_GROUP_ARNS="$(cat "$VERIFY_DIR/target-group-arns.txt")"
ALB_SG_ARNS="$(cat "$VERIFY_DIR/alb-security-group-arns.txt")"
SERVICE_SG_ARNS="$(cat "$VERIFY_DIR/service-security-group-arns.txt")"
EXPRESS_LOG_GROUPS="$(cat "$VERIFY_DIR/express-log-group-names.txt")"

# Klassifiziert AWS-CLI-Aufrufe:
# - Exit 0 => present
# - Exit != 0 + dokumentierter Not-found-Text => absent
# - jeder andere Fehler => FAIL (AccessDenied, Credentials, Netzwerk, Region, ...)
classify_aws_presence() {
  local label="$1"
  local not_found_re="$2"
  shift 2
  local out ec
  set +e
  out="$("$@" 2>&1)"
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then
    AWS_PRESENCE=present
    AWS_PRESENCE_OUTPUT="$out"
    return 0
  fi
  if printf '%s\n' "$out" | grep -Eqi -- "$not_found_re"; then
    AWS_PRESENCE=absent
    AWS_PRESENCE_OUTPUT="$out"
    return 0
  fi
  echo "FAIL: AWS-Fehler bei Prüfung von '$label' (nicht der erwartete Not-found-Fall)." >&2
  echo "FAIL: Mögliche Ursachen: AccessDenied, fehlende/abgelaufene Credentials, Netzwerk, falsche Region oder sonstiger AWS-Fehler." >&2
  printf '%s\n' "$out" >&2
  exit 1
}

assert_aws_absent() {
  local label="$1"
  local not_found_re="$2"
  shift 2
  classify_aws_presence "$label" "$not_found_re" "$@"
  if [ "$AWS_PRESENCE" = present ]; then
    echo "FAIL: $label existiert noch" >&2
    printf '%s\n' "$AWS_PRESENCE_OUTPUT" >&2
    exit 1
  fi
}

# CloudWatch describe-log-groups liefert bei Abwesenheit Exit 0 und leere Trefferliste.
# Jeder Non-zero-Exit ist FAIL (kein "stillschweigendes Abwesend").
classify_log_group_presence() {
  local name="$1"
  local out ec
  set +e
  out="$(aws logs describe-log-groups \
    --region "$REGION" \
    --log-group-name-prefix "$name" \
    --query "logGroups[?logGroupName=='${name}']" \
    --output text 2>&1)"
  ec=$?
  set -e
  if [ "$ec" -ne 0 ]; then
    echo "FAIL: AWS-Fehler bei Log-Group-Prüfung '$name'." >&2
    echo "FAIL: Mögliche Ursachen: AccessDenied, fehlende/abgelaufene Credentials, Netzwerk, falsche Region oder sonstiger AWS-Fehler." >&2
    printf '%s\n' "$out" >&2
    exit 1
  fi
  if [ -n "$out" ]; then
    AWS_PRESENCE=present
  else
    AWS_PRESENCE=absent
  fi
  AWS_PRESENCE_OUTPUT="$out"
}

set -e

assert_aws_absent \
  "Express Gateway Service" \
  'ResourceNotFoundException' \
  aws ecs describe-express-gateway-service \
    --region "$REGION" \
    --service-arn "$EXPRESS_SERVICE_ARN"

assert_aws_absent \
  "ECR-Repository" \
  'RepositoryNotFoundException' \
  aws ecr describe-repositories \
    --region "$REGION" \
    --repository-names "$ECR_REPO_NAME"

classify_log_group_presence "$LOG_GROUP_NAME"
if [ "$AWS_PRESENCE" = present ]; then
  echo "FAIL: stackeigene Log Group existiert noch: $LOG_GROUP_NAME" >&2
  exit 1
fi

if [ -n "$MANAGED_SECRET_ARN" ] && [ "$MANAGED_SECRET_ARN" != "None" ]; then
  assert_aws_absent \
    "Managed Secret" \
    'ResourceNotFoundException' \
    aws secretsmanager describe-secret \
      --region "$REGION" \
      --secret-id "$MANAGED_SECRET_ARN"
fi

assert_aws_absent \
  "Task Execution Role ${TASK_EXECUTION_ROLE_NAME}" \
  'NoSuchEntity' \
  aws iam get-role \
    --role-name "$TASK_EXECUTION_ROLE_NAME"

assert_aws_absent \
  "Express Infrastructure Role ${EXPRESS_INFRASTRUCTURE_ROLE_NAME}" \
  'NoSuchEntity' \
  aws iam get-role \
    --role-name "$EXPRESS_INFRASTRUCTURE_ROLE_NAME"

assert_aws_absent \
  "stackeigene VPC ${VPC_ID}" \
  'InvalidVpcID\.NotFound' \
  aws ec2 describe-vpcs \
    --region "$REGION" \
    --vpc-ids "$VPC_ID"

assert_aws_absent \
  "PublicSubnetA ${PUBLIC_SUBNET_A_ID}" \
  'InvalidSubnetID\.NotFound' \
  aws ec2 describe-subnets \
    --region "$REGION" \
    --subnet-ids "$PUBLIC_SUBNET_A_ID"

assert_aws_absent \
  "PublicSubnetB ${PUBLIC_SUBNET_B_ID}" \
  'InvalidSubnetID\.NotFound' \
  aws ec2 describe-subnets \
    --region "$REGION" \
    --subnet-ids "$PUBLIC_SUBNET_B_ID"

assert_aws_absent \
  "Internet Gateway ${IGW_ID}" \
  'InvalidInternetGatewayID\.NotFound' \
  aws ec2 describe-internet-gateways \
    --region "$REGION" \
    --internet-gateway-ids "$IGW_ID"

assert_aws_absent \
  "Public Route Table ${ROUTE_TABLE_ID}" \
  'InvalidRouteTableID\.NotFound' \
  aws ec2 describe-route-tables \
    --region "$REGION" \
    --route-table-ids "$ROUTE_TABLE_ID"

for tg_arn in $TARGET_GROUP_ARNS; do
  [ -z "$tg_arn" ] || [ "$tg_arn" = "None" ] && continue
  assert_aws_absent \
    "serviceeigene Target Group ${tg_arn}" \
    'TargetGroupNotFound' \
    aws elbv2 describe-target-groups \
      --region "$REGION" \
      --target-group-arns "$tg_arn"
done

# serviceSecurityGroups: hart
for sg_arn in $SERVICE_SG_ARNS; do
  [ -z "$sg_arn" ] || [ "$sg_arn" = "None" ] && continue
  sg_id="${sg_arn##*/}"
  assert_aws_absent \
    "serviceSecurityGroup ${sg_arn}" \
    'InvalidGroup\.NotFound' \
    aws ec2 describe-security-groups \
      --region "$REGION" \
      --group-ids "$sg_id"
done

# Geteilter ALB und loadBalancerSecurityGroups: WARN
if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
  classify_aws_presence \
    "ALB ${ALB_ARN}" \
    'LoadBalancerNotFound' \
    aws elbv2 describe-load-balancers \
      --region "$REGION" \
      --load-balancer-arns "$ALB_ARN"
  if [ "$AWS_PRESENCE" = present ]; then
    echo "WARN: ALB existiert noch: $ALB_ARN" >&2
    echo "WARN: Prüfe manuell, ob der ALB von anderen Express-Services geteilt wird." >&2
    echo "WARN: Attribution: ELB-Tags (z. B. AmazonECSManaged), Listener-Regeln und" >&2
    echo "WARN: verbleibende Target Groups anderer Services prüfen, bevor du löschst." >&2
  fi
fi

for sg_arn in $ALB_SG_ARNS; do
  [ -z "$sg_arn" ] || [ "$sg_arn" = "None" ] && continue
  sg_id="${sg_arn##*/}"
  classify_aws_presence \
    "loadBalancerSecurityGroup ${sg_arn}" \
    'InvalidGroup\.NotFound' \
    aws ec2 describe-security-groups \
      --region "$REGION" \
      --group-ids "$sg_id"
  if [ "$AWS_PRESENCE" = present ]; then
    echo "WARN: loadBalancerSecurityGroup existiert noch: $sg_arn" >&2
    echo "WARN: Vor manueller Löschung Zuordnung zu anderen Express-Services" >&2
    echo "WARN: bzw. zum geteilten ALB prüfen (nicht blind löschen)." >&2
  fi
done

for lg_name in $EXPRESS_LOG_GROUPS; do
  [ -z "$lg_name" ] || [ "$lg_name" = "None" ] && continue
  classify_log_group_presence "$lg_name"
  if [ "$AWS_PRESENCE" = present ]; then
    echo "WARN: Express-Log-Group existiert noch: $lg_name" >&2
    echo "WARN: Attributiere manuell, ob sie ausschließlich dieser Demo gehört." >&2
    echo "WARN: Bei bestätigter Demo-Zugehörigkeit manuell löschen:" >&2
    echo "aws logs delete-log-group --region ${REGION} --log-group-name ${lg_name}" >&2
  fi
done

echo "Harte Post-delete-Checks für Service/ECR/stack-Log/Secret/IAM-Rollen/VPC/TG/serviceSecurityGroups bestanden."
echo "WARN-Fälle (geteilter ALB, ALB-Security-Groups, zurückbehaltene Express-Log-Groups, Default-Cluster) ggf. manuell bereinigen."
rm -rf "$VERIFY_DIR"
unset VERIFY_DIR EXPRESS_SERVICE_ARN ECR_REPO_NAME LOG_GROUP_NAME \
  MANAGED_SECRET_ARN TASK_EXECUTION_ROLE_NAME EXPRESS_INFRASTRUCTURE_ROLE_NAME \
  VPC_ID PUBLIC_SUBNET_A_ID PUBLIC_SUBNET_B_ID IGW_ID ROUTE_TABLE_ID \
  ALB_ARN TARGET_GROUP_ARNS ALB_SG_ARNS SERVICE_SG_ARNS \
  EXPRESS_LOG_GROUPS AWS_PRESENCE AWS_PRESENCE_OUTPUT
```

Hinweise zum erwarteten Ergebnis:

- Express Gateway Service, stackeigenes ECR, stackeigene Log Group,
  Managed Secret, Runtime-Rollen und die stackeigene VPC-Netzwerkbasis sind
  weg (`FAIL`, falls nicht oder bei AWS-Fehlern jenseits Not-found).
- Eindeutig serviceeigene Target Groups und `serviceSecurityGroups` sind weg
  (`FAIL`, falls nicht).
- Ein geteilter Application Load Balancer, zugehörige
  `loadBalancerSecurityGroups` oder von Express Mode zurückbehaltene Log Groups
  sind möglich und werden als `WARN` behandelt; Cleanup erst nach manueller
  Attribution zu anderen Express-Services bzw. dem geteilten ALB.
- Automatisch erzeugte **accountweite Service-Linked Roles** (z. B. für ECS
  Application Auto Scaling oder Elastic Load Balancing) und der Cluster
  `default` sind **kein Fehler** dieses Stack-Deletes und müssen nicht
  entfernt werden.
- Der IAM-Control-Plane-Abbau folgt erst nach erfolgreicher
  Post-Delete-Verifikation mit
  `python tools/aws_reference_demo_iam_control_plane.py teardown` und ist
  kein Stack-Schritt.

## 9. Kosten- und Budgetkontrolle

- Demo nur bei Bedarf deployen; nach dem Nachweis Stack löschen
- `MinTaskCount`/`MaxTaskCount` bleiben `1`
- Billing-Budget oder Kostenalarm im Account aktiv halten
- keine Dauerbetriebsannahme für diesen Portfolio-Stack

## Bekannte Grenzen

- keine Authentifizierung, Custom Domain, WAF, private Subnetze/NAT, DB oder
  Multi-Cloud
- keine Default-VPC-Abhängigkeit; Netzwerkbasis ist stackeigen und öffentlich
- keine Unterstützung einer vorhandenen externen Secret-ARN in diesem Stack
- keine Task Role; Anwendungscode hat keine AWS-Rechte
- manuelle AWS-Verifikation bleibt ausstehend, bis ein Operator den Stack
  bewusst im eigenen Account durchspielt und das Go-/No-Go-Gate aus dem
  IAM-/Lifecycle-Modell v2.3 erfüllt ist
- strukturierte Runtime-Logs und Basis-Metriken folgen in späteren
  Phase-5-Branches
