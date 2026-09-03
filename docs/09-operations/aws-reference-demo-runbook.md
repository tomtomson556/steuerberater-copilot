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
  dieses Stack-Laufs. Die separate Bootstrap-Rolle
  `reference-demo-iam-bootstrap` und die privilegierte Ausgangsidentität
  `reference-demo-privileged-caller` sind der IAM-Vertrag unter
  `infra/iam/reference-demo/v2.3/`; dieses Runbook erzeugt oder löscht sie nicht.
- lokale Docker-Build-Fähigkeit für `linux/amd64` und AWS-CLI als Operator
  mit den v2.3-Operator-Policies, einschließlich der Verifier-Policy
- Read-only AWS Account-Preflight mit genau diesen vorhandenen
  v2.3-Verifier-Rechten vor `aws cloudformation validate-template` und vor
  jedem ersten AWS-Write. Der Preflight erzeugt, ändert oder löscht keine
  Ressourcen, repariert nichts und benennt bei Kollisionen nicht um
- Billing-Budget oder Kostenalarm im Account; diese Kostenkontrolle ist ein
  vorab extern zu bestätigendes Gate und nicht über die Verifier-Policy
  introspektierbar
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
von `TaskRoleArn`. `ImageUri` muss exakt
`^$|^[0-9]{12}\.dkr\.ecr\.eu-central-1\.amazonaws\.com/steuerberater-copilot-reference-demo@sha256:[A-Fa-f0-9]{64}$`
entsprechen.

Lokale Operator-Variablen ohne AWS-Aufruf. `ACCOUNT_ID` und
`SERVICE_ROLE_ARN` setzt erst der folgende Preflight.

```bash
REGION=eu-central-1
STACK_NAME=steuerberater-copilot-reference-demo
TEMPLATE="file://infra/cloudformation/reference-demo.yaml"
ECR_REPO_NAME=steuerberater-copilot-reference-demo
LOG_GROUP_NAME=/steuerberater-copilot/reference-demo/application
SECRET_NAME=steuerberater-copilot/reference-demo/synthetic
EXPRESS_SERVICE_NAME=steuerberater-copilot-reference-demo
```

### Read-only AWS Account-Preflight

Dieser Abschnitt ist der verbindliche Account-Preflight vor
`aws cloudformation validate-template` und vor jedem ersten AWS-Write
dieses Runbooks (`create-change-set` und jede andere schreibende Aktion).
Er nutzt ausschließlich die vorhandenen Rechte aus
`infra/iam/reference-demo/v2.3/operator-verifier-policy.json`. Policies
werden während des Ablaufs nicht erweitert. Es gibt kein automatisches
Reparieren und kein spontanes Umbenennen bei Kollisionen.

Jedes unerwartete Ergebnis, jede nicht ausdrücklich als zulässiger
Pre-State inventarisierte fehlende Voraussetzung und jedes `AccessDenied`
ist **No-Go**. Die inventarisierte Absenz des ECS-Clusters `default` nur
mit `describe-clusters`-Failure Reason `MISSING` für genau diesen Cluster
sowie `NoSuchEntity` für eine der drei kanonischen Service-Linked Roles
ist kein `AccessDenied` und kein automatisches No-Go. Jeder andere
Failure-Inhalt bei Cluster `default` ist **No-Go**. Ein bestandener
Preflight gibt nur den Weg zu `validate-template` frei. Er ist kein allgemeines AWS-Live-Test-Go, kein
Change-Set-Go und kein Stack-Create.

Bereits abgeschlossen und nicht Teil dieses Preflights: IAM-Simulator
SIM-001 bis SIM-146 sowie AWS Access Analyzer / `ValidatePolicy` (zuvor 19/19
Dokumente, 0 Findings; für die beiden in SIM-143 bis SIM-146 korrigierten
Policy-Dokumente erneut 2/2 mit 0 Findings). Dieser Ablauf führt sie nicht
erneut aus und behandelt sie nicht als offenes Preflight-Ziel. Template und
Guard bleiben unverändert.

