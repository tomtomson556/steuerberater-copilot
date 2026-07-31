#!/usr/bin/env python3
"""Fail-closed IAM control-plane bootstrap and teardown for the AWS reference demo."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIRECTORY = ROOT / "infra" / "iam" / "reference-demo" / "v2.3"
ACCOUNT_TOKEN = "<ACCOUNT_ID>"
REGION = "eu-central-1"
IAM_MANAGED_POLICY_CHARACTER_LIMIT = 6_144
STACK_NAME = "steuerberater-copilot-reference-demo"
SERVICE_ROLE_NAME = "reference-demo-cfn-service-role"
SERVICE_ROLE_PATH = "/steuerberater-copilot/control-plane/"
OPERATOR_POLICY_KEYS = (
    "operator-cloudformation",
    "operator-ecr-publisher",
    "operator-secret-initializer",
    "operator-verifier",
)
SERVICE_ROLE_POLICY_KEYS = (
    "cloudformation-service-foundation-policy",
    "cloudformation-service-policy",
)
FIXED_TAGS = {
    "Project": "steuerberater-copilot",
    "Component": "reference-demo",
    "Environment": "portfolio-test",
    "ManagedBy": "cloudformation",
    "Lifecycle": "ephemeral",
}
ACCOUNT_ID_RE = re.compile(r"^[0-9]{12}$")
IDENTITY_NAME_RE = re.compile(r"^[A-Za-z0-9+=,.@_-]{1,64}$")


class ControlPlaneError(RuntimeError):
    """Raised when fail-closed control-plane validation rejects an operation."""


@dataclass(frozen=True)
class PolicyArtifact:
    key: str
    filename: str
    name: str
    path: str

    @property
    def source_path(self) -> Path:
        return POLICY_DIRECTORY / self.filename

    def arn(self, account_id: str) -> str:
        return f"arn:aws:iam::{account_id}:policy{self.path}{self.name}"

    def rendered_document(self, account_id: str) -> dict[str, Any]:
        document = _load_json(self.source_path)
        rendered = _replace_account_token(document, account_id)
        if _contains_placeholder(rendered):
            raise ControlPlaneError(f"Unresolved placeholder in {self.filename}.")
        if len(_canonical_json(rendered)) > IAM_MANAGED_POLICY_CHARACTER_LIMIT:
            raise ControlPlaneError(
                f"IAM managed-policy character quota exceeded: {self.filename}."
            )
        return rendered


POLICIES = (
    PolicyArtifact(
        "task-execution-boundary",
        "task-execution-boundary.json",
        "task-execution-boundary",
        "/steuerberater-copilot/reference-demo/",
    ),
    PolicyArtifact(
        "express-infrastructure-boundary",
        "express-infrastructure-boundary.json",
        "express-infrastructure-boundary",
        "/steuerberater-copilot/reference-demo/",
    ),
    PolicyArtifact(
        "cloudformation-service-foundation-policy",
        "cloudformation-service-role-foundation-policy.json",
        "reference-demo-cfn-foundation-policy",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "cloudformation-service-policy",
        "cloudformation-service-role-policy.json",
        "reference-demo-cfn-service-policy",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "cloudformation-service-boundary",
        "cloudformation-service-role-boundary.json",
        "reference-demo-cfn-service-boundary",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "operator-cloudformation",
        "operator-cloudformation-policy.json",
        "reference-demo-operator-cloudformation",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "operator-ecr-publisher",
        "operator-ecr-publisher-policy.json",
        "reference-demo-operator-ecr-publisher",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "operator-secret-initializer",
        "operator-secret-initializer-policy.json",
        "reference-demo-operator-secret-initializer",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "operator-verifier",
        "operator-verifier-policy.json",
        "reference-demo-operator-verifier",
        SERVICE_ROLE_PATH,
    ),
    PolicyArtifact(
        "operator-boundary",
        "operator-boundary.json",
        "reference-demo-operator-boundary",
        SERVICE_ROLE_PATH,
    ),
)
POLICY_BY_KEY = {artifact.key: artifact for artifact in POLICIES}


@dataclass(frozen=True)
class Config:
    account_id: str
    operator_type: str
    operator_name: str

    @property
    def service_role_arn(self) -> str:
        return (
            f"arn:aws:iam::{self.account_id}:role"
            f"{SERVICE_ROLE_PATH}{SERVICE_ROLE_NAME}"
        )


class IamClient(Protocol):
    def call(
        self,
        *arguments: str,
        allow_not_found: bool = False,
    ) -> dict[str, Any] | None: ...

    def call_cloudformation(
        self,
        *arguments: str,
        allow_stack_absent: bool = False,
    ) -> dict[str, Any] | None: ...

    def call_sts(self, *arguments: str) -> dict[str, Any]: ...


class AwsCli:
    """Small AWS CLI boundary; no command is run by dry-run planning."""

    def call(
        self,
        *arguments: str,
        allow_not_found: bool = False,
    ) -> dict[str, Any] | None:
        return self._call(
            "iam",
            arguments,
            not_found_markers=("NoSuchEntity",) if allow_not_found else None,
        )

    def call_cloudformation(
        self,
        *arguments: str,
        allow_stack_absent: bool = False,
    ) -> dict[str, Any] | None:
        return self._call(
            "cloudformation",
            arguments,
            not_found_markers=(
                ("ValidationError", "does not exist")
                if allow_stack_absent
                else None
            ),
        )

    def call_sts(self, *arguments: str) -> dict[str, Any]:
        response = self._call("sts", arguments, not_found_markers=None)
        if response is None:
            raise ControlPlaneError("AWS STS returned no response.")
        return response

    def _call(
        self,
        service: str,
        arguments: tuple[str, ...],
        *,
        not_found_markers: tuple[str, ...] | None,
    ) -> dict[str, Any] | None:
        command = [
            "aws",
            service,
            *arguments,
            "--no-cli-pager",
            "--output",
            "json",
        ]
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            if not_found_markers is not None and all(
                marker in result.stderr for marker in not_found_markers
            ):
                return None
            detail = result.stderr.strip() or "AWS CLI returned no error detail."
            raise ControlPlaneError(f"AWS IAM command failed: {detail}")
        if not result.stdout.strip():
            return {}
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ControlPlaneError("AWS CLI returned invalid JSON.") from exc
        if not isinstance(response, dict):
            raise ControlPlaneError("AWS CLI returned a non-object JSON response.")
        return response


def _load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(f"Cannot load IAM artifact {path}.") from exc
    if not isinstance(document, dict):
        raise ControlPlaneError(f"IAM artifact must be a JSON object: {path}.")
    return document


def _replace_account_token(value: Any, account_id: str) -> Any:
    if isinstance(value, str):
        return value.replace(ACCOUNT_TOKEN, account_id)
    if isinstance(value, list):
        return [_replace_account_token(item, account_id) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_account_token(item, account_id)
            for key, item in value.items()
        }
    return value


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "<" in value or ">" in value
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    return False


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _document_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _decode_policy_document(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(unquote(value))
        except json.JSONDecodeError as exc:
            raise ControlPlaneError("IAM returned an invalid policy document.") from exc
        if isinstance(decoded, dict):
            return decoded
    raise ControlPlaneError("IAM returned a non-object policy document.")


def _tags_from_response(items: Any) -> dict[str, str]:
    if not isinstance(items, list):
        raise ControlPlaneError("IAM returned invalid tags.")
    tags: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("Key"), str):
            raise ControlPlaneError("IAM returned invalid tags.")
        value = item.get("Value")
        if not isinstance(value, str):
            raise ControlPlaneError("IAM returned invalid tags.")
        tags[item["Key"]] = value
    return tags


def _policy_document_argument(document: dict[str, Any]) -> str:
    return _canonical_json(document)


def _tag_arguments() -> list[str]:
    return [f"Key={key},Value={value}" for key, value in FIXED_TAGS.items()]


def _operator_reference(config: Config) -> str:
    return f"{config.operator_type}:{config.operator_name}"


def _operator_entity(config: Config) -> tuple[str, str]:
    key = "UserName" if config.operator_type == "user" else "RoleName"
    return key, config.operator_name


def _get_operator(config: Config, client: IamClient) -> dict[str, Any]:
    identity_key, identity_name = _operator_entity(config)
    response = client.call(
        f"get-{config.operator_type}",
        f"--{config.operator_type}-name",
        identity_name,
        allow_not_found=True,
    )
    if response is None:
        raise ControlPlaneError(
            f"Explicit operator {config.operator_type} {identity_name!r} does not exist."
        )
    identity = response.get(config.operator_type.capitalize())
    if not isinstance(identity, dict):
        raise ControlPlaneError("IAM returned an invalid operator identity.")
    if identity.get(identity_key) != identity_name:
        raise ControlPlaneError("IAM returned a different operator identity.")
    actual_arn = identity.get("Arn")
    expected_prefix = (
        f"arn:aws:iam::{config.account_id}:{config.operator_type}/"
    )
    if (
        not isinstance(actual_arn, str)
        or not actual_arn.startswith(expected_prefix)
        or actual_arn.rsplit("/", maxsplit=1)[-1] != identity_name
    ):
        raise ControlPlaneError("Operator ARN does not match the explicit identity.")
    return identity


def _operator_boundary_arn(identity: dict[str, Any]) -> str | None:
    boundary = identity.get("PermissionsBoundary")
    if boundary is None:
        return None
    if not isinstance(boundary, dict):
        raise ControlPlaneError("IAM returned an invalid operator boundary.")
    arn = boundary.get("PermissionsBoundaryArn")
    if not isinstance(arn, str):
        raise ControlPlaneError("IAM returned an invalid operator boundary ARN.")
    return arn


def _verify_apply_caller(config: Config, client: IamClient) -> None:
    response = client.call_sts("get-caller-identity")
    account = response.get("Account")
    arn = response.get("Arn")
    if account != config.account_id:
        raise ControlPlaneError("Caller account does not match --account-id.")
    if not isinstance(arn, str):
        raise ControlPlaneError("AWS STS returned an invalid caller ARN.")
    if arn == f"arn:aws:iam::{config.account_id}:root":
        raise ControlPlaneError("Root credentials are forbidden for this tool.")


def _assert_stack_absent(client: IamClient) -> None:
    response = client.call_cloudformation(
        "describe-stacks",
        "--region",
        REGION,
        "--stack-name",
        STACK_NAME,
        allow_stack_absent=True,
    )
    if response is not None:
        raise ControlPlaneError(
            "Reference-demo stack still exists; IAM teardown is refused."
        )


def _inspect_policy(
    artifact: PolicyArtifact,
    config: Config,
    client: IamClient,
    *,
    required: bool,
) -> bool:
    policy_arn = artifact.arn(config.account_id)
    response = client.call(
        "get-policy",
        "--policy-arn",
        policy_arn,
        allow_not_found=True,
    )
    if response is None:
        if required:
            raise ControlPlaneError(f"Required policy is absent: {policy_arn}.")
        return False
    policy = response.get("Policy")
    if not isinstance(policy, dict):
        raise ControlPlaneError(f"IAM returned invalid policy metadata: {policy_arn}.")
    expected_metadata = {
        "Arn": policy_arn,
        "Path": artifact.path,
        "PolicyName": artifact.name,
        "DefaultVersionId": "v1",
    }
    for key, expected in expected_metadata.items():
        if policy.get(key) != expected:
            raise ControlPlaneError(
                f"Policy metadata mismatch for {policy_arn}: {key}."
            )

    versions_response = client.call(
        "list-policy-versions",
        "--policy-arn",
        policy_arn,
    )
    versions = versions_response.get("Versions") if versions_response else None
    if not isinstance(versions, list) or len(versions) != 1:
        raise ControlPlaneError(f"Unexpected policy versions for {policy_arn}.")
    version = versions[0]
    if (
        not isinstance(version, dict)
        or version.get("VersionId") != "v1"
        or version.get("IsDefaultVersion") is not True
    ):
        raise ControlPlaneError(f"Policy is not on its sole v1 version: {policy_arn}.")

    document_response = client.call(
        "get-policy-version",
        "--policy-arn",
        policy_arn,
        "--version-id",
        "v1",
    )
    policy_version = (
        document_response.get("PolicyVersion") if document_response else None
    )
    if not isinstance(policy_version, dict):
        raise ControlPlaneError(f"IAM returned invalid policy content: {policy_arn}.")
    actual_document = _decode_policy_document(policy_version.get("Document"))
    expected_document = artifact.rendered_document(config.account_id)
    if _document_hash(actual_document) != _document_hash(expected_document):
        raise ControlPlaneError(
            f"Policy hash mismatch for {policy_arn}; no update is permitted."
        )

    tags_response = client.call("list-policy-tags", "--policy-arn", policy_arn)
    actual_tags = _tags_from_response(tags_response.get("Tags") if tags_response else None)
    if actual_tags != FIXED_TAGS:
        raise ControlPlaneError(f"Policy tags mismatch for {policy_arn}.")
    return True


def _entity_names(response: dict[str, Any] | None) -> dict[str, set[str]]:
    if response is None:
        raise ControlPlaneError("IAM returned no policy entity response.")
    result: dict[str, set[str]] = {}
    for response_key, name_key in (
        ("PolicyGroups", "GroupName"),
        ("PolicyUsers", "UserName"),
        ("PolicyRoles", "RoleName"),
    ):
        values = response.get(response_key)
        if not isinstance(values, list):
            raise ControlPlaneError("IAM returned invalid policy entities.")
        names: set[str] = set()
        for value in values:
            if not isinstance(value, dict) or not isinstance(value.get(name_key), str):
                raise ControlPlaneError("IAM returned invalid policy entities.")
            names.add(value[name_key])
        result[response_key] = names
    return result


def _expected_policy_entities(
    artifact: PolicyArtifact,
    config: Config,
    *,
    usage: str,
) -> dict[str, set[str]]:
    expected = {"PolicyGroups": set(), "PolicyUsers": set(), "PolicyRoles": set()}
    target_key = (
        "PolicyUsers" if config.operator_type == "user" else "PolicyRoles"
    )
    if usage == "PermissionsPolicy":
        if artifact.key in SERVICE_ROLE_POLICY_KEYS:
            expected["PolicyRoles"].add(SERVICE_ROLE_NAME)
        elif artifact.key in OPERATOR_POLICY_KEYS:
            expected[target_key].add(config.operator_name)
    elif usage == "PermissionsBoundary":
        if artifact.key == "cloudformation-service-boundary":
            expected["PolicyRoles"].add(SERVICE_ROLE_NAME)
        elif artifact.key == "operator-boundary":
            expected[target_key].add(config.operator_name)
    else:
        raise AssertionError(f"Unsupported policy usage: {usage}")
    return expected


def _inspect_policy_entities(
    artifact: PolicyArtifact,
    config: Config,
    client: IamClient,
    *,
    require_exact: bool,
) -> None:
    for usage in ("PermissionsPolicy", "PermissionsBoundary"):
        response = client.call(
            "list-entities-for-policy",
            "--policy-arn",
            artifact.arn(config.account_id),
            "--policy-usage-filter",
            usage,
        )
        actual = _entity_names(response)
        expected = _expected_policy_entities(artifact, config, usage=usage)
        valid = actual == expected if require_exact else all(
            actual[key].issubset(expected[key]) for key in expected
        )
        if not valid:
            raise ControlPlaneError(
                f"Unexpected {usage} attachment for "
                f"{artifact.arn(config.account_id)}."
            )


def _service_role_expected(config: Config) -> dict[str, Any]:
    trust = _load_json(POLICY_DIRECTORY / "cloudformation-service-role-trust-policy.json")
    return {
        "Arn": config.service_role_arn,
        "Path": SERVICE_ROLE_PATH,
        "RoleName": SERVICE_ROLE_NAME,
        "AssumeRolePolicyDocument": trust,
        "PermissionsBoundaryArn": POLICY_BY_KEY[
            "cloudformation-service-boundary"
        ].arn(config.account_id),
        "Tags": FIXED_TAGS,
    }


def _inspect_service_role(
    config: Config,
    client: IamClient,
    *,
    required: bool,
    require_complete_attachment: bool,
) -> bool:
    response = client.call(
        "get-role",
        "--role-name",
        SERVICE_ROLE_NAME,
        allow_not_found=True,
    )
    if response is None:
        if required:
            raise ControlPlaneError("Required CloudFormation service role is absent.")
        return False
    role = response.get("Role")
    if not isinstance(role, dict):
        raise ControlPlaneError("IAM returned invalid service-role metadata.")
    expected = _service_role_expected(config)
    for key in ("Arn", "Path", "RoleName"):
        if role.get(key) != expected[key]:
            raise ControlPlaneError(f"Service-role metadata mismatch: {key}.")
    actual_trust = _decode_policy_document(role.get("AssumeRolePolicyDocument"))
    if _document_hash(actual_trust) != _document_hash(
        expected["AssumeRolePolicyDocument"]
    ):
        raise ControlPlaneError("Service-role trust-policy hash mismatch.")
    boundary = role.get("PermissionsBoundary")
    if not isinstance(boundary, dict) or boundary.get(
        "PermissionsBoundaryArn"
    ) != expected["PermissionsBoundaryArn"]:
        raise ControlPlaneError("Service-role boundary mismatch.")
    if _tags_from_response(role.get("Tags")) != FIXED_TAGS:
        raise ControlPlaneError("Service-role tags mismatch.")

    attached_response = client.call(
        "list-attached-role-policies",
        "--role-name",
        SERVICE_ROLE_NAME,
    )
    attached_items = (
        attached_response.get("AttachedPolicies") if attached_response else None
    )
    if not isinstance(attached_items, list):
        raise ControlPlaneError("IAM returned invalid service-role attachments.")
    attached = {
        item.get("PolicyArn")
        for item in attached_items
        if isinstance(item, dict) and isinstance(item.get("PolicyArn"), str)
    }
    if len(attached) != len(attached_items):
        raise ControlPlaneError("IAM returned invalid service-role attachments.")
    expected_attachment = {
        POLICY_BY_KEY[key].arn(config.account_id)
        for key in SERVICE_ROLE_POLICY_KEYS
    }
    valid_attachment = (
        attached == expected_attachment
        if require_complete_attachment
        else attached.issubset(expected_attachment)
    )
    if not valid_attachment:
        raise ControlPlaneError("Unexpected service-role managed-policy attachment.")

    inline_response = client.call(
        "list-role-policies",
        "--role-name",
        SERVICE_ROLE_NAME,
    )
    inline_names = inline_response.get("PolicyNames") if inline_response else None
    if inline_names != []:
        raise ControlPlaneError("Unexpected service-role inline policy.")
    profiles_response = client.call(
        "list-instance-profiles-for-role",
        "--role-name",
        SERVICE_ROLE_NAME,
    )
    profiles = profiles_response.get("InstanceProfiles") if profiles_response else None
    if profiles != []:
        raise ControlPlaneError("Unexpected service-role instance-profile dependency.")
    return True


def _create_policy(
    artifact: PolicyArtifact,
    config: Config,
    client: IamClient,
) -> None:
    client.call(
        "create-policy",
        "--policy-name",
        artifact.name,
        "--path",
        artifact.path,
        "--description",
        f"Steuerberater-Copilot AWS reference demo IAM v2.3: {artifact.key}",
        "--policy-document",
        _policy_document_argument(artifact.rendered_document(config.account_id)),
        "--tags",
        *_tag_arguments(),
    )


def _create_service_role(config: Config, client: IamClient) -> None:
    expected = _service_role_expected(config)
    client.call(
        "create-role",
        "--role-name",
        SERVICE_ROLE_NAME,
        "--path",
        SERVICE_ROLE_PATH,
        "--assume-role-policy-document",
        _policy_document_argument(expected["AssumeRolePolicyDocument"]),
        "--permissions-boundary",
        expected["PermissionsBoundaryArn"],
        "--tags",
        *_tag_arguments(),
    )


def _attach_operator_policy(
    artifact: PolicyArtifact,
    config: Config,
    client: IamClient,
) -> None:
    client.call(
        f"attach-{config.operator_type}-policy",
        f"--{config.operator_type}-name",
        config.operator_name,
        "--policy-arn",
        artifact.arn(config.account_id),
    )


def _put_operator_boundary(config: Config, client: IamClient) -> None:
    client.call(
        f"put-{config.operator_type}-permissions-boundary",
        f"--{config.operator_type}-name",
        config.operator_name,
        "--permissions-boundary",
        POLICY_BY_KEY["operator-boundary"].arn(config.account_id),
    )


def bootstrap(config: Config, client: IamClient) -> None:
    """Validate all existing state before creating the frozen control plane."""
    operator = _get_operator(config, client)
    expected_operator_boundary = POLICY_BY_KEY["operator-boundary"].arn(
        config.account_id
    )
    actual_operator_boundary = _operator_boundary_arn(operator)
    if actual_operator_boundary not in (None, expected_operator_boundary):
        raise ControlPlaneError("Operator has an unexpected permissions boundary.")

    existing_policies: dict[str, bool] = {}
    for artifact in POLICIES:
        exists = _inspect_policy(
            artifact,
            config,
            client,
            required=False,
        )
        existing_policies[artifact.key] = exists
        if exists:
            _inspect_policy_entities(
                artifact,
                config,
                client,
                require_exact=False,
            )
    service_role_exists = _inspect_service_role(
        config,
        client,
        required=False,
        require_complete_attachment=False,
    )

    initial_policy_keys = (
        "task-execution-boundary",
        "express-infrastructure-boundary",
        "cloudformation-service-foundation-policy",
        "cloudformation-service-policy",
        "cloudformation-service-boundary",
    )
    for key in initial_policy_keys:
        if not existing_policies[key]:
            _create_policy(POLICY_BY_KEY[key], config, client)

    if not service_role_exists:
        _create_service_role(config, client)
    for key in SERVICE_ROLE_POLICY_KEYS:
        service_policy = POLICY_BY_KEY[key]
        if not _policy_is_attached_to_role(
            service_policy,
            SERVICE_ROLE_NAME,
            config,
            client,
        ):
            client.call(
                "attach-role-policy",
                "--role-name",
                SERVICE_ROLE_NAME,
                "--policy-arn",
                service_policy.arn(config.account_id),
            )

    for key in (*OPERATOR_POLICY_KEYS, "operator-boundary"):
        if not existing_policies[key]:
            _create_policy(POLICY_BY_KEY[key], config, client)
    for key in OPERATOR_POLICY_KEYS:
        artifact = POLICY_BY_KEY[key]
        if not _policy_is_attached_to_operator(artifact, config, client):
            _attach_operator_policy(artifact, config, client)
    if actual_operator_boundary is None:
        _put_operator_boundary(config, client)


def _policy_is_attached_to_role(
    artifact: PolicyArtifact,
    role_name: str,
    config: Config,
    client: IamClient,
) -> bool:
    response = client.call(
        "list-entities-for-policy",
        "--policy-arn",
        artifact.arn(config.account_id),
        "--policy-usage-filter",
        "PermissionsPolicy",
    )
    entities = _entity_names(response)
    return role_name in entities["PolicyRoles"]


def _policy_is_attached_to_operator(
    artifact: PolicyArtifact,
    config: Config,
    client: IamClient,
) -> bool:
    response = client.call(
        "list-entities-for-policy",
        "--policy-arn",
        artifact.arn(config.account_id),
        "--policy-usage-filter",
        "PermissionsPolicy",
    )
    entities = _entity_names(response)
    target = "PolicyUsers" if config.operator_type == "user" else "PolicyRoles"
    return config.operator_name in entities[target]


def teardown(config: Config, client: IamClient) -> None:
    """Refuse teardown until every attachment and dependency is exactly expected."""
    _assert_stack_absent(client)
    operator = _get_operator(config, client)
    expected_operator_boundary = POLICY_BY_KEY["operator-boundary"].arn(
        config.account_id
    )
    actual_operator_boundary = _operator_boundary_arn(operator)
    if actual_operator_boundary not in (None, expected_operator_boundary):
        raise ControlPlaneError("Operator has an unexpected permissions boundary.")

    existing_policies: dict[str, bool] = {}
    for artifact in POLICIES:
        exists = _inspect_policy(artifact, config, client, required=False)
        existing_policies[artifact.key] = exists
        if exists:
            _inspect_policy_entities(
                artifact,
                config,
                client,
                require_exact=False,
            )
    service_role_exists = _inspect_service_role(
        config,
        client,
        required=False,
        require_complete_attachment=False,
    )

    for key in OPERATOR_POLICY_KEYS:
        artifact = POLICY_BY_KEY[key]
        if existing_policies[key] and _policy_is_attached_to_operator(
            artifact,
            config,
            client,
        ):
            client.call(
                f"detach-{config.operator_type}-policy",
                f"--{config.operator_type}-name",
                config.operator_name,
                "--policy-arn",
                artifact.arn(config.account_id),
            )
    if actual_operator_boundary == expected_operator_boundary:
        client.call(
            f"delete-{config.operator_type}-permissions-boundary",
            f"--{config.operator_type}-name",
            config.operator_name,
        )

    if service_role_exists:
        for key in SERVICE_ROLE_POLICY_KEYS:
            artifact = POLICY_BY_KEY[key]
            if existing_policies[key] and _policy_is_attached_to_role(
                artifact,
                SERVICE_ROLE_NAME,
                config,
                client,
            ):
                client.call(
                    "detach-role-policy",
                    "--role-name",
                    SERVICE_ROLE_NAME,
                    "--policy-arn",
                    artifact.arn(config.account_id),
                )
        client.call("delete-role", "--role-name", SERVICE_ROLE_NAME)

    teardown_policy_order = (
        "cloudformation-service-foundation-policy",
        "cloudformation-service-policy",
        "cloudformation-service-boundary",
        "task-execution-boundary",
        "express-infrastructure-boundary",
        *OPERATOR_POLICY_KEYS,
        "operator-boundary",
    )
    for key in teardown_policy_order:
        if existing_policies[key]:
            client.call(
                "delete-policy",
                "--policy-arn",
                POLICY_BY_KEY[key].arn(config.account_id),
            )


def _plan_steps(operation: str, config: Config) -> list[dict[str, Any]]:
    if operation == "bootstrap":
        keys_before_role = (
            "task-execution-boundary",
            "express-infrastructure-boundary",
            "cloudformation-service-foundation-policy",
            "cloudformation-service-policy",
            "cloudformation-service-boundary",
        )
        steps: list[dict[str, Any]] = [
            _policy_plan_step("create-or-verify-policy", key, config)
            for key in keys_before_role
        ]
        steps.extend(
            [
                {
                    "action": "create-or-verify-service-role",
                    "arn": config.service_role_arn,
                    "trust_sha256": _document_hash(
                        _service_role_expected(config)["AssumeRolePolicyDocument"]
                    ),
                },
            ]
        )
        steps.extend(
            {
                "action": "attach-service-role-policy",
                "policy_arn": POLICY_BY_KEY[key].arn(config.account_id),
                "role_arn": config.service_role_arn,
            }
            for key in SERVICE_ROLE_POLICY_KEYS
        )
        steps.extend(
            _policy_plan_step("create-or-verify-policy", key, config)
            for key in (*OPERATOR_POLICY_KEYS, "operator-boundary")
        )
        steps.extend(
            {
                "action": "attach-operator-policy",
                "operator_identity": _operator_reference(config),
                "policy_arn": POLICY_BY_KEY[key].arn(config.account_id),
            }
            for key in OPERATOR_POLICY_KEYS
        )
        steps.append(
            {
                "action": "set-operator-boundary",
                "operator_identity": _operator_reference(config),
                "policy_arn": POLICY_BY_KEY["operator-boundary"].arn(
                    config.account_id
                ),
            }
        )
        return steps

    steps = [
        {
            "action": (
                "preflight-stack-absence-exact-hashes-attachments-and-dependencies"
            ),
        }
    ]
    steps.extend(
        {
            "action": "detach-operator-policy",
            "operator_identity": _operator_reference(config),
            "policy_arn": POLICY_BY_KEY[key].arn(config.account_id),
        }
        for key in OPERATOR_POLICY_KEYS
    )
    steps.extend(
        [
            {
                "action": "remove-operator-boundary",
                "operator_identity": _operator_reference(config),
            },
        ]
    )
    steps.extend(
        {
            "action": "detach-service-role-policy",
            "policy_arn": POLICY_BY_KEY[key].arn(config.account_id),
            "role_arn": config.service_role_arn,
        }
        for key in SERVICE_ROLE_POLICY_KEYS
    )
    steps.append(
        {
            "action": "delete-service-role",
            "role_arn": config.service_role_arn,
        }
    )
    teardown_policy_order = (
        "cloudformation-service-foundation-policy",
        "cloudformation-service-policy",
        "cloudformation-service-boundary",
        "task-execution-boundary",
        "express-infrastructure-boundary",
        *OPERATOR_POLICY_KEYS,
        "operator-boundary",
    )
    steps.extend(
        _policy_plan_step("delete-policy", key, config)
        for key in teardown_policy_order
    )
    return steps


def _policy_plan_step(
    action: str,
    key: str,
    config: Config,
) -> dict[str, Any]:
    artifact = POLICY_BY_KEY[key]
    document = artifact.rendered_document(config.account_id)
    return {
        "action": action,
        "artifact": artifact.filename,
        "arn": artifact.arn(config.account_id),
        "non_whitespace_characters": len(_canonical_json(document)),
        "sha256": _document_hash(document),
    }


def build_plan(operation: str, config: Config) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "mode": "dry-run",
        "operation": operation,
        "region": REGION,
        "account_id": config.account_id,
        "operator": {
            "type": config.operator_type,
            "name": config.operator_name,
            "reference": _operator_reference(config),
        },
        "steps": [
            {"order": index, **step}
            for index, step in enumerate(
                _plan_steps(operation, config),
                start=1,
            )
        ],
    }


def _validated_config(args: argparse.Namespace) -> Config:
    if not ACCOUNT_ID_RE.fullmatch(args.account_id):
        raise ControlPlaneError("Account ID must contain exactly 12 digits.")
    if not IDENTITY_NAME_RE.fullmatch(args.operator_name):
        raise ControlPlaneError(
            "Operator name must be an explicit IAM user or role name without a path."
        )
    if args.apply and args.confirm_aws_write_account != args.account_id:
        raise ControlPlaneError(
            "--apply requires --confirm-aws-write-account matching --account-id."
        )
    if args.apply and not (
        args.confirm_mfa_authenticated_session
        and args.confirm_temporary_session
    ):
        raise ControlPlaneError(
            "--apply requires explicit MFA-authenticated and temporary-session "
            "confirmations."
        )
    if not args.apply and any(
        (
            args.confirm_aws_write_account is not None,
            args.confirm_mfa_authenticated_session,
            args.confirm_temporary_session,
        )
    ):
        raise ControlPlaneError(
            "AWS write confirmations are only valid together with --apply."
        )
    return Config(
        account_id=args.account_id,
        operator_type=args.operator_type,
        operator_name=args.operator_name,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan the frozen AWS reference-demo IAM control plane. "
            "AWS writes require both --apply and an exact account confirmation."
        )
    )
    parser.add_argument("operation", choices=("bootstrap", "teardown"))
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--operator-type", required=True, choices=("user", "role"))
    parser.add_argument("--operator-name", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enable AWS IAM reads and writes after fail-closed preflight.",
    )
    parser.add_argument(
        "--confirm-aws-write-account",
        help="Required with --apply; must exactly match --account-id.",
    )
    parser.add_argument(
        "--confirm-mfa-authenticated-session",
        action="store_true",
        help="Required with --apply; confirms the current session used MFA.",
    )
    parser.add_argument(
        "--confirm-temporary-session",
        action="store_true",
        help="Required with --apply; confirms credentials are temporary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        config = _validated_config(args)
        plan = build_plan(args.operation, config)
        if not args.apply:
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 0

        client = AwsCli()
        _verify_apply_caller(config, client)
        if args.operation == "bootstrap":
            bootstrap(config, client)
        else:
            teardown(config, client)
        print(
            json.dumps(
                {
                    "status": "completed",
                    "mode": "apply",
                    "operation": args.operation,
                    "account_id": config.account_id,
                    "operator_identity": _operator_reference(config),
                },
                sort_keys=True,
            )
        )
        return 0
    except ControlPlaneError as exc:
        print(f"status=refused reason={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
