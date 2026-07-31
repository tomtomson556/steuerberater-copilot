# AWS Reference Demo IAM Control Plane v2.3

Versionierte IAM-Artefakte für die synthetische AWS-Referenzdemo in
`eu-central-1`. Sie setzen ausschließlich die IAM-Control-Plane aus dem
IAM-/Lifecycle-Konzept Version 2.3 um. Das CloudFormation-Template und das
Deployment-Runbook werden in diesem Stand nicht verändert.

## Artefakte

| Datei | Art | IAM-Name | IAM-Pfad |
|---|---|---|---|
| `task-execution-boundary.json` | Permissions Boundary | `task-execution-boundary` | `/steuerberater-copilot/reference-demo/` |
| `express-infrastructure-boundary.json` | Permissions Boundary | `express-infrastructure-boundary` | `/steuerberater-copilot/reference-demo/` |
| `cloudformation-service-role-foundation-policy.json` | Berechtigungs-Policy (ECR, Logs, EC2) | `reference-demo-cfn-foundation-policy` | `/steuerberater-copilot/control-plane/` |
| `cloudformation-service-role-iam-lifecycle-policy.json` | Berechtigungs-Policy (IAM-Rollenlebenszyklus) | `reference-demo-cfn-iam-lifecycle-policy` | `/steuerberater-copilot/control-plane/` |
| `cloudformation-service-role-policy.json` | Berechtigungs-Policy (Secrets Manager, ECS) | `reference-demo-cfn-service-policy` | `/steuerberater-copilot/control-plane/` |
| `cloudformation-service-role-boundary.json` | Permissions Boundary | `reference-demo-cfn-service-boundary` | `/steuerberater-copilot/control-plane/` |
| `operator-boundary.json` | Permissions Boundary | `reference-demo-operator-boundary` | `/steuerberater-copilot/control-plane/` |
| `operator-cloudformation-policy.json` | Berechtigungs-Policy | `reference-demo-operator-cloudformation` | `/steuerberater-copilot/control-plane/` |
| `operator-ecr-publisher-policy.json` | Berechtigungs-Policy | `reference-demo-operator-ecr-publisher` | `/steuerberater-copilot/control-plane/` |
| `operator-secret-initializer-policy.json` | Berechtigungs-Policy | `reference-demo-operator-secret-initializer` | `/steuerberater-copilot/control-plane/` |
| `operator-verifier-policy.json` | Berechtigungs-Policy | `reference-demo-operator-verifier` | `/steuerberater-copilot/control-plane/` |
| `cloudformation-service-role-trust-policy.json` | Trust Policy | Service-Rolle `reference-demo-cfn-service-role` | `/steuerberater-copilot/control-plane/` |

`<ACCOUNT_ID>` ist der einzige Platzhalter in den Policy-JSON-Dateien. Das
Werkzeug ersetzt ihn ausschließlich durch die explizit übergebene zwölfstellige
Account-ID. Die vorhandene Operatoridentität wird nicht in den Artefakten
gespeichert und muss bei jedem Aufruf ausdrücklich als Typ und Name angegeben
werden.

Die Express-Infrastructure-Boundary friert die für die Demo benötigte
Aktionsmenge der am 31. Juli 2026 aktuellen AWS-verwalteten Policy
`AmazonECSInfrastructureRoleforExpressGatewayServices` v6 ein und begrenzt ihre
regionalen und accountbezogenen ARNs auf den Referenzpfad. Änderungen der
AWS-verwalteten Policy erweitern die effektiven Rechte dadurch nicht
automatisch.

Die in Version 2.3 als ein Artefakt geplante CloudFormation-Service-Role-Policy
überschreitet mit ihrer vollständigen Aktions- und Condition-Matrix die
nicht erhöhbare AWS-Grenze von 6.144 Nicht-Whitespace-Zeichen pro
kundenverwalteter Policy. Sie ist deshalb in drei gemeinsam erforderliche,
getrennt gehashte Berechtigungs-Policies aufgeteilt: Foundation (ECR, Logs,
EC2), IAM-Lifecycle (CreateRole/TagRole und übrige IAM-Rollenaktionen) und
Service (Secrets Manager, ECS). Die weiterhin einzelne Service-Role-Boundary
begrenzt die Vereinigungsmenge aller drei Policies. Die beiden
`iam:CreateRole`-Statements und das `iam:TagRole`-Statement erzwingen alle
fünf festen Rollen-Tag-Werte über `aws:RequestTag/<Key>` und begrenzen
`aws:TagKeys` zusätzlich auf genau diese fünf Schlüssel. Tests prüfen die
Zeichengrenze für jedes kundenverwaltete Policy-Artefakt.

## Lokale Plan-Ausgabe

Der Standard ist rein lokal. Er liest keine AWS-Identität und führt keinen
externen Prozess aus:

```bash
python tools/aws_reference_demo_iam_control_plane.py bootstrap \
  --account-id 123456789012 \
  --operator-type role \
  --operator-name reference-demo-operator
```