Noch ausstehendes Draft-PR-Gate, nicht Teil dieses Account-Preflight-Ablaufs
und keine Wiederholung von SIM-001 bis SIM-146: read-only IAM-Policy-
Simulator- und Access-Analyzer-`ValidatePolicy`-Evidenz für die geänderten
Dokumente `operator-verifier-policy.json` und `operator-boundary.json`,
einschließlich der zusätzlichen `iam:GetRole`-Freigabe auf die drei
pfadlosen Pre-Existence-Lookup-ARNs.

Vor den AWS-Leseaufrufen organisatorisch bestätigen. Die vorhandenen
Operatorrechte können diese Gates nicht zuverlässig introspektieren;
unbestätigt oder unklar ist **No-Go**:

- kurzlebige, freigegebene Operator-Session mit MFA. `sts:GetCallerIdentity`
  beweist MFA nicht
  ([get-caller-identity](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html))
- aktives Billing-Budget oder Kostenalarm im Account (Kostenkontrolle)
- Organizations-SCPs in `eu-central-1` blockieren den Referenzpfad nicht
- Permission Sets erweitern den Operator nicht über v2.3 hinaus und
  entziehen keine Verifier-/CloudFormation-Rechte
- Session Policies schränken die Operator-Session nicht unter die
  v2.3-Operator-Policies ein
- keine unerwartete übergeordnete Permissions Boundary an der
  Operatoridentität außer `reference-demo-operator-boundary`
- keine Instanzprofile an der CloudFormation-Service-Rolle; kundenverwaltete
  Control-Plane-Policies haben nur die Default-Version `v1`. Beides ist mit
  der Verifier-Policy nicht vollständig enumerierbar (`iam:ListInstanceProfilesForRole`
  und `iam:ListPolicyVersions` sind kein Verifier-Recht) und wird deshalb
  vorab bestätigt, nicht durch neue Berechtigungen

Inventar, das v2.3 später schreiben darf, ohne es im Preflight zu erzeugen:

- ECS-Cluster `default`: Präsenz oder Absenz inventarisieren. Liefert
  `describe-clusters` keinen Cluster, ist Absenz nur zulässiger Pre-State,
  wenn die Failure-Antwort den angefragten Cluster `default` mit Reason
  `MISSING` ausweist
  ([API failure reasons](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/api_failures_messages.html)).
  Jeder andere Failure-Inhalt ist **No-Go**. Protokollieren und **nicht**
  erstellen. Ist der Cluster vorhanden, exakten ARN
  `arn:aws:ecs:eu-central-1:<ACCOUNT_ID>:cluster/default`, Status und
  vorhandene Tags prüfen. Abweichender ARN oder unerwarteter Status ist
  No-Go. Der unmittelbar validierte Zustand wird für die Express-Service-
  Kollisionsprüfung weiterverwendet: Bei `ABSENT` wird der von einem Cluster
  abhängige Describe übersprungen und der Service als absent inventarisiert.
  Bei `PRESENT` wird er ausgeführt; `ClusterNotFoundException` ist dann kein
  zulässiger Not-found-Fall, sondern unerwartet und **No-Go**.
- Die drei kanonischen Service-Linked Roles
  (`AWSServiceRoleForECS`, `AWSServiceRoleForElasticLoadBalancing`,
  `AWSServiceRoleForApplicationAutoScaling_ECSService`): kanonischer Name,
  exakter IAM-Pfad/ARN und Service-Principal der Trust Policy prüfen.
  `aws iam get-role --role-name` autorisiert AWS bei noch nicht vorhandener
  Rolle gegen den pfadlosen Lookup-ARN
  `arn:aws:iam::<ACCOUNT_ID>:role/<RoleName>`, nicht gegen den späteren
  kanonischen pfadbehafteten SLR-ARN. Deshalb erlaubt die Verifier-Policy
  `iam:GetRole` zusätzlich genau auf
  `arn:aws:iam::<ACCOUNT_ID>:role/AWSServiceRoleForECS`,
  `arn:aws:iam::<ACCOUNT_ID>:role/AWSServiceRoleForElasticLoadBalancing` und
  `arn:aws:iam::<ACCOUNT_ID>:role/AWSServiceRoleForApplicationAutoScaling_ECSService`.
  Die Operator-Boundary enthält dieselbe getrennte `iam:GetRole`-Freigabe.
  `GetRolePolicy`, `ListAttachedRolePolicies`, `ListRolePolicies` und
  `ListRoleTags` bleiben auf die kanonischen pfadbehafteten SLR-ARNs und die
  bestehenden Referenzrollen begrenzt. Ist die Rolle vorhanden, bleiben
  Name, Pfad, ARN und Trust-Principal unverändert gegen den kanonischen
  Vertrag zu prüfen. `NoSuchEntity` ist inventarisierte Absenz, kein
  `AccessDenied`. Absenz im Preflight nicht durch ein manuelles SLR-Create
  beheben. Falscher Pfad, ARN oder Trust ist No-Go. Jedes `AccessDenied` bleibt No-Go.
