"""Static, offline structure checks for the AWS reference CloudFormation template."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "infra" / "cloudformation" / "reference-demo.yaml"
GUARD_PATH = ROOT / "infra" / "cloudformation" / "guards" / "reference-demo.guard"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

FORBIDDEN_RESOURCE_TYPE_PREFIXES = (
    "AWS::IAM::",
    "AWS::SecretsManager::",
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
    "AWS::IAM::Role",
    "AWS::IAM::Policy",
    "AWS::IAM::ManagedPolicy",
    "AWS::SecretsManager::Secret",
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
    "AWS::ECS::ExpressGatewayService",
    *ALLOWED_NETWORK_RESOURCE_TYPES,
}

ALLOWED_PARAMETERS = {
    "DeployService",
    "ImageUri",
    "TaskExecutionRoleArn",
    "ExpressInfrastructureRoleArn",
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
)

TAGGABLE_RESOURCE_IDS = (
    "ReferenceDemoRepository",
    "ApplicationLogGroup",
    "DemoVpc",
    "PublicSubnetA",
    "PublicSubnetB",
    "InternetGateway",
    "PublicRouteTable",
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

EXPLICIT_FIXED_RESOURCE_TAGS = """\
        - Key: Project
          Value: steuerberater-copilot
        - Key: Component
          Value: reference-demo
        - Key: Environment
          Value: portfolio-test
        - Key: ManagedBy
          Value: cloudformation
        - Key: Lifecycle
          Value: ephemeral
