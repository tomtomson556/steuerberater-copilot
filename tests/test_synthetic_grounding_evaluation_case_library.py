import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    GroundingEvaluationCase,
    SyntheticEvaluationFixture,
    assess_grounding_evaluation_case,
    build_synthetic_evaluation_case_library,
    build_synthetic_grounding_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
)
from steuerberater_copilot.offline_mvp import GroundedDraft, GroundedDraftCitation
from steuerberater_copilot.rag import SourceDocument

EXPECTED_GROUNDING_EVALUATION_IDS = (
    "EVAL_GROUNDING_BASELINE_FULL_MATCH",
    "EVAL_GROUNDING_BASELINE_PARTIAL_COVERAGE",
    "EVAL_GROUNDING_BASELINE_WRONG_PASSAGE",
    "EVAL_GROUNDING_BASELINE_WRONG_SOURCE",
    "EVAL_GROUNDING_BASELINE_MISSING_CITATIONS",
    "EVAL_GROUNDING_BASELINE_NO_ACCEPTABLE_EVIDENCE",
    "EVAL_GROUNDING_BASELINE_ALTERNATIVE_EVIDENCE",
    "EVAL_GROUNDING_BASELINE_MIXED_CITATIONS",
    "EVAL_GROUNDING_BASELINE_EMPTY_DRAFT",
)

EXPECTED_RATES = {
    "EVAL_GROUNDING_BASELINE_FULL_MATCH": (1.0, 1.0, 1.0, 0.0),
    "EVAL_GROUNDING_BASELINE_PARTIAL_COVERAGE": (0.5, 1.0, 1.0, 0.5),
    "EVAL_GROUNDING_BASELINE_WRONG_PASSAGE": (1.0, 1.0, 0.0, 1.0),
    "EVAL_GROUNDING_BASELINE_WRONG_SOURCE": (1.0, 0.0, 0.0, 1.0),
    "EVAL_GROUNDING_BASELINE_MISSING_CITATIONS": (0.0, None, None, 1.0),
    "EVAL_GROUNDING_BASELINE_NO_ACCEPTABLE_EVIDENCE": (1.0, 0.0, 0.0, 1.0),
    "EVAL_GROUNDING_BASELINE_ALTERNATIVE_EVIDENCE": (1.0, 1.0, 1.0, 0.0),
    "EVAL_GROUNDING_BASELINE_MIXED_CITATIONS": (1.0, 2 / 3, 1 / 3, 0.5),
    "EVAL_GROUNDING_BASELINE_EMPTY_DRAFT": (None, None, None, None),
}


def test_library_returns_tuple_with_exact_stable_order() -> None:
    cases = build_synthetic_grounding_evaluation_case_library()
    evaluation_ids = tuple(case.evaluation_id for case in cases)

    assert isinstance(cases, tuple)
    assert len(cases) == 9
    assert evaluation_ids == EXPECTED_GROUNDING_EVALUATION_IDS
    assert all(isinstance(case, GroundingEvaluationCase) for case in cases)
    assert len(evaluation_ids) == len(set(evaluation_ids))


def test_separate_library_builds_share_no_nested_instances() -> None:
    first_library = build_synthetic_grounding_evaluation_case_library()
    second_library = build_synthetic_grounding_evaluation_case_library()

    assert first_library is not second_library
    for first_case, second_case in zip(first_library, second_library, strict=True):
        assert first_case is not second_case
        assert (
            first_case.candidate_grounded_draft
            is not second_case.candidate_grounded_draft
        )
        if first_case.source_documents:
            assert first_case.source_documents is not second_case.source_documents
        if first_case.acceptable_evidence:
            assert first_case.acceptable_evidence is not second_case.acceptable_evidence
        for first_document, second_document in zip(
            first_case.source_documents,
            second_case.source_documents,
            strict=True,
        ):
            assert first_document is not second_document
            assert isinstance(first_document, SourceDocument)
        for first_citation, second_citation in zip(
            first_case.candidate_grounded_draft.citations,
            second_case.candidate_grounded_draft.citations,
            strict=True,
        ):
            assert first_citation is not second_citation
            assert isinstance(first_citation, GroundedDraftCitation)
        for first_label, second_label in zip(
            first_case.acceptable_evidence,
            second_case.acceptable_evidence,
            strict=True,
        ):
            assert first_label is not second_label


def test_all_baseline_cases_assess_with_expected_rates() -> None:
    for case in build_synthetic_grounding_evaluation_case_library():
        assessment = assess_grounding_evaluation_case(case)
        expected = EXPECTED_RATES[case.evaluation_id]

        assert assessment.evaluation_case is case
        assert isinstance(case.candidate_grounded_draft, GroundedDraft)
        assert assessment.citation_coverage == expected[0]
        assert assessment.source_match_rate == expected[1]
        assert assessment.passage_match_rate == expected[2]
        assert assessment.unsupported_summary_point_rate == expected[3]


