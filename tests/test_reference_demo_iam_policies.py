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
    "bootstrap-role-boundary.json",
    "bootstrap-role-policy.json",
    "bootstrap-role-trust-policy.json",
    "cloudformation-service-role-boundary.json",
    "cloudformation-service-role-foundation-policy.json",
    "cloudformation-service-role-iam-lifecycle-policy.json",
    "cloudformation-service-role-policy.json",
    "cloudformation-service-role-trust-policy.json",
    "express-infrastructure-boundary.json",
    "express-infrastructure-acm-request-policy.json",
    "operator-boundary.json",
    "operator-cloudformation-policy.json",
    "operator-ecr-publisher-policy.json",
    "operator-secret-initializer-policy.json",
    "operator-verifier-policy.json",
    "task-execution-boundary.json",
}
TRUST_POLICY_FILES = {
    "bootstrap-role-trust-policy.json",
    "cloudformation-service-role-trust-policy.json",
}
BOOTSTRAP_PERMISSION_FILES = {
    "bootstrap-role-boundary.json",
    "bootstrap-role-policy.json",
}
FORBIDDEN_ACTIONS = {
    "iam:CreatePolicyVersion",
    "iam:DeleteRolePermissionsBoundary",
    "iam:PutRolePermissionsBoundary",
    "iam:UpdateAssumeRolePolicy",
    "iam:UpdateRole",
    "iam:UpdateRoleDescription",
}
BOOTSTRAP_ALLOWED_FORBIDDEN_ACTIONS = {
    "iam:DeleteRolePermissionsBoundary",
    "iam:PutRolePermissionsBoundary",
}
IAM_ROLE_TRUST_POLICY_DEFAULT_CHARACTER_LIMIT = 2_048
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


def statements_for_action(filename: str, action: str) -> list[dict[str, Any]]:
    matches = [
        statement
        for statement in statements(filename)
        if action in actions(statement)
    ]
    assert matches, (filename, action)
    return matches


def resources(statement: dict[str, Any]) -> set[str]:
    value = statement["Resource"]
    if isinstance(value, str):
        return {value}
    assert isinstance(value, list)
    assert all(isinstance(resource, str) for resource in value)
    return set(value)


def statements_for_action_and_resource(
    filename: str,
    action: str,
    resource: str,
) -> list[dict[str, Any]]:
    matches = [
        statement
        for statement in statements_for_action(filename, action)
        if resource in resources(statement)
    ]
    assert matches, (filename, action, resource)
    return matches


