# AWS Reference Demo Operations Runbook

Betriebs- und Deployment-Anleitung für den minimalen AWS-Referenz-Stack
(`infra/cloudformation/reference-demo.yaml`). Synthetische Portfolio-Demo
nur; keine echten Mandanten-, Kanzlei- oder Steuerdaten.

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Voraussetzungen

- AWS-Konto mit Default-VPC in `eu-central-1` (mindestens zwei öffentliche
  Subnetze in zwei AZs, mindestens acht freie IPs je Subnetz)
- lokale Docker-Build-Fähigkeit und AWS-CLI mit Rechten für CloudFormation,
  ECR, ECS, IAM, Logs und Secrets Manager
- Billing-Budget oder Kostenalarm im Account
- keine Credentials, Secret-Werte oder Access Keys im Repository

Dieses Runbook wird manuell ausgeführt. CI und Standardtests deployen keinen
Stack und benötigen kein AWS-Konto.

## 1. Stack-Create ohne Service

```bash
aws cloudformation create-stack \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo \
  --template-body file://infra/cloudformation/reference-demo.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=DeployService,ParameterValue=false \
    ParameterKey=CreateManagedSecret,ParameterValue=false \
    ParameterKey=InjectManagedSecret,ParameterValue=false

aws cloudformation wait stack-create-complete \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo

aws cloudformation describe-stacks \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo \
  --query 'Stacks[0].Outputs'
```

Erwartete Outputs: `EcrRepositoryUri`, `LogGroupName`. Kein Service-Endpoint.

## 2. Docker-Build und ECR-Push

```bash
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGION=eu-central-1
ECR_URI="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name steuerberater-copilot-reference-demo \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)"

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

docker build -t steuerberater-copilot:reference .
docker tag steuerberater-copilot:reference "${ECR_URI}:bootstrap"
docker push "${ECR_URI}:bootstrap"
```

## 3. Digest-Ermittlung

```bash
IMAGE_DIGEST="$(aws ecr describe-images \
  --region "$REGION" \
  --repository-name "$(basename "$ECR_URI")" \
  --image-ids imageTag=bootstrap \
  --query 'imageDetails[0].imageDigest' \
  --output text)"

IMAGE_URI="${ECR_URI}@${IMAGE_DIGEST}"
echo "$IMAGE_URI"
```

Nur Digest-URIs (`…@sha256:…`) sind für `DeployService=true` zulässig.

## 4. Stack-Update mit Service

```bash
aws cloudformation update-stack \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo \
  --template-body file://infra/cloudformation/reference-demo.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=DeployService,ParameterValue=true \
    ParameterKey=ImageUri,ParameterValue="$IMAGE_URI" \
    ParameterKey=CreateManagedSecret,ParameterValue=false \
    ParameterKey=InjectManagedSecret,ParameterValue=false

aws cloudformation wait stack-update-complete \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo

ENDPOINT="$(aws cloudformation describe-stacks \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo \
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
Im Runbook steht deshalb **kein** `--secret-string`-Literal.

1. Stack mit `CreateManagedSecret=true` und weiterhin
   `InjectManagedSecret=false` aktualisieren.
2. ARN aus Output `ManagedSecretArn` lesen.
3. **Außerhalb des Repositorys** einen synthetischen Demo-Wert setzen und
   danach sofort löschen bzw. unsetten.

Interaktive Eingabe (Wert wird nicht ausgegeben):

```bash
REGION=eu-central-1
MANAGED_SECRET_ARN="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name steuerberater-copilot-reference-demo \
  --query "Stacks[0].Outputs[?OutputKey=='ManagedSecretArn'].OutputValue" \
  --output text)"

read -r -s -p "Synthetischen Demo-Secret-Wert eingeben (Eingabe wird nicht angezeigt): " SECRET_VALUE
printf '\n'
aws secretsmanager put-secret-value \
  --region "$REGION" \
  --secret-id "$MANAGED_SECRET_ARN" \
  --secret-string "$SECRET_VALUE"
unset SECRET_VALUE
```

Alternativ temporäre Datei außerhalb des Repositorys:

```bash
SECRET_FILE="$(mktemp "${TMPDIR:-/tmp}/sbc-demo-secret.XXXXXX")"
chmod 600 "$SECRET_FILE"
read -r -s -p "Synthetischen Demo-Secret-Wert eingeben: " SECRET_VALUE
printf '\n'
printf '%s' "$SECRET_VALUE" > "$SECRET_FILE"
unset SECRET_VALUE
aws secretsmanager put-secret-value \
  --region "$REGION" \
  --secret-id "$MANAGED_SECRET_ARN" \
  --secret-string "file://${SECRET_FILE}"
