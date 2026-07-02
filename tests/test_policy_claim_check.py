import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "policy_claim_check.py"
SPEC = importlib.util.spec_from_file_location("policy_claim_check", SCRIPT_PATH)
policy_claim_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = policy_claim_check
SPEC.loader.exec_module(policy_claim_check)


def write_markdown(tmp_path, text):
    path = tmp_path / "sample.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_allows_neutral_policy_text(tmp_path):
    path = write_markdown(
        tmp_path,
        "Alle steuerlich relevanten Outputs bleiben Entwuerfe und benoetigen Human Review.\n",
    )

    assert policy_claim_check.check_file(path) == []


def test_blocks_compliance_guarantee_claim(tmp_path):
    path = write_markdown(tmp_path, "Das System ist DSGVO-konform.\n")

    findings = policy_claim_check.check_file(path)

    assert len(findings) == 1
    assert findings[0].label == "DSGVO-konform"


def test_blocks_autonomous_tax_advisor_wording(tmp_path):
    path = write_markdown(tmp_path, "This is an autonomous tax advisor for clients.\n")

    findings = policy_claim_check.check_file(path)

    assert len(findings) == 1
    assert findings[0].label == "autonomous tax advisor"


def test_blocks_final_risk_classification_wording(tmp_path):
    path = write_markdown(tmp_path, "The output provides a final risk classification.\n")

    findings = policy_claim_check.check_file(path)

    assert len(findings) == 1
    assert findings[0].label == "final risk classification"


def test_allows_negative_context_for_project_boundary(tmp_path):
    path = write_markdown(tmp_path, "Dieses Projekt ist kein KI-Steuerberater.\n")

    assert policy_claim_check.check_file(path) == []


def test_ignores_pytest_cache_markdown_files(tmp_path):
    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    ignored_path = cache_dir / "README.md"
    ignored_path.write_text("Das System ist DSGVO-konform.\n", encoding="utf-8")

    files = policy_claim_check.markdown_files(tmp_path)
    findings = policy_claim_check.check_paths(files)

    assert ignored_path not in files
    assert findings == []
