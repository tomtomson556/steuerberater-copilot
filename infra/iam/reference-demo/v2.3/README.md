# AWS Reference Demo IAM Control Plane v2.3

Versionierte IAM-Artefakte für die synthetische AWS-Referenzdemo in
`eu-central-1`. Sie setzen die IAM-Control-Plane aus dem IAM-/Lifecycle-Konzept
Version 2.3 um. Das CloudFormation-Template wird ausschließlich dort ergänzt,
wo die Express Infrastructure Role die für `acm:RequestCertificate`
erforderliche Zusatzpolicy referenziert. Das Deployment-Runbook verweist auf
den Bootstrap-Role-Vertrag; es erzeugt die Bootstrap-Rolle nicht.

## Artefakte

| Datei | Art | IAM-Name | IAM-Pfad |
|---|---|---|---|
| `task-execution-boundary.json` | Permissions Boundary | `task-execution-boundary` | `/steuerberater-copilot/reference-demo/` |
| `express-infrastructure-boundary.json` | Permissions Boundary | `express-infrastructure-boundary` | `/steuerberater-copilot/reference-demo/` |
| `express-infrastructure-acm-request-policy.json` | Berechtigungs-Policy (`acm:RequestCertificate`) | `express-infrastructure-acm-request-policy` | `/steuerberater-copilot/reference-demo/` |
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
| `bootstrap-role-trust-policy.json` | Trust Policy | Bootstrap-Rolle `reference-demo-iam-bootstrap` | `/steuerberater-copilot/control-plane/` |
| `bootstrap-role-policy.json` | Berechtigungs-Policy | `reference-demo-iam-bootstrap-policy` | `/steuerberater-copilot/control-plane/` |
| `bootstrap-role-boundary.json` | Permissions Boundary | `reference-demo-iam-bootstrap-boundary` | `/steuerberater-copilot/control-plane/` |

`<ACCOUNT_ID>` ist der einzige Platzhalter in den Policy-JSON-Dateien. Das
Werkzeug ersetzt ihn ausschließlich durch die explizit übergebene zwölfstellige
Account-ID. Die vorhandene Operatoridentität wird nicht in den Artefakten
gespeichert und muss bei jedem Aufruf ausdrücklich als Typ und Name angegeben
werden.

## Bootstrap-Role-Vertrag

Die Bootstrap-Rolle ist strikt getrennt von Operator und
`reference-demo-cfn-service-role`. Sie existiert organisatorisch bereits, bevor
`bootstrap --apply` oder `teardown --apply` laufen darf. Das Control-Plane-Werkzeug
erzeugt, verändert oder löscht die Bootstrap-Rolle, ihre Trust-Policy, ihre
Permissions-Policy und ihre Boundary nicht. Deshalb gehören die drei
Bootstrap-Artefakte nicht zur Apply-/Teardown-Menge `POLICIES`.

`reference-demo-privileged-caller` ist ein neu definierter Vertragsname für die
später manuell bereitgestellte Bootstrap-Ausgangsidentität. Das
Control-Plane-Werkzeug erstellt, verändert oder löscht diesen IAM-User nicht.

Für diesen v2.3-Contract wird bewusst ausschließlich ein MFA-geschützter IAM-User
als Bootstrap-Ausgangsidentität unterstützt. Federated-/SSO- und
Role-Chaining-Varianten sind Nicht-Ziel. Die Trust-Policy verlangt
`sts:AssumeRole` nur für
`arn:aws:iam::<ACCOUNT_ID>:user/reference-demo-privileged-caller` und
`aws:MultiFactorAuthPresent=true` ohne `IfExists`.

Die Bootstrap-Permissions-Boundary ist die verbindliche Obergrenze der
Bootstrap-Rolle. Zusätzlich angehängte Identity-Policies können die effektiven
Rechte nicht über diese Grenze erweitern.

Cleanup ist zweistufig:

1. Control-Plane-Teardown läuft als kurzlebige Session von
   `reference-demo-iam-bootstrap`.
2. Die privilegierte Ausgangsidentität entfernt später Bootstrap-Rolle, Policy
   und Boundary. Das Werkzeug tut das nicht.

`--bootstrap-role-name` bleibt bei `--apply` Pflicht und akzeptiert nur
`reference-demo-iam-bootstrap`.