rm -f "$SECRET_FILE"
unset SECRET_FILE
```

4. Erst danach Stack mit `InjectManagedSecret=true` und
   `DeployService=true` aktualisieren (Digest-`ImageUri` beibehalten).
5. Injection anhand der Task-Definition / Container-Secret-Verdrahtung prüfen
   (`REFERENCE_DEMO_SECRET` → Managed-Secret-ARN). Secret-Werte nicht in Logs
   oder Tickets schreiben.

Ungültige Kombinationen (Injection ohne Create, Injection ohne Deploy,
Deploy ohne Digest-URI) lehnt CloudFormation per Rules bzw. AllowedPattern ab.

## 7. Stack-Delete

Vor dem Delete Resource-IDs **außerhalb des Repositorys** sichern. Sonst sind
Express-ALB-, Target-Group- und Security-Group-Prüfungen nach dem Löschen nicht
reproduzierbar.

```bash
REGION=eu-central-1
STACK_NAME=steuerberater-copilot-reference-demo
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
ECR_REPO_NAME="$(basename "$ECR_URI")"
printf '%s\n' "$ECR_REPO_NAME" > "$VERIFY_DIR/ecr-repository-name.txt"

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

Danach den Stack löschen:

```bash
aws cloudformation delete-stack \
  --region "$REGION" \
  --stack-name "$STACK_NAME"

aws cloudformation wait stack-delete-complete \
  --region "$REGION" \
  --stack-name "$STACK_NAME"
```

`EmptyOnDelete: true` leert das ECR-Repository beim Löschen. Die
stackverwaltete Log Group mit 14 Tagen Retention wird mit dem Stack entfernt.
Bloßes Verringern der Task-Anzahl ist keine Abschaltung.

## 8. Prüfung auf verbliebene Ressourcen

Nach `DELETE_COMPLETE` die zuvor gesicherten IDs in `eu-central-1` prüfen.
Erwartetes Ergebnis: Express Service, stackeigenes ECR, stackeigene Log Group
und Managed Secret existieren nicht mehr; die zuvor erfassten dedizierten
Express-Ressourcen (ALB, Target Groups, Security Groups, Express-Log-Groups)
sind entfernt.

