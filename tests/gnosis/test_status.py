"""Tests for the gnosis status command."""
import os
import pytest

from gnosis.readiness import load_rules, STAGE_NAMES
from gnosis.status import compute_status, format_status, validate_workspace


@pytest.fixture
def rules_path():
    """Path to the real artifacts.yaml rules file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "gnosis",
        "rules", "artifacts.yaml"
    )


@pytest.fixture
def workspace_ready(tmp_path):
    """Workspace with stage 0 files filled in."""
    ws = tmp_path / "ontology"
    (ws / "00_scope").mkdir(parents=True)
    (ws / "00_scope" / "engagement.md").write_text(
        "# Engagement\n\n"
        "## domain\nPayments platform.\n\n"
        "## outcomes\nCanonical model, glossary.\n\n"
        "## out_of_scope\nReporting, BI.\n"
    )
    (ws / "00_scope" / "stakeholders.yaml").write_text(
        "- name: Alice\n  role: PM\n- name: Bob\n  role: Dev\n"
    )
    return ws


@pytest.fixture
def workspace_empty(tmp_path):
    """Workspace with stage directories but no content."""
    ws = tmp_path / "ontology"
    for stage in ["00_scope", "01_language", "02_concepts",
                   "03_mappings", "04_behavior", "05_formalization"]:
        (ws / stage).mkdir(parents=True)
    (ws / "generated" / "reports").mkdir(parents=True)
    (ws / "generated" / "glossary").mkdir(parents=True)
    (ws / "generated" / "diagrams").mkdir(parents=True)
    (ws / "workspace.yaml").write_text("domain: test\n")
    return ws


class TestStageNames:
    def test_has_behavior_and_constraints(self):
        """STAGE_NAMES must include 'Behavior & Constraints'."""
        assert "Behavior & Constraints" in STAGE_NAMES

    def test_has_six_stages(self):
        assert len(STAGE_NAMES) == 6


class TestComputeStatus:
    def test_returns_stages_and_artifacts(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        assert "stages" in status
        assert "artifacts" in status
        assert len(status["stages"]) == 6

    def test_stage_completion_range(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        for stage in status["stages"]:
            assert 0 <= stage["completion_pct"] <= 100

    def test_artifact_states_valid(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        for key, art_status in status["artifacts"].items():
            assert art_status.state in ("READY", "PARTIAL", "BLOCKED")


class TestFormatStatus:
    def test_contains_stage_header(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        output = format_status(status, rules)
        assert "Stage Completion" in output

    def test_contains_artifact_header(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        output = format_status(status, rules)
        assert "Artifact Readiness" in output

    def test_contains_stage_names(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        output = format_status(status, rules)
        assert "Setup" in output
        assert "Behavior & Constraints" in output

    def test_contains_artifact_names(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        output = format_status(status, rules)
        assert "Engagement Brief" in output
        assert "Draft Glossary" in output

    def test_shows_ready_state(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_ready))
        output = format_status(status, rules)
        assert "READY" in output

    def test_empty_workspace_shows_blocked(self, rules_path, workspace_empty):
        rules = load_rules(rules_path)
        status = compute_status(rules, str(workspace_empty))
        output = format_status(status, rules)
        assert "BLOCKED" in output


class TestValidateWorkspace:
    def test_valid_workspace(self, workspace_empty):
        issues = validate_workspace(str(workspace_empty))
        assert len(issues) == 0

    def test_missing_workspace_yaml(self, tmp_path):
        ws = tmp_path / "ontology"
        ws.mkdir()
        issues = validate_workspace(str(ws))
        assert any("workspace.yaml" in i for i in issues)

    def test_missing_stage_dirs(self, tmp_path):
        ws = tmp_path / "ontology"
        ws.mkdir()
        (ws / "workspace.yaml").write_text("domain: test\n")
        issues = validate_workspace(str(ws))
        assert any("stage directory" in i for i in issues)

    def test_missing_generated_dirs(self, tmp_path):
        ws = tmp_path / "ontology"
        for stage in ["00_scope", "01_language", "02_concepts",
                       "03_mappings", "04_behavior", "05_formalization"]:
            (ws / stage).mkdir(parents=True)
        (ws / "workspace.yaml").write_text("domain: test\n")
        issues = validate_workspace(str(ws))
        assert any("generated/" in i for i in issues)
