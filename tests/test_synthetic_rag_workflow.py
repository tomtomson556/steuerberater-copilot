import json
from unittest.mock import Mock

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
import steuerberater_copilot.offline_mvp.rag_workflow as rag_workflow
from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelInvocationPolicyViolationError,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.offline_mvp._response_markers import (
    DRAFT_REVIEW_DISCLAIMER,
    NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER,
    PRODUCTIVE_TRANSMISSION_MARKER,
    TAX_ADVICE_MARKER,
)
from steuerberater_copilot.offline_mvp.grounded_draft import (
    GroundedDraft,
    GroundedDraftCitation,
)
from steuerberater_copilot.offline_mvp.grounded_draft_parser import (
    GroundedDraftParseError,
)
from steuerberater_copilot.offline_mvp.grounded_draft_validator import (
    GroundedDraftValidationError,
)
from steuerberater_copilot.offline_mvp.model_invocation import (
    SYNTHETIC_RAG_MODEL_INVOCATION_POLICY,
)
from steuerberater_copilot.offline_mvp.models import (
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    MockRiskSignal,
    ReviewStatus,
    RiskLevel,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.prompt_builder import (
    build_synthetic_grounded_model_request,
)
from steuerberater_copilot.offline_mvp.rag_workflow import (
    SyntheticRAGWorkflowOutput,
    build_synthetic_rag_workflow,
)
from steuerberater_copilot.offline_mvp.structured_output import StructuredDraftOutput
from steuerberater_copilot.offline_mvp.structured_output_validator import (
    StructuredDraftOutputValidationError,
)
from steuerberater_copilot.rag import LocalDocumentRetriever, SourceDocument

RETRIEVAL_QUERY = "synthetic invoice retention"
RETRIEVAL_TOP_K = 1

SUPPORTING_PASSAGE = "Synthetic invoices remain available for internal review."

VALID_GROUNDED_CONTENT = json.dumps(
    {
        "summary_points": ["Synthetic grounded summary."],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": SUPPORTING_PASSAGE,
            }
        ],
    }
)

SEMANTICALLY_INVALID_GROUNDED_CONTENT = json.dumps(
    {
        "summary_points": [""],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": SUPPORTING_PASSAGE,
            }
        ],
    }
)

UNGROUNDED_CONTENT = json.dumps(
    {
        "summary_points": ["Synthetic grounded summary."],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": "Passage absent from retrieved documents.",
            }
        ],
    }
)


def test_synthetic_rag_workflow_runs_successful_controlled_path() -> None:
    case = _allowed_class_a_case()
    documents = _matching_source_documents()
    response = _model_response(VALID_GROUNDED_CONTENT)
    provider = FakeModelProvider(response)
    retriever = LocalDocumentRetriever(documents=documents)

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=retriever,
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.intake is case
    assert result.gateway.decision is GatewayDecision.ALLOW_DRAFT
    assert result.risk_classification.risk_level is RiskLevel.CLASS_A
    assert result.review_gate.allows_offline_mock_continuation is True
    assert result.retrieved_documents == (documents[0],)
    assert provider.requests == (
        build_synthetic_grounded_model_request(
            case,
            retrieved_documents=result.retrieved_documents,
        ),
    )
    assert result.model_response is response
    assert result.abstained_for_missing_evidence is False
    assert result.grounded_draft == GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=("Synthetic grounded summary.",),
            uncertainties=("Synthetic grounded uncertainty.",),
            review_questions=("Synthetic grounded review question?",),
        ),
        citations=(
            GroundedDraftCitation(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text=SUPPORTING_PASSAGE,
            ),
        ),
    )
    assert result.gateway.checks[5:] == (
        "response_keeps_draft_status",
        "response_requires_human_review_when_needed",
        "response_no_productive_transmission",
        "response_no_tax_advice_or_calculation_claim",
    )