Für den Abbau wird `bootstrap` durch `teardown` ersetzt. Beide Ausgaben nennen
Reihenfolge, feste ARNs und den kanonischen SHA-256-Hash jedes für die
Account-ID gerenderten Policy-Dokuments.

AWS-Zugriff ist nur mit allen ausdrücklichen Bestätigungen möglich:

```text
--apply
--bootstrap-role-name <explizite separate Bootstrap-Rollenname>
--confirm-aws-write-account <dieselbe zwölfstellige Account-ID>
--confirm-mfa-authenticated-session
--confirm-temporary-session
```

Diese Option ist für einen späteren, separat freigegebenen manuellen Test
bestimmt. Sie wurde beim Erstellen dieser Artefakte nicht ausgeführt.
Ein Apply darf ausschließlich aus einer bereits vorhandenen kurzlebigen,
MFA-geschützten Session der ausdrücklich benannten Bootstrap-Rolle erfolgen.
Zulässig ist nur der Caller-ARN

```text
arn:aws:sts::<ACCOUNT_ID>:assumed-role/<BOOTSTRAP_ROLE_NAME>/<SESSION_NAME>
```

Account-ID und Bootstrap-Rollenname müssen exakt passen. Die Bootstrap-Rolle
darf weder die ausdrücklich angegebene Operatorrolle noch
`reference-demo-cfn-service-role` sein. IAM User, Root, Federated User,
direkte IAM-Role-ARNs und andere Assumed Roles werden abgelehnt. MFA bleibt
eine ausdrückliche Attestation; das Werkzeug erkennt MFA nicht technisch. Das
Werkzeug erzeugt oder verlängert keine Session und kann deren organisatorische
Freigabe nicht ersetzen. Dry-Run bleibt vollständig lokal und benötigt keine
Bootstrap-Rolle.

## Fail-closed-Verhalten

Das Werkzeug:

- sucht oder erstellt keine Operatoridentität;
- erstellt keine Access Keys, Login-Profile oder Administrator-Credentials;
- akzeptiert vorhandene gleichnamige kundenverwaltete Policies nur mit
  exaktem Pfad, festen Tags, genau der alleinigen Default-Version `v1` und
  identischem kanonischem Dokument-Hash;
- erstellt niemals eine weitere Policy-Version und aktualisiert keine Policy;
- akzeptiert die vorhandene CloudFormation-Service-Rolle nur mit exaktem Pfad,
  Trust-Policy-Hash, Boundary, Tags und ohne unerwartete Inline-Policies,
  Anhänge oder Instance Profiles;
- setzt Operator-Policies und Operator-Boundary ausschließlich auf die
  ausdrücklich benannte vorhandene IAM-User- oder IAM-Role-Identität;
- führt vor dem Teardown eine vollständige Nur-Lese-Prüfung aller Hashes,
  Policy-Versionen, Attachments, Boundary-Nutzungen und
  Service-Rollen-Abhängigkeiten durch;
- prüft vor jedem Teardown anhand des exakten Stack-Namens, dass der
  CloudFormation-Stack nicht mehr existiert;
- beginnt keinen Teardown, solange eine Policy unerwartet verwendet wird, eine
  Runtime-Rolle noch eine Boundary nutzt oder die Service-Rolle eine
  unerwartete Abhängigkeit besitzt;
- akzeptiert beim erneuten Teardown bereits erfolgreich entfernte erwartete
  Anhänge und Artefakte, ohne unerwartete Abhängigkeiten zu tolerieren.

Der IAM-Abbau ist erst nach erfolgreichem Stack-Delete und
Post-Delete-Verifikation vorgesehen. Service-Linked Roles und die explizit
übergebene Operatoridentität werden nicht gelöscht.

## Lokale Validierung

Alle Prüfungen bleiben netzwerkfrei:

```bash
ruff check .
pytest -q
python tools/policy_claim_check.py
git diff --check
```

Die fokussierten Tests prüfen zusätzlich JSON-Syntax, Artefakttrennung,
erlaubte Aktionen, feste Ressourcen, Conditions, Change-Set-only,
`iam:PassRole`, `iam:CreateRole`, Secret-Löschung, verbotene Rechte,
Dry-Run-Verhalten sowie Bootstrap-/Teardown-Reihenfolge.

## Geprüfte AWS-Primärquellen

- [CloudFormation Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_cloudformation.html)
- [ECS Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ecs.html)
- [IAM Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_iam.html)
- [IAM- und STS-Zeichenlimits](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html)
- [Secrets Manager Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_secretsmanager.html)
- [AmazonECSInfrastructureRoleforExpressGatewayServices](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonECSInfrastructureRoleforExpressGatewayServices.html)

Die regionalen CloudFormation-Resource-Provider-Schemata, Access Analyzer,
Policy Simulator und ein AWS-Live-Test bleiben Teil des späteren ausdrücklich
freigegebenen Freeze-/Review-Prozesses.