def test_wrong_passage_case_keeps_source_match_without_passage_match() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_WRONG_PASSAGE")
    assessment = assess_grounding_evaluation_case(case)

    assert assessment.source_matched_citation_indices == (0,)
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0,)


def test_wrong_source_case_rejects_identical_text_from_other_document() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_WRONG_SOURCE")
    citation = case.candidate_grounded_draft.citations[0]
    label = case.acceptable_evidence[0]
    assessment = assess_grounding_evaluation_case(case)

    assert citation.supporting_text == label.supporting_text
    assert citation.document_id != label.document_id
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0,)


def test_missing_citations_case_has_evidence_but_no_observed_citations() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_MISSING_CITATIONS")
    assessment = assess_grounding_evaluation_case(case)

    assert case.acceptable_evidence
    assert case.candidate_grounded_draft.citations == ()
    assert assessment.citation_covered_summary_point_indices == ()
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0,)


def test_no_acceptable_evidence_case_covers_but_does_not_support() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_NO_ACCEPTABLE_EVIDENCE")
    assessment = assess_grounding_evaluation_case(case)

    assert case.acceptable_evidence == ()
    assert case.candidate_grounded_draft.citations
    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0,)


def test_alternative_evidence_case_matches_second_label() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_ALTERNATIVE_EVIDENCE")
    citation = case.candidate_grounded_draft.citations[0]
    second_label = case.acceptable_evidence[1]
    assessment = assess_grounding_evaluation_case(case)

    assert len(case.acceptable_evidence) == 2
    assert citation.document_id == second_label.document_id
    assert citation.supporting_text == second_label.supporting_text
    assert assessment.passage_matched_citation_indices == (0,)
    assert assessment.unsupported_summary_point_indices == ()


def test_mixed_citations_case_keeps_expected_index_tuples() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_MIXED_CITATIONS")
    assessment = assess_grounding_evaluation_case(case)

    assert len(case.candidate_grounded_draft.citations) == 3
    assert assessment.citation_covered_summary_point_indices == (0, 1)
    assert assessment.source_matched_citation_indices == (0, 1)
    assert assessment.passage_matched_citation_indices == (0,)
    assert assessment.unsupported_summary_point_indices == (1,)


def test_empty_draft_case_has_empty_inputs_and_none_rates() -> None:
    case = _case("EVAL_GROUNDING_BASELINE_EMPTY_DRAFT")
    assessment = assess_grounding_evaluation_case(case)

    assert case.source_documents == ()
    assert case.candidate_grounded_draft.structured_draft.summary_points == ()
    assert case.candidate_grounded_draft.citations == ()
    assert case.acceptable_evidence == ()
    assert assessment.citation_covered_summary_point_indices == ()
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.citation_coverage is None
    assert assessment.source_match_rate is None
    assert assessment.passage_match_rate is None
    assert assessment.unsupported_summary_point_rate is None


def test_evaluation_package_exports_grounding_library_builder() -> None:
    assert (
        evaluation.build_synthetic_grounding_evaluation_case_library
        is build_synthetic_grounding_evaluation_case_library
    )
    assert "build_synthetic_grounding_evaluation_case_library" in evaluation.__all__


def test_existing_ai_and_retrieval_libraries_remain_unchanged() -> None:
    ai_fixtures = build_synthetic_evaluation_case_library()
    retrieval_cases = build_synthetic_retrieval_evaluation_case_library()

    assert isinstance(ai_fixtures, tuple)
    assert len(ai_fixtures) == 7
    assert tuple(
        fixture.evaluation_case.evaluation_id for fixture in ai_fixtures
    ) == (
        "EVAL_BASELINE_GATEWAY_BLOCK",
        "EVAL_BASELINE_GATEWAY_ESCALATION",
        "EVAL_BASELINE_REVIEW_GATE_STOP",
        "EVAL_BASELINE_STRUCTURED_DRAFT",
        "EVAL_BASELINE_PROVIDER_ERROR",
        "EVAL_BASELINE_PARSE_ERROR",
        "EVAL_BASELINE_VALIDATION_ERROR",
    )
    assert evaluation.SyntheticEvaluationFixture is SyntheticEvaluationFixture
    assert isinstance(retrieval_cases, tuple)
    assert len(retrieval_cases) == 4
    assert tuple(case.evaluation_id for case in retrieval_cases) == (
        "EVAL_RETRIEVAL_BASELINE_FULL_RECALL",
        "EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL",
        "EVAL_RETRIEVAL_BASELINE_ZERO_RECALL",
        "EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE",
    )
    assert (
        evaluation.build_synthetic_retrieval_evaluation_case_library
        is build_synthetic_retrieval_evaluation_case_library
    )


def _case(evaluation_id: str) -> GroundingEvaluationCase:
    cases = {
        case.evaluation_id: case
        for case in build_synthetic_grounding_evaluation_case_library()
    }
    return cases[evaluation_id]
