# AWS-Referenzdemo: IAM-Policy-Simulator-Testprotokoll - Teil 2

Stand: 19. August 2026  
Repository: `tomtomson556/steuerberater-copilot`  
Branch: `agent/add-iam-simulator-test-protocol`  
Fortsetzung von: `docs/09-operations/aws-reference-demo-iam-simulator-test-protocol.md`  
Letzter in Teil 1 bestätigter Fall: `SIM-140`  
Zuletzt für dieses Testpaar geprüfter Ausgangsstand: `aa1b052033281796a63eafaaa411f252c67c1b6c`  
Zuletzt diagnostisch geprüfter Ausgangsstand: `ca096ec74431857eea4776faf1505d40fe16a156`
Policy-Verzeichnis: `infra/iam/reference-demo/v2.3`  
Zielregion: `eu-central-1`  
Simulatorprofil: `administrator`

## Zweck und Status

Dieses Dokument setzt das bestehende IAM-Policy-Simulator-Testprotokoll ab
`SIM-141` fort. Teil 1 bleibt bis zur späteren kontrollierten Zusammenführung
unverändert die Evidenzquelle für `SIM-001` bis `SIM-140`.

Bisher wurde weiterhin ausschließlich `aws iam simulate-custom-policy`
verwendet. Die Simulationen haben keine AWS-Ressourcen erstellt, verändert,
zurückgesetzt oder gelöscht.

Der AWS-Live-Test bleibt **No-Go**, bis die vollständige Vorprüfung und die
weiteren V2.3-Gates abgeschlossen sind.

## Zählweise

- In Teil 1 bestätigte nummerierte Simulatorfälle: **140**
- In Teil 2 bestätigte nummerierte Simulatorfälle: **2**
- Gesamtstand der bestätigten nummerierten Simulatorfälle: **142**
- Teil 2 beginnt mit `SIM-141`.

Nur tatsächlich ausgeführte und vollständig bestandene Simulatorfälle werden
nummeriert. Fehlgeschlagene Harness-Versuche oder reine Diagnoseläufe erhalten
keine SIM-Nummer.

## Bestätigte Simulatorfälle - Teil 2

| ID | Identität / Bereich | Aktion und Gegenstand | Kontext / Gegenfall | Entscheidung | Status |
|---|---|---|---|---|---|
| SIM-141 | CloudFormation-Service-Rolle | sechs ECS-Service-Leseaktionen: `ecs:DescribeExpressGatewayService`, `ecs:DescribeServiceDeployments`, `ecs:DescribeServiceRevisions`, `ecs:DescribeServices`, `ecs:ListServiceDeployments`, `ecs:ListTagsForResource` | exakter Referenzservice sowie zugehörige synthetische Deployment-/Revision-ARNs; sechs atomare Evaluationen und sechs `ResourceSpecificResults`; keine fehlenden Kontextwerte; sechs passende Statements; Boundary sechsmal freigebend; keine Trunkierung | `allowed` × 6 | bestanden |
| SIM-142 | CloudFormation-Service-Rolle | dieselben sechs ECS-Service-Leseaktionen | falscher Servicename, dieselben Referenzpfade in `eu-west-1` und im fremden Konto; 18 atomare Evaluationen und 18 `ResourceSpecificResults`; ausschließlich fachlich unbeteiligte fehlende Kontextwerte; relevante Kontextwerte vollständig; keine passenden Statements; Boundary niemals freigebend; keine Trunkierung | `implicitDeny` × 18 | bestanden |

## Ausführungsnachweis SIM-141/142

Geprüfter Ausgangsstand:

```text
TESTED_HEAD=aa1b052033281796a63eafaaa411f252c67c1b6c
HEAD_CHECK=passed
POLICY_WORKTREE_CHECK=passed
ACCOUNT_ID_CHECK=passed
```

Statischer Vorcheck:

```text
CFN_SERVICE_ROLE_ECS_READS_STATIC_DOCUMENTS=4
CFN_SERVICE_ROLE_ECS_READS_STATIC_ACTIONS=6
CFN_SERVICE_ROLE_ECS_READS_STATIC_IDENTITY_ACTION_OCCURRENCES=6
CFN_SERVICE_ROLE_ECS_READS_STATIC_BOUNDARY_ACTION_OCCURRENCES=6
CFN_SERVICE_ROLE_ECS_READS_STATIC_ACTION_DOCUMENT_PAIRS=12
CFN_SERVICE_ROLE_ECS_READS_STATIC_CONDITIONED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_READS_STATIC_SERVICE_EXACT_STATEMENTS=1
CFN_SERVICE_ROLE_ECS_READS_STATIC_BOUNDARY_CONTAINER_STATEMENTS=1
CFN_SERVICE_ROLE_ECS_READS_STATIC_ACTION_WILDCARDS=0
CFN_SERVICE_ROLE_ECS_READS_STATIC_CHECK=passed
```

