"""Offline tests for the fail-closed reference-demo IAM control-plane tool."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "aws_reference_demo_iam_control_plane.py"
)
SPEC = importlib.util.spec_from_file_location(
    "aws_reference_demo_iam_control_plane",
    SCRIPT_PATH,
)
control_plane = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = control_plane
SPEC.loader.exec_module(control_plane)

ACCOUNT_ID = "123456789012"
OPERATOR_NAME = "reference-demo-operator"
BOOTSTRAP_ROLE_NAME = "reference-demo-iam-bootstrap"


def config(**overrides):
    values = {
        "account_id": ACCOUNT_ID,
        "operator_type": "user",
        "operator_name": OPERATOR_NAME,
        "bootstrap_role_name": None,
    }
    values.update(overrides)
    return control_plane.Config(**values)


def apply_config(**overrides):
    values = {
        "operator_type": "role",
        "bootstrap_role_name": BOOTSTRAP_ROLE_NAME,
    }
    values.update(overrides)
    return config(**values)


class FreshIam:
    def __init__(self):
        self.calls = []

    def call(self, *arguments, allow_not_found=False):
        self.calls.append((arguments, allow_not_found))
        operation = arguments[0]
        if operation == "get-user":
            return {
                "User": {
                    "UserName": OPERATOR_NAME,
                    "Arn": f"arn:aws:iam::{ACCOUNT_ID}:user/{OPERATOR_NAME}",
                }
            }
        if operation in {"get-policy", "get-role"}:
            assert allow_not_found is True
            return None
        if operation == "list-entities-for-policy":
            return {"PolicyGroups": [], "PolicyUsers": [], "PolicyRoles": []}
        return {}


class MismatchedPolicyIam:
    def __init__(self):
        self.calls = []

    def call(self, *arguments, allow_not_found=False):
        self.calls.append((arguments, allow_not_found))
        operation = arguments[0]
        if operation == "get-user":
            return {
                "User": {
                    "UserName": OPERATOR_NAME,
                    "Arn": f"arn:aws:iam::{ACCOUNT_ID}:user/{OPERATOR_NAME}",
                }
            }
        artifact = control_plane.POLICIES[0]
        if operation == "get-policy":
            return {
                "Policy": {
                    "Arn": artifact.arn(ACCOUNT_ID),
                    "Path": artifact.path,
                    "PolicyName": artifact.name,
                    "DefaultVersionId": "v1",
                }
            }
        if operation == "list-policy-versions":
            return {"Versions": [{"VersionId": "v1", "IsDefaultVersion": True}]}
        if operation == "get-policy-version":
            return {
                "PolicyVersion": {
                    "Document": {
                        "Version": "2012-10-17",
                        "Statement": [],
                    }
                }
            }
        raise AssertionError(f"Unexpected operation: {operation}")


class UnexpectedAttachmentIam:
    def __init__(self):
        self.calls = []

    def call(self, *arguments, allow_not_found=False):
        self.calls.append((arguments, allow_not_found))
        assert arguments[0] == "list-entities-for-policy"
        usage = arguments[arguments.index("--policy-usage-filter") + 1]
        if usage == "PermissionsPolicy":
            return {
                "PolicyGroups": [],
                "PolicyUsers": [],
                "PolicyRoles": [{"RoleName": "unexpected-role"}],
            }
        return {"PolicyGroups": [], "PolicyUsers": [], "PolicyRoles": []}


class AbsentTeardownIam:
    def __init__(self):
        self.calls = []

    def call_cloudformation(self, *arguments, allow_stack_absent=False):
        self.calls.append((("cloudformation", *arguments), allow_stack_absent))
        assert allow_stack_absent is True
        return None

    def call(self, *arguments, allow_not_found=False):
        self.calls.append((arguments, allow_not_found))
        if arguments[0] == "get-user":
            return {
                "User": {
                    "UserName": OPERATOR_NAME,
                    "Arn": f"arn:aws:iam::{ACCOUNT_ID}:user/{OPERATOR_NAME}",
                }
            }
        if arguments[0] in {"get-policy", "get-role"}:
            assert allow_not_found is True
            return None
        raise AssertionError(f"Unexpected operation: {arguments[0]}")


class StackPresentIam:
    def __init__(self):
        self.calls = []

    def call_cloudformation(self, *arguments, allow_stack_absent=False):
        self.calls.append((("cloudformation", *arguments), allow_stack_absent))
        return {"Stacks": [{"StackName": "steuerberater-copilot-reference-demo"}]}

    def call(self, *arguments, allow_not_found=False):
        raise AssertionError("IAM must not be called while the stack exists.")


class RootCaller:
    def call_sts(self, *arguments):
        assert arguments == ("get-caller-identity",)
        return {
            "Account": ACCOUNT_ID,
            "Arn": f"arn:aws:iam::{ACCOUNT_ID}:root",
        }


class AssumedBootstrapCaller:
    def __init__(
        self,
        *,
        account_id: str = ACCOUNT_ID,
        role_name: str = BOOTSTRAP_ROLE_NAME,
        session_name: str = "manual-session",
        response_account: str | None = None,
    ):
        self.account_id = account_id
        self.role_name = role_name
        self.session_name = session_name
        self.response_account = (
            account_id if response_account is None else response_account
        )

    def call_sts(self, *arguments):
        assert arguments == ("get-caller-identity",)
        return {
            "Account": self.response_account,
            "Arn": (
                f"arn:aws:sts::{self.account_id}:assumed-role/"
                f"{self.role_name}/{self.session_name}"
            ),
        }


class FixedArnCaller:
    def __init__(self, arn: str, *, account_id: str = ACCOUNT_ID):
        self.arn = arn
        self.account_id = account_id

    def call_sts(self, *arguments):
        assert arguments == ("get-caller-identity",)
        return {"Account": self.account_id, "Arn": self.arn}


def mutation_names(client):
    prefixes = (
        "attach-",
        "create-",
        "delete-",
        "detach-",
        "put-",
    )
    return [
        arguments[0]
        for arguments, _ in client.calls
        if arguments[0].startswith(prefixes)
    ]


def test_dry_run_outputs_plan_without_any_external_process(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "user",
                "--operator-name",
                OPERATOR_NAME,
            ]
        )

    assert result == 0
    run.assert_not_called()
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "dry-run"
    assert output["operation"] == "bootstrap"
    assert output["region"] == "eu-central-1"
    assert output["operator"]["name"] == OPERATOR_NAME
    assert all(len(step.get("sha256", "0" * 64)) == 64 for step in output["steps"])
    assert all(
        step.get("non_whitespace_characters", 0) <= 6_144
        for step in output["steps"]
    )


def test_apply_requires_matching_explicit_account_confirmation(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert "--confirm-aws-write-account" in capsys.readouterr().err


def test_apply_requires_mfa_and_temporary_session_confirmations(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--confirm-aws-write-account",
                ACCOUNT_ID,
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert "MFA-authenticated" in capsys.readouterr().err


def test_apply_rejects_root_caller() -> None:
    with pytest.raises(control_plane.ControlPlaneError, match="Root"):
        control_plane._verify_apply_caller(apply_config(), RootCaller())


def test_apply_accepts_exact_bootstrap_assumed_role_session() -> None:
    control_plane._verify_apply_caller(apply_config(), AssumedBootstrapCaller())


def test_apply_rejects_caller_account_mismatch() -> None:
    with pytest.raises(control_plane.ControlPlaneError, match="Caller account"):
        control_plane._verify_apply_caller(
            apply_config(),
            AssumedBootstrapCaller(
                account_id="999999999999",
                response_account="999999999999",
            ),
        )


def test_apply_rejects_wrong_bootstrap_role_name() -> None:
    with pytest.raises(
        control_plane.ControlPlaneError,
        match="does not match --bootstrap-role-name",
    ):
        control_plane._verify_apply_caller(
            apply_config(),
            AssumedBootstrapCaller(role_name="other-bootstrap-role"),
        )


def test_apply_rejects_bootstrap_role_equal_to_operator_role(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--bootstrap-role-name",
                OPERATOR_NAME,
                "--confirm-aws-write-account",
                ACCOUNT_ID,
                "--confirm-mfa-authenticated-session",
                "--confirm-temporary-session",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert "separate from the explicit operator role" in capsys.readouterr().err


def test_apply_rejects_bootstrap_role_equal_to_service_role(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--bootstrap-role-name",
                control_plane.SERVICE_ROLE_NAME,
                "--confirm-aws-write-account",
                ACCOUNT_ID,
                "--confirm-mfa-authenticated-session",
                "--confirm-temporary-session",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert "CloudFormation service role" in capsys.readouterr().err


def test_teardown_apply_rejects_without_post_delete_attestation(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "teardown",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--bootstrap-role-name",
                BOOTSTRAP_ROLE_NAME,
                "--confirm-aws-write-account",
                ACCOUNT_ID,
                "--confirm-mfa-authenticated-session",
                "--confirm-temporary-session",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert "--confirm-post-delete-verification" in capsys.readouterr().err


def test_post_delete_attestation_rejected_for_bootstrap_apply(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "bootstrap",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "role",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--bootstrap-role-name",
                BOOTSTRAP_ROLE_NAME,
                "--confirm-aws-write-account",
                ACCOUNT_ID,
                "--confirm-mfa-authenticated-session",
                "--confirm-temporary-session",
                "--confirm-post-delete-verification",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert (
        "--confirm-post-delete-verification is only valid with teardown --apply."
        in capsys.readouterr().err
    )


def test_post_delete_attestation_rejected_for_dry_run(capsys) -> None:
    with patch.object(control_plane.subprocess, "run") as run:
        result = control_plane.main(
            [
                "teardown",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "user",
                "--operator-name",
                OPERATOR_NAME,
                "--confirm-post-delete-verification",
            ]
        )

    assert result == 1
    run.assert_not_called()
    assert (
        "--confirm-post-delete-verification is only valid with teardown --apply."
        in capsys.readouterr().err
    )


def test_teardown_apply_accepts_post_delete_attestation_before_aws_calls(
    capsys,
) -> None:
    client = AbsentTeardownIam()
    with (
        patch.object(
            control_plane,
            "AwsCli",
            return_value=client,
        ),
        patch.object(
            control_plane,
            "_verify_apply_caller",
        ) as verify_caller,
    ):
        result = control_plane.main(
            [
                "teardown",
                "--account-id",
                ACCOUNT_ID,
                "--operator-type",
                "user",
                "--operator-name",
                OPERATOR_NAME,
                "--apply",
                "--bootstrap-role-name",
                BOOTSTRAP_ROLE_NAME,
                "--confirm-aws-write-account",
                ACCOUNT_ID,
                "--confirm-mfa-authenticated-session",
                "--confirm-temporary-session",
                "--confirm-post-delete-verification",
            ]
        )

    assert result == 0
    verify_caller.assert_called_once()
    assert mutation_names(client) == []
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "completed"
    assert output["operation"] == "teardown"
    assert output["mode"] == "apply"


def test_apply_rejects_iam_user_caller() -> None:
    with pytest.raises(control_plane.ControlPlaneError, match="assumed-role session"):
        control_plane._verify_apply_caller(
            apply_config(),
            FixedArnCaller(f"arn:aws:iam::{ACCOUNT_ID}:user/{OPERATOR_NAME}"),
        )


def test_apply_rejects_federated_user_caller() -> None:
    with pytest.raises(control_plane.ControlPlaneError, match="assumed-role session"):
        control_plane._verify_apply_caller(
            apply_config(),
            FixedArnCaller(
                f"arn:aws:sts::{ACCOUNT_ID}:federated-user/{OPERATOR_NAME}"
            ),
        )


def test_bootstrap_plan_matches_v23_phase_order() -> None:
    actions = [
        step["action"]
        for step in control_plane.build_plan("bootstrap", config())["steps"]
    ]
    assert actions == [
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-service-role",
        "attach-service-role-policy",
        "attach-service-role-policy",
        "attach-service-role-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "create-or-verify-policy",
        "attach-operator-policy",
        "attach-operator-policy",
        "attach-operator-policy",
        "attach-operator-policy",
        "set-operator-boundary",
    ]
    artifacts = [
        step["artifact"]
        for step in control_plane.build_plan("bootstrap", config())["steps"]
        if "artifact" in step
    ]
    assert artifacts == [
        "task-execution-boundary.json",
        "express-infrastructure-boundary.json",
        "express-infrastructure-acm-request-policy.json",
        "cloudformation-service-role-foundation-policy.json",
        "cloudformation-service-role-iam-lifecycle-policy.json",
        "cloudformation-service-role-policy.json",
        "cloudformation-service-role-boundary.json",
        "operator-cloudformation-policy.json",
        "operator-ecr-publisher-policy.json",
        "operator-secret-initializer-policy.json",
        "operator-verifier-policy.json",
        "operator-boundary.json",
    ]


def test_fresh_bootstrap_writes_only_the_fixed_control_plane_in_order() -> None:
    client = FreshIam()

    control_plane.bootstrap(config(), client)

    assert mutation_names(client) == [
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-role",
        "attach-role-policy",
        "attach-role-policy",
        "attach-role-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "create-policy",
        "attach-user-policy",
        "attach-user-policy",
        "attach-user-policy",
        "attach-user-policy",
        "put-user-permissions-boundary",
    ]
    flattened = " ".join(
        argument
        for arguments, _ in client.calls
        for argument in arguments
    )
    assert "create-user" not in flattened
    assert "create-access-key" not in flattened
    assert "create-policy-version" not in flattened


def test_existing_policy_hash_mismatch_refuses_before_any_write() -> None:
    client = MismatchedPolicyIam()

    with pytest.raises(control_plane.ControlPlaneError, match="hash mismatch"):
        control_plane.bootstrap(config(), client)

    assert mutation_names(client) == []


def test_unexpected_attachment_is_rejected() -> None:
    client = UnexpectedAttachmentIam()
    artifact = control_plane.POLICY_BY_KEY["operator-verifier"]

    with pytest.raises(control_plane.ControlPlaneError, match="Unexpected"):
        control_plane._inspect_policy_entities(
            artifact,
            config(),
            client,
            require_exact=True,
        )

    assert mutation_names(client) == []


def test_teardown_is_resumable_after_all_expected_artifacts_are_absent() -> None:
    client = AbsentTeardownIam()

    control_plane.teardown(config(), client)

    assert mutation_names(client) == []


def test_teardown_refuses_before_iam_changes_while_stack_exists() -> None:
    client = StackPresentIam()

    with pytest.raises(control_plane.ControlPlaneError, match="stack still exists"):
        control_plane.teardown(config(), client)

    assert mutation_names(client) == []


def test_teardown_plan_reflects_exact_reverse_dependency_order() -> None:
    steps = control_plane.build_plan("teardown", config())["steps"]
    assert steps[0]["action"] == (
        "preflight-stack-absence-exact-hashes-attachments-and-dependencies"
    )
    assert [step["action"] for step in steps[1:5]] == [
        "detach-operator-policy",
        "detach-operator-policy",
        "detach-operator-policy",
        "detach-operator-policy",
    ]
    assert [step["action"] for step in steps[5:10]] == [
        "remove-operator-boundary",
        "detach-service-role-policy",
        "detach-service-role-policy",
        "detach-service-role-policy",
        "delete-service-role",
    ]
    deleted_artifacts = [
        step["artifact"] for step in steps if step["action"] == "delete-policy"
    ]
    assert deleted_artifacts == [
        "cloudformation-service-role-foundation-policy.json",
        "cloudformation-service-role-iam-lifecycle-policy.json",
        "cloudformation-service-role-policy.json",
        "cloudformation-service-role-boundary.json",
        "task-execution-boundary.json",
        "express-infrastructure-boundary.json",
        "express-infrastructure-acm-request-policy.json",
        "operator-cloudformation-policy.json",
        "operator-ecr-publisher-policy.json",
        "operator-secret-initializer-policy.json",
        "operator-verifier-policy.json",
        "operator-boundary.json",
    ]


def test_aws_cli_boundary_uses_argv_and_parses_mocked_json() -> None:
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"Policy": {"PolicyName": "synthetic"}}',
        stderr="",
    )
    with patch.object(control_plane.subprocess, "run", return_value=completed) as run:
        response = control_plane.AwsCli().call(
            "get-policy",
            "--policy-arn",
            "arn:aws:iam::123456789012:policy/synthetic",
        )

    assert response == {"Policy": {"PolicyName": "synthetic"}}
    command = run.call_args.args[0]
    assert command[:3] == ["aws", "iam", "get-policy"]
    assert run.call_args.kwargs == {
        "check": False,
        "capture_output": True,
        "text": True,
    }
