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

1. Stack mit `CreateManagedSecret=true` und weiterhin
   `InjectManagedSecret=false` aktualisieren.
2. ARN aus Output `ManagedSecretArn` lesen.
3. **Außerhalb des Repositorys** einen synthetischen Demo-Wert setzen:

```bash
aws secretsmanager put-secret-value \
  --region eu-central-1 \
  --secret-id "$MANAGED_SECRET_ARN" \
  --secret-string 'synthetic-demo-only-not-a-real-credential'
```

4. Erst danach Stack mit `InjectManagedSecret=true` und
   `DeployService=true` aktualisieren (Digest-`ImageUri` beibehalten).
5. Injection anhand der Task-Definition / Container-Secret-Verdrahtung prüfen
   (`REFERENCE_DEMO_SECRET` → Managed-Secret-ARN). Secret-Werte nicht in Logs
   oder Tickets schreiben.

Ungültige Kombinationen (Injection ohne Create, Injection ohne Deploy,
Deploy ohne Digest-URI) lehnt CloudFormation per Rules bzw. AllowedPattern ab.

## 7. Stack-Delete

```bash
aws cloudformation delete-stack \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo

aws cloudformation wait stack-delete-complete \
  --region eu-central-1 \
  --stack-name steuerberater-copilot-reference-demo
```

`EmptyOnDelete: true` leert das ECR-Repository beim Löschen. Die
stackverwaltete Log Group mit 14 Tagen Retention wird mit dem Stack entfernt.

## 8. Prüfung auf verbliebene Ressourcen

Nach erfolgreichem Delete in `eu-central-1` prüfen, dass keine Demo-Reste
verbleiben:

- Express Gateway Services / zugehörige ECS-Services
- Application Load Balancer und Target Groups mit Tag `AmazonECSManaged`
- von Express erzeugte Security Groups
- stackverwaltete Log Group
- ECR-Repository der Demo
- Managed Secret der Demo

Bloßes Verringern der Task-Anzahl ist keine Abschaltung.

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