TASK_DEFINITION_ARN = (
    f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/*"
)
TASK_EXECUTION_ROLE_ARN = (
    f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
    "reference-demo/task-execution"
)
EXPRESS_INFRASTRUCTURE_ROLE_ARN = (
    f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
    "reference-demo/express-infrastructure"
)
CUSTOMER_MANAGED_VERIFIER_POLICY_ARNS = {
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-foundation-policy"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-iam-lifecycle-policy"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-service-boundary"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-service-policy"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-boundary"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-cloudformation"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-ecr-publisher"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-secret-initializer"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-verifier"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/reference-demo/"
        "express-infrastructure-boundary"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/reference-demo/"
        "express-infrastructure-acm-request-policy"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/reference-demo/"
        "task-execution-boundary"
    ),
}


def test_exact_versioned_artifact_set_parses_as_json() -> None:
    actual = {path.name for path in POLICY_DIR.glob("*.json")}
    assert actual == EXPECTED_FILES
    for filename in EXPECTED_FILES:
        document = load_document(filename)
        assert document["Version"] == "2012-10-17"
        assert document["Statement"]


@pytest.mark.parametrize(
    "filename",
    sorted(EXPECTED_FILES - TRUST_POLICY_FILES),
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
    assert documents["bootstrap-role-policy.json"] != documents[
        "bootstrap-role-boundary.json"
    ]


def allow_actions(filename: str) -> set[str]:
    return {
        action
        for statement in statements(filename)
        if statement["Effect"] == "Allow"
        for action in actions(statement)
    }


def test_no_wildcard_action_forbidden_managed_policy_or_deny_bypass() -> None:
    for filename in EXPECTED_FILES:
        raw = (POLICY_DIR / filename).read_text(encoding="utf-8")
        for forbidden_name in FORBIDDEN_POLICY_NAMES:
            assert forbidden_name not in raw
        forbidden = FORBIDDEN_ACTIONS
        if filename in BOOTSTRAP_PERMISSION_FILES:
            forbidden = FORBIDDEN_ACTIONS - BOOTSTRAP_ALLOWED_FORBIDDEN_ACTIONS
        assert not (allow_actions(filename) & forbidden)
        for statement in statements(filename):
            if filename in BOOTSTRAP_PERMISSION_FILES:
                assert statement["Effect"] in {"Allow", "Deny"}
            else:
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
        "/steuerberater-copilot/reference-demo/application:*"
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
    create_slr_statements = statements_for_action(
        filename,
        "iam:CreateServiceLinkedRole",
    )
    assert len(create_slr_statements) == 2
    assert all(
        actions(statement) == {"iam:CreateServiceLinkedRole"}
        and isinstance(statement["Resource"], str)
        and isinstance(
            statement["Condition"]["StringEquals"]["iam:AWSServiceName"],
            str,
        )
        for statement in create_slr_statements
    )
    assert {
        (
            statement["Resource"],
            statement["Condition"]["StringEquals"]["iam:AWSServiceName"],
        )
        for statement in create_slr_statements
    } == {
        (
            f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/"
            "ecs.application-autoscaling.amazonaws.com/"
            "AWSServiceRoleForApplicationAutoScaling_ECSService",
            "ecs.application-autoscaling.amazonaws.com",
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/"
            "elasticloadbalancing.amazonaws.com/"
            "AWSServiceRoleForElasticLoadBalancing",
            "elasticloadbalancing.amazonaws.com",
        ),
    }
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
        "application-autoscaling:RegisterScalableTarget",
        "elasticloadbalancing:CreateLoadBalancer",
    ):
        assert statement_for_action(filename, action)["Condition"]["StringEquals"][
            "aws:ResourceTag/AmazonECSManaged"
        ] == "true"

    certificate = statement_for_action(filename, "acm:DescribeCertificate")
    assert actions(certificate) == {
        "acm:AddTagsToCertificate",
        "acm:DeleteCertificate",
        "acm:DescribeCertificate",
    }
    assert resources(certificate) == {
        f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*"
    }
    assert certificate["Condition"] == {
        "StringEquals": {
            "aws:ResourceTag/AmazonECSManaged": "true",
        },
    }

    request = statement_for_action(filename, "acm:RequestCertificate")
    assert actions(request) == {"acm:RequestCertificate"}
    assert resources(request) == {"*"}
    assert request["Condition"] == {
        "StringEquals": {
            "aws:RequestTag/AmazonECSManaged": "true",
            "aws:RequestedRegion": REGION,
        },
    }


def test_express_acm_request_supplement_is_minimal_and_attachable() -> None:
    filename = "express-infrastructure-acm-request-policy.json"
    assert all_actions(filename) == {"acm:RequestCertificate"}

    request = statement_for_action(filename, "acm:RequestCertificate")
    assert resources(request) == {"*"}
    assert request["Condition"] == {
        "StringEquals": {
            "aws:RequestTag/AmazonECSManaged": "true",
            "aws:RequestedRegion": REGION,
        },
    }

    expected_policy_arns = {
        (
            "arn:aws:iam::aws:policy/service-role/"
            "AmazonECSInfrastructureRoleforExpressGatewayServices"
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/"
            "reference-demo/express-infrastructure-acm-request-policy"
        ),
    }

    for lifecycle_file in (
        "cloudformation-service-role-iam-lifecycle-policy.json",
        "cloudformation-service-role-boundary.json",
    ):
        matches = [
            statement
            for statement in statements(lifecycle_file)
            if actions(statement)
            == {"iam:AttachRolePolicy", "iam:DetachRolePolicy"}
            and resources(statement) == {EXPRESS_INFRASTRUCTURE_ROLE_ARN}
        ]
        assert len(matches) == 1
        policy_arns = matches[0]["Condition"]["ArnEquals"]["iam:PolicyARN"]
        assert isinstance(policy_arns, list)
        assert set(policy_arns) == expected_policy_arns


def test_service_role_create_role_is_split_by_exact_role_and_boundary() -> None:
    filename = "cloudformation-service-role-iam-lifecycle-policy.json"
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


def test_service_role_create_and_tag_role_enforce_all_fixed_request_tags() -> None:
    filename = "cloudformation-service-role-iam-lifecycle-policy.json"
    checked = [
        statement
        for statement in statements(filename)
        if actions(statement) in ({"iam:CreateRole"}, {"iam:TagRole"})
    ]
    assert len(checked) == 3
    expected_tag_keys = list(FIXED_TAGS)
    for statement in checked:
        string_equals = statement["Condition"]["StringEquals"]
        request_tags = {
            key.removeprefix("aws:RequestTag/"): value
            for key, value in string_equals.items()
            if key.startswith("aws:RequestTag/")
        }
        assert request_tags == FIXED_TAGS
        assert set(string_equals) >= {
            f"aws:RequestTag/{key}" for key in FIXED_TAGS
        }
        assert statement["Condition"]["ForAllValues:StringEquals"][
            "aws:TagKeys"
        ] == expected_tag_keys


def test_service_role_permission_modules_match_the_single_boundary_action_ceiling() -> None:
    permission_actions = (
        all_actions("cloudformation-service-role-foundation-policy.json")
        | all_actions("cloudformation-service-role-iam-lifecycle-policy.json")
        | all_actions("cloudformation-service-role-policy.json")
    )
    assert permission_actions == all_actions(
        "cloudformation-service-role-boundary.json"
    )


def test_service_role_has_exact_pass_role_statements_and_no_role_updates() -> None:
    filename = "cloudformation-service-role-iam-lifecycle-policy.json"
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


def test_operator_secrets_manager_statements_are_region_bound() -> None:
    expected_resource = (
        f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:"
        "steuerberater-copilot/reference-demo/synthetic-*"
    )
    expected_condition = {
        "StringEquals": {
            "aws:RequestedRegion": REGION,
        },
    }

    verifier = statement_for_action(
        "operator-verifier-policy.json",
        "secretsmanager:DescribeSecret",
    )
    assert actions(verifier) == {
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds",
    }
    assert resources(verifier) == {expected_resource}
    assert verifier["Condition"] == expected_condition

    boundary = statement_for_action(
        "operator-boundary.json",
        "secretsmanager:PutSecretValue",
    )
    assert actions(boundary) == {
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds",
        "secretsmanager:PutSecretValue",
    }
    assert resources(boundary) == {expected_resource}
    assert boundary["Condition"] == expected_condition


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


def test_service_role_allows_register_and_tag_on_task_definition() -> None:
    filename = "cloudformation-service-role-policy.json"
    register = statements_for_action_and_resource(
        filename,
        "ecs:RegisterTaskDefinition",
        TASK_DEFINITION_ARN,
    )
    assert len(register) == 1
    assert actions(register[0]) == {"ecs:RegisterTaskDefinition"}
    assert resources(register[0]) == {TASK_DEFINITION_ARN}
    assert "Condition" not in register[0]

    tag = statements_for_action_and_resource(
        filename,
        "ecs:TagResource",
        TASK_DEFINITION_ARN,
    )
    assert len(tag) == 1
    assert actions(tag[0]) == {"ecs:TagResource"}
    assert resources(tag[0]) == {TASK_DEFINITION_ARN}
    assert "Condition" not in tag[0]

    service_tag_resources = {
        resource
        for statement in statements_for_action(filename, "ecs:TagResource")
        for resource in resources(statement)
    }
    assert TASK_DEFINITION_ARN in service_tag_resources
    assert (
        f"arn:aws:ecs:{REGION}:{ACCOUNT}:service/default/"
        "steuerberater-copilot-reference-demo"
    ) in service_tag_resources


def test_verifier_includes_iam_lifecycle_policy_and_all_control_plane_reads() -> None:
    filename = "operator-verifier-policy.json"
    get_policy = statement_for_action(filename, "iam:GetPolicy")
    get_version = statement_for_action(filename, "iam:GetPolicyVersion")
    assert actions(get_policy) == {"iam:GetPolicy", "iam:GetPolicyVersion"}
    assert actions(get_version) == {"iam:GetPolicy", "iam:GetPolicyVersion"}
    assert resources(get_policy) == resources(get_version)
    read_resources = resources(get_policy)
    lifecycle_arn = (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-iam-lifecycle-policy"
    )
    assert lifecycle_arn in read_resources
    assert CUSTOMER_MANAGED_VERIFIER_POLICY_ARNS <= read_resources
    assert not {
        action
        for action in all_actions(filename)
        if action.startswith("iam:")
        and not action.split(":", maxsplit=1)[1].startswith(("Get", "List"))
    }


def test_inline_role_policy_writes_are_limited_to_task_execution_role() -> None:
    permission_file = "cloudformation-service-role-iam-lifecycle-policy.json"
    boundary_file = "cloudformation-service-role-boundary.json"
    for filename in (permission_file, boundary_file):
        for action in ("iam:PutRolePolicy", "iam:DeleteRolePolicy"):
            matches = statements_for_action(filename, action)
            assert len(matches) == 1, (filename, action)
            statement = matches[0]
            assert actions(statement) == {
                "iam:DeleteRolePolicy",
                "iam:PutRolePolicy",
            }
            assert resources(statement) == {TASK_EXECUTION_ROLE_ARN}
            assert EXPRESS_INFRASTRUCTURE_ROLE_ARN not in resources(statement)
            assert "Condition" not in statement

    for action in (
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:ListRoleTags",
        "iam:TagRole",
        "iam:UntagRole",
    ):
        for filename in (permission_file, boundary_file):
            role_resources = {
                resource
                for statement in statements_for_action(filename, action)
                for resource in resources(statement)
            }
            assert {
                TASK_EXECUTION_ROLE_ARN,
                EXPRESS_INFRASTRUCTURE_ROLE_ARN,
            } <= role_resources


def test_critical_service_role_statements_match_action_resource_and_conditions() -> None:
    lifecycle = "cloudformation-service-role-iam-lifecycle-policy.json"
    service = "cloudformation-service-role-policy.json"
    boundary = "cloudformation-service-role-boundary.json"

    pass_task = statements_for_action_and_resource(
        lifecycle,
        "iam:PassRole",
        TASK_EXECUTION_ROLE_ARN,
    )[0]
    assert actions(pass_task) == {"iam:PassRole"}
    assert pass_task["Condition"]["StringEquals"]["iam:PassedToService"] == (
        "ecs-tasks.amazonaws.com"
    )

    pass_express = statements_for_action_and_resource(
        lifecycle,
        "iam:PassRole",
        EXPRESS_INFRASTRUCTURE_ROLE_ARN,
    )[0]
    assert actions(pass_express) == {"iam:PassRole"}
    assert pass_express["Condition"]["StringEquals"]["iam:PassedToService"] == (
        "ecs.amazonaws.com"
    )

    delete_secret = statements_for_action_and_resource(
        service,
        "secretsmanager:DeleteSecret",
        (
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:"
            "steuerberater-copilot/reference-demo/synthetic-*"
        ),
    )[0]
    assert delete_secret["Condition"]["Bool"] == {
        "secretsmanager:ForceDeleteWithoutRecovery": "true"
    }

    for filename in (lifecycle, boundary):
        put_inline = statements_for_action_and_resource(
            filename,
            "iam:PutRolePolicy",
            TASK_EXECUTION_ROLE_ARN,
        )[0]
        assert resources(put_inline) == {TASK_EXECUTION_ROLE_ARN}
        assert EXPRESS_INFRASTRUCTURE_ROLE_ARN not in resources(put_inline)

    for filename in (service, boundary):
        register = statements_for_action_and_resource(
            filename,
            "ecs:RegisterTaskDefinition",
            TASK_DEFINITION_ARN,
        )[0]
        tag = statements_for_action_and_resource(
            filename,
            "ecs:TagResource",
            TASK_DEFINITION_ARN,
        )[0]
        assert TASK_DEFINITION_ARN in resources(register)
        assert TASK_DEFINITION_ARN in resources(tag)


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


SERVICE_ROLE_ARN = (
    f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
    "control-plane/reference-demo-cfn-service-role"
)
BOOTSTRAP_ROLE_ARN = (
    f"arn:aws:iam::{ACCOUNT}:role/steuerberater-copilot/"
    "control-plane/reference-demo-iam-bootstrap"
)
PRIVILEGED_CALLER_ARN = (
    f"arn:aws:iam::{ACCOUNT}:user/reference-demo-privileged-caller"
)
OPERATOR_POLICY_ARNS = {
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-cloudformation"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-ecr-publisher"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-secret-initializer"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-verifier"
    ),
}
CONTROL_PLANE_POLICY_RESOURCE_PREFIXES = {
    f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/reference-demo/*",
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-*"
    ),
    (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-operator-*"
    ),
}
BOOTSTRAP_POLICY_ARN_PREFIX = (
    f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
    "reference-demo-iam-bootstrap-"
)


def statement_by_sid(filename: str, sid: str) -> dict[str, Any]:
    matches = [
        statement
        for statement in statements(filename)
        if statement.get("Sid") == sid
    ]
    assert len(matches) == 1, (filename, sid, len(matches))
    return matches[0]


@pytest.mark.parametrize("filename", sorted(TRUST_POLICY_FILES))
def test_trust_policies_fit_the_default_iam_quota(filename: str) -> None:
    document = load_document(filename)
    character_count = len(
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    assert character_count <= IAM_ROLE_TRUST_POLICY_DEFAULT_CHARACTER_LIMIT, (
        filename,
        character_count,
    )


def test_bootstrap_role_trusts_only_the_privileged_caller_with_mfa() -> None:
    trust = load_document("bootstrap-role-trust-policy.json")
    assert trust["Statement"] == [
        {
            "Sid": "TrustPrivilegedCallerWithMfa",
            "Effect": "Allow",
            "Principal": {"AWS": PRIVILEGED_CALLER_ARN},
            "Action": "sts:AssumeRole",
            "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
        }
    ]


@pytest.mark.parametrize("filename", sorted(BOOTSTRAP_PERMISSION_FILES))
def test_bootstrap_permissions_cover_control_plane_tool_actions(
    filename: str,
) -> None:
    allowed = allow_actions(filename)
    assert {
        "cloudformation:DescribeStacks",
        "iam:AttachRolePolicy",
        "iam:AttachUserPolicy",
        "iam:CreatePolicy",
        "iam:CreateRole",
        "iam:DeletePolicy",
        "iam:DeleteRole",
        "iam:DeleteRolePermissionsBoundary",
        "iam:DeleteUserPermissionsBoundary",
        "iam:DetachRolePolicy",
        "iam:DetachUserPolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:GetRole",
        "iam:GetUser",
        "iam:ListAttachedRolePolicies",
        "iam:ListEntitiesForPolicy",
        "iam:ListInstanceProfilesForRole",
        "iam:ListPolicyTags",
        "iam:ListPolicyVersions",
        "iam:ListRolePolicies",
        "iam:PutRolePermissionsBoundary",
        "iam:PutUserPermissionsBoundary",
        "iam:TagPolicy",
        "iam:TagRole",
    } == allowed
    assert not allowed & {
        "iam:CreateAccessKey",
        "iam:CreateLoginProfile",
        "iam:CreatePolicyVersion",
        "iam:CreateUser",
        "iam:PassRole",
        "iam:SetDefaultPolicyVersion",
        "iam:UpdateAssumeRolePolicy",
        "iam:UpdateRole",
        "iam:UpdateRoleDescription",
        "sts:GetCallerIdentity",
    }
    create_policy = next(
        statement
        for statement in statements(filename)
        if statement["Effect"] == "Allow"
        and actions(statement) == {"iam:CreatePolicy", "iam:TagPolicy"}
    )
    assert resources(create_policy) == CONTROL_PLANE_POLICY_RESOURCE_PREFIXES
    assert not any(
        resource.startswith(BOOTSTRAP_POLICY_ARN_PREFIX)
        for resource in resources(create_policy)
    )
    assert create_policy["Condition"]["StringEquals"] == {
        "aws:RequestTag/Component": "reference-demo",
        "aws:RequestTag/Environment": "portfolio-test",
        "aws:RequestTag/Lifecycle": "ephemeral",
        "aws:RequestTag/ManagedBy": "cloudformation",
        "aws:RequestTag/Project": "steuerberater-copilot",
    }
    create_role = next(
        statement
        for statement in statements(filename)
        if statement["Effect"] == "Allow" and "iam:CreateRole" in actions(statement)
    )
    assert resources(create_role) == {SERVICE_ROLE_ARN}
    assert create_role["Condition"]["ArnEquals"]["iam:PermissionsBoundary"] == (
        f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
        "reference-demo-cfn-service-boundary"
    )
    attach_service = next(
        statement
        for statement in statements(filename)
        if statement["Effect"] == "Allow"
        and actions(statement) == {"iam:AttachRolePolicy", "iam:DetachRolePolicy"}
        and resources(statement) == {SERVICE_ROLE_ARN}
    )
    assert set(attach_service["Condition"]["ArnEquals"]["iam:PolicyARN"]) == {
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
            "reference-demo-cfn-foundation-policy"
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
            "reference-demo-cfn-iam-lifecycle-policy"
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
            "reference-demo-cfn-service-policy"
        ),
    }
    attach_operator = next(
        statement
        for statement in statements(filename)
        if statement["Effect"] == "Allow"
        and "iam:AttachUserPolicy" in actions(statement)
    )
    assert resources(attach_operator) == {
        f"arn:aws:iam::{ACCOUNT}:role/*",
        f"arn:aws:iam::{ACCOUNT}:user/*",
    }
    assert set(attach_operator["Condition"]["ArnEquals"]["iam:PolicyARN"]) == (
        OPERATOR_POLICY_ARNS
    )
    describe_stacks = next(
        statement
        for statement in statements(filename)
        if "cloudformation:DescribeStacks" in actions(statement)
    )
    assert describe_stacks["Effect"] == "Allow"
    assert describe_stacks["Resource"] == (
        f"arn:aws:cloudformation:{REGION}:{ACCOUNT}:stack/"
        "steuerberater-copilot-reference-demo/*"
    )


@pytest.mark.parametrize("filename", sorted(BOOTSTRAP_PERMISSION_FILES))
def test_bootstrap_permissions_deny_operator_mutation_of_protected_roles(
    filename: str,
) -> None:
    runtime_protect = statement_by_sid(
        filename, "DenyMutateBootstrapAndRuntimeRoles"
    )
    assert runtime_protect["Effect"] == "Deny"
    assert actions(runtime_protect) == {
        "iam:AttachRolePolicy",
        "iam:DeleteRolePermissionsBoundary",
        "iam:DetachRolePolicy",
        "iam:PutRolePermissionsBoundary",
    }
    assert resources(runtime_protect) == {
        BOOTSTRAP_ROLE_ARN,
        EXPRESS_INFRASTRUCTURE_ROLE_ARN,
        TASK_EXECUTION_ROLE_ARN,
    }

    operator_on_service = statement_by_sid(
        filename, "DenyOperatorPoliciesOnServiceRole"
    )
    assert operator_on_service["Effect"] == "Deny"
    assert resources(operator_on_service) == {SERVICE_ROLE_ARN}
    assert set(operator_on_service["Condition"]["ArnEquals"]["iam:PolicyARN"]) == {
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
            "reference-demo-iam-bootstrap-*"
        ),
        (
            f"arn:aws:iam::{ACCOUNT}:policy/steuerberater-copilot/control-plane/"
            "reference-demo-operator-*"
        ),
    }

    caller_protect = statement_by_sid(filename, "DenyMutatePrivilegedCaller")
    assert caller_protect["Effect"] == "Deny"
    assert resources(caller_protect) == {PRIVILEGED_CALLER_ARN}
    assert "iam:DeleteUser" in actions(caller_protect)

    delete_service_boundary = statement_by_sid(
        filename, "DenyDeleteServiceRoleBoundary"
    )
    assert delete_service_boundary == {
        "Sid": "DenyDeleteServiceRoleBoundary",
        "Effect": "Deny",
        "Action": "iam:DeleteRolePermissionsBoundary",
        "Resource": SERVICE_ROLE_ARN,
    }