- Service Quotas entlang des v2.3-Vertrags: VPC/EIP-IPv4 (`vpc`), ECS
  (`ecs`), ELB (`elasticloadbalancing`), ACM (`acm`) und Fargate
  (`fargate`). Für `vpc`, `elasticloadbalancing`, `acm` und `fargate` die
  angewendeten Limits mit `list-service-quotas` lesen. AWS unterstützt für
  ECS keine applied quotas; `list-service-quotas --service-code ecs`
  liefert sie deshalb nicht. ECS-Default-Quotas mit dem bereits erlaubten
  `list-aws-default-service-quotas` lesen. Das ist **kein** automatischer
  Nachweis von Restkapazität oder aktueller Nutzung. Der Operator bewertet
  die Ausgabe manuell als read-only Go-/No-Go-Gate. Kein Quota-Increase in
  diesem Ablauf.

Technische Lese-Gates in derselben Operator-Shell. `set -e` beendet bei
jedem unerwarteten Fehler. Dokumentierte Not-found-Fälle sind die
Kollisionsprüfungen fester Referenzressourcen, die Inventar-Absenz von
Cluster `default` nur bei Failure Reason `MISSING` für genau diesen
Cluster und `NoSuchEntity` für die drei Service-Linked Roles. Jeder andere
Fehler einschließlich `AccessDenied` oder anderem Cluster-Failure-Inhalt
ist **No-Go**.

