"""Static, offline structure checks for the reference-demo static IAM roles."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from test_reference_cloudformation_template import (
    GUARD_PATH as EPHEMERAL_STACK_GUARD_PATH,
)
from test_reference_cloudformation_template import (
    ROLE_ARN_ALLOWED_PATTERN,
    CfnLoader,
    cloudformation_incompatible_yaml_constructs,
)
from test_reference_cloudformation_template import (
    TEMPLATE_PATH as EPHEMERAL_STACK_TEMPLATE_PATH,
)
from test_reference_cloudformation_template import (
    load_template as load_ephemeral_stack_template,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo-static-roles.yaml"
GUARD_PATH = ROOT / "infra" / "cloudformation" / "guards" / "reference-demo-static-roles.guard"

TASK_EXECUTION_ROLE_NAME = "steuerberater-copilot-reference-demo-task-execution"
EXPRESS_INFRASTRUCTURE_ROLE_NAME = (
    "steuerberater-copilot-reference-demo-express-infrastructure"
)
TASK_EXECUTION_MANAGED_POLICY_ARN = (
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)
EXPRESS_INFRASTRUCTURE_MANAGED_POLICY_ARN = (
    "arn:aws:iam::aws:policy/service-role/"
    "AmazonECSInfrastructureRoleforExpressGatewayServices"
)

ALLOWED_ROLE_PROPERTIES = {
    "RoleName",
    "Description",
    "AssumeRolePolicyDocument",
    "ManagedPolicyArns",
}

FORBIDDEN_RESOURCE_TYPES = (
    "AWS::IAM::Policy",
    "AWS::IAM::ManagedPolicy",
    "AWS::IAM::InstanceProfile",
    "AWS::IAM::User",
    "AWS::SecretsManager::Secret",
    "AWS::ECS::ExpressGatewayService",
)

SUSPICIOUS_CREDENTIAL_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws_secret_access_key\s*[:=]"),
    re.compile(r"(?i)secret[_-]?string\s*:"),
    re.compile(r"(?i)generatesecretstring\s*:"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
)


def load_template() -> dict[str, Any]:
    assert TEMPLATE_PATH.is_file(), TEMPLATE_PATH
    loaded = yaml.load(TEMPLATE_PATH.read_text(encoding="utf-8"), Loader=CfnLoader)
    assert isinstance(loaded, dict)
    return loaded


def _resource_by_type(
    template: dict[str, Any], type_name: str
) -> list[tuple[str, dict[str, Any]]]:
    resources = template.get("Resources", {})
    assert isinstance(resources, dict)
    matches: list[tuple[str, dict[str, Any]]] = []
    for logical_id, resource in resources.items():
        assert isinstance(resource, dict)
        if resource.get("Type") == type_name:
            matches.append((logical_id, resource))
    return matches


def _getatt_target(node: Any) -> tuple[str, str]:
    assert isinstance(node, dict)
    if "GetAtt" in node:
        value = node["GetAtt"]
        if isinstance(value, str):
            logical_id, attr = value.split(".", 1)
            return logical_id, attr
        assert isinstance(value, list) and len(value) == 2
        return str(value[0]), str(value[1])
    value = node["Fn::GetAtt"]
    assert isinstance(value, list) and len(value) == 2
    return str(value[0]), str(value[1])


def _trust_statement(role: dict[str, Any]) -> dict[str, Any]:
    document = role["Properties"]["AssumeRolePolicyDocument"]
    statements = document["Statement"]
    assert isinstance(statements, list)
    assert len(statements) == 1
    statement = statements[0]
    assert isinstance(statement, dict)
    return statement


def cfn_guard_executable() -> Path:
    found = shutil.which("cfn-guard")
    if found:
        return Path(found)
    fallback = Path.home() / ".local" / "bin" / "cfn-guard"
    assert fallback.is_file(), (
        "cfn-guard CLI is required for the offline freeze; "
        "install AWS CloudFormation Guard and retry"
    )
    return fallback


def run_cfn_guard(
    data_path: Path, rules_path: Path = GUARD_PATH
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(cfn_guard_executable()),
            "validate",
            "--data",
            str(data_path),
            "--rules",
            str(rules_path),
            "--show-summary",
            "fail",
            "--type",
            "CFNTemplate",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_template_exists_and_contains_exactly_two_iam_roles() -> None:
    template = load_template()
    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert "Parameters" not in template
    assert "Conditions" not in template
    assert "Rules" not in template
    assert set(template["Resources"]) == {
        "TaskExecutionRole",
        "ExpressInfrastructureRole",
    }
    roles = _resource_by_type(template, "AWS::IAM::Role")
    assert {logical_id for logical_id, _ in roles} == {
        "TaskExecutionRole",
        "ExpressInfrastructureRole",
    }
    assert len(roles) == 2
    for type_name in FORBIDDEN_RESOURCE_TYPES:
        assert not _resource_by_type(template, type_name)


def test_role_names_are_fixed_and_project_specific() -> None:
    resources = load_template()["Resources"]
    execution = resources["TaskExecutionRole"]["Properties"]
    infrastructure = resources["ExpressInfrastructureRole"]["Properties"]
    assert execution["RoleName"] == TASK_EXECUTION_ROLE_NAME
    assert infrastructure["RoleName"] == EXPRESS_INFRASTRUCTURE_ROLE_NAME
    assert TASK_EXECUTION_ROLE_NAME.startswith("steuerberater-copilot-reference-demo-")
    assert EXPRESS_INFRASTRUCTURE_ROLE_NAME.startswith(
        "steuerberater-copilot-reference-demo-"
    )
    assert len(TASK_EXECUTION_ROLE_NAME) <= 64
    assert len(EXPRESS_INFRASTRUCTURE_ROLE_NAME) <= 64
    assert execution["RoleName"] != infrastructure["RoleName"]


def test_task_execution_role_trusts_only_ecs_tasks_and_aws_managed_policy() -> None:
    role = load_template()["Resources"]["TaskExecutionRole"]
    props = role["Properties"]
    assert set(props) <= ALLOWED_ROLE_PROPERTIES
    statement = _trust_statement(role)
    assert statement["Effect"] == "Allow"
    assert statement["Principal"] == {"Service": "ecs-tasks.amazonaws.com"}
    assert statement["Action"] == "sts:AssumeRole"
    assert "Condition" not in statement
    assert props["ManagedPolicyArns"] == [TASK_EXECUTION_MANAGED_POLICY_ARN]


def test_express_infrastructure_role_trusts_only_ecs_and_aws_managed_policy() -> None:
    role = load_template()["Resources"]["ExpressInfrastructureRole"]
    props = role["Properties"]
    assert set(props) <= ALLOWED_ROLE_PROPERTIES
    statement = _trust_statement(role)
    assert statement["Effect"] == "Allow"
    assert statement["Principal"] == {"Service": "ecs.amazonaws.com"}
    assert statement["Action"] == "sts:AssumeRole"
    assert "Condition" not in statement
    assert props["ManagedPolicyArns"] == [EXPRESS_INFRASTRUCTURE_MANAGED_POLICY_ARN]


def test_roles_have_no_inline_policies_boundaries_task_role_or_secrets() -> None:
    template = load_template()
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    lowered = raw.lower()

    for _logical_id, role in _resource_by_type(template, "AWS::IAM::Role"):
        props = role["Properties"]
        assert "Policies" not in props
        assert "PermissionsBoundary" not in props
        assert "Path" not in props
        assert len(props["ManagedPolicyArns"]) == 1
        assert all(
            arn.startswith("arn:aws:iam::aws:policy/")
            for arn in props["ManagedPolicyArns"]
        )

    assert "AWS::IAM::Policy" not in raw
    assert "AWS::IAM::ManagedPolicy" not in raw
    assert "PermissionsBoundary" not in raw
    assert "TaskRole" not in raw
    assert "TaskRoleArn" not in raw
    assert "secretsmanager" not in lowered
    assert "secretstring" not in lowered
    assert "BootstrapRole" not in raw
    assert "DeployerRole" not in raw
    assert "CloudFormationServiceRole" not in raw
    assert "infra/iam/reference-demo/v2.3" not in raw
    assert "task-execution-boundary" not in raw
    assert "express-infrastructure-boundary" not in raw
    for pattern in SUSPICIOUS_CREDENTIAL_PATTERNS:
        assert pattern.search(raw) is None, pattern.pattern


def test_outputs_are_the_two_role_arns() -> None:
    outputs = load_template()["Outputs"]
    assert set(outputs) == {
        "TaskExecutionRoleArn",
        "ExpressInfrastructureRoleArn",
    }
    execution_id, execution_attr = _getatt_target(outputs["TaskExecutionRoleArn"]["Value"])
    infrastructure_id, infrastructure_attr = _getatt_target(
        outputs["ExpressInfrastructureRoleArn"]["Value"]
    )
    assert (execution_id, execution_attr) == ("TaskExecutionRole", "Arn")
    assert (infrastructure_id, infrastructure_attr) == (
        "ExpressInfrastructureRole",
        "Arn",
    )
    assert "Condition" not in outputs["TaskExecutionRoleArn"]
    assert "Condition" not in outputs["ExpressInfrastructureRoleArn"]
    assert "Export" not in outputs["TaskExecutionRoleArn"]
    assert "Export" not in outputs["ExpressInfrastructureRoleArn"]


def test_static_role_arns_match_ephemeral_stack_parameter_contract() -> None:
    ephemeral = load_ephemeral_stack_template()
    parameters = ephemeral["Parameters"]
    execution_pattern = parameters["TaskExecutionRoleArn"]["AllowedPattern"]
    infrastructure_pattern = parameters["ExpressInfrastructureRoleArn"]["AllowedPattern"]
    assert execution_pattern == ROLE_ARN_ALLOWED_PATTERN
    assert infrastructure_pattern == ROLE_ARN_ALLOWED_PATTERN

    account = "123456789012"
    execution_arn = f"arn:aws:iam::{account}:role/{TASK_EXECUTION_ROLE_NAME}"
    infrastructure_arn = (
        f"arn:aws:iam::{account}:role/{EXPRESS_INFRASTRUCTURE_ROLE_NAME}"
    )
    assert re.fullmatch(execution_pattern, execution_arn)
    assert re.fullmatch(infrastructure_pattern, infrastructure_arn)

    outputs = load_template()["Outputs"]
    assert set(outputs) == {
        "TaskExecutionRoleArn",
        "ExpressInfrastructureRoleArn",
    }
    assert "TaskExecutionRoleArn" in parameters
    assert "ExpressInfrastructureRoleArn" in parameters
    assert "AWS::IAM::Role" not in {
        resource["Type"] for resource in ephemeral["Resources"].values()
    }


def test_template_and_tests_are_decoupled_from_iam_v23_artifacts() -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    guard = GUARD_PATH.read_text(encoding="utf-8")
    for text in (raw, guard):
        assert "infra/iam/reference-demo/v2.3" not in text
        assert "task-execution-boundary" not in text
        assert "express-infrastructure-boundary" not in text
        assert "ManagedSecretGetSecretValue" not in text
        assert "CreateManagedSecret" not in text
        assert "aws_reference_demo_iam_control_plane" not in text
    iam_paths = [
        value
        for value in globals().values()
        if isinstance(value, Path) and "iam/reference-demo" in value.as_posix()
    ]
    assert iam_paths == []


def test_template_has_no_cloudformation_incompatible_yaml_aliases() -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert cloudformation_incompatible_yaml_constructs(raw) == []


def test_guard_rules_encode_static_role_invariants() -> None:
    text = GUARD_PATH.read_text(encoding="utf-8")
    required_snippets = (
        "%resource_count == 2",
        "Resources.TaskExecutionRole exists",
        "Resources.ExpressInfrastructureRole exists",
        f'RoleName == "{TASK_EXECUTION_ROLE_NAME}"',
        f'RoleName == "{EXPRESS_INFRASTRUCTURE_ROLE_NAME}"',
        f'ManagedPolicyArns == ["{TASK_EXECUTION_MANAGED_POLICY_ARN}"]',
        f'ManagedPolicyArns == ["{EXPRESS_INFRASTRUCTURE_MANAGED_POLICY_ARN}"]',
        'Principal.Service == "ecs-tasks.amazonaws.com"',
        'Principal.Service == "ecs.amazonaws.com"',
        'Action == "sts:AssumeRole"',
        "Properties.Policies not exists",
        "Properties.PermissionsBoundary not exists",
        'Value["Fn::GetAtt"] == "TaskExecutionRole.Arn"',
        'Value["Fn::GetAtt"] == "ExpressInfrastructureRole.Arn"',
        "AWS::IAM::Policy",
        "AWS::SecretsManager::Secret",
        "Parameters not exists",
        "%output_count == 2",
    )
    for snippet in required_snippets:
        assert snippet in text, snippet
    assert "AmazonECSTaskExecutionRolePolicy" in text
    assert "AmazonECSInfrastructureRoleforExpressGatewayServices" in text
    assert "secretsmanager:GetSecretValue" not in text


def test_cfn_guard_cli_parses_rules_and_accepts_template() -> None:
    parsed = subprocess.run(
        [
            str(cfn_guard_executable()),
            "parse-tree",
            "--rules",
            str(GUARD_PATH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert parsed.returncode == 0, parsed.stderr or parsed.stdout

    completed = run_cfn_guard(TEMPLATE_PATH)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" not in combined
    assert "Parser Error" not in combined


def test_ephemeral_stack_guard_rejects_static_roles_template() -> None:
    completed = run_cfn_guard(TEMPLATE_PATH, EPHEMERAL_STACK_GUARD_PATH)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert (
        "resources_are_allowlisted" in combined
        or "forbidden_resource_types_are_absent" in combined
    )
    assert "Parser Error" not in combined
    assert EPHEMERAL_STACK_TEMPLATE_PATH.is_file()


def test_cfn_guard_cli_rejects_inline_policy(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    marker = "      ManagedPolicyArns:\n"
    injected = (
        "      Policies:\n"
        "        - PolicyName: extra-inline\n"
        "          PolicyDocument:\n"
        "            Version: '2012-10-17'\n"
        "            Statement:\n"
        "              - Effect: Allow\n"
        "                Action: secretsmanager:GetSecretValue\n"
        "                Resource: '*'\n"
        "      ManagedPolicyArns:\n"
    )
    assert raw.count(marker) == 2
    mutated = tmp_path / "inline-policy.yaml"
    mutated.write_text(raw.replace(marker, injected, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "roles_have_no_inline_policies_boundaries_or_customer_managed_extras" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_permissions_boundary(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    marker = "      ManagedPolicyArns:\n"
    injected = (
        "      PermissionsBoundary: arn:aws:iam::123456789012:policy/boundary\n"
        "      ManagedPolicyArns:\n"
    )
    assert raw.count(marker) == 2
    mutated = tmp_path / "permissions-boundary.yaml"
    mutated.write_text(raw.replace(marker, injected, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "roles_have_no_inline_policies_boundaries_or_customer_managed_extras" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_extra_managed_policy(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved = f"        - {TASK_EXECUTION_MANAGED_POLICY_ARN}\n"
    extra = (
        f"        - {TASK_EXECUTION_MANAGED_POLICY_ARN}\n"
        "        - arn:aws:iam::aws:policy/SecretsManagerReadWrite\n"
    )
    assert raw.count(approved) == 1
    mutated = tmp_path / "extra-managed-policy.yaml"
    mutated.write_text(raw.replace(approved, extra, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "roles_use_fixed_names_and_aws_managed_policies_only" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_wrong_trust_principal(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved = "              Service: ecs-tasks.amazonaws.com\n"
    mutated_trust = "              Service: lambda.amazonaws.com\n"
    assert raw.count(approved) == 1
    mutated = tmp_path / "wrong-trust.yaml"
    mutated.write_text(raw.replace(approved, mutated_trust, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "task_execution_role_trusts_only_ecs_tasks" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_third_iam_role(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    marker = "  TaskExecutionRole:\n"
    extra_role = (
        "  ExtraTaskRole:\n"
        "    Type: AWS::IAM::Role\n"
        "    Properties:\n"
        "      RoleName: extra-task-role\n"
        "      AssumeRolePolicyDocument:\n"
        "        Version: '2012-10-17'\n"
        "        Statement:\n"
        "          - Effect: Allow\n"
        "            Principal:\n"
        "              Service: ecs-tasks.amazonaws.com\n"
        "            Action: sts:AssumeRole\n"
        "  TaskExecutionRole:\n"
    )
    assert raw.count(marker) == 1
    mutated = tmp_path / "third-role.yaml"
    mutated.write_text(raw.replace(marker, extra_role, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "template_contains_exactly_two_iam_roles" in combined
    assert "Parser Error" not in combined