```bash
REGION=eu-central-1
# VERIFY_DIR aus Schritt 7 wiederverwenden
EXPRESS_SERVICE_ARN="$(cat "$VERIFY_DIR/express-service-arn.txt")"
ECR_REPO_NAME="$(cat "$VERIFY_DIR/ecr-repository-name.txt")"
LOG_GROUP_NAME="$(cat "$VERIFY_DIR/log-group-name.txt")"
MANAGED_SECRET_ARN="$(cat "$VERIFY_DIR/managed-secret-arn.txt")"
ALB_ARN="$(cat "$VERIFY_DIR/alb-arn.txt")"
TARGET_GROUP_ARNS="$(cat "$VERIFY_DIR/target-group-arns.txt")"
ALB_SG_ARNS="$(cat "$VERIFY_DIR/alb-security-group-arns.txt")"
SERVICE_SG_ARNS="$(cat "$VERIFY_DIR/service-security-group-arns.txt")"
EXPRESS_LOG_GROUPS="$(cat "$VERIFY_DIR/express-log-group-names.txt")"

# Express Gateway Service darf nicht mehr existieren
if aws ecs describe-express-gateway-service \
  --region "$REGION" \
  --service-arn "$EXPRESS_SERVICE_ARN"; then
  echo "FAIL: Express Gateway Service existiert noch" >&2
  exit 1
fi

# Stackeigenes ECR
if aws ecr describe-repositories \
  --region "$REGION" \
  --repository-names "$ECR_REPO_NAME"; then
  echo "FAIL: ECR-Repository existiert noch" >&2
  exit 1
fi

# Stackeigene Log Group
STACK_LOG_MATCHES="$(aws logs describe-log-groups \
  --region "$REGION" \
  --log-group-name-prefix "$LOG_GROUP_NAME" \
  --query "logGroups[?logGroupName=='${LOG_GROUP_NAME}']" \
  --output text)"
test -z "$STACK_LOG_MATCHES"

# Managed Secret (nur wenn zuvor angelegt; sonst steht None/leerer Wert in der Datei)
if [ -n "$MANAGED_SECRET_ARN" ] && [ "$MANAGED_SECRET_ARN" != "None" ]; then
  if aws secretsmanager describe-secret \
    --region "$REGION" \
    --secret-id "$MANAGED_SECRET_ARN"; then
    echo "FAIL: Managed Secret existiert noch" >&2
    exit 1
  fi
fi

# Dedizierte Express-ALB-Ressource
if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
  if aws elbv2 describe-load-balancers \
    --region "$REGION" \
    --load-balancer-arns "$ALB_ARN"; then
    echo "FAIL: Express ALB existiert noch (ggf. geteilter ALB; siehe Hinweis unten)" >&2
    exit 1
  fi
fi

# Target Groups
for tg_arn in $TARGET_GROUP_ARNS; do
  [ -z "$tg_arn" ] || [ "$tg_arn" = "None" ] && continue
  if aws elbv2 describe-target-groups \
    --region "$REGION" \
    --target-group-arns "$tg_arn"; then
    echo "FAIL: Target Group existiert noch: $tg_arn" >&2
    exit 1
  fi
done

# Security Groups (ALB- und Service-SG)
for sg_arn in $ALB_SG_ARNS $SERVICE_SG_ARNS; do
  [ -z "$sg_arn" ] || [ "$sg_arn" = "None" ] && continue
  sg_id="${sg_arn##*/}"
  SG_MATCHES="$(aws ec2 describe-security-groups \
    --region "$REGION" \
    --group-ids "$sg_id" \
    --query 'SecurityGroups' \
    --output text 2>/dev/null || true)"
  test -z "$SG_MATCHES"
done

# Von Express verwaltete Log Groups
for lg_name in $EXPRESS_LOG_GROUPS; do
  [ -z "$lg_name" ] || [ "$lg_name" = "None" ] && continue
  LG_MATCHES="$(aws logs describe-log-groups \
    --region "$REGION" \
    --log-group-name-prefix "$lg_name" \
    --query "logGroups[?logGroupName=='${lg_name}']" \
    --output text)"
  test -z "$LG_MATCHES"
done

echo "Post-delete checks passed for saved demo resource IDs."
rm -rf "$VERIFY_DIR"
unset VERIFY_DIR EXPRESS_SERVICE_ARN ECR_REPO_NAME LOG_GROUP_NAME \
  MANAGED_SECRET_ARN ALB_ARN TARGET_GROUP_ARNS ALB_SG_ARNS SERVICE_SG_ARNS \
  EXPRESS_LOG_GROUPS
```

Hinweise zum erwarteten Ergebnis:

- Service, stackeigenes ECR, stackeigene Log Group und Managed Secret sind weg.
- Dedizierte Express-Ressourcen aus `ecsManagedResources` sind entfernt.
- Ein von mehreren Express-Services **geteilter** Application Load Balancer kann
  laut AWS-Dokumentation beim Löschen eines einzelnen Express-Services erhalten
  bleiben; in einer isolierten Portfolio-Demo mit nur diesem Stack soll der
  erfasste ALB ebenfalls fehlen.
- Automatisch erzeugte **accountweite Service-Linked Roles** (z. B. für ECS
  Application Auto Scaling oder Elastic Load Balancing) sind **kein Fehler**
  dieses Stack-Deletes und müssen nicht entfernt werden.

## 9. Kosten- und Budgetkontrolle

- Demo nur bei Bedarf deployen; nach dem Nachweis Stack löschen
- `MinTaskCount`/`MaxTaskCount` bleiben `1`
- Billing-Budget oder Kostenalarm im Account aktiv halten
- keine Dauerbetriebsannahme für diesen Portfolio-Stack

## Bekannte Grenzen

- keine Authentifizierung, Custom Domain, WAF, private VPC, DB oder Multi-Cloud
- keine Unterstützung einer vorhandenen externen Secret-ARN in diesem Stack
- manuelle AWS-Verifikation bleibt ausstehend, bis ein Operator den Stack
  bewusst im eigenen Account durchspielt
- strukturierte Runtime-Logs und Basis-Metriken folgen in späteren
  Phase-5-Branches
