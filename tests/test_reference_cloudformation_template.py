"""Static, offline structure checks for the AWS reference CloudFormation template."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo.yaml"

FORBIDDEN_RESOURCE_TYPE_PREFIXES = (
    "AWS::EC2::VPC",
    "AWS::EC2::Subnet",
    "AWS::EC2::SecurityGroup",
    "AWS::ElasticLoadBalancingV2::",
    "AWS::RDS::",
    "AWS::Cognito::",
    "AWS::ApiGateway::",
    "AWS::ApiGatewayV2::",
    "AWS::EKS::",
    "AWS::Azure",
    "Google::",
    "Azure::",
)

SUSPICIOUS_CREDENTIAL_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws_secret_access_key\s*[:=]"),
    re.compile(r"(?i)secret[_-]?string\s*:"),
    re.compile(r"(?i)generatesecretstring\s*:"),
    re.compile(r"(?i)password\s*[:=]\s*\S+"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
)


def _construct_cfn_tag(loader: yaml.Loader, tag_suffix: str, node: yaml.Node) -> Any:
    key = tag_suffix
    if isinstance(node, yaml.ScalarNode):
        return {key: loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {key: loader.construct_sequence(node)}
    if isinstance(node, yaml.MappingNode):
        return {key: loader.construct_mapping(node)}
    raise TypeError(f"Unsupported CloudFormation YAML node for tag !{tag_suffix}")


class CfnLoader(yaml.SafeLoader):
    """SafeLoader that keeps CloudFormation short-form tags as dicts."""


CfnLoader.add_multi_constructor("!", _construct_cfn_tag)


def load_template() -> dict[str, Any]:
    assert TEMPLATE_PATH.is_file(), TEMPLATE_PATH
    loaded = yaml.load(TEMPLATE_PATH.read_text(encoding="utf-8"), Loader=CfnLoader)
    assert isinstance(loaded, dict)
    return loaded


def _find_keys(obj: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(obj, dict):
        if key in obj:
            found.append(obj[key])
        for value in obj.values():
            found.extend(_find_keys(value, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_keys(item, key))
    return found


def _resource_by_type(template: dict[str, Any], type_name: str) -> list[tuple[str, dict[str, Any]]]:
    resources = template.get("Resources", {})
    assert isinstance(resources, dict)
    matches: list[tuple[str, dict[str, Any]]] = []
    for logical_id, resource in resources.items():
        assert isinstance(resource, dict)
        if resource.get("Type") == type_name:
            matches.append((logical_id, resource))
    return matches


def test_template_exists_and_parses() -> None:
    template = load_template()
    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert "Parameters" in template
    assert "Conditions" in template
    assert "Rules" in template
    assert "Resources" in template
    assert "Outputs" in template


def test_parameters_defaults_and_allowed_values() -> None:
    parameters = load_template()["Parameters"]
    for name in ("DeployService", "CreateManagedSecret", "InjectManagedSecret"):
        param = parameters[name]
        assert param["Type"] == "String"
        assert param["Default"] == "false"
        assert param["AllowedValues"] == ["true", "false"]

    image = parameters["ImageUri"]
    assert image["Type"] == "String"
    assert image["Default"] == ""
    assert "@sha256:" in image["AllowedPattern"]
    assert image["AllowedPattern"].startswith("^$|")


def test_conditions_and_rules_cover_bootstrap_and_secret_guards() -> None:
    template = load_template()
    conditions = template["Conditions"]
    assert "DeployExpressService" in conditions
    assert "CreateManagedSecretEnabled" in conditions
    assert "InjectManagedSecretEnabled" in conditions

    rules = template["Rules"]
    assert "DeployServiceRequiresDigestImageUri" in rules
    assert "InjectRequiresCreateManagedSecret" in rules
    assert "InjectRequiresDeployService" in rules


def test_digest_required_for_service_deployment() -> None:
    template = load_template()
    image_pattern = template["Parameters"]["ImageUri"]["AllowedPattern"]
    assert re.fullmatch(image_pattern, "")
    assert re.fullmatch(
        image_pattern,
        "123456789012.dkr.ecr.eu-central-1.amazonaws.com/demo@sha256:"
        + ("a" * 64),
    )
    assert not re.fullmatch(
        image_pattern,
        "123456789012.dkr.ecr.eu-central-1.amazonaws.com/demo:latest",
    )
    assert not re.fullmatch(
        image_pattern,
        "123456789012.dkr.ecr.eu-central-1.amazonaws.com/demo:bootstrap",
    )

    service = _resource_by_type(template, "AWS::ECS::ExpressGatewayService")
    assert len(service) == 1
    _, resource = service[0]
    assert resource["Condition"] == "DeployExpressService"


def test_express_service_port_health_scaling_and_logs() -> None:
    template = load_template()
    _, service = _resource_by_type(template, "AWS::ECS::ExpressGatewayService")[0]
    props = service["Properties"]
    container = props["PrimaryContainer"]

    assert container["ContainerPort"] == 8000
    assert props["HealthCheckPath"] == "/health"
    assert props["ScalingTarget"] == {"MinTaskCount": 1, "MaxTaskCount": 1}

    logs = container["AwsLogsConfiguration"]
    assert logs["LogStreamPrefix"] == "ecs"
    assert "LogGroup" in logs
    assert "Image" in container
    assert "TaskRoleArn" not in props


def test_log_group_retention_and_ecr_empty_on_delete() -> None:
    template = load_template()
    _, log_group = _resource_by_type(template, "AWS::Logs::LogGroup")[0]
    assert log_group["Properties"]["RetentionInDays"] == 14

    _, repository = _resource_by_type(template, "AWS::ECR::Repository")[0]
    assert repository["Properties"]["EmptyOnDelete"] is True


def test_iam_trusts_and_managed_policies() -> None:
    template = load_template()
    roles = {
        logical_id: resource
        for logical_id, resource in _resource_by_type(template, "AWS::IAM::Role")
    }
    assert "TaskExecutionRole" in roles
    assert "ExpressInfrastructureRole" in roles
    assert "RoleName" not in roles["TaskExecutionRole"]["Properties"]
    assert "RoleName" not in roles["ExpressInfrastructureRole"]["Properties"]

    execution_trust = roles["TaskExecutionRole"]["Properties"]["AssumeRolePolicyDocument"]
    assert execution_trust["Statement"][0]["Principal"]["Service"] == "ecs-tasks.amazonaws.com"
    assert roles["TaskExecutionRole"]["Properties"]["ManagedPolicyArns"] == [
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
    ]

    infra_trust = roles["ExpressInfrastructureRole"]["Properties"]["AssumeRolePolicyDocument"]
    assert infra_trust["Statement"][0]["Principal"]["Service"] == "ecs.amazonaws.com"
    assert roles["ExpressInfrastructureRole"]["Properties"]["ManagedPolicyArns"] == [
        "arn:aws:iam::aws:policy/service-role/"
        "AmazonECSInfrastructureRoleforExpressGatewayServices"
    ]


def test_secret_permissions_are_conditional_and_arn_scoped() -> None:
    template = load_template()
    secrets = _resource_by_type(template, "AWS::SecretsManager::Secret")
    assert len(secrets) == 1
    logical_id, secret = secrets[0]
    assert secret["Condition"] == "CreateManagedSecretEnabled"
    props = secret.get("Properties", {})
    assert "SecretString" not in props
    assert "GenerateSecretString" not in props

    execution_roles = _resource_by_type(template, "AWS::IAM::Role")
    _, execution_role = next(item for item in execution_roles if item[0] == "TaskExecutionRole")
    policies_if = execution_role["Properties"]["Policies"]
    assert "If" in policies_if
    assert policies_if["If"][0] == "InjectManagedSecretEnabled"
    inline_policies = policies_if["If"][1]
    statement = inline_policies[0]["PolicyDocument"]["Statement"][0]
    assert statement["Action"] == ["secretsmanager:GetSecretValue"]
    assert statement["Resource"] == {"Ref": logical_id}
    assert statement["Resource"] != "*"

    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert 'Resource: "*"' not in raw
    assert "Resource: '*'" not in raw
    get_secret_blocks = [
        block
        for block in raw.split("secretsmanager:GetSecretValue")
        if "Resource:" in block[:200]
    ]
    assert get_secret_blocks
    for block in get_secret_blocks:
        nearby = block[:200]
        assert 'Resource: "*"' not in nearby
        assert "Resource: '*'" not in nearby


def test_no_task_role_and_no_forbidden_resources() -> None:
    template = load_template()
    raw_types = [resource["Type"] for resource in template["Resources"].values()]
    assert "AWS::ECS::ExpressGatewayService" in raw_types
    assert "AWS::ECR::Repository" in raw_types
    assert "AWS::Logs::LogGroup" in raw_types
    assert "AWS::SecretsManager::Secret" in raw_types

    for type_name in raw_types:
        assert not type_name.startswith(FORBIDDEN_RESOURCE_TYPE_PREFIXES)

    assert not _find_keys(template, "TaskRoleArn")
    network_keys = _find_keys(template, "NetworkConfiguration")
    assert network_keys == []


def test_no_secret_values_or_suspicious_credential_literals() -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    lowered = raw.lower()
    assert "secretstring:" not in lowered
    assert "generatesecretstring:" not in lowered
    for pattern in SUSPICIOUS_CREDENTIAL_PATTERNS:
        assert pattern.search(raw) is None, pattern.pattern


def test_outputs_are_minimal_and_conditional() -> None:
    outputs = load_template()["Outputs"]
    assert set(outputs) == {
        "EcrRepositoryUri",
        "LogGroupName",
        "ServiceEndpoint",
        "ManagedSecretArn",
    }
    assert outputs["ServiceEndpoint"]["Condition"] == "DeployExpressService"
    assert outputs["ManagedSecretArn"]["Condition"] == "CreateManagedSecretEnabled"
    assert "Condition" not in outputs["EcrRepositoryUri"]
    assert "Condition" not in outputs["LogGroupName"]