SIM-141:

```text
CFN_SERVICE_ROLE_ECS_READS=allowed allowed allowed allowed allowed allowed
CFN_SERVICE_ROLE_ECS_READS_TOTAL=6
CFN_SERVICE_ROLE_ECS_READS_RESOURCE_SPECIFIC_RESULTS=6
CFN_SERVICE_ROLE_ECS_READS_MISSING_CONTEXT=none|none|none|none|none|none
CFN_SERVICE_ROLE_ECS_READS_RELEVANT_MISSING_CONTEXT=none
CFN_SERVICE_ROLE_ECS_READS_MATCHED_STATEMENTS=6
CFN_SERVICE_ROLE_ECS_READS_BOUNDARY_ALLOWED=6
CFN_SERVICE_ROLE_ECS_READS_TRUNCATED=false
CFN_SERVICE_ROLE_ECS_READS_POSITIVE=passed
```

SIM-142 - falscher Service:

```text
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE=implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_TOTAL=6
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_RESOURCE_SPECIFIC_RESULTS=6
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_RELEVANT_MISSING_CONTEXT=none
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_MATCHED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_BOUNDARY_ALLOWED=0
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_TRUNCATED=false
CFN_SERVICE_ROLE_ECS_READS_WRONG_SERVICE_NEGATIVE=passed
```

SIM-142 - falsche Region:

```text
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION=implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_TOTAL=6
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_RESOURCE_SPECIFIC_RESULTS=6
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_RELEVANT_MISSING_CONTEXT=none
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_MATCHED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_BOUNDARY_ALLOWED=0
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_TRUNCATED=false
CFN_SERVICE_ROLE_ECS_READS_WRONG_REGION_NEGATIVE=passed
```

SIM-142 - fremdes Konto:

```text
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT=implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny implicitDeny
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_TOTAL=6
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_RESOURCE_SPECIFIC_RESULTS=6
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_RELEVANT_MISSING_CONTEXT=none
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_MATCHED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_BOUNDARY_ALLOWED=0
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_TRUNCATED=false
CFN_SERVICE_ROLE_ECS_READS_FOREIGN_ACCOUNT_NEGATIVE=passed
CFN_SERVICE_ROLE_ECS_READS_NEGATIVE_TOTAL=18
CFN_SERVICE_ROLE_ECS_READS_NEGATIVE_RESOURCE_SPECIFIC_RESULTS=18
CFN_SERVICE_ROLE_ECS_READS_NEGATIVE_MATCHED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_READS_NEGATIVE_BOUNDARY_ALLOWED=0
CFN_SERVICE_ROLE_ECS_READS_NEGATIVE=passed
```

Die rohen `MissingContextValues` der drei Negativgruppen enthielten mehrfach
Context Keys aus fachlich unbeteiligten Statements der vier vollständig
eingereichten Policy-Dokumente. Für den getesteten unbedingten ECS-Read-Block
war kein Context Key erforderlich; der Harness bestätigte deshalb jeweils
`RELEVANT_MISSING_CONTEXT=none`.

## Stand nach SIM-141/142

SIM-141 bestätigt die sechs unbedingten ECS-Service-Leseaktionen
`DescribeExpressGatewayService`, `DescribeServiceDeployments`,
`DescribeServiceRevisions`, `DescribeServices`, `ListServiceDeployments` und
`ListTagsForResource` auf dem exakten Referenzservice sowie den zugehörigen
synthetischen Service-Deployment- und Service-Revision-ARNs. Alle sechs
Gesamt- und Ressourcenentscheidungen sind `allowed`; es fehlte kein relevanter
Kontextwert, sechs Identity-Statements trafen zu, die Boundary gab alle sechs
Ressourcen frei und kein Ergebnis war trunkiert.

Der statische Vorcheck bestätigt je genau ein Action-Vorkommen in der
Service-Policy und der Boundary, insgesamt zwölf Action-Dokument-Paare, ein
gemeinsames unbedingtes Read-Statement pro Policy-Pfad und keine
Action-Wildcards.

SIM-142 bestätigt denselben Read-Block gegen einen falschen Servicenamen,
dieselben Referenzpfade in `eu-west-1` und im fremden Konto. Alle 18 Gesamt-
und Ressourcenentscheidungen sind `implicitDeny`; kein Identity-Statement traf
zu und die Boundary gab keine Ressource frei. Kein Ergebnis war trunkiert.

