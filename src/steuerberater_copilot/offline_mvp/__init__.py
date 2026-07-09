"""Offline MVP building blocks without productive integrations."""

from .ai_workflow import SyntheticAIWorkflowOutput, build_synthetic_ai_workflow
from .models import (
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    ReviewGateDecision,
    ReviewGateStatus,
    ReviewStatus,
    RiskClassification,
    RiskLevel,
    SyntheticDocument,
    WorkflowOutput,
)
from .prompt_builder import build_synthetic_model_request
from .prompt_definition import (
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
    VersionedPromptDefinition,
)
from .structured_output import StructuredDraftOutput
from .structured_output_parser import (
    StructuredDraftOutputParseError,
    parse_structured_draft_output,
)
from .structured_output_validator import (
    StructuredDraftOutputValidationError,
    validate_structured_draft_output,
)
from .workflow import build_mock_workflow, classify_internal_risk, run_human_review_gate

__all__ = [
    "DraftPackage",
    "GatewayDecision",
    "GatewayResult",
    "IntakeCase",
    "RiskClassification",
    "RiskLevel",
    "ReviewGateDecision",
    "ReviewGateStatus",
    "ReviewStatus",
    "SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1",
    "StructuredDraftOutput",
    "StructuredDraftOutputParseError",
    "StructuredDraftOutputValidationError",
    "SyntheticAIWorkflowOutput",
    "SyntheticDocument",
    "VersionedPromptDefinition",
    "WorkflowOutput",
    "build_synthetic_ai_workflow",
    "build_synthetic_model_request",
    "build_mock_workflow",
    "classify_internal_risk",
    "parse_structured_draft_output",
    "run_human_review_gate",
    "validate_structured_draft_output",
]