def test_synthetic_rag_workflow_checks_complete_model_fields_with_disclaimers(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    checked_packages: list[DraftPackage] = []
    original_gateway_check = rag_workflow.run_response_gateway_check

    def response_gateway_spy(draft_package: DraftPackage) -> GatewayResult:
        checked_packages.append(draft_package)
        return original_gateway_check(draft_package)

    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        response_gateway_spy,
    )

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=_matching_retriever(),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert len(checked_packages) == 1
    checked_package = checked_packages[0]
    assert checked_package.review_status is ReviewStatus.DRAFT
    assert checked_package.risk_classification is result.risk_classification
    assert checked_package.review_required is False
    assert checked_package.summary_points == ("Synthetic grounded summary.",)
    assert checked_package.handoff_notes == ("Synthetic grounded uncertainty.",)
    assert checked_package.question_drafts == ("Synthetic grounded review question?",)
    assert checked_package.disclaimers == (
        DRAFT_REVIEW_DISCLAIMER,
        NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER,
    )


def test_synthetic_rag_workflow_passes_exact_retrieved_documents_to_prompt_and_validator(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    documents = _matching_source_documents()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    prompt_contexts: list[tuple[SourceDocument, ...]] = []
    validator_contexts: list[tuple[SourceDocument, ...]] = []
    original_prompt_builder = rag_workflow.build_synthetic_grounded_model_request
    original_validator = rag_workflow.validate_grounded_draft

    def prompt_spy(
        prompt_case: IntakeCase,
        *,
        retrieved_documents: tuple[SourceDocument, ...],
    ) -> ModelRequest:
        prompt_contexts.append(retrieved_documents)
        return original_prompt_builder(
            prompt_case,
            retrieved_documents=retrieved_documents,
        )

    def validator_spy(
        grounded_draft: GroundedDraft,
        *,
        retrieved_documents: tuple[SourceDocument, ...],
    ) -> None:
        validator_contexts.append(retrieved_documents)
        original_validator(
            grounded_draft,
            retrieved_documents=retrieved_documents,
        )

    monkeypatch.setattr(
        rag_workflow,
        "build_synthetic_grounded_model_request",
        prompt_spy,
    )
    monkeypatch.setattr(rag_workflow, "validate_grounded_draft", validator_spy)

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=LocalDocumentRetriever(documents=documents),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert prompt_contexts == [result.retrieved_documents]
    assert validator_contexts == [result.retrieved_documents]
    assert result.retrieved_documents == (documents[0],)
    assert prompt_contexts[0] is validator_contexts[0]


def test_synthetic_rag_workflow_uses_rag_invocation_boundary(monkeypatch) -> None:
    case = _allowed_class_a_case()
    response = _model_response(VALID_GROUNDED_CONTENT)
    provider = FakeModelProvider(response)
    calls: list[tuple[ModelRequest, object]] = []

    def invoke_spy(**kwargs):
        calls.append((kwargs["request"], kwargs["policy"]))
        return provider.generate(kwargs["request"])

    monkeypatch.setattr(rag_workflow, "invoke_model_if_allowed", invoke_spy)

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=_matching_retriever(),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    expected_request = build_synthetic_grounded_model_request(
        case,
        retrieved_documents=result.retrieved_documents,
    )
    assert calls == [(expected_request, SYNTHETIC_RAG_MODEL_INVOCATION_POLICY)]
    assert provider.requests == (expected_request,)
    assert result.model_response is response


def test_synthetic_rag_workflow_runs_boundaries_in_controlled_order(monkeypatch) -> None:
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    calls: list[str] = []
    original_parser = rag_workflow.parse_grounded_draft
    original_semantic_validator = rag_workflow.validate_structured_draft_output
    original_grounding_validator = rag_workflow.validate_grounded_draft
    original_gateway_check = rag_workflow.run_response_gateway_check

    def parse_spy(content: str) -> GroundedDraft:
        calls.append("parser")
        return original_parser(content)

    def semantic_spy(structured_draft: StructuredDraftOutput) -> None:
        calls.append("semantic_validator")
        original_semantic_validator(structured_draft)

    def grounding_spy(
        grounded_draft: GroundedDraft,
        *,
        retrieved_documents: tuple[SourceDocument, ...],
    ) -> None:
        calls.append("grounding_validator")
        original_grounding_validator(
            grounded_draft,
            retrieved_documents=retrieved_documents,
        )

    def response_gateway_spy(draft_package: DraftPackage) -> GatewayResult:
        calls.append("response_gateway")
        return original_gateway_check(draft_package)

    monkeypatch.setattr(rag_workflow, "parse_grounded_draft", parse_spy)
    monkeypatch.setattr(
        rag_workflow,
        "validate_structured_draft_output",
        semantic_spy,
    )
    monkeypatch.setattr(rag_workflow, "validate_grounded_draft", grounding_spy)
    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        response_gateway_spy,
    )

    build_synthetic_rag_workflow(
        _allowed_class_a_case(),
        provider=provider,
        retriever=_matching_retriever(),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert calls == [
        "parser",
        "semantic_validator",
        "grounding_validator",
        "response_gateway",
    ]


def test_synthetic_rag_workflow_gateway_stop_skips_retrieval_and_provider(
    monkeypatch,
) -> None:
    case = _missing_context_case()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    retriever = Mock(spec=LocalDocumentRetriever)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("prompt builder must not run after gateway stop")

    monkeypatch.setattr(
        rag_workflow,
        "build_synthetic_grounded_model_request",
        fail_if_called,
    )

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=retriever,
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.gateway.decision is GatewayDecision.ESCALATE
    assert result.review_gate.allows_offline_mock_continuation is False
    assert result.retrieved_documents == ()
    assert result.abstained_for_missing_evidence is False
    assert provider.requests == ()
    assert result.model_response is None
    assert result.grounded_draft is None
    retriever.retrieve.assert_not_called()


def test_synthetic_rag_workflow_review_gate_stop_skips_retrieval_and_provider(
    monkeypatch,
) -> None:
    case = _review_gate_stop_case()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    retriever = Mock(spec=LocalDocumentRetriever)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("prompt builder must not run after review-gate stop")

    monkeypatch.setattr(
        rag_workflow,
        "build_synthetic_grounded_model_request",
        fail_if_called,
    )

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=retriever,
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.gateway.decision is GatewayDecision.ALLOW_DRAFT
    assert result.risk_classification.risk_level is RiskLevel.CLASS_B
    assert result.review_gate.allows_offline_mock_continuation is False
    assert result.retrieved_documents == ()
    assert result.abstained_for_missing_evidence is False
    assert provider.requests == ()
    assert result.model_response is None
    assert result.grounded_draft is None
    retriever.retrieve.assert_not_called()


def test_synthetic_rag_workflow_abstains_without_provider_when_retrieval_empty() -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    retriever = LocalDocumentRetriever(
        documents=(
            SourceDocument(
                document_id="SYNTHETIC_SOURCE_UNRELATED",
                title="Payroll calendar overview",
                content="Completely unrelated payroll calendar body text.",
            ),
        )
    )

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=retriever,
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.gateway.decision is GatewayDecision.ALLOW_DRAFT
    assert result.review_gate.allows_offline_mock_continuation is True
    assert result.retrieved_documents == ()
    assert result.abstained_for_missing_evidence is True
    assert provider.requests == ()
    assert result.model_response is None
    assert result.grounded_draft is None


@pytest.mark.parametrize(
    ("claim", "expected_block_reason"),
    (
        (f"{TAX_ADVICE_MARKER} ist vorbereitet.", "tax_advice_suggested"),
        (
            f"{PRODUCTIVE_TRANSMISSION_MARKER} ist vorbereitet.",
            "productive_transmission_suggested",
        ),
    ),
)
def test_synthetic_rag_workflow_blocks_response_claims_and_withholds_grounded_draft(
    claim: str,
    expected_block_reason: str,
) -> None:
    case = _allowed_class_a_case()
    payload = {
        "summary_points": ["Synthetic grounded summary.", claim],
        "uncertainties": ["Synthetic grounded uncertainty."],
        "review_questions": ["Synthetic grounded review question?"],
        "citations": [
            {
                "summary_point_index": 0,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": SUPPORTING_PASSAGE,
            },
            {
                "summary_point_index": 1,
                "document_id": "SYNTHETIC_SOURCE_001",
                "supporting_text": SUPPORTING_PASSAGE,
            },
        ],
    }
    response = _model_response(json.dumps(payload))
    provider = FakeModelProvider(response)

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=_matching_retriever(),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.gateway.decision is GatewayDecision.BLOCK
    assert result.gateway.block_reasons == (expected_block_reason,)
    assert result.model_response is response
    assert result.grounded_draft is None
    assert result.abstained_for_missing_evidence is False


def test_synthetic_rag_workflow_response_gateway_escalation_withholds_grounded_draft(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    response = _model_response(VALID_GROUNDED_CONTENT)
    provider = FakeModelProvider(response)
    response_gateway = GatewayResult(
        decision=GatewayDecision.ESCALATE,
        checks=("response_requires_human_review_when_needed",),
        escalation_reasons=("synthetic_response_requires_review",),
    )
    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        lambda _draft_package: response_gateway,
    )

    result = build_synthetic_rag_workflow(
        case,
        provider=provider,
        retriever=_matching_retriever(),
        retrieval_query=RETRIEVAL_QUERY,
        top_k=RETRIEVAL_TOP_K,
    )

    assert result.gateway.decision is GatewayDecision.ESCALATE
    assert result.gateway.escalation_reasons == (
        "synthetic_response_requires_review",
    )
    assert result.model_response is response
    assert result.grounded_draft is None


def test_synthetic_rag_workflow_applies_response_policy_before_later_boundaries(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response("X" * 16_001))
    later_boundary_calls: list[str] = []

    def parse_spy(content: str):
        later_boundary_calls.append("parser")
        raise AssertionError("parser must not receive a policy-rejected response")

    monkeypatch.setattr(rag_workflow, "parse_grounded_draft", parse_spy)

    with pytest.raises(ModelInvocationPolicyViolationError):
        build_synthetic_rag_workflow(
            case,
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    assert later_boundary_calls == []
    assert provider.requests == (
        build_synthetic_grounded_model_request(
            case,
            retrieved_documents=_matching_source_documents()[:1],
        ),
    )


def test_synthetic_rag_workflow_propagates_parser_errors_unchanged(monkeypatch) -> None:
    provider = FakeModelProvider(_model_response('{"summary_points": []}'))
    response_gateway = Mock(
        side_effect=AssertionError("response gateway must not run after parser failure")
    )
    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        response_gateway,
    )

    with pytest.raises(GroundedDraftParseError):
        build_synthetic_rag_workflow(
            _allowed_class_a_case(),
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    response_gateway.assert_not_called()


def test_synthetic_rag_workflow_propagates_semantic_validation_errors_unchanged(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(SEMANTICALLY_INVALID_GROUNDED_CONTENT))
    grounding_validator = Mock(
        side_effect=AssertionError(
            "grounding validator must not run after semantic validation failure"
        )
    )
    response_gateway = Mock(
        side_effect=AssertionError(
            "response gateway must not run after semantic validation failure"
        )
    )
    monkeypatch.setattr(rag_workflow, "validate_grounded_draft", grounding_validator)
    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        response_gateway,
    )

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        build_synthetic_rag_workflow(
            case,
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    error = exc_info.value
    assert error.rule == "blank_entry"
    assert error.field_name == "summary_points"
    assert error.item_index == 0
    grounding_validator.assert_not_called()
    response_gateway.assert_not_called()


def test_synthetic_rag_workflow_propagates_grounding_validation_errors_unchanged(
    monkeypatch,
) -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(UNGROUNDED_CONTENT))
    response_gateway = Mock(
        side_effect=AssertionError(
            "response gateway must not run after grounding validation failure"
        )
    )
    monkeypatch.setattr(
        rag_workflow,
        "run_response_gateway_check",
        response_gateway,
    )

    with pytest.raises(GroundedDraftValidationError) as exc_info:
        build_synthetic_rag_workflow(
            case,
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    error = exc_info.value
    assert error.rule == "supporting_text_not_found"
    assert error.citation_index == 0
    response_gateway.assert_not_called()


def test_synthetic_rag_workflow_propagates_provider_errors_unchanged() -> None:
    class FailingProvider:
        def __init__(self) -> None:
            self.requests: list[ModelRequest] = []

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            raise RuntimeError("provider failed")

    case = _allowed_class_a_case()
    provider = FailingProvider()

    with pytest.raises(RuntimeError, match=r"^provider failed$"):
        build_synthetic_rag_workflow(
            case,
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    assert provider.requests == [
        build_synthetic_grounded_model_request(
            case,
            retrieved_documents=_matching_source_documents()[:1],
        )
    ]


def test_synthetic_rag_workflow_rejects_unauthorized_prompt(monkeypatch) -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(VALID_GROUNDED_CONTENT))
    invalid_request = ModelRequest(
        prompt_id="synthetic_structured_draft",
        prompt_version="1",
        system_prompt="Synthetic system prompt.",
        user_prompt="Synthetic user prompt.",
    )
    monkeypatch.setattr(
        rag_workflow,
        "build_synthetic_grounded_model_request",
        lambda _case, *, retrieved_documents: invalid_request,
    )

    with pytest.raises(ModelInvocationPolicyViolationError):
        build_synthetic_rag_workflow(
            case,
            provider=provider,
            retriever=_matching_retriever(),
            retrieval_query=RETRIEVAL_QUERY,
            top_k=RETRIEVAL_TOP_K,
        )

    assert provider.requests == ()


def test_synthetic_rag_workflow_public_export() -> None:
    assert offline_mvp.SyntheticRAGWorkflowOutput is SyntheticRAGWorkflowOutput
    assert offline_mvp.build_synthetic_rag_workflow is build_synthetic_rag_workflow
    assert "SyntheticRAGWorkflowOutput" in offline_mvp.__all__
    assert "build_synthetic_rag_workflow" in offline_mvp.__all__


def _allowed_class_a_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_300",
        client_ref="CLIENT_300",
        scenario="synthetic controlled RAG workflow fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_300",
                label="synthetic invoice descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        notes=("Internal synthetic preparation note.",),
    )


def _missing_context_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_301",
        client_ref="CLIENT_301",
        scenario="synthetic missing context fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_301",
                label="synthetic payment overview descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        missing_items=("Synthetic missing source reference.",),
    )


def _review_gate_stop_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_302",
        client_ref="CLIENT_302",
        scenario="synthetic document preparation fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_302",
                label="synthetic document descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        mock_risk_signals=(MockRiskSignal.DOCUMENT_PREPARATION.value,),
    )


def _matching_source_documents() -> tuple[SourceDocument, ...]:
    return (
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_001",
            title="Synthetic invoice retention note",
            content=f"Prefix. {SUPPORTING_PASSAGE} Suffix.",
        ),
        SourceDocument(
            document_id="SYNTHETIC_SOURCE_002",
            title="Synthetic invoice archive note",
            content="Secondary synthetic invoice archive content.",
        ),
    )


def _matching_retriever() -> LocalDocumentRetriever:
    return LocalDocumentRetriever(documents=_matching_source_documents())


def _model_response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="fake",
        model_name="fake-model",
    )