Damit ist der vollständige unbedingte ECS-Service-Read-Pfad der
CloudFormation-Service-Rolle positiv sowie gegen Servicebezug, Region und
Konto adversarial abgedeckt. Eine Policy-Änderung war für SIM-141/142 nicht
erforderlich.

## Nicht nummerierter Diagnoseblock nach SIM-141/142

Der danach untersuchte Restblock bestand aus
`ecs:UpdateExpressGatewayService` und
`ecs:DeleteExpressGatewayService` auf dem exakten Referenzservice. Die
Service-Policy bindet beide Aktionen mit
`ecs:ResourceTag/Project=steuerberater-copilot`; die Boundary erlaubt beide
Aktionen auf derselben Ressource.

Der erste positive Harness-Versuch auf dem Ausgangsstand
`ca096ec74431857eea4776faf1505d40fe16a156` ergab trotz vollständig
bereitgestelltem `ecs:ResourceTag/Project`-Kontext zweimal `implicitDeny`:

```text
TESTED_HEAD=ca096ec74431857eea4776faf1505d40fe16a156
HEAD_CHECK=passed
POLICY_WORKTREE_CHECK=passed
ACCOUNT_ID_CHECK=passed
CFN_SERVICE_ROLE_ECS_MUTATIONS_STATIC_CHECK=passed
CFN_SERVICE_ROLE_ECS_MUTATIONS=implicitDeny implicitDeny
CFN_SERVICE_ROLE_ECS_MUTATIONS_TOTAL=2
CFN_SERVICE_ROLE_ECS_MUTATIONS_RESOURCE_SPECIFIC_RESULTS=2
CFN_SERVICE_ROLE_ECS_MUTATIONS_RELEVANT_MISSING_CONTEXT=none
CFN_SERVICE_ROLE_ECS_MUTATIONS_MATCHED_STATEMENTS=0
CFN_SERVICE_ROLE_ECS_MUTATIONS_BOUNDARY_ALLOWED=2
CFN_SERVICE_ROLE_ECS_MUTATIONS_TRUNCATED=false
CFN_SERVICE_ROLE_ECS_MUTATIONS_POSITIVE=failed
```

Dieser Versuch erhielt keine SIM-Nummer. Ein anschließender unnummerierter
Diagnoselauf verglich die unveränderte Policy mit isolierten und ausschließlich
im Speicher erzeugten Kontrollvarianten. Die Context-Key-Ermittlung erkannte
den in der Repository-Policy verwendeten service-spezifischen Schlüssel:

```text
DIAG_ECS_MUTATIONS_CURRENT_TARGET_CONDITION=[{"StringEquals":{"ecs:ResourceTag/Project":"steuerberater-copilot"}}]
DIAG_ECS_MUTATIONS_GLOBAL_TARGET_CONDITION=[{"StringEquals":{"aws:ResourceTag/Project":"steuerberater-copilot"}}]
DIAG_ECS_MUTATIONS_UNCONDITIONED_TARGET_CONDITION_COUNT=0
DIAG_ECS_MUTATIONS_IN_MEMORY_VARIANTS_CHECK=passed
DIAG_ECS_MUTATIONS_CURRENT_CONTEXT_KEYS=aws:RequestTag/Component aws:RequestTag/Environment aws:RequestTag/Lifecycle aws:RequestTag/ManagedBy aws:RequestTag/Project aws:RequestedRegion aws:TagKeys ecs:ResourceTag/Project secretsmanager:ForceDeleteWithoutRecovery
```

Die unveränderte Policy blieb sowohl mit vollständigem Policy-Satz als auch
isoliert mit dem service-spezifischen Kontextwert und mit beiden Tag-Kontexten
bei `implicitDeny`. Die Boundary gab die Ressource in allen Fällen frei; das
Identity-Statement traf jedoch nicht zu:

```text
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS=implicitDeny implicitDeny
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS_RELEVANT_MISSING_CONTEXT=none
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS_MATCHED_STATEMENTS=0
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_CURRENT_FULL_ECS_TRUNCATED=false
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS=implicitDeny implicitDeny
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS_RELEVANT_MISSING_CONTEXT=none
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS_MATCHED_STATEMENTS=0
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_ECS_TRUNCATED=false
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH=implicitDeny implicitDeny
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH_RELEVANT_MISSING_CONTEXT=none
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH_MATCHED_STATEMENTS=0
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_BOTH_TRUNCATED=false
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS=implicitDeny implicitDeny
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS_RELEVANT_MISSING_CONTEXT=ecs:ResourceTag/Project
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS_MATCHED_STATEMENTS=0
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_CURRENT_ISOLATED_AWS_TRUNCATED=false
```