```bash
set -euo pipefail

REGION=eu-central-1
STACK_NAME=steuerberater-copilot-reference-demo
TEMPLATE="file://infra/cloudformation/reference-demo.yaml"
ECR_REPO_NAME=steuerberater-copilot-reference-demo
LOG_GROUP_NAME=/steuerberater-copilot/reference-demo/application
SECRET_NAME=steuerberater-copilot/reference-demo/synthetic
EXPRESS_SERVICE_NAME=steuerberater-copilot-reference-demo

preflight_fail() {
  echo "No-Go: $*" >&2
  exit 1
}

preflight_require_success() {
  local label="$1"
  shift
  local out ec
  set +e
  out="$("$@" 2>&1)"
  ec=$?
  set -e
  if [ "$ec" -ne 0 ]; then
    echo "$out" >&2
    preflight_fail "$label fehlgeschlagen (AccessDenied, fehlende Voraussetzung oder unerwartetes Ergebnis)."
  fi
  PREFLIGHT_OUTPUT="$out"
}

preflight_require_absent() {
  local label="$1"
  local not_found_re="$2"
  shift 2
  local out ec
  set +e
  out="$("$@" 2>&1)"
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then
    echo "$out" >&2
    preflight_fail "Kollision: $label existiert bereits. Kein Umbenennen, kein Reparieren."
  fi
  if ! printf '%s\n' "$out" | grep -Eqi -- "$not_found_re"; then
    echo "$out" >&2
    preflight_fail "$label: unerwartetes Ergebnis oder AccessDenied statt dokumentiertem Not-found."
  fi
}

preflight_inventory_get_role() {
  local label="$1"
  local role_name="$2"
  local expected_path="$3"
  local expected_principal="$4"
  local expected_arn="arn:aws:iam::${ACCOUNT_ID}:role${expected_path}${role_name}"
  local out ec
  # Absente SLRs autorisiert AWS auf arn:aws:iam::<ACCOUNT_ID>:role/<RoleName>.
  set +e
  out="$(aws iam get-role --role-name "$role_name" --output json 2>&1)"
  ec=$?
  set -e
  if [ "$ec" -ne 0 ]; then
    if printf '%s\n' "$out" | grep -Eqi -- 'NoSuchEntity'; then
      echo "Inventar: $label ABSENT (NoSuchEntity, zulässiger Pre-State). Nicht erstellen."
      return 0
    fi
    echo "$out" >&2
    preflight_fail "$label: AccessDenied oder unerwarteter Fehler, nicht NoSuchEntity."
  fi
  PREFLIGHT_OUTPUT="$out"
  EXPECTED_ROLE_ARN="$expected_arn"
  EXPECTED_ROLE_PATH="$expected_path"
  EXPECTED_ROLE_NAME="$role_name"
  EXPECTED_TRUST_PRINCIPAL="$expected_principal"
  export EXPECTED_ROLE_ARN EXPECTED_ROLE_PATH EXPECTED_ROLE_NAME EXPECTED_TRUST_PRINCIPAL
  printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c "
import json, os, sys
role = json.load(sys.stdin)['Role']
name = os.environ['EXPECTED_ROLE_NAME']
path = os.environ['EXPECTED_ROLE_PATH']
arn = os.environ['EXPECTED_ROLE_ARN']
principal = os.environ['EXPECTED_TRUST_PRINCIPAL']
assert role.get('RoleName') == name, role.get('RoleName')
assert role.get('Path') == path, role.get('Path')
assert role.get('Arn') == arn, role.get('Arn')
trust = role.get('AssumeRolePolicyDocument') or {}
statements = trust.get('Statement') or []
if isinstance(statements, dict):
    statements = [statements]
services = []
for statement in statements:
    if statement.get('Effect') != 'Allow':
        continue
    action = statement.get('Action')
    actions = action if isinstance(action, list) else [action]
    if 'sts:AssumeRole' not in actions:
        continue
    prin = (statement.get('Principal') or {}).get('Service')
    if isinstance(prin, list):
        services.extend(prin)
    elif prin:
        services.append(prin)
assert principal in services, (arn, services)
print(
    'Inventar: %s PRESENT name=%s path=%s arn=%s trust=%s'
    % (name, role.get('RoleName'), role.get('Path'), role.get('Arn'), principal)
)
" || preflight_fail "$label: Name, Pfad, ARN oder Trust-Principal weichen vom kanonischen Vertrag ab."
  preflight_require_success \
    "$label angehängte Policies" \
    aws iam list-attached-role-policies --role-name "$role_name" --output json
  echo "Inventar: $label Attachments gelesen (nur Bestand, keine Änderung)."
}

# 1. Caller Identity, Account-ID, Region
preflight_require_success \
  "Caller Identity" \
  aws sts get-caller-identity --output json
ACCOUNT_ID="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c 'import json,sys; print(json.load(sys.stdin)["Account"])')"
CALLER_ARN="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c 'import json,sys; print(json.load(sys.stdin)["Arn"])')"
printf '%s\n' "$ACCOUNT_ID" | grep -Eq '^[0-9]{12}$' \
  || preflight_fail "Account-ID ist nicht zwölfstellig."
printf '%s\n' "$CALLER_ARN" | grep -Eq "^arn:aws:sts::${ACCOUNT_ID}:(assumed-role|federated-user)/" \
  || preflight_fail "Caller ist keine kurzlebige STS-Session (assumed-role oder federated-user)."
printf '%s\n' "$CALLER_ARN" | grep -Eq 'assumed-role/reference-demo-iam-bootstrap/' \
  && preflight_fail "Bootstrap-Rolle ist keine Operator-Session."
printf '%s\n' "$CALLER_ARN" | grep -Eq 'assumed-role/reference-demo-cfn-service-role/' \
  && preflight_fail "CloudFormation-Service-Rolle ist keine Operator-Session."
printf '%s\n' "$CALLER_ARN" | grep -Eq ":root$" \
  && preflight_fail "Root ist unzulässig."

SERVICE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/steuerberater-copilot/control-plane/reference-demo-cfn-service-role"
EXPRESS_SERVICE_ARN="arn:aws:ecs:${REGION}:${ACCOUNT_ID}:service/default/${EXPRESS_SERVICE_NAME}"
EXPRESS_MANAGED_POLICY_ARN="arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
CFN_FOUNDATION_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/steuerberater-copilot/control-plane/reference-demo-cfn-foundation-policy"
CFN_LIFECYCLE_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/steuerberater-copilot/control-plane/reference-demo-cfn-iam-lifecycle-policy"
CFN_SERVICE_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/steuerberater-copilot/control-plane/reference-demo-cfn-service-policy"
CFN_SERVICE_BOUNDARY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/steuerberater-copilot/control-plane/reference-demo-cfn-service-boundary"
export ACCOUNT_ID REGION \
  CFN_FOUNDATION_POLICY_ARN CFN_LIFECYCLE_POLICY_ARN CFN_SERVICE_POLICY_ARN

preflight_require_success \
  "Availability Zones in eu-central-1" \
  aws ec2 describe-availability-zones \
    --region "$REGION" \
    --query 'AvailabilityZones[?State==`available`].ZoneName' \
    --output text
AZ_COUNT="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | wc -w)"
[ "$AZ_COUNT" -ge 2 ] || preflight_fail "eu-central-1 hat nicht mindestens zwei verfügbare AZs."

# 2. CloudFormation-Service-Rolle: Existenz, Trust, Boundary, Tags, Anhänge
preflight_require_success \
  "CloudFormation-Service-Rolle" \
  aws iam get-role --role-name reference-demo-cfn-service-role --output json
printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c "
import json, sys
role = json.load(sys.stdin)['Role']
assert role['RoleName'] == 'reference-demo-cfn-service-role'
assert role['Path'] == '/steuerberater-copilot/control-plane/'
assert role['Arn'].endswith('/steuerberater-copilot/control-plane/reference-demo-cfn-service-role')
boundary = role.get('PermissionsBoundary') or {}
assert boundary.get('PermissionsBoundaryArn', '').endswith('reference-demo-cfn-service-boundary')
trust = role['AssumeRolePolicyDocument']
statements = trust['Statement'] if isinstance(trust['Statement'], list) else [trust['Statement']]
assert statements == [{
    'Sid': 'TrustCloudFormationOnly',
    'Effect': 'Allow',
    'Principal': {'Service': 'cloudformation.amazonaws.com'},
    'Action': 'sts:AssumeRole',
}], trust
" || preflight_fail "Service-Rolle: Trust, Path oder Boundary weichen vom v2.3-Vertrag ab."
preflight_require_success \
  "Service-Rollen-Tags" \
  aws iam list-role-tags --role-name reference-demo-cfn-service-role --output json
printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c "
import json, sys
tags = {item['Key']: item['Value'] for item in json.load(sys.stdin).get('Tags', [])}
assert tags == {
    'Project': 'steuerberater-copilot',
    'Component': 'reference-demo',
    'Environment': 'portfolio-test',
    'ManagedBy': 'cloudformation',
    'Lifecycle': 'ephemeral',
}, tags
" || preflight_fail "Service-Rolle hat unerwartete Tags."
preflight_require_success \
  "Service-Rollen-Policy-Anhänge" \
  aws iam list-attached-role-policies --role-name reference-demo-cfn-service-role --output json
printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c "
import json, os, sys
attached = {item['PolicyArn'] for item in json.load(sys.stdin).get('AttachedPolicies', [])}
expected = {
    os.environ['CFN_FOUNDATION_POLICY_ARN'],
    os.environ['CFN_LIFECYCLE_POLICY_ARN'],
    os.environ['CFN_SERVICE_POLICY_ARN'],
}
assert attached == expected, attached
" || preflight_fail "Service-Rolle hat unerwartete oder fehlende Policy-Anhänge."
preflight_require_success \
  "Service-Rollen-Inline-Policies" \
  aws iam list-role-policies --role-name reference-demo-cfn-service-role \
    --query 'PolicyNames' --output text
[ -z "$PREFLIGHT_OUTPUT" ] || preflight_fail "Service-Rolle hat unerwartete Inline-Policies."

for POLICY_ARN in \
  "$CFN_FOUNDATION_POLICY_ARN" \
  "$CFN_LIFECYCLE_POLICY_ARN" \
  "$CFN_SERVICE_POLICY_ARN" \
  "$CFN_SERVICE_BOUNDARY_ARN"
do
  preflight_require_success \
    "Policy $POLICY_ARN" \
    aws iam get-policy --policy-arn "$POLICY_ARN" \
      --query 'Policy.DefaultVersionId' --output text
  [ "$PREFLIGHT_OUTPUT" = "v1" ] || preflight_fail "DefaultVersionId von $POLICY_ARN ist nicht v1."
  preflight_require_success \
    "PolicyVersion $POLICY_ARN v1" \
    aws iam get-policy-version \
      --policy-arn "$POLICY_ARN" \
      --version-id v1 \
      --query 'PolicyVersion.VersionId' \
      --output text
  [ "$PREFLIGHT_OUTPUT" = "v1" ] || preflight_fail "Policy-Version v1 für $POLICY_ARN nicht lesbar."
done

# 3. ECS-Cluster default inventarisieren; Absenz nur bei Reason MISSING
preflight_require_success \
  "ECS-Cluster default" \
  aws ecs describe-clusters \
    --region "$REGION" \
    --clusters default \
    --include TAGS \
    --output json
ECS_CLUSTER_DEFAULT_STATE="$(printf '%s\n' "$PREFLIGHT_OUTPUT" | python -c "
import json, os, sys
payload = json.load(sys.stdin)
clusters = payload.get('clusters') or []
failures = payload.get('failures') or []
account = os.environ['ACCOUNT_ID']
region = os.environ['REGION']
expected_arn = f'arn:aws:ecs:{region}:{account}:cluster/default'
if not clusters:
    failure = failures[0] if len(failures) == 1 else None
    failure_arn = (failure or {}).get('arn') or ''
    identifies_default = (
        failure_arn == expected_arn
        or failure_arn.endswith(':cluster/default')
        or failure_arn.rstrip('/').split('/')[-1] == 'default'
    )
    if (
        failure is None
        or failure.get('reason') != 'MISSING'
        or not identifies_default
    ):
        raise SystemExit(
            'unerwarteter Failure-Inhalt statt Reason MISSING für Cluster default'
        )
    print(
        'Inventar: ECS-Cluster default ABSENT (zulässiger Pre-State, Reason MISSING). '
        'Nicht erstellen. failures=%s' % (failures,),
        file=sys.stderr,
    )
    print('ABSENT')
    raise SystemExit
if len(clusters) != 1:
    raise SystemExit('unerwartete Anzahl Cluster in der Describe-Antwort')
cluster = clusters[0]
arn = cluster.get('clusterArn')
status = cluster.get('status')
tags = cluster.get('tags') or []
print(
    'Inventar: ECS-Cluster default PRESENT arn=%s status=%s tags=%s'
    % (arn, status, tags),
    file=sys.stderr,
)
if cluster.get('clusterName') != 'default' or arn != expected_arn:
    raise SystemExit('Cluster-ARN oder Name weicht vom kanonischen default-ARN ab')
if status != 'ACTIVE':
    raise SystemExit('vorhandener default-Cluster ist nicht ACTIVE')
print('PRESENT')
")" || preflight_fail "ECS-Cluster default: unerwarteter Zustand. Nicht erstellen und nicht reparieren."
case "$ECS_CLUSTER_DEFAULT_STATE" in
  ABSENT|PRESENT) ;;
  *) preflight_fail "ECS-Cluster default: interner Inventarzustand ist weder ABSENT noch PRESENT." ;;
esac

# 4. Kanonische Service-Linked Roles inventarisieren
preflight_inventory_get_role \
  "Service-Linked Role AWSServiceRoleForECS" \
  AWSServiceRoleForECS \
  /aws-service-role/ecs.amazonaws.com/ \
  ecs.amazonaws.com
preflight_inventory_get_role \
  "Service-Linked Role AWSServiceRoleForElasticLoadBalancing" \
  AWSServiceRoleForElasticLoadBalancing \
  /aws-service-role/elasticloadbalancing.amazonaws.com/ \
  elasticloadbalancing.amazonaws.com
preflight_inventory_get_role \
  "Service-Linked Role AWSServiceRoleForApplicationAutoScaling_ECSService" \
  AWSServiceRoleForApplicationAutoScaling_ECSService \
  /aws-service-role/ecs.application-autoscaling.amazonaws.com/ \
  ecs.application-autoscaling.amazonaws.com

# 5. Kollisionen fester Referenzressourcen
preflight_require_absent \
  "CloudFormation-Stack $STACK_NAME" \
  'does not exist' \
  aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME"

preflight_require_absent \
  "ECR-Repository $ECR_REPO_NAME" \
  'RepositoryNotFoundException' \
  aws ecr describe-repositories \
    --region "$REGION" \
    --repository-names "$ECR_REPO_NAME"

set +e
LOG_OUT="$(aws logs describe-log-groups \
  --region "$REGION" \
  --log-group-name-prefix "$LOG_GROUP_NAME" \
  --query "logGroups[?logGroupName=='${LOG_GROUP_NAME}'].logGroupName" \
  --output text 2>&1)"
LOG_EC=$?
set -e
if [ "$LOG_EC" -ne 0 ]; then
  echo "$LOG_OUT" >&2
  preflight_fail "Log-Group-Prüfung fehlgeschlagen (AccessDenied oder unerwartetes Ergebnis)."
fi
[ -z "$LOG_OUT" ] || preflight_fail "Kollision: Log Group $LOG_GROUP_NAME existiert bereits."

preflight_require_absent \
  "Secret $SECRET_NAME" \
  'ResourceNotFoundException' \
  aws secretsmanager describe-secret \
    --region "$REGION" \
    --secret-id "$SECRET_NAME"

if [ "$ECS_CLUSTER_DEFAULT_STATE" = "ABSENT" ]; then
  echo "Inventar: Express Service $EXPRESS_SERVICE_NAME ABSENT, weil der unmittelbar validierte Cluster default ABSENT ist. Collision-Describe übersprungen."
else
  preflight_require_absent \
    "Express Service $EXPRESS_SERVICE_NAME" \
    'ResourceNotFoundException' \
    aws ecs describe-express-gateway-service \
      --region "$REGION" \
      --service-arn "$EXPRESS_SERVICE_ARN"
  echo "Inventar: Express Service $EXPRESS_SERVICE_NAME ABSENT (ResourceNotFoundException bei vorhandenem Cluster default)."
fi

preflight_require_absent \
  "Task Execution Role" \
  'NoSuchEntity' \
  aws iam get-role --role-name task-execution
preflight_require_absent \
  "Express Infrastructure Role" \
  'NoSuchEntity' \
  aws iam get-role --role-name express-infrastructure

# 6. Service-Quota-Limits lesen; Restkapazität manuell bewerten
# v2.3: VPC/EIP-IPv4, ECS, ELB, ACM, Fargate. ECS ohne applied quotas.
preflight_require_success \
  "Service Quotas ecs default" \
  aws service-quotas list-aws-default-service-quotas \
    --region "$REGION" \
    --service-code ecs \
    --query 'Quotas[].{Name:QuotaName,Value:Value}' \
    --output json
for SERVICE_CODE in \
  vpc elasticloadbalancing acm fargate ecr logs secretsmanager cloudformation iam
do
  preflight_require_success \
    "Service Quotas $SERVICE_CODE" \
    aws service-quotas list-service-quotas \
      --region "$REGION" \
      --service-code "$SERVICE_CODE" \
      --query 'Quotas[].{Name:QuotaName,Value:Value}' \
      --output json
done
echo "Service-Quota-Limits gelesen. vpc, elasticloadbalancing, acm und fargate über list-service-quotas (angewendete Limits). ecs über list-aws-default-service-quotas, weil AWS für ECS keine applied quotas unterstützt. Keine Restnutzung. Restkapazität ist damit nicht automatisch nachgewiesen. Manuell als read-only Go/No-Go bewerten. Kein Quota-Increase in diesem Ablauf."

# 7. Zugriff auf CloudTrail Event History
preflight_require_success \
  "CloudTrail Event History" \
  aws cloudtrail lookup-events \
    --region "$REGION" \
    --max-items 1 \
    --output json

# 8. AWS-verwaltete Express-Policy gegen eingefrorene Infrastructure-Boundary
preflight_require_success \
  "Express-Managed-Policy-Metadaten" \
  aws iam get-policy \
    --policy-arn "$EXPRESS_MANAGED_POLICY_ARN" \
    --query 'Policy.DefaultVersionId' \
    --output text
EXPRESS_DEFAULT_VERSION="$PREFLIGHT_OUTPUT"
[ "$EXPRESS_DEFAULT_VERSION" = "v6" ] || preflight_fail "AWS-verwaltete Express-Policy ist nicht mehr die eingefrorene Version v6 (Stand 31. Juli 2026). Kein Policy-Update in diesem Ablauf."
preflight_require_success \
  "Express-Managed-Policy-Version" \
  aws iam get-policy-version \
    --policy-arn "$EXPRESS_MANAGED_POLICY_ARN" \
    --version-id "$EXPRESS_DEFAULT_VERSION" \
    --output json
echo "Lokal gegen infra/iam/reference-demo/v2.3/express-infrastructure-boundary.json abgleichen. Neue Aktionen außerhalb der eingefrorenen Boundary sind No-Go. Die Boundary nicht erweitern."

echo "Read-only AWS Account-Preflight bestanden. Als Nächstes nur validate-template; kein Live-Test-Go."
```