"""

IMAGE_URI_ALLOWED_PATTERN = (
    r"^$|^[0-9]{12}\.dkr\.ecr\.eu-central-1\.amazonaws\.com/"
    r"steuerberater-copilot-reference-demo@sha256:[A-Fa-f0-9]{64}$"
)

ROLE_ARN_ALLOWED_PATTERN = (
    r"^arn:aws:iam::[0-9]{12}:role"
    r"(/[A-Za-z0-9+=,.@_-]+)*/[A-Za-z0-9+=,.@_-]+$"
)

# CloudFormation YAML does not support anchors, aliases, or hash merges.
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-formats.html
CFN_INCOMPATIBLE_YAML_ANCHOR = re.compile(r"(?:^|[\s,{])&[A-Za-z_][\w-]*", re.MULTILINE)
CFN_INCOMPATIBLE_YAML_ALIAS = re.compile(r"(?:^|[\s,{])\*[A-Za-z_][\w-]*", re.MULTILINE)
CFN_INCOMPATIBLE_YAML_MERGE = re.compile(r"(?:^|[\s])<<\s*:", re.MULTILINE)

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


def _ref_value(node: Any) -> str:
    assert isinstance(node, dict)
    if "Ref" in node:
        value = node["Ref"]
    else:
        value = node["Fn::Ref"]
    assert isinstance(value, str)
    return value


def cloudformation_incompatible_yaml_constructs(text: str) -> list[str]:
    findings: list[str] = []
    for pattern, label in (
        (CFN_INCOMPATIBLE_YAML_ANCHOR, "anchor"),
        (CFN_INCOMPATIBLE_YAML_ALIAS, "alias"),
        (CFN_INCOMPATIBLE_YAML_MERGE, "merge"),
    ):
        for match in pattern.finditer(text):
            findings.append(f"{label}:{match.group(0)!r}")
    return findings


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

    deploy = parameters["DeployService"]
    assert deploy["Type"] == "String"
    assert deploy["Default"] == "false"
    assert deploy["AllowedValues"] == ["true", "false"]

    image = parameters["ImageUri"]
    assert image["Type"] == "String"
    assert image["Default"] == ""
    assert image["AllowedPattern"] == IMAGE_URI_ALLOWED_PATTERN

    for name in ("TaskExecutionRoleArn", "ExpressInfrastructureRoleArn"):
        param = parameters[name]
        assert param["Type"] == "String"
        assert "Default" not in param
        assert param["AllowedPattern"] == ROLE_ARN_ALLOWED_PATTERN
        assert "AllowedValues" not in param


def test_external_role_arn_parameters_accept_only_iam_role_arns() -> None:
    parameters = load_template()["Parameters"]
    pattern = parameters["TaskExecutionRoleArn"]["AllowedPattern"]
    assert pattern == parameters["ExpressInfrastructureRoleArn"]["AllowedPattern"]

    approved = (
        "arn:aws:iam::123456789012:role/task-execution",
        "arn:aws:iam::123456789012:role/steuerberater-copilot/reference-demo/task-execution",
        "arn:aws:iam::999999999999:role/service-role/AmazonECSTaskExecutionRole",
    )
    rejected = (
        "",
        "arn:aws:iam::123456789012:role/",
        "arn:aws:iam::123456789012:user/operator",
        "arn:aws:iam::123456789012:policy/task-execution",
        "arn:aws:iam::123456789012:instance-profile/task-execution",
        "arn:aws-us-gov:iam::123456789012:role/task-execution",
        "arn:aws:secretsmanager:eu-central-1:123456789012:secret:demo",
        "arn:aws:iam::12345678901:role/task-execution",
        "arn:aws:iam::ABCDEFGHIJKL:role/task-execution",
        "task-execution",
        "arn:aws:iam::123456789012:role/task execution",
        "arn:aws:iam::123456789012:role/task-execution*",
    )
    for value in approved:
        assert re.fullmatch(pattern, value), value
    for value in rejected:
        assert re.fullmatch(pattern, value) is None, value


def test_ci_installs_guard_from_locked_official_commit() -> None:
    workflow = CI_PATH.read_text(encoding="utf-8")
    install_step = workflow.split(
        "      - name: Install CloudFormation Guard from pinned source\n", maxsplit=1
    )[1].split("      - name: Run tests\n", maxsplit=1)[0]

    assert 'CFN_GUARD_VERSION: "3.1.2"' in install_step
    assert (
        'CFN_GUARD_COMMIT: "de26750fa2d97099272156238041968abeb3b95b"'
        in install_step
    )
    assert 'CFN_GUARD_RUST_TOOLCHAIN: "1.77.2"' in install_step
    assert (
        'rustup toolchain install "$CFN_GUARD_RUST_TOOLCHAIN" --profile minimal'
        in install_step
    )
    assert 'cargo +"$CFN_GUARD_RUST_TOOLCHAIN" install' in install_step
    assert "https://github.com/aws-cloudformation/cloudformation-guard.git" in install_step
    assert '--rev "$CFN_GUARD_COMMIT"' in install_step
    assert "--locked" in install_step
    assert 'test "$actual_version" = "cfn-guard ${CFN_GUARD_VERSION}"' in install_step
    assert "curl" not in install_step
    assert "tar " not in install_step
    assert "releases/download" not in install_step


def test_conditions_and_rules_cover_two_stage_digest_bootstrap() -> None:
    template = load_template()
    assert set(template["Conditions"]) == {"DeployExpressService"}
    assert set(template["Rules"]) == {"DeployServiceRequiresDigestImageUri"}


def test_digest_required_for_service_deployment() -> None:
    template = load_template()
    image_pattern = template["Parameters"]["ImageUri"]["AllowedPattern"]
    digest = "a" * 64
    approved_image_uri = (
        "123456789012.dkr.ecr.eu-central-1.amazonaws.com/"
        f"steuerberater-copilot-reference-demo@sha256:{digest}"
    )
    rejected_image_uris = (
        f"docker.io/library/demo@sha256:{digest}",
        f"ghcr.io/example/demo@sha256:{digest}",
        f"registry.example.com/demo@sha256:{digest}",
        (
            "123456789012.dkr.ecr.eu-west-1.amazonaws.com/"
            f"steuerberater-copilot-reference-demo@sha256:{digest}"
        ),
        (
            "123456789012.dkr.ecr.eu-central-1.amazonaws.com/"
            f"other-repository@sha256:{digest}"
        ),
        (
            "123456789012.dkr.ecr.eu-central-1.amazonaws.com/"
            "steuerberater-copilot-reference-demo:bootstrap"
        ),
        (
            "12345678901.dkr.ecr.eu-central-1.amazonaws.com/"
            f"steuerberater-copilot-reference-demo@sha256:{digest}"
        ),
        (
            "ABCDEFGHIJKL.dkr.ecr.eu-central-1.amazonaws.com/"
            f"steuerberater-copilot-reference-demo@sha256:{digest}"
        ),
    )

    assert re.fullmatch(image_pattern, "")
    assert re.fullmatch(image_pattern, approved_image_uri)
    for rejected in rejected_image_uris:
        assert re.fullmatch(image_pattern, rejected) is None, rejected

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
    assert "Secrets" not in container
    assert "TaskRoleArn" not in props
    assert "TaskDefinitionArn" not in props


def test_express_service_references_external_role_arn_parameters() -> None:
    template = load_template()
    _, service = _resource_by_type(template, "AWS::ECS::ExpressGatewayService")[0]
    props = service["Properties"]
    assert _ref_value(props["ExecutionRoleArn"]) == "TaskExecutionRoleArn"
    assert _ref_value(props["InfrastructureRoleArn"]) == "ExpressInfrastructureRoleArn"
    assert not _find_keys(template, "TaskRoleArn")
    assert not _find_keys(service, "GetAtt")
    assert "Fn::GetAtt" not in str(props["ExecutionRoleArn"])
    assert "Fn::GetAtt" not in str(props["InfrastructureRoleArn"])


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
    assert len(STAGE1_RESOURCE_IDS) == 11
    for logical_id in STAGE1_RESOURCE_IDS:
        assert "Condition" not in resources[logical_id]
    assert resources["ExpressGatewayService"]["Condition"] == "DeployExpressService"
    assert set(resources) == set(STAGE1_RESOURCE_IDS) | {"ExpressGatewayService"}


def test_stack_does_not_create_iam_roles_or_secrets() -> None:
    template = load_template()
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    resource_types = [resource["Type"] for resource in template["Resources"].values()]

    assert "AWS::IAM::Role" not in resource_types
    assert "AWS::SecretsManager::Secret" not in resource_types
    assert not _resource_by_type(template, "AWS::IAM::Role")
    assert not _resource_by_type(template, "AWS::SecretsManager::Secret")
    assert "CreateManagedSecret" not in template["Parameters"]
    assert "InjectManagedSecret" not in template["Parameters"]
    assert "ManagedSecret" not in template["Resources"]
    assert "TaskExecutionRole:" not in raw
    assert "ExpressInfrastructureRole:" not in raw
    assert "ManagedSecretArn" not in template.get("Outputs", {})
    assert "PrimaryContainer" in str(template["Resources"]["ExpressGatewayService"])
    _, service = _resource_by_type(template, "AWS::ECS::ExpressGatewayService")[0]
    assert "Secrets" not in service["Properties"]["PrimaryContainer"]


def test_no_task_role_and_no_forbidden_resources() -> None:
    template = load_template()
    raw_types = [resource["Type"] for resource in template["Resources"].values()]
    assert "AWS::ECS::ExpressGatewayService" in raw_types
    assert "AWS::ECR::Repository" in raw_types
    assert "AWS::Logs::LogGroup" in raw_types
    for allowed in ALLOWED_NETWORK_RESOURCE_TYPES:
        assert allowed in raw_types
    assert set(raw_types) <= ALLOWED_RESOURCE_TYPES
    assert set(raw_types) == ALLOWED_RESOURCE_TYPES

    for type_name in raw_types:
        assert not type_name.startswith(FORBIDDEN_RESOURCE_TYPE_PREFIXES)
        assert type_name not in FORBIDDEN_EXACT_RESOURCE_TYPES

    assert not _find_keys(template, "TaskRoleArn")
    assert "AWS::ElasticLoadBalancingV2::LoadBalancer" not in raw_types
    assert "AWS::ElasticLoadBalancingV2::TargetGroup" not in raw_types
    assert "AWS::IAM::Role" not in raw_types
    assert "AWS::SecretsManager::Secret" not in raw_types


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
    assert "aws::secretsmanager::secret" not in lowered
    for pattern in SUSPICIOUS_CREDENTIAL_PATTERNS:
        assert pattern.search(raw) is None, pattern.pattern


def test_outputs_are_minimal_and_conditional() -> None:
    outputs = load_template()["Outputs"]
    assert set(outputs) == {
        "EcrRepositoryUri",
        "LogGroupName",
        "ServiceEndpoint",
    }
    assert outputs["ServiceEndpoint"]["Condition"] == "DeployExpressService"
    assert "Condition" not in outputs["EcrRepositoryUri"]
    assert "Condition" not in outputs["LogGroupName"]
    assert "ManagedSecretArn" not in outputs


def test_template_and_tests_are_decoupled_from_iam_v23_artifacts() -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    guard = GUARD_PATH.read_text(encoding="utf-8")
    for text in (raw, guard):
        assert "infra/iam/reference-demo/v2.3" not in text
        assert "task-execution-boundary" not in text
        assert "express-infrastructure-boundary" not in text
        assert "ManagedSecretGetSecretValue" not in text
        assert "CreateManagedSecret" not in text
        assert "InjectManagedSecret" not in text
    iam_paths = [
        value
        for value in globals().values()
        if isinstance(value, Path) and "iam/reference-demo" in value.as_posix()
    ]
    assert iam_paths == []


def test_guard_rules_encode_simplified_stack_invariants() -> None:
    assert GUARD_PATH.is_file()
    text = GUARD_PATH.read_text(encoding="utf-8")
    required_snippets = (
        "steuerberater-copilot-reference-demo",
        'ServiceName == "steuerberater-copilot-reference-demo"',
        'Cpu == "256"',
        'Memory == "512"',
        "TaskRoleArn not exists",
        "Parameters.TaskExecutionRoleArn exists",
        "Parameters.ExpressInfrastructureRoleArn exists",
        "Parameters.TaskExecutionRoleArn.Default not exists",
        "Parameters.ExpressInfrastructureRoleArn.Default not exists",
        f'Parameters.TaskExecutionRoleArn.AllowedPattern == "{ROLE_ARN_ALLOWED_PATTERN}"',
        f'Parameters.ExpressInfrastructureRoleArn.AllowedPattern == "{ROLE_ARN_ALLOWED_PATTERN}"',
        'Parameters.ImageUri.Default == ""',
        f'Parameters.ImageUri.AllowedPattern == "{IMAGE_URI_ALLOWED_PATTERN}"',
        "count(Parameters.*)",
        "%parameter_count == 4",
        "AWS::IAM::Role",
        "AWS::SecretsManager::Secret",
        "ExecutionRoleArn.Ref == \"TaskExecutionRoleArn\"",
        "InfrastructureRoleArn.Ref == \"ExpressInfrastructureRoleArn\"",
        "PrimaryContainer.Secrets not exists",
        "AWS::EC2::NatGateway",
        "AWS::EC2::SecurityGroup",
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        'AllowedValues == ["true", "false"]',
        "count(Tags[*])",
        'Tags[0].Key == "Project"',
        'Tags[0].Value == "steuerberater-copilot"',
        'Tags[1].Key == "Component"',
        'Tags[1].Value == "reference-demo"',
        'Tags[2].Key == "Environment"',
        'Tags[2].Value == "portfolio-test"',
        'Tags[3].Key == "ManagedBy"',
        'Tags[3].Value == "cloudformation"',
        'Tags[4].Key == "Lifecycle"',
        'Tags[4].Value == "ephemeral"',
        "%taggable_count == 8",
        "EmptyOnDelete == true",
        "RetentionInDays == 14",
    )
    for snippet in required_snippets:
        assert snippet in text, snippet
    assert "TaskRoleArn exists" not in text.replace("TaskRoleArn not exists", "")
    assert "Properties.Tags !empty" not in text
    assert "CreateManagedSecret" not in text
    assert "InjectManagedSecret" not in text
    assert "ManagedSecret" not in text
    assert "ecs-tasks.amazonaws.com" not in text
    assert "secretsmanager:GetSecretValue" not in text


def test_template_has_no_cloudformation_incompatible_yaml_aliases() -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert cloudformation_incompatible_yaml_constructs(raw) == []
    assert "&ReferenceDemoTags" not in raw
    assert "*ReferenceDemoTags" not in raw
    assert raw.count(EXPLICIT_FIXED_RESOURCE_TAGS) == len(TAGGABLE_RESOURCE_IDS)


def test_yaml_alias_detector_flags_anchors_aliases_and_merges() -> None:
    sample = (
        "Tags: &ReferenceDemoTags\n"
        "  - Key: Project\n"
        "Other: *ReferenceDemoTags\n"
        "Merged:\n"
        "  <<: *ReferenceDemoTags\n"
    )
    findings = cloudformation_incompatible_yaml_constructs(sample)
    assert any(item.startswith("anchor:") for item in findings)
    assert any(item.startswith("alias:") for item in findings)
    assert any(item.startswith("merge:") for item in findings)


def test_yaml_alias_detector_ignores_arn_glob_suffixes() -> None:
    sample = (
        f"AllowedPattern: '{IMAGE_URI_ALLOWED_PATTERN}'\n"
        f"RolePattern: '{ROLE_ARN_ALLOWED_PATTERN}'\n"
        "Resource: arn:aws:iam::123456789012:role/demo-*\n"
    )
    assert cloudformation_incompatible_yaml_constructs(sample) == []


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


def test_cfn_guard_cli_rejects_yaml_aliases(tmp_path: Path) -> None:
    aliased = tmp_path / "aliased-reference-demo.yaml"
    aliased.write_text(
        'AWSTemplateFormatVersion: "2010-09-09"\n'
        "Resources:\n"
        "  DemoVpc:\n"
        "    Type: AWS::EC2::VPC\n"
        "    Properties:\n"
        "      CidrBlock: 10.0.0.0/16\n"
        "      Tags: &ReferenceDemoTags\n"
        "        - Key: Project\n"
        "          Value: steuerberater-copilot\n"
        "  InternetGateway:\n"
        "    Type: AWS::EC2::InternetGateway\n"
        "    Properties:\n"
        "      Tags: *ReferenceDemoTags\n",
        encoding="utf-8",
    )
    completed = run_cfn_guard(aliased)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Parser Error" in combined or "Error occurred" in combined


def test_cfn_guard_cli_rejects_broadened_image_uri_pattern(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved_pattern = f"    AllowedPattern: '{IMAGE_URI_ALLOWED_PATTERN}'\n"
    broadened_pattern = "    AllowedPattern: '^$|^.+@sha256:[A-Fa-f0-9]{64}$'\n"
    assert raw.count(approved_pattern) == 1
    mutated = tmp_path / "broadened-image-uri-pattern.yaml"
    mutated.write_text(
        raw.replace(approved_pattern, broadened_pattern, 1),
        encoding="utf-8",
    )

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "parameters_remain_the_approved_set" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_broadened_role_arn_pattern(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved_pattern = f"    AllowedPattern: '{ROLE_ARN_ALLOWED_PATTERN}'\n"
    broadened_pattern = "    AllowedPattern: '^arn:aws:.+$'\n"
    assert raw.count(approved_pattern) == 2
    mutated = tmp_path / "broadened-role-arn-pattern.yaml"
    mutated.write_text(
        raw.replace(approved_pattern, broadened_pattern, 1),
        encoding="utf-8",
    )

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "parameters_remain_the_approved_set" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_hardcoded_execution_role_arn(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved = "      ExecutionRoleArn: !Ref TaskExecutionRoleArn\n"
    hardcoded = (
        "      ExecutionRoleArn: arn:aws:iam::123456789012:role/task-execution\n"
    )
    assert raw.count(approved) == 1
    mutated = tmp_path / "hardcoded-execution-role.yaml"
    mutated.write_text(raw.replace(approved, hardcoded, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "express_service_uses_external_role_arn_parameters" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_task_role_arn(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved = "      ExecutionRoleArn: !Ref TaskExecutionRoleArn\n"
    with_task_role = (
        "      ExecutionRoleArn: !Ref TaskExecutionRoleArn\n"
        "      TaskRoleArn: !Ref TaskExecutionRoleArn\n"
    )
    assert raw.count(approved) == 1
    mutated = tmp_path / "added-task-role.yaml"
    mutated.write_text(raw.replace(approved, with_task_role, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "express_service_fixed_identity_cpu_memory_and_no_task_role" in combined
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_stack_owned_iam_role(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    marker = "  ReferenceDemoRepository:\n"
    extra_role = (
        "  ExtraTaskRole:\n"
        "    Type: AWS::IAM::Role\n"
        "    Properties:\n"
        "      RoleName: extra-task-role\n"
        "  ReferenceDemoRepository:\n"
    )
    assert raw.count(marker) == 1
    mutated = tmp_path / "stack-owned-iam-role.yaml"
    mutated.write_text(raw.replace(marker, extra_role, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert (
        "resources_are_allowlisted" in combined
        or "forbidden_resource_types_are_absent" in combined
    )
    assert "Parser Error" not in combined


def test_cfn_guard_cli_rejects_container_secret_injection(tmp_path: Path) -> None:
    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    approved = "        ContainerPort: 8000\n"
    injected = (
        "        ContainerPort: 8000\n"
        "        Secrets:\n"
        "          - Name: REFERENCE_DEMO_SECRET\n"
        "            ValueFrom: arn:aws:secretsmanager:eu-central-1:123456789012:secret:demo\n"
    )
    assert raw.count(approved) == 1
    mutated = tmp_path / "container-secret-injection.yaml"
    mutated.write_text(raw.replace(approved, injected, 1), encoding="utf-8")

    completed = run_cfn_guard(mutated)
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Status = FAIL" in combined
    assert "express_service_uses_external_role_arn_parameters" in combined
    assert "Parser Error" not in combined
