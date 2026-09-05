"""Static, offline checks for the AWS reference-demo change-set-only runbook."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = ROOT / "docs" / "09-operations" / "aws-reference-demo-runbook.md"
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo.yaml"
GUARD_PATH = ROOT / "infra" / "cloudformation" / "guards" / "reference-demo.guard"
TEMPLATE_RELATIVE_PATH = "infra/cloudformation/reference-demo.yaml"
GUARD_RELATIVE_PATH = "infra/cloudformation/guards/reference-demo.guard"
HISTORICAL_V23_COMMIT = "9a8465ec9f19ec4db8635004ec009dad14d7665d"
STATUS_HEADING = "## Status: Legacy und superseded"
VORAUSSETZUNGEN_HEADING = "## Voraussetzungen"

FIXED_STACK_TAGS = (
    "Key=Project,Value=steuerberater-copilot",
    "Key=Component,Value=reference-demo",
    "Key=Environment,Value=portfolio-test",
    "Key=ManagedBy,Value=cloudformation",
    "Key=Lifecycle,Value=ephemeral",
)

IMAGE_URI_ALLOWED_PATTERN = (
    r"^$|^[0-9]{12}\.dkr\.ecr\.eu-central-1\.amazonaws\.com/"
    r"steuerberater-copilot-reference-demo@sha256:[A-Fa-f0-9]{64}$"
)

PREFLIGHT_HEADING = "### Read-only AWS Account-Preflight"
VALIDATE_TEMPLATE_FENCE = "```bash\naws cloudformation validate-template"
CREATE_CHANGE_SET = "aws cloudformation create-change-set"
AWS_INVOCATION_RE = re.compile(r"\baws\s+([a-z0-9-]+)\s+([a-z0-9-]+)")
READ_ONLY_OPERATIONS = {
    "describe-availability-zones",
    "describe-clusters",
    "describe-express-gateway-service",
    "describe-log-groups",
    "describe-repositories",
    "describe-secret",
    "describe-stacks",
    "get-caller-identity",
    "get-policy",
    "get-policy-version",
    "get-role",
    "list-attached-role-policies",
    "list-role-policies",
    "list-role-tags",
    "list-aws-default-service-quotas",
    "list-service-quotas",
    "lookup-events",
}
FORBIDDEN_OPERATION_PREFIXES = (
    "add-",
    "attach-",
    "create-",
    "delete-",
    "detach-",
    "detect-",
    "execute-",
    "modify-",
    "pass-",
    "put-",
    "register-",
    "remove-",
    "set-",
    "start-",
    "stop-",
    "tag-",
    "untag-",
    "update-",
)


def load_runbook() -> str:
    assert RUNBOOK_PATH.is_file(), RUNBOOK_PATH
    return RUNBOOK_PATH.read_text(encoding="utf-8")


def status_section(text: str) -> str:
    start = text.index(STATUS_HEADING)
    end = text.index(VORAUSSETZUNGEN_HEADING)
    assert start < end
    return text[start:end]


def preflight_section(text: str) -> str:
    start = text.index(PREFLIGHT_HEADING)
    end = text.index(VALIDATE_TEMPLATE_FENCE)
    assert start < end
    return text[start:end]


def bash_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    parts = markdown.split("```")
    for index in range(1, len(parts), 2):
        payload = parts[index]
        newline_at = payload.find("\n")
        language = payload[:newline_at] if newline_at >= 0 else payload
        if language.strip() == "bash":
            blocks.append(payload[newline_at + 1 :] if newline_at >= 0 else "")
    return blocks


def preflight_aws_operations(text: str) -> list[tuple[str, str]]:
    operations: list[tuple[str, str]] = []
    for block in bash_blocks(preflight_section(text)):
        joined = block.replace("\\\n", " ")
        operations.extend(
            (match.group(1), match.group(2))
            for match in AWS_INVOCATION_RE.finditer(joined)
        )
    return operations


def preflight_applied_quota_service_codes(text: str) -> list[str]:
    section = preflight_section(text)
    match = re.search(
        r"for SERVICE_CODE in \\\n(.*?)\ndo\n",
        section,
        flags=re.DOTALL,
    )
    assert match, section
    return match.group(1).replace("\\", " ").split()


def cluster_inventory_python(text: str) -> str:
    section = preflight_section(text)
    anchor = section.index("aws ecs describe-clusters")
    start = section.index("import json, os, sys\n", anchor)
    end = section.index('")" || preflight_fail "ECS-Cluster default:', start)
    script = section[start:end]
    assert script.strip().startswith("import json, os, sys")
    return script


def express_service_collision_shell(text: str) -> str:
    section = preflight_section(text)
    start = section.index('if [ "$ECS_CLUSTER_DEFAULT_STATE" = "ABSENT" ]')
    end = section.index(
        'preflight_require_absent \\\n  "Task Execution Role"',
        start,
    )
    return section[start:end]


def run_cluster_inventory(payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ACCOUNT_ID"] = "123456789012"
    env["REGION"] = "eu-central-1"
    return subprocess.run(
        [sys.executable, "-c", cluster_inventory_python(load_runbook())],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_runbook_is_change_set_only_with_named_iam() -> None:
    text = load_runbook()
    assert "aws cloudformation create-stack" not in text
    assert "aws cloudformation update-stack" not in text
    assert "aws cloudformation create-change-set" in text
    assert "aws cloudformation describe-change-set" in text
    assert "aws cloudformation execute-change-set" in text
    assert "aws cloudformation delete-change-set" in text
    assert "--change-set-type CREATE" in text
    assert "--change-set-type UPDATE" in text
    assert "--capabilities CAPABILITY_NAMED_IAM" in text
    assert "--capabilities CAPABILITY_IAM\n" not in text
    assert "--capabilities CAPABILITY_IAM " not in text
    assert "--resource-types" not in text
    assert "wird nicht gesetzt" in text


def test_runbook_binds_service_role_tags_and_fixed_names() -> None:
    text = load_runbook()
    assert "steuerberater-copilot-reference-demo" in text
    assert "steuerberater-copilot-reference-demo-" in text
    assert (
        "role/steuerberater-copilot/control-plane/reference-demo-cfn-service-role"
        in text
    )
    assert "--role-arn" in text
    for tag in FIXED_STACK_TAGS:
        assert tag in text
        assert text.count(tag) >= 2
    assert "RepositoryName" in text or "steuerberater-copilot-reference-demo" in text
    assert "/steuerberater-copilot/reference-demo/application" in text
    assert "task-execution" in text
    assert "express-infrastructure" in text
    assert "steuerberater-copilot/reference-demo/synthetic" in text


def test_runbook_requires_offline_hash_guard_and_change_set_review() -> None:
    text = load_runbook()
    assert "sha256sum" in text
    assert "infra/cloudformation/reference-demo.yaml" in text
    assert "infra/cloudformation/guards/reference-demo.guard" in text
    assert GUARD_PATH.is_file()
    assert "cfn-guard validate" in text
    assert "optional für den Operator" not in text
    assert "Optionale Guard-Ausführung" not in text
    assert "aws cloudformation validate-template" in text
    assert "--template-body" in text
    assert "CAPABILITY_NAMED_IAM" in text
    assert "TaskRoleArn" in text
    assert "Modify" in text
    assert "Replace" in text
    assert "CREATE_COMPLETE" in text or "stack-create-complete" in text
    assert "13" in text
    assert "aws cloudformation create-stack" not in text
    assert "aws cloudformation update-stack" not in text


def test_runbook_status_scopes_relative_template_guard_paths_to_historical_commit() -> None:
    text = load_runbook()
    status = status_section(text)
    commands = text[text.index(VORAUSSETZUNGEN_HEADING) :]
    historical_template = f"{HISTORICAL_V23_COMMIT}:{TEMPLATE_RELATIVE_PATH}"
    historical_guard = f"{HISTORICAL_V23_COMMIT}:{GUARD_RELATIVE_PATH}"

    status_text = " ".join(status.split())
    assert HISTORICAL_V23_COMMIT in status
    assert "vor #149" in status
    assert historical_template in status
    assert historical_guard in status
    assert "vereinfachte Stack" in status
    assert "keine v2.3-Artefakte" in status
    assert "historischen Kommandoteil" in status
    assert "nur im Kontext dieses historischen Commits" in status_text
    assert "nicht auf die heutigen Dateien auf `main`" in status_text
    assert re.search(
        r"v2\.3-Referenz-Stack\s*\(\s*`infra/cloudformation/reference-demo\.yaml`\s*\)",
        status,
    ) is None
    assert "Das vorhandene Template, die Guard-Regeln" not in status

    assert f"sha256sum {TEMPLATE_RELATIVE_PATH}" in commands
    assert f"sha256sum {GUARD_RELATIVE_PATH}" in commands
    assert "cfn-guard validate" in commands
    assert f"--data {TEMPLATE_RELATIVE_PATH}" in commands
    assert f"--rules {GUARD_RELATIVE_PATH}" in commands

    current_template = TEMPLATE_PATH.read_text(encoding="utf-8")
    current_guard = GUARD_PATH.read_text(encoding="utf-8")
    allowed_types = re.search(
        r"let allowed_resource_types = \[(.*?)]",
        current_guard,
        flags=re.DOTALL,
    )
    assert allowed_types, current_guard
    allowed = allowed_types.group(1)
    assert "TaskExecutionRoleArn" in current_template
    assert "CreateManagedSecret" not in current_template
    assert "AWS::IAM::Role" not in current_template
    assert "AWS::SecretsManager::Secret" not in current_template
    assert "AWS::IAM::Role" not in allowed
    assert "AWS::SecretsManager::Secret" not in allowed
    assert "AWS::IAM::Role" in current_guard
    assert "AWS::SecretsManager::Secret" in current_guard


def test_runbook_documents_secret_force_delete_and_x86_image() -> None:
    text = load_runbook()
    assert "DeletionPolicy: Delete" in text or "DeletionPolicy" in text
    assert "ForceDeleteWithoutRecovery" in text
    assert "linux/amd64" in text
    assert "Cpu" in text and "256" in text
    assert "Memory" in text and "512" in text
    assert "CAPABILITY_NAMED_IAM" in text
    assert "No-Go" in text or "No-go" in text or "nicht ausfuehren" in text or (
        "nicht ausführen" in text
    )


def test_runbook_builds_image_uri_only_from_stack_ecr_and_digest() -> None:
    text = load_runbook()
    image_uri_assignments = [
        line.strip() for line in text.splitlines() if line.startswith("IMAGE_URI=")
    ]
    image_parameters = [
        line.strip()
        for line in text.splitlines()
        if "ParameterKey=ImageUri,ParameterValue=" in line
    ]

    assert image_uri_assignments == ['IMAGE_URI="${ECR_URI}@${IMAGE_DIGEST}"']
    assert 'ECR_URI="$(aws cloudformation describe-stacks \\' in text
    assert 'IMAGE_DIGEST="$(aws ecr describe-images \\' in text
    assert image_parameters
    assert all(
        parameter.startswith('ParameterKey=ImageUri,ParameterValue="$IMAGE_URI"')
        for parameter in image_parameters
    )
    assert IMAGE_URI_ALLOWED_PATTERN in text


def test_runbook_places_read_only_preflight_before_validate_template() -> None:
    text = load_runbook()
    preflight_at = text.index(PREFLIGHT_HEADING)
    validate_at = text.index(VALIDATE_TEMPLATE_FENCE)
    first_write_at = text.index(CREATE_CHANGE_SET)
    after_preflight_at = text.index("Erst nach bestandenem Preflight folgt die read-only")

    assert preflight_at < after_preflight_at < validate_at < first_write_at
    assert "`aws cloudformation validate-template`" in preflight_section(text)
    assert "vor jedem ersten AWS-Write" in preflight_section(text)
    assert "kein allgemeines AWS-Live-Test-Go" in preflight_section(text)


def test_runbook_preflight_commands_are_read_only() -> None:
    operations = preflight_aws_operations(load_runbook())
    assert operations
    seen = {operation for _service, operation in operations}
    assert seen <= READ_ONLY_OPERATIONS
    assert "get-caller-identity" in seen
    assert "create-change-set" not in seen
    assert "validate-template" not in seen
    for service, operation in operations:
        assert not operation.startswith(FORBIDDEN_OPERATION_PREFIXES), (
            service,
            operation,
        )
        assert "pass-role" not in operation
        assert "create" not in operation
        assert "update" not in operation
        assert "delete" not in operation
        assert "attach" not in operation.split("-")[0]
        assert not operation.startswith("put-")


def test_runbook_preflight_covers_required_account_gates() -> None:
    section = preflight_section(load_runbook())
    required = (
        "aws sts get-caller-identity",
        "eu-central-1",
        "reference-demo-cfn-service-role",
        "aws iam get-role",
        "aws iam list-attached-role-policies",
        "aws iam list-role-policies",
        "aws iam list-role-tags",
        "aws iam get-policy",
        "aws iam get-policy-version",
        "aws ecs describe-clusters",
        "--clusters default",
        "AWSServiceRoleForECS",
        "AWSServiceRoleForElasticLoadBalancing",
        "AWSServiceRoleForApplicationAutoScaling_ECSService",
        "aws ecr describe-repositories",
        "aws logs describe-log-groups",
        "aws secretsmanager describe-secret",
        "aws ecs describe-express-gateway-service",
        "aws service-quotas list-aws-default-service-quotas",
        "aws service-quotas list-service-quotas",
        "--service-code ecs",
        "aws cloudtrail lookup-events",
        "AmazonECSInfrastructureRoleforExpressGatewayServices",
        "express-infrastructure-boundary.json",
        "Billing-Budget oder Kostenalarm",
        "Organizations-SCPs",
        "Permission Sets",
        "Session Policies",
        "AccessDenied",
        "Kein Umbenennen, kein Reparieren",
        "Policies\nwerden während des Ablaufs nicht erweitert",
        "zulässiger Pre-State",
        "NoSuchEntity",
        "/aws-service-role/ecs.amazonaws.com/",
        "/aws-service-role/elasticloadbalancing.amazonaws.com/",
        "/aws-service-role/ecs.application-autoscaling.amazonaws.com/",
        "nicht automatisch nachgewiesen",
        "vpc elasticloadbalancing acm fargate",
    )
    for needle in required:
        assert needle in section, needle


def test_runbook_preflight_allows_absent_default_cluster() -> None:
    section = preflight_section(load_runbook())
    operations = preflight_aws_operations(load_runbook())
    assert ("ecs", "describe-clusters") in operations
    assert "--clusters default" in section
    assert "--include TAGS" in section
    assert "arn:aws:ecs:eu-central-1:<ACCOUNT_ID>:cluster/default" in section
    assert "ABSENT (zulässiger Pre-State, Reason MISSING)" in section
    assert "Nicht erstellen" in section
    assert "ECS-Cluster default fehlt" not in section
    assert "create-cluster" not in section
    assert ("ecs", "create-cluster") not in operations
    assert "status=%s" in section
    assert "tags=%s" in section
    assert "failure.get('reason') != 'MISSING'" in section
    assert "unerwarteter Failure-Inhalt statt Reason MISSING" in section


def test_runbook_preflight_absent_default_cluster_requires_missing_failure() -> None:
    expected_arn = "arn:aws:ecs:eu-central-1:123456789012:cluster/default"
    allowed = run_cluster_inventory(
        {
            "clusters": [],
            "failures": [{"arn": expected_arn, "reason": "MISSING"}],
        }
    )
    assert allowed.returncode == 0, allowed.stderr
    assert allowed.stdout.strip() == "ABSENT"
    assert "ABSENT" in allowed.stderr
    assert "MISSING" in allowed.stderr

    empty_failures = run_cluster_inventory({"clusters": [], "failures": []})
    assert empty_failures.returncode != 0

    wrong_reason = run_cluster_inventory(
        {
            "clusters": [],
            "failures": [{"arn": expected_arn, "reason": "UNKNOWN"}],
        }
    )
    assert wrong_reason.returncode != 0

    wrong_cluster = run_cluster_inventory(
        {
            "clusters": [],
            "failures": [
                {
                    "arn": "arn:aws:ecs:eu-central-1:123456789012:cluster/other",
                    "reason": "MISSING",
                }
            ],
        }
    )
    assert wrong_cluster.returncode != 0

    extra_failure = run_cluster_inventory(
        {
            "clusters": [],
            "failures": [
                {"arn": expected_arn, "reason": "MISSING"},
                {"arn": expected_arn, "reason": "MISSING"},
            ],
        }
    )
    assert extra_failure.returncode != 0

    present = run_cluster_inventory(
        {
            "clusters": [
                {
                    "clusterName": "default",
                    "clusterArn": expected_arn,
                    "status": "ACTIVE",
                    "tags": [],
                }
            ],
            "failures": [],
        }
    )
    assert present.returncode == 0, present.stderr
    assert present.stdout.strip() == "PRESENT"
    assert "PRESENT" in present.stderr

    inactive = run_cluster_inventory(
        {
            "clusters": [
                {
                    "clusterName": "default",
                    "clusterArn": expected_arn,
                    "status": "INACTIVE",
                    "tags": [],
                }
            ],
            "failures": [],
        }
    )
    assert inactive.returncode != 0


def test_runbook_preflight_reuses_cluster_state_for_express_collision() -> None:
    text = load_runbook()
    section = preflight_section(text)
    collision = express_service_collision_shell(text)
    absent_branch, present_branch = collision.split("else", maxsplit=1)

    assert 'ECS_CLUSTER_DEFAULT_STATE="$(' in section
    assert "print('ABSENT')" in section
    assert "print('PRESENT')" in section
    assert 'ABSENT|PRESENT)' in section
    assert "describe-express-gateway-service" not in absent_branch
    assert "Collision-Describe übersprungen" in absent_branch
    assert "describe-express-gateway-service" in present_branch
    assert "'ResourceNotFoundException'" in present_branch
    assert "ClusterNotFoundException" not in collision
    assert "bei vorhandenem Cluster default" in present_branch


def test_runbook_preflight_inventories_service_linked_roles_without_conflating_absence() -> None:
    section = preflight_section(load_runbook())
    operations = preflight_aws_operations(load_runbook())
    assert ("iam", "get-role") in operations
    assert "AWSServiceRoleForECS" in section
    assert "AWSServiceRoleForElasticLoadBalancing" in section
    assert "AWSServiceRoleForApplicationAutoScaling_ECSService" in section
    assert "/aws-service-role/ecs.amazonaws.com/" in section
    assert "/aws-service-role/elasticloadbalancing.amazonaws.com/" in section
    assert "/aws-service-role/ecs.application-autoscaling.amazonaws.com/" in section
    assert "ecs.amazonaws.com" in section
    assert "elasticloadbalancing.amazonaws.com" in section
    assert "ecs.application-autoscaling.amazonaws.com" in section
    assert "NoSuchEntity" in section
    assert "nicht NoSuchEntity" in section
    assert "create-service-linked-role" not in section
    assert ("iam", "create-service-linked-role") not in operations
    assert "AssumeRolePolicyDocument" in section or "Trust-Principal" in section


def test_runbook_preflight_service_quotas_are_manual_read_only_gate() -> None:
    text = load_runbook()
    section = preflight_section(text)
    operations = preflight_aws_operations(text)
    applied = preflight_applied_quota_service_codes(text)
    assert ("service-quotas", "list-aws-default-service-quotas") in operations
    assert ("service-quotas", "list-service-quotas") in operations
    assert "--service-code ecs" in section
    assert "keine applied quotas" in section
    assert {"vpc", "elasticloadbalancing", "acm", "fargate"} <= set(applied)
    assert "ecs" not in applied
    assert "acm" in applied
    assert "Manuell als read-only Go/No-Go bewerten" in section
    assert "nicht automatisch nachgewiesen" in section
    assert "UsageMetric" not in section
    assert "keine Restkapazität bleibt" not in section
    assert "Fargate On-Demand vCPU >= 0.25" not in section
    assert "Kein Quota-Increase" in section
    assert "list-service-quotas liefert angewendete Limits, keine Restnutzung" not in section


def test_runbook_does_not_treat_access_analyzer_as_open_branch_goal() -> None:
    section = preflight_section(load_runbook())
    assert "AWS Access Analyzer / `ValidatePolicy`" in section
    assert "zuvor 19/19" in section
    assert "erneut 2/2 mit 0 Findings" in section
    assert "SIM-001 bis SIM-146" in section
    assert "nicht als offenes Preflight-Ziel" in section
    assert "führt sie nicht\nerneut aus" in section
    assert "Access Analyzer bleibt ausstehend" not in section
    assert "ValidatePolicy noch offen" not in section
    assert "Access Analyzer erneut ausführen" not in section


def test_runbook_static_checks_stay_network_free() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported <= {
        "__future__",
        "ast",
        "json",
        "os",
        "pathlib",
        "re",
        "subprocess",
        "sys",
    }
    assert "preflight_aws_operations" in source
    assert "load_runbook" in source
    assert "status_section" in source