Die Kostenkontrolle (aktives Billing-Budget oder Kostenalarm) bleibt das
externe Gate aus den Voraussetzungen. Die Verifier-Policy enthält keine
Budgets-APIs; ein fehlendes oder unbestätigtes Budget ist **No-Go**, kein
Schreibversuch.

Erst nach bestandenem Preflight folgt die read-only
CloudFormation-Templatevalidierung. Der Aufruf `validate-template` erzeugt
oder ändert keine Ressourcen; er prüft, ob CloudFormation das YAML
akzeptiert, und nennt die erforderlichen Capabilities
([validate-template](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/validate-template.html)).
Account-Preflight und `validate-template` gehören nicht zu den
netzwerkfreien Standardtests und werden hier nicht ausgeführt.

```bash
aws cloudformation validate-template \
  --region "$REGION" \
  --template-body "$TEMPLATE"
```

Erwartung: die Antwort enthält `CAPABILITY_NAMED_IAM`. Validierungsfehler,
YAML-Parserfehler oder unerwartete Capabilities sind ein No-Go. Der Aufruf
ist kein Change Set und kein `create-stack`/`update-stack`. Die Variablen
`REGION`, `STACK_NAME`, `ACCOUNT_ID`, `SERVICE_ROLE_ARN` und `TEMPLATE`
gelten für die folgenden Schritte weiter.

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