Eine nur im Speicher erzeugte, ansonsten identische Kontrollvariante mit dem
ebenfalls von AWS für beide Aktionen dokumentierten globalen Schlüssel
`aws:ResourceTag/Project` wurde dagegen zweimal erlaubt. Auch die
unbedingte Kontrollvariante wurde zweimal erlaubt:

```text
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS=allowed allowed
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_TOTAL=2
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_RELEVANT_MISSING_CONTEXT=none
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_MATCHED_STATEMENTS=2
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_GLOBAL_KEY_CONTROL_AWS_TRUNCATED=false
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE=allowed allowed
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_TOTAL=2
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_RESOURCE_SPECIFIC_RESULTS=2
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_RELEVANT_MISSING_CONTEXT=none
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_MATCHED_STATEMENTS=2
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_BOUNDARY_ALLOWED=2
DIAG_ECS_MUTATIONS_UNCONDITIONED_CONTROL_NONE_TRUNCATED=false
DIAG_ECS_MUTATIONS_COMPLETE=passed
```

Die AWS Service Authorization Reference führt für beide Aktionen auf dem
Ressourcentyp `service` sowohl `aws:ResourceTag/${TagKey}` als auch
`ecs:ResourceTag/${TagKey}` als unterstützte Condition Keys auf. Der
Diagnoselauf isoliert daher eine Abweichung der Simulatorauswertung für den
bereitgestellten service-spezifischen Tag-Kontext; er weist keinen Action-,
Ressourcen- oder Boundary-Fehler nach. Ohne einen vollständig erfolgreichen
Lauf der unveränderten Repository-Policy werden diese beiden Aktionen nicht
als SIM-143/144 gezählt.

Es erfolgte keine IAM-Policyänderung. Eine reale AWS-Ausführung bleibt bis zum
Abschluss der vorgesehenen Gates weiterhin **No-Go**.

## Fortsetzungsregel

Für alle weiteren Testpaare wird weiterhin dieselbe temporäre Datei
`/workspaces/exports/sim-065-066.sh` wiederverwendet. Vor jedem neuen Paar wird
ihr bisheriger Inhalt vollständig durch den neuen kontrollierten Harness ersetzt.

1. Immer genau zwei fachlich zusammengehörige Simulatorfälle in einem
   kontrollierten Block ausführen.
2. Vor jedem Paar aktuellen PR-Head, Policy-Dateien und verbleibende
   Pflichtmatrix erneut live prüfen.
3. Beide tatsächlichen Terminalergebnisse vollständig prüfen.
4. Nur bei vollständigem Erfolg beide Fälle als `bestanden` markieren.
5. Nach jedem bestandenen Paar Teil 2 unmittelbar aktualisieren.
6. Bei jeder Abweichung stoppen; keine reaktive Policy-Erweiterung während der
   Testausführung.
7. Fehlgeschlagene Harness-Versuche oder Diagnoseläufe erhalten keine
   SIM-Nummer.
8. Pull Requests werden niemals durch den Assistenten gemergt.

## Spätere Zusammenführung

Teil 1 und Teil 2 werden erst nach Abschluss dieser Testreihe kontrolliert zu
einem durchgehenden Protokoll zusammengeführt. Dabei müssen Nummerierung,
Ausführungsnachweise, Quellenangaben und getestete Ausgangsstände vollständig
erhalten bleiben. Bis dahin sind beide Dateien gemeinsam die Evidenzquelle der
Testreihe.

## Noch ausstehende Gates außerhalb dieses Simulatorprotokolls

Dieses Dokument ersetzt nicht:

- Template- und Guard-Prüfungen
- Template-Hash- und Change-Set-Prüfungen
- AWS Access Analyzer
- unabhängige Reviews
- kontrollierte Live-Lifecycle-Tests
- Post-Delete-Restressourcenprüfung

## Quelle

Quelle für SIM-141 und SIM-142: vom Nutzer am 19. August 2026 ausdrücklich
gemeldete Terminalausgaben des vollständig bestandenen Harnesses auf dem
geprüften Ausgangsstand
`aa1b052033281796a63eafaaa411f252c67c1b6c`.

Quelle für den nicht nummerierten Diagnoseblock: vom Nutzer am 19. August 2026
gemeldete Terminalausgaben auf dem geprüften Ausgangsstand
`ca096ec74431857eea4776faf1505d40fe16a156` sowie die AWS Service Authorization
Reference für Amazon ECS:
<https://docs.aws.amazon.com/service-authorization/latest/reference/list_ecs.html>.
