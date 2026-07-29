"""Static, offline structure checks for the AWS reference CloudFormation template."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo.yaml"

FORBIDDEN_RESOURCE_TYPE_PREFIXES = (
    "AWS::EC2::SecurityGroup",
    "AWS::EC2::NatGateway",
    "AWS::EC2::EIP",
    "AWS::EC2::VPCEndpoint",
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

FORBIDDEN_EXACT_RESOURCE_TYPES = (
    "AWS::EC2::NatGateway",
    "AWS::EC2::EIP",
    "AWS::EC2::VPCEndpoint",
    "AWS::EC2::SecurityGroup",
    "AWS::EC2::SecurityGroupIngress",
    "AWS::EC2::SecurityGroupEgress",
)

ALLOWED_NETWORK_RESOURCE_TYPES = (
    "AWS::EC2::VPC",
    "AWS::EC2::Subnet",
    "AWS::EC2::InternetGateway",
    "AWS::EC2::VPCGatewayAttachment",
    "AWS::EC2::RouteTable",
    "AWS::EC2::Route",
    "AWS::EC2::SubnetRouteTableAssociation",
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
    for allowed in ALLOWED_NETWORK_RESOURCE_TYPES:
        assert allowed in raw_types

    for type_name in raw_types:
        assert not type_name.startswith(FORBIDDEN_RESOURCE_TYPE_PREFIXES)
        assert type_name not in FORBIDDEN_EXACT_RESOURCE_TYPES

    assert not _find_keys(template, "TaskRoleArn")
    assert "AWS::ElasticLoadBalancingV2::LoadBalancer" not in raw_types
    assert "AWS::ElasticLoadBalancingV2::TargetGroup" not in raw_types


def test_stack_owned_public_vpc_routing_and_network_configuration() -> None:
    template = load_template()
    resources = template["Resources"]

    vpc = resources["DemoVpc"]
    assert vpc["Type"] == "AWS::EC2::VPC"
    assert "Condition" not in vpc
    vpc_props = vpc["Properties"]
    assert vpc_props["CidrBlock"] == "10.0.0.0/16"
    assert vpc_props["EnableDnsHostnames"] is True
    assert vpc_props["EnableDnsSupport"] is True

    subnet_a = resources["PublicSubnetA"]
    subnet_b = resources["PublicSubnetB"]
    assert subnet_a["Type"] == "AWS::EC2::Subnet"
    assert subnet_b["Type"] == "AWS::EC2::Subnet"
    assert "Condition" not in subnet_a
    assert "Condition" not in subnet_b
    assert subnet_a["Properties"]["VpcId"] == {"Ref": "DemoVpc"}
    assert subnet_b["Properties"]["VpcId"] == {"Ref": "DemoVpc"}
    assert subnet_a["Properties"]["CidrBlock"] == "10.0.0.0/24"
    assert subnet_b["Properties"]["CidrBlock"] == "10.0.1.0/24"
    assert subnet_a["Properties"]["CidrBlock"] != subnet_b["Properties"]["CidrBlock"]
    assert subnet_a["Properties"]["MapPublicIpOnLaunch"] is True
    assert subnet_b["Properties"]["MapPublicIpOnLaunch"] is True
    assert subnet_a["Properties"]["AvailabilityZone"] == {"Select": [0, {"GetAZs": ""}]}
    assert subnet_b["Properties"]["AvailabilityZone"] == {"Select": [1, {"GetAZs": ""}]}

    igw = resources["InternetGateway"]
    assert igw["Type"] == "AWS::EC2::InternetGateway"
    assert "Condition" not in igw

    attachment = resources["AttachGateway"]
    assert attachment["Type"] == "AWS::EC2::VPCGatewayAttachment"
    assert attachment["Properties"]["VpcId"] == {"Ref": "DemoVpc"}
    assert attachment["Properties"]["InternetGatewayId"] == {"Ref": "InternetGateway"}

    route_table = resources["PublicRouteTable"]
    assert route_table["Type"] == "AWS::EC2::RouteTable"
    assert route_table["Properties"]["VpcId"] == {"Ref": "DemoVpc"}

    route = resources["PublicRoute"]
    assert route["Type"] == "AWS::EC2::Route"
    assert route["DependsOn"] == "AttachGateway"
    assert route["Properties"]["RouteTableId"] == {"Ref": "PublicRouteTable"}
    assert route["Properties"]["DestinationCidrBlock"] == "0.0.0.0/0"
    assert route["Properties"]["GatewayId"] == {"Ref": "InternetGateway"}

    assoc_a = resources["PublicSubnetARouteTableAssociation"]
    assoc_b = resources["PublicSubnetBRouteTableAssociation"]
    assert assoc_a["Type"] == "AWS::EC2::SubnetRouteTableAssociation"
    assert assoc_b["Type"] == "AWS::EC2::SubnetRouteTableAssociation"
    assert assoc_a["Properties"]["SubnetId"] == {"Ref": "PublicSubnetA"}
    assert assoc_b["Properties"]["SubnetId"] == {"Ref": "PublicSubnetB"}
    assert assoc_a["Properties"]["RouteTableId"] == {"Ref": "PublicRouteTable"}
    assert assoc_b["Properties"]["RouteTableId"] == {"Ref": "PublicRouteTable"}

    _, service = _resource_by_type(template, "AWS::ECS::ExpressGatewayService")[0]
    assert service["DependsOn"] == [
        "PublicRoute",
        "PublicSubnetARouteTableAssociation",
        "PublicSubnetBRouteTableAssociation",
    ]
    network = service["Properties"]["NetworkConfiguration"]
    assert set(network) == {"Subnets"}
    assert "SecurityGroups" not in network
    assert network["Subnets"] == [{"Ref": "PublicSubnetA"}, {"Ref": "PublicSubnetB"}]

    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "default VPC" not in raw.lower()
    assert "DefaultVpc" not in raw
    assert "AWS::EC2::NatGateway" not in raw
    assert "AWS::EC2::EIP" not in raw
    assert "AWS::EC2::VPCEndpoint" not in raw
    assert "AWS::EC2::SecurityGroup" not in raw
    assert "PrivateSubnet" not in raw
    assert "MapPublicIpOnLaunch: false" not in raw


def test_no_nat_eip_private_subnets_or_custom_security_groups() -> None:
    template = load_template()
    resources = template["Resources"]
    types = {logical_id: resource["Type"] for logical_id, resource in resources.items()}

    assert "AWS::EC2::NatGateway" not in types.values()
    assert "AWS::EC2::EIP" not in types.values()
    assert "AWS::EC2::VPCEndpoint" not in types.values()
    assert "AWS::EC2::SecurityGroup" not in types.values()
    assert not any(name.startswith("Private") for name in types)
    assert not any(t.startswith("AWS::ElasticLoadBalancingV2::") for t in types.values())

    subnet_ids = [
        logical_id
        for logical_id, type_name in types.items()
        if type_name == "AWS::EC2::Subnet"
    ]
    assert set(subnet_ids) == {"PublicSubnetA", "PublicSubnetB"}
    for logical_id in subnet_ids:
        assert resources[logical_id]["Properties"]["MapPublicIpOnLaunch"] is True


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