Die Express-Infrastructure-Boundary friert die für die Demo benötigte
Aktionsmenge der am 31. Juli 2026 aktuellen AWS-verwalteten Policy
`AmazonECSInfrastructureRoleforExpressGatewayServices` v6 ein und begrenzt ihre
regionalen und accountbezogenen ARNs auf den Referenzpfad. Änderungen der
AWS-verwalteten Policy erweitern die effektiven Rechte dadurch nicht
automatisch.

Die Simulatorprüfung hat für `acm:RequestCertificate` eine Abweichung in der
AWS-verwalteten Policy v6 bestätigt: Das dort verwendete Zertifikat-ARN- und
`aws:ResourceTag`-Modell autorisiert die Create-Aktion nicht. Deshalb ergänzt
`express-infrastructure-acm-request-policy.json` ausschließlich diese eine
Aktion mit `Resource="*"`, `aws:RequestTag/AmazonECSManaged=true` und der festen
Region `eu-central-1`. Die Boundary enthält dieselbe Maximalgrenze. Die
bestehenden ACM-Aktionen auf bereits vorhandenen Zertifikaten bleiben weiterhin
auf den Zertifikat-ARN und `aws:ResourceTag/AmazonECSManaged=true` begrenzt.

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
--bootstrap-role-name reference-demo-iam-bootstrap
--confirm-aws-write-account <dieselbe zwölfstellige Account-ID>
--confirm-mfa-authenticated-session
--confirm-temporary-session
```

Für `teardown --apply` ist zusätzlich erforderlich:

```text
--confirm-post-delete-verification
```

Diese Attestation bestätigt, dass Stack-Delete und die vollständige
Post-Delete-Verifikation aus dem später gehärteten Runbook erfolgreich
abgeschlossen wurden. Sie ersetzt nicht die technische
Stack-Abwesenheitsprüfung des Werkzeugs und führt keine zusätzlichen
AWS-Account- oder Ressourcenabfragen aus. Die Option ist nur für
`teardown --apply` zulässig; Bootstrap-Apply und Dry-Run lehnen sie ab.

Diese Optionen sind für einen späteren, separat freigegebenen manuellen Test
bestimmt. Sie wurden beim Erstellen dieser Artefakte nicht ausgeführt.
Ein Apply darf ausschließlich aus einer bereits vorhandenen kurzlebigen,
MFA-geschützten Session der ausdrücklich benannten Bootstrap-Rolle erfolgen.
Zulässig ist nur der Caller-ARN

```text
arn:aws:sts::<ACCOUNT_ID>:assumed-role/reference-demo-iam-bootstrap/<SESSION_NAME>
```

Account-ID und der feste Bootstrap-Rollenname müssen exakt passen. Die
Bootstrap-Rolle darf weder die ausdrücklich angegebene Operatorrolle noch
`reference-demo-cfn-service-role` sein. IAM User, Root, Federated User,
direkte IAM-Role-ARNs und andere Assumed Roles werden abgelehnt. MFA bleibt
eine ausdrückliche Attestation; das Werkzeug erkennt MFA nicht technisch. Das
Werkzeug erzeugt oder verlängert keine Session und kann deren organisatorische
Freigabe nicht ersetzen. Dry-Run bleibt vollständig lokal und benötigt keine
Bootstrap-Rolle.

## Fail-closed-Verhalten

Das Werkzeug:

- sucht oder erstellt keine Operatoridentität;
- erstellt, verändert oder löscht weder die Bootstrap-Rolle noch
  `reference-demo-privileged-caller`;
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
Post-Delete-Verifikation vorgesehen und verlangt dafür die ausdrückliche
`--confirm-post-delete-verification`. Service-Linked Roles und die explizit
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
Dry-Run-Verhalten, den festen Bootstrap-Rollennamen sowie
Bootstrap-/Teardown-Reihenfolge.

## Bootstrap-Permissions: Aktionen und Begründung

`sts:GetCallerIdentity` braucht keine Policy-Zeile. Die übrigen Rechte folgen
den tatsächlichen `bootstrap`-/`teardown`-Aufrufen. Laut IAM-SAR autorisiert
`CreatePolicy` mit Tags zusätzlich `iam:TagPolicy`; `CreateRole` mit Tags
autorisiert zusätzlich `iam:TagRole`. Der `PermissionsBoundary`-Parameter des
`CreateRole`-Aufrufs wird dagegen durch `iam:CreateRole` und dessen
`iam:PermissionsBoundary`-Condition autorisiert, nicht durch einen separaten
`iam:PutRolePermissionsBoundary`-Allow.

| Aktion | Werkzeugaufruf | Begründung |
|---|---|---|
| `iam:CreatePolicy`, `iam:TagPolicy` | `create-policy --tags` | legt die festen v2.3-Control-Plane-Policies mit den fünf Pflicht-Tags an |
| `iam:GetPolicy`, `iam:ListPolicyVersions`, `iam:GetPolicyVersion`, `iam:ListPolicyTags`, `iam:ListEntitiesForPolicy` | Preflight | prüft Hash, alleinige Version `v1`, Pfad, Tags und erwartete Anhänge |
| `iam:CreateRole`, `iam:TagRole` | `create-role --permissions-boundary --tags` | legt nur `reference-demo-cfn-service-role` mit Service-Boundary und Pflicht-Tags an; beide Aktionen stehen wegen ihrer unterschiedlichen unterstützten Condition Keys in getrennten Statements |
| `iam:GetRole`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`, `iam:ListInstanceProfilesForRole` | Preflight | prüft Trust-Hash, Boundary, Tags und fehlende Inline-/Instance-Profile |
| `iam:AttachRolePolicy`, `iam:DetachRolePolicy` | Service-Rollen-Anhang | nur die drei CFN-Service-Policies an die Service-Rolle |
| `iam:GetUser` / `iam:GetRole` | Operator-Preflight | bestätigt die explizit übergebene vorhandene Operatoridentität |
| `iam:AttachUserPolicy` / `iam:AttachRolePolicy` und Detach | Operator-Anhang | nur die vier Operator-Policies; Operatorname bleibt Laufzeitparameter |
| `iam:PutUserPermissionsBoundary` / `iam:PutRolePermissionsBoundary` und Delete | separater Operator-Boundary-Aufruf | nur `reference-demo-operator-boundary` |
| `iam:DeleteRole` | Teardown | nur die Service-Rolle, erst nach Detach |
| `iam:DeletePolicy` | Teardown | nur die v2.3-Control-Plane-Policies, nicht die Bootstrap-Artefakte |
| `cloudformation:DescribeStacks` | Teardown-Preflight | verweigert IAM-Abbau, solange der feste Demo-Stack existiert |