`IMAGE_URI` wird ausschließlich aus dem stackeigenen `ECR_URI` und dem über
ECR ermittelten `IMAGE_DIGEST` gebildet. Docker Hub, GHCR, andere Registries,
andere Regionen oder Repositorynamen, Image-Tags ohne Digest und ungültige
Account-IDs sind für `DeployService=true` unzulässig.

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
- `POST /ai/draft` emittiert CloudWatch-Embedded-Metric-Format-Events über
  den bestehenden awslogs-Pfad (`logs:PutLogEvents`, ohne `PutMetricData`).
  Benutzerdefinierte CloudWatch-Metriken können zusätzliche Kosten
  verursachen
  ([CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/)).
  Es gibt kein verwaltetes Dashboard und keine Alarme in diesem Stand.

## Bekannte Grenzen

- keine Authentifizierung, Custom Domain, WAF, private Subnetze/NAT, DB oder
  Multi-Cloud
- keine Default-VPC-Abhängigkeit; Netzwerkbasis ist stackeigen und öffentlich
- keine Unterstützung einer vorhandenen externen Secret-ARN in diesem Stack
- keine Task Role; Anwendungscode hat keine AWS-Rechte
- manuelle AWS-Verifikation bleibt ausstehend, bis ein Operator den Stack
  bewusst im eigenen Account durchspielt und das Go-/No-Go-Gate aus dem
  IAM-/Lifecycle-Modell v2.3 erfüllt ist. Ein bestandener read-only
  Account-Preflight ist kein allgemeines AWS-Live-Test-Go
- strukturierte Runtime-Logs und Basic Runtime Metrics für `POST /ai/draft`
  sind vorhanden (genau ein CloudWatch-Embedded-Metric-Format-JSON-Event je
  Aufruf auf stdout, serverseitige `X-Request-ID`). EMF wird mindestens
  einmal verarbeitet; gelegentliche doppelte Metrikwerte sind möglich
  ([EMF-Spezifikation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html),
  [Embedding metrics within logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)).
  Die reale EMF-Extraktion bleibt bis zur bewussten AWS-Verifikation
  unbestätigt. Kein AWS-Live-Test, kein Dashboard und keine Alarme in diesem
  Stand. `/health` und `/version` erzeugen keine Runtime-Metriken.
