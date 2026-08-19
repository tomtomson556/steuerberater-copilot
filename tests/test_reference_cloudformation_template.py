"""Static, offline structure checks for the AWS reference CloudFormation template."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo.yaml"
GUARD_PATH = ROOT / "infra" / "cloudformation" / "guards" / "reference-demo.guard"
IAM_POLICY_DIR = ROOT / "infra" / "iam" / "reference-demo" / "v2.3"

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

ALLOWED_RESOURCE_TYPES = {
    "AWS::ECR::Repository",
    "AWS::Logs::LogGroup",
    "AWS::IAM::Role",
    "AWS::SecretsManager::Secret",
    "AWS::ECS::ExpressGatewayService",
    *ALLOWED_NETWORK_RESOURCE_TYPES,
}

ALLOWED_PARAMETERS = {
    "DeployService",
    "ImageUri",
    "CreateManagedSecret",
    "InjectManagedSecret",
}

STAGE1_RESOURCE_IDS = (
    "ReferenceDemoRepository",
    "ApplicationLogGroup",
    "DemoVpc",
    "PublicSubnetA",
    "PublicSubnetB",
    "InternetGateway",
    "AttachGateway",
    "PublicRouteTable",
    "PublicRoute",
    "PublicSubnetARouteTableAssociation",
    "PublicSubnetBRouteTableAssociation",
    "TaskExecutionRole",
    "ExpressInfrastructureRole",
)

TAGGABLE_RESOURCE_IDS = (
    "ReferenceDemoRepository",
    "ApplicationLogGroup",
    "DemoVpc",
    "PublicSubnetA",
    "PublicSubnetB",
    "InternetGateway",
    "PublicRouteTable",
    "TaskExecutionRole",
    "ExpressInfrastructureRole",
    "ManagedSecret",
    "ExpressGatewayService",
)

UNTAGGABLE_RESOURCE_IDS = (
    "AttachGateway",
    "PublicRoute",
    "PublicSubnetARouteTableAssociation",
    "PublicSubnetBRouteTableAssociation",
)

FIXED_RESOURCE_TAGS = {
    "Project": "steuerberater-copilot",
    "Component": "reference-demo",
    "Environment": "portfolio-test",
    "ManagedBy": "cloudformation",
    "Lifecycle": "ephemeral",
}

SECRET_ARN_PATTERN = (
    "arn:aws:secretsmanager:eu-central-1:${AWS::AccountId}:secret:"
    "steuerberater-copilot/reference-demo/synthetic-*"
)
TASK_EXECUTION_BOUNDARY_ARN = (
    "arn:aws:iam::${AWS::AccountId}:policy/steuerberater-copilot/"
    "reference-demo/task-execution-boundary"
)
EXPRESS_INFRASTRUCTURE_BOUNDARY_ARN = (
    "arn:aws:iam::${AWS::AccountId}:policy/steuerberater-copilot/"
    "reference-demo/express-infrastructure-boundary"
)
ECS_SOURCE_ARN = "arn:aws:ecs:eu-central-1:${AWS::AccountId}:*"

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


def _tag_map(tags: Any) -> dict[str, str]:
    assert isinstance(tags, list)
    mapped: dict[str, str] = {}
    for item in tags:
        assert isinstance(item, dict)
        key = item["Key"]
        value = item["Value"]
        assert isinstance(key, str)
        assert isinstance(value, str)
        mapped[key] = value
    return mapped


def _sub_value(node: Any) -> str:
    assert isinstance(node, dict)
    if "Sub" in node:
        value = node["Sub"]
    else:
        value = node["Fn::Sub"]
    assert isinstance(value, str)
    return value


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
    assert set(parameters) == ALLOWED_PARAMETERS
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
    assert props["Cluster"] == "default"
    assert props["ServiceName"] == "steuerberater-copilot-reference-demo"
    assert props["Cpu"] == "256"
    assert props["Memory"] == "512"

    logs = container["AwsLogsConfiguration"]
    assert logs["LogStreamPrefix"] == "ecs"
    assert "LogGroup" in logs
    assert "Image" in container
    assert "TaskRoleArn" not in props
    assert "TaskDefinitionArn" not in props


def test_log_group_retention_and_ecr_empty_on_delete() -> None:
    template = load_template()
    _, log_group = _resource_by_type(template, "AWS::Logs::LogGroup")[0]
    assert log_group["Properties"]["RetentionInDays"] == 14
    assert log_group["Properties"]["LogGroupName"] == (
        "/steuerberater-copilot/reference-demo/application"
    )

    _, repository = _resource_by_type(template, "AWS::ECR::Repository")[0]
    assert repository["Properties"]["EmptyOnDelete"] is True
    assert repository["Properties"]["RepositoryName"] == "steuerberater-copilot-reference-demo"


def test_stage1_resources_are_unconditional_and_complete() -> None:
    resources = load_template()["Resources"]
    assert len(STAGE1_RESOURCE_IDS) == 13
    for logical_id in STAGE1_RESOURCE_IDS:
        assert "Condition" not in resources[logical_id]
    assert resources["ManagedSecret"]["Condition"] == "CreateManagedSecretEnabled"
    assert resources["ExpressGatewayService"]["Condition"] == "DeployExpressService"
    assert set(resources) == set(STAGE1_RESOURCE_IDS) | {
        "ManagedSecret",
        "ExpressGatewayService",
    }


def test_iam_trusts_boundaries_and_managed_policies() -> None:
    template = load_template()
    roles = {
        logical_id: resource
        for logical_id, resource in _resource_by_type(template, "AWS::IAM::Role")
    }
    assert set(roles) == {"TaskExecutionRole", "ExpressInfrastructureRole"}

    execution_props = roles["TaskExecutionRole"]["Properties"]
    assert execution_props["RoleName"] == "task-execution"
    assert execution_props["Path"] == "/steuerberater-copilot/reference-demo/"
    assert _sub_value(execution_props["PermissionsBoundary"]) == TASK_EXECUTION_BOUNDARY_ARN

    execution_trust = execution_props["AssumeRolePolicyDocument"]["Statement"][0]
    assert execution_trust["Principal"]["Service"] == "ecs-tasks.amazonaws.com"
    assert execution_trust["Action"] == "sts:AssumeRole"
    assert execution_trust["Condition"]["StringEquals"]["aws:SourceAccount"] == {
        "Ref": "AWS::AccountId"
    }
    assert _sub_value(execution_trust["Condition"]["ArnLike"]["aws:SourceArn"]) == ECS_SOURCE_ARN
    assert execution_props["ManagedPolicyArns"] == [
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
    ]

    infra_props = roles["ExpressInfrastructureRole"]["Properties"]
    assert infra_props["RoleName"] == "express-infrastructure"
    assert infra_props["Path"] == "/steuerberater-copilot/reference-demo/"
    assert _sub_value(infra_props["PermissionsBoundary"]) == EXPRESS_INFRASTRUCTURE_BOUNDARY_ARN
    assert "Policies" not in infra_props

    infra_trust = infra_props["AssumeRolePolicyDocument"]["Statement"][0]
    assert infra_trust["Principal"]["Service"] == "ecs.amazonaws.com"
    assert infra_trust["Action"] == "sts:AssumeRole"
    assert "Condition" not in infra_trust
    assert infra_props["ManagedPolicyArns"] == [
        "arn:aws:iam::aws:policy/service-role/"
        "AmazonECSInfrastructureRoleforExpressGatewayServices",
        {
            "Sub": (
                "arn:aws:iam::${AWS::AccountId}:policy/"
                "steuerberater-copilot/reference-demo/"
                "express-infrastructure-acm-request-policy"
            )
        },
    ]


def test_secret_read_policy_is_static_from_stage1_and_arn_pattern_scoped() -> None:
    template = load_template()
    secrets = _resource_by_type(template, "AWS::SecretsManager::Secret")
    assert len(secrets) == 1
    logical_id, secret = secrets[0]
    assert logical_id == "ManagedSecret"
    assert secret["Condition"] == "CreateManagedSecretEnabled"
    assert secret["DeletionPolicy"] == "Delete"
    assert secret["UpdateReplacePolicy"] == "Delete"
    props = secret.get("Properties", {})
    assert props["Name"] == "steuerberater-copilot/reference-demo/synthetic"
    assert "SecretString" not in props
    assert "GenerateSecretString" not in props

    execution_roles = _resource_by_type(template, "AWS::IAM::Role")
    _, execution_role = next(item for item in execution_roles if item[0] == "TaskExecutionRole")
    policies = execution_role["Properties"]["Policies"]
    assert isinstance(policies, list)
    assert len(policies) == 1
    assert "If" not in policies[0]
    assert policies[0]["PolicyName"] == "ManagedSecretGetSecretValue"
    statements = policies[0]["PolicyDocument"]["Statement"]
    assert len(statements) == 1
    statement = statements[0]
    assert statement["Action"] == "secretsmanager:GetSecretValue"
    assert _sub_value(statement["Resource"]) == SECRET_ARN_PATTERN
    assert statement["Resource"] != {"Ref": logical_id}
    assert "Ref" not in statement["Resource"]

    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert 'Resource: "*"' not in raw
    assert "Resource: '*'" not in raw
    role_block = raw.split("TaskExecutionRole:")[1].split("ExpressInfrastructureRole:")[0]
    assert "!Ref ManagedSecret" not in role_block
    assert "InjectManagedSecretEnabled" not in role_block


def test_no_task_role_and_no_forbidden_resources() -> None:
    template = load_template()
    raw_types = [resource["Type"] for resource in template["Resources"].values()]
    assert "AWS::ECS::ExpressGatewayService" in raw_types
    assert "AWS::ECR::Repository" in raw_types
    assert "AWS::Logs::LogGroup" in raw_types
    assert "AWS::SecretsManager::Secret" in raw_types
    for allowed in ALLOWED_NETWORK_RESOURCE_TYPES:
        assert allowed in raw_types
    assert set(raw_types) <= ALLOWED_RESOURCE_TYPES

    for type_name in raw_types:
        assert not type_name.startswith(FORBIDDEN_RESOURCE_TYPE_PREFIXES)
        assert type_name not in FORBIDDEN_EXACT_RESOURCE_TYPES

    assert not _find_keys(template, "TaskRoleArn")
    assert "AWS::ElasticLoadBalancingV2::LoadBalancer" not in raw_types
    assert "AWS::ElasticLoadBalancingV2::TargetGroup" not in raw_types


def test_taggable_resources_have_exactly_the_five_fixed_tags() -> None:
    resources = load_template()["Resources"]
    assert set(TAGGABLE_RESOURCE_IDS) | set(UNTAGGABLE_RESOURCE_IDS) == set(resources)
    for logical_id in TAGGABLE_RESOURCE_IDS:
        tags = resources[logical_id]["Properties"]["Tags"]
        assert _tag_map(tags) == FIXED_RESOURCE_TAGS
        assert [item["Key"] for item in tags] == list(FIXED_RESOURCE_TAGS)
    for logical_id in UNTAGGABLE_RESOURCE_IDS:
        properties = resources[logical_id].get("Properties", {})
        assert "Tags" not in properties


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
    assert "default vpc" not in raw.lower()
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


def test_template_names_match_iam_v23_arn_patterns() -> None:
    task_boundary = (IAM_POLICY_DIR / "task-execution-boundary.json").read_text(
        encoding="utf-8"
    )
    assert "repository/steuerberater-copilot-reference-demo" in task_boundary
    assert "/steuerberater-copilot/reference-demo/application" in task_boundary
    assert "steuerberater-copilot/reference-demo/synthetic-*" in task_boundary

    lifecycle_path = IAM_POLICY_DIR / "cloudformation-service-role-iam-lifecycle-policy.json"
    lifecycle = lifecycle_path.read_text(encoding="utf-8")
    assert "role/steuerberater-copilot/reference-demo/task-execution" in lifecycle
    assert "role/steuerberater-copilot/reference-demo/express-infrastructure" in lifecycle
    assert "policy/steuerberater-copilot/reference-demo/task-execution-boundary" in lifecycle
    assert (
        "policy/steuerberater-copilot/reference-demo/express-infrastructure-boundary"
        in lifecycle
    )


def test_guard_rules_encode_lifecycle_invariants() -> None:
    assert GUARD_PATH.is_file()
    text = GUARD_PATH.read_text(encoding="utf-8")
    required_snippets = (
        "steuerberater-copilot-reference-demo",
        "/steuerberater-copilot/reference-demo/",
        "task-execution",
        "express-infrastructure",
        "task-execution-boundary",
        "express-infrastructure-boundary",
        "ManagedSecretGetSecretValue",
        "secretsmanager:GetSecretValue",
        "steuerberater-copilot/reference-demo/synthetic-*",
        'ServiceName == "steuerberater-copilot-reference-demo"',
        'Cpu == "256"',
        'Memory == "512"',
        "TaskRoleArn not exists",
        'DeletionPolicy == "Delete"',
        'UpdateReplacePolicy == "Delete"',
        "AWS::EC2::NatGateway",
        "AWS::EC2::SecurityGroup",
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "ecs-tasks.amazonaws.com",
        "ecs.amazonaws.com",
        "aws:SourceAccount",
        "aws:SourceArn",
    )
    for snippet in required_snippets:
        assert snippet in text, snippet
    assert "TaskRoleArn exists" not in text.replace("TaskRoleArn not exists", "")
