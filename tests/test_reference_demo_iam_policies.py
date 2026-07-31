"""Static, offline checks for the versioned AWS reference-demo IAM artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "infra" / "iam" / "reference-demo" / "v2.3"
ACCOUNT = "<ACCOUNT_ID>"
REGION = "eu-central-1"
FIXED_TAGS = {
    "Project": "steuerberater-copilot",
    "Component": "reference-demo",
    "Environment": "portfolio-test",
    "ManagedBy": "cloudformation",
    "Lifecycle": "ephemeral",
}
EXPECTED_FILES = {
    "cloudformation-service-role-boundary.json",
    "cloudformation-service-role-foundation-policy.json",
    "cloudformation-service-role-policy.json",
    "cloudformation-service-role-trust-policy.json",
    "express-infrastructure-boundary.json",
    "operator-boundary.json",
    "operator-cloudformation-policy.json",
    "operator-ecr-publisher-policy.json",
    "operator-secret-initializer-policy.json",
    "operator-verifier-policy.json",
    "task-execution-boundary.json",
}
FORBIDDEN_ACTIONS = {
    "iam:CreatePolicyVersion",
    "iam:DeleteRolePermissionsBoundary",
    "iam:PutRolePermissionsBoundary",
    "iam:UpdateAssumeRolePolicy",
    "iam:UpdateRole",
    "iam:UpdateRoleDescription",
}
FORBIDDEN_POLICY_NAMES = {
    "AdministratorAccess",
    "AmazonECS_FullAccess",
    "IAMFullAccess",
    "PowerUserAccess",
}
IAM_MANAGED_POLICY_CHARACTER_LIMIT = 6_144


def load_document(filename: str) -> dict[str, Any]:
    loaded = json.loads((POLICY_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def statements(filename: str) -> list[dict[str, Any]]:
    loaded = load_document(filename)
    result = loaded["Statement"]
    assert isinstance(result, list)
    assert all(isinstance(statement, dict) for statement in result)
    return result


def actions(statement: dict[str, Any]) -> set[str]:
    value = statement.get("Action", [])
    if isinstance(value, str):
        return {value}
    assert isinstance(value, list)
    assert all(isinstance(action, str) for action in value)
    return set(value)


def all_actions(filename: str) -> set[str]:
    return {
        action
        for statement in statements(filename)
        for action in actions(statement)
    }


def statement_for_action(filename: str, action: str) -> dict[str, Any]:
    matches = [
        statement
        for statement in statements(filename)
        if action in actions(statement)
    ]
    assert len(matches) == 1, (filename, action, len(matches))
    return matches[0]


def test_exact_versioned_artifact_set_parses_as_json() -> None:
    actual = {path.name for path in POLICY_DIR.glob("*.json")}
    assert actual == EXPECTED_FILES
    for filename in EXPECTED_FILES:
        document = load_document(filename)
        assert document["Version"] == "2012-10-17"
        assert document["Statement"]


@pytest.mark.parametrize(
    "filename",
    sorted(
        EXPECTED_FILES - {"cloudformation-service-role-trust-policy.json"}
    ),
)
def test_customer_managed_policy_documents_fit_the_iam_quota(
    filename: str,
) -> None:
    document = load_document(filename)
    character_count = len(
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    assert character_count <= IAM_MANAGED_POLICY_CHARACTER_LIMIT, (
        filename,
        character_count,
    )


def test_only_account_id_placeholder_is_present() -> None:
    for filename in EXPECTED_FILES:
        raw = (POLICY_DIR / filename).read_text(encoding="utf-8")
        placeholders = set(re.findall(r"<[^<>]+>", raw))
        assert placeholders <= {ACCOUNT}, filename


def test_policies_and_boundaries_are_distinct_artifacts() -> None:
    documents = {
        filename: json.dumps(load_document(filename), sort_keys=True)
        for filename in EXPECTED_FILES
    }
    assert len(set(documents.values())) == len(documents)
    assert documents["cloudformation-service-role-policy.json"] != documents[
        "cloudformation-service-role-boundary.json"
    ]
    assert documents["operator-boundary.json"] not in {
        documents["operator-cloudformation-policy.json"],
        documents["operator-ecr-publisher-policy.json"],
        documents["operator-secret-initializer-policy.json"],
        documents["operator-verifier-policy.json"],
    }


def test_no_wildcard_action_forbidden_managed_policy_or_deny_bypass() -> None:
    for filename in EXPECTED_FILES:
        raw = (POLICY_DIR / filename).read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_POLICY_NAMES:
            assert forbidden_name not in raw
        assert not (all_actions(filename) & FORBIDDEN_ACTIONS)
        for statement in statements(filename):
            assert statement["Effect"] == "Allow"
            assert "NotAction" not in statement
            assert "NotResource" not in statement
            assert "*" not in actions(statement)


def test_task_execution_boundary_is_the_fixed_runtime_ceiling() -> None:
    filename = "task-execution-boundary.json"
    assert all_actions(filename) == {
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken",
        "ecr:GetDownloadUrlForLayer",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "secretsmanager:GetSecretValue",
    }
    assert statement_for_action(filename, "ecr:BatchGetImage")["Resource"] == (
        f"arn:aws:ecr:{REGION}:{ACCOUNT}:"
        "repository/steuerberater-copilot-reference-demo"
    )
    assert statement_for_action(filename, "logs:PutLogEvents")["Resource"] == (
        f"arn:aws:logs:{REGION}:{ACCOUNT}:log-group:"
        "/steuerberater-copilot/reference-demo/application:log-stream:*"
    )
    assert statement_for_action(filename, "secretsmanager:GetSecretValue")[
        "Resource"
    ] == (
        f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:"
        "steuerberater-copilot/reference-demo/synthetic-*"
    )


def test_express_boundary_freezes_v6_service_names_and_reference_region() -> None:
    filename = "express-infrastructure-boundary.json"
    assert all_actions(filename) == {
        "acm:AddTagsToCertificate",
        "acm:DeleteCertificate",
        "acm:DescribeCertificate",
        "acm:RequestCertificate",
        "application-autoscaling:DeleteScalingPolicy",
        "application-autoscaling:DeregisterScalableTarget",
        "application-autoscaling:DescribeScalableTargets",
        "application-autoscaling:DescribeScalingActivities",
        "application-autoscaling:DescribeScalingPolicies",
        "application-autoscaling:PutScalingPolicy",
        "application-autoscaling:RegisterScalableTarget",
        "application-autoscaling:TagResource",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:TagResource",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:CreateSecurityGroup",
        "ec2:CreateTags",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "elasticloadbalancing:AddListenerCertificates",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateRule",
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:DeleteRule",
        "elasticloadbalancing:DeleteTargetGroup",
        "elasticloadbalancing:DeregisterTargets",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:ModifyListener",
        "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:RemoveListenerCertificates",
        "iam:CreateServiceLinkedRole",
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:TagResource",
    }
    create_slr = statement_for_action(filename, "iam:CreateServiceLinkedRole")
    assert create_slr["Condition"]["StringEquals"]["iam:AWSServiceName"] == [
        "ecs.application-autoscaling.amazonaws.com",
        "elasticloadbalancing.amazonaws.com",
    ]
    assert all(
        f":{REGION}:" in resource
        for statement in statements(filename)
        for resource in (
            [statement["Resource"]]
            if isinstance(statement["Resource"], str)
            else statement["Resource"]
        )
        if resource.startswith("arn:aws:") and ":iam::" not in resource
    )
    assert "iam:CreateServiceLinkedRole" in all_actions(filename)
    assert "elasticloadbalancing:CreateLoadBalancer" in all_actions(filename)
    assert "ec2:CreateSecurityGroup" in all_actions(filename)
    assert "acm:RequestCertificate" in all_actions(filename)
    assert "application-autoscaling:RegisterScalableTarget" in all_actions(filename)
    assert "cloudwatch:PutMetricAlarm" in all_actions(filename)
    for action in (
        "acm:RequestCertificate",
        "application-autoscaling:RegisterScalableTarget",
        "elasticloadbalancing:CreateLoadBalancer",
    ):
        assert statement_for_action(filename, action)["Condition"]["StringEquals"][
            "aws:ResourceTag/AmazonECSManaged"
        ] == "true"


def test_service_role_create_role_is_split_by_exact_role_and_boundary() -> None:
    filename = "cloudformation-service-role-policy.json"
    create_statements = [
        statement
        for statement in statements(filename)
        if actions(statement) == {"iam:CreateRole"}
    ]
    assert len(create_statements) == 2
    expected = {
        (
            f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
            "reference-demo/task-execution",
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/"
            "reference-demo/task-execution-boundary",
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
            "reference-demo/express-infrastructure",
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/"
            "reference-demo/express-infrastructure-boundary",
        ),
    }
    actual = {
        (
            statement["Resource"],
            statement["Condition"]["ArnEquals"]["iam:PermissionsBoundary"],
        )
        for statement in create_statements
    }
    assert actual == expected


def test_service_role_permission_modules_match_the_single_boundary_action_ceiling() -> None:
    permission_actions = all_actions(
        "cloudformation-service-role-foundation-policy.json"
    ) | all_actions("cloudformation-service-role-policy.json")
    assert permission_actions == all_actions(
        "cloudformation-service-role-boundary.json"
    )


def test_service_role_has_exact_pass_role_statements_and_no_role_updates() -> None:
    filename = "cloudformation-service-role-policy.json"
    pass_statements = [
        statement
        for statement in statements(filename)
        if actions(statement) == {"iam:PassRole"}
    ]
    assert len(pass_statements) == 2
    assert {
        (
            statement["Resource"],
            statement["Condition"]["StringEquals"]["iam:PassedToService"],
        )
        for statement in pass_statements
    } == {
        (
            f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
            "reference-demo/task-execution",
            "ecs-tasks.amazonaws.com",
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
            "reference-demo/express-infrastructure",
            "ecs.amazonaws.com",
        ),
    }
    assert not (all_actions(filename) & FORBIDDEN_ACTIONS)
    assert "iam:CreatePolicy" not in all_actions(filename)


def test_service_role_keeps_cluster_create_separate_and_non_speculative() -> None:
    filename = "cloudformation-service-role-policy.json"
    create_cluster = statement_for_action(filename, "ecs:CreateCluster")
    assert actions(create_cluster) == {"ecs:CreateCluster"}
    assert create_cluster["Resource"] == (
        f"arn:aws:ecs:{REGION}:{ACCOUNT}:cluster/default"
    )
    condition_text = json.dumps(create_cluster["Condition"])
    assert "aws:RequestTag/" not in condition_text
    assert "aws:TagKeys" not in condition_text
    assert not {
        "ecs:DeleteTaskDefinitions",
        "ecs:DeregisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
    } & all_actions(filename)


def test_service_role_force_deletes_only_the_reference_secret() -> None:
    statement = statement_for_action(
        "cloudformation-service-role-policy.json",
        "secretsmanager:DeleteSecret",
    )
    assert statement["Resource"] == (
        f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:"
        "steuerberater-copilot/reference-demo/synthetic-*"
    )
    assert statement["Condition"]["Bool"] == {
        "secretsmanager:ForceDeleteWithoutRecovery": "true"
    }
    assert "BoolIfExists" not in statement["Condition"]


def test_operator_cloudformation_is_change_set_only_with_action_specific_keys() -> None:
    filename = "operator-cloudformation-policy.json"
    operator_actions = all_actions(filename)
    assert "cloudformation:CreateStack" not in operator_actions
    assert "cloudformation:UpdateStack" not in operator_actions

    create = statement_for_action(filename, "cloudformation:CreateChangeSet")
    create_condition = create["Condition"]
    assert set(create_condition["StringEquals"]) == {
        "aws:RequestTag/Component",
        "aws:RequestTag/Environment",
        "aws:RequestTag/Lifecycle",
        "aws:RequestTag/ManagedBy",
        "aws:RequestTag/Project",
        "aws:RequestedRegion",
    }
    assert {
        key.removeprefix("aws:RequestTag/"): value
        for key, value in create_condition["StringEquals"].items()
        if key.startswith("aws:RequestTag/")
    } == FIXED_TAGS
    assert create_condition["ForAllValues:StringEquals"]["aws:TagKeys"] == list(
        FIXED_TAGS
    )
    assert "cloudformation:RoleArn" in create_condition["ArnEquals"]
    assert "cloudformation:ChangeSetName" in create_condition["StringLike"]

    execute = statement_for_action(filename, "cloudformation:ExecuteChangeSet")
    assert "cloudformation:RoleArn" not in json.dumps(execute["Condition"])
    tag = statement_for_action(filename, "cloudformation:TagResource")
    tag_condition = tag["Condition"]
    assert tag_condition["StringEquals"]["cloudformation:CreateAction"] == (
        "CreateChangeSet"
    )
    assert "cloudformation:RoleArn" not in json.dumps(tag_condition)
    assert "cloudformation:ChangeSetName" not in json.dumps(tag_condition)
    cancel = statement_for_action(filename, "cloudformation:CancelUpdateStack")
    assert "cloudformation:RoleArn" not in json.dumps(cancel["Condition"])
    delete = statement_for_action(filename, "cloudformation:DeleteStack")
    assert "cloudformation:RoleArn" in delete["Condition"]["ArnEquals"]


def test_operator_never_receives_secret_read_or_direct_infrastructure_writes() -> None:
    operator_policy_files = {
        "operator-cloudformation-policy.json",
        "operator-ecr-publisher-policy.json",
        "operator-secret-initializer-policy.json",
        "operator-verifier-policy.json",
    }
    operator_files = {"operator-boundary.json", *operator_policy_files}
    operator_actions = {
        action
        for filename in operator_files
        for action in all_actions(filename)
    }
    permission_actions = {
        action
        for filename in operator_policy_files
        for action in all_actions(filename)
    }
    assert permission_actions <= all_actions("operator-boundary.json")
    assert "secretsmanager:GetSecretValue" not in operator_actions
    assert not {
        "ec2:CreateVpc",
        "ecs:CreateExpressGatewayService",
        "elasticloadbalancing:CreateLoadBalancer",
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
    } & operator_actions


def test_verifier_is_read_only_and_exactly_scopes_express_description() -> None:
    filename = "operator-verifier-policy.json"
    verifier_actions = all_actions(filename)
    assert all(
        action.split(":", maxsplit=1)[1].startswith(
            ("Describe", "Detect", "Filter", "Get", "List", "Lookup")
        )
        for action in verifier_actions
    )
    describe = statement_for_action(filename, "ecs:DescribeExpressGatewayService")
    assert describe["Resource"] == (
        f"arn:aws:ecs:{REGION}:{ACCOUNT}:service/default/"
        "steuerberater-copilot-reference-demo"
    )
    assert "iam:ListRoles" not in verifier_actions
    assert "secretsmanager:GetSecretValue" not in verifier_actions


def test_verifier_can_read_both_required_aws_managed_policy_versions() -> None:
    statement = statement_for_action(
        "operator-verifier-policy.json",
        "iam:GetPolicyVersion",
    )
    assert {
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        (
            "arn:aws:iam::aws:policy/service-role/"
            "AmazonECSInfrastructureRoleforExpressGatewayServices"
        ),
    } <= set(statement["Resource"])


def test_cloudformation_service_role_trusts_only_cloudformation() -> None:
    trust = load_document("cloudformation-service-role-trust-policy.json")
    assert trust["Statement"] == [
        {
            "Sid": "TrustCloudFormationOnly",
            "Effect": "Allow",
            "Principal": {"Service": "cloudformation.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ]
