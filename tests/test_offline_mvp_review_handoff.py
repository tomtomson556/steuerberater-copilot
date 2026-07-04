from steuerberater_copilot.offline_mvp.review_handoff import render_review_handoff
from steuerberater_copilot.offline_mvp.workflow import build_mock_workflow, load_fixture_cases

RISKY_CLAIMS = (
    "GoBD-compliant",
    "GoBD-konform",
    "rechtssicher",
    "revisionssicher",
    "ordnungsgem\u00e4\u00df archiviert",
    "ordnungsgemaess archiviert",
    "produktives Archiv",
    "finales steuerliches Dokument",
)


def test_review_handoff_marks_output_as_draft_review_artifact() -> None:
    handoff = _render_case("CASE_002")

    assert handoff.startswith("# Review Handoff\n")
    assert "Draft-/Review-Artefakt fuer den Offline-MVP. Nicht final." in handoff
    assert "## Closing Note" in handoff
    assert "menschliche Pruefung und Freigabe" in handoff


def test_review_handoff_avoids_risky_claims() -> None:
    for case_id in ("CASE_001", "CASE_002", "CASE_003", "CASE_004"):
        handoff = _render_case(case_id)

        for claim in RISKY_CLAIMS:
            assert claim not in handoff


def test_review_required_case_contains_questions_or_review_gate_hint() -> None:
    handoff = _render_case("CASE_001")

    assert "- Status: `requires_human_review`" in handoff
    assert "Bitte im Human Review intern klaeren" in handoff
    assert "Draft available: `False`" in handoff


def test_available_draft_case_remains_marked_for_review() -> None:
    handoff = _render_case("CASE_002")

    assert "- Status: `allowed_offline_mock_continuation`" in handoff
    assert "Draft available: `True`" in handoff
    assert "Draft-/Review-Artefakt" in handoff
    assert "Vor jeder fachlichen Nutzung" in handoff


def test_review_handoff_uses_existing_workflow_fields() -> None:
    handoff = _render_case("CASE_001")

    assert "- Case ID: `CASE_001`" in handoff
    assert "- Risk level: `C`" in handoff
    assert "- missing_fixture_context" in handoff
    assert "Keine automatische Rueckfragenkommunikation" in handoff
    assert "Keine Steuerberatung, keine Berechnung" in handoff


def _render_case(case_id: str) -> str:
    cases = {case.case_id: case for case in load_fixture_cases()}
    return render_review_handoff(build_mock_workflow(cases[case_id]))
