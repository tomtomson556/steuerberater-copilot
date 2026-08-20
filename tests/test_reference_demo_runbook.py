"""Static, offline checks for the AWS reference-demo change-set-only runbook."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = ROOT / "docs" / "09-operations" / "aws-reference-demo-runbook.md"
GUARD_PATH = ROOT / "infra" / "cloudformation" / "guards" / "reference-demo.guard"

FIXED_STACK_TAGS = (
    "Key=Project,Value=steuerberater-copilot",
    "Key=Component,Value=reference-demo",
    "Key=Environment,Value=portfolio-test",
    "Key=ManagedBy,Value=cloudformation",
    "Key=Lifecycle,Value=ephemeral",
)


def load_runbook() -> str:
    assert RUNBOOK_PATH.is_file(), RUNBOOK_PATH
    return RUNBOOK_PATH.read_text(encoding="utf-8")


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