Operator-Attach und Operator-Boundary nutzen `user/*` und `role/*`, weil der
Operatorname nicht in den Artefakten steht. `iam:PolicyARN` und
`iam:PermissionsBoundary` begrenzen die übertragbaren Policies. Explizite
Deny-Statements schützen Bootstrap-Rolle, Runtime-Rollen, die Service-Rolle
vor Operator-Mutationen und den privilegierten Vertragsuser. Create/Delete
von Policies bleiben auf die v2.3-Präfixe
`/reference-demo/*`, `reference-demo-cfn-*` und `reference-demo-operator-*`
begrenzt; die Bootstrap-eigenen Artefakte `reference-demo-iam-bootstrap-*`
liegen außerhalb dieser Allow-Präfixe.

## Geprüfte AWS-Primärquellen

- [CloudFormation Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_cloudformation.html)
- [ECS Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ecs.html)
- [IAM Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_iam.html)
- [IAM- und STS-Zeichenlimits](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html)
- [Permissions boundaries for IAM entities](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
- [Control access to AWS resources using policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_controlling.html)
- [assume-role (AWS CLI)](https://docs.aws.amazon.com/cli/latest/reference/sts/assume-role.html)
- [Secrets Manager Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_secretsmanager.html)
- [AmazonECSInfrastructureRoleforExpressGatewayServices](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonECSInfrastructureRoleforExpressGatewayServices.html)

Die regionalen CloudFormation-Resource-Provider-Schemata, Access Analyzer,
Policy Simulator und ein AWS-Live-Test bleiben Teil des späteren ausdrücklich
freigegebenen Freeze-/Review-Prozesses.
