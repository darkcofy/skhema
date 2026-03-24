"""Tests for the readiness rules engine."""
import os
import pytest

from scripts.readiness import (
    load_rules,
    evaluate_artifact,
    evaluate_all,
    compute_stage_completion,
    ArtifactStatus,
)


@pytest.fixture
def rules_path():
    """Path to the real artifacts.yaml rules file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "rules", "artifacts.yaml"
    )


@pytest.fixture
def workspace_ready(tmp_path):
    """Create a workspace with enough content for engagement_brief to be READY."""
    ws = tmp_path / "ontology"
    (ws / "00_scope").mkdir(parents=True)

    # engagement.md with required sections
    (ws / "00_scope" / "engagement.md").write_text(
        "# Engagement\n\n"
        "## domain\nPayments platform.\n\n"
        "## outcomes\nCanonical model, glossary.\n\n"
        "## out_of_scope\nReporting, BI.\n"
    )

    # stakeholders.yaml with 2 entries
    (ws / "00_scope" / "stakeholders.yaml").write_text(
        "- name: Alice\n  role: PM\n- name: Bob\n  role: Dev\n"
    )
    return ws


@pytest.fixture
def workspace_partial(tmp_path):
    """Create a workspace where engagement_brief is PARTIAL."""
    ws = tmp_path / "ontology"
    (ws / "00_scope").mkdir(parents=True)

    # engagement.md with only one required section
    (ws / "00_scope" / "engagement.md").write_text(
        "# Engagement\n\n## domain\nPayments.\n"
    )

    # stakeholders.yaml with entries
    (ws / "00_scope" / "stakeholders.yaml").write_text(
        "- name: Alice\n  role: PM\n"
    )
    return ws


@pytest.fixture
def workspace_blocked(tmp_path):
    """Create a workspace where engagement_brief is BLOCKED."""
    ws = tmp_path / "ontology"
    (ws / "00_scope").mkdir(parents=True)
    # No files created
    return ws


class TestLoadRules:
    def test_loads_artifacts(self, rules_path):
        rules = load_rules(rules_path)
        assert "engagement_brief" in rules
        assert "draft_glossary" in rules
        assert "concept_map" in rules
        assert rules["engagement_brief"]["name"] == "Engagement Brief"

    def test_has_required_fields(self, rules_path):
        rules = load_rules(rules_path)
        for key, artifact in rules.items():
            assert "name" in artifact
            assert "stage" in artifact
            assert "output" in artifact
            assert "requires" in artifact


class TestEvaluateArtifact:
    def test_ready(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        status = evaluate_artifact(rules["engagement_brief"], str(workspace_ready))
        assert status.state == "READY"

    def test_partial(self, rules_path, workspace_partial):
        rules = load_rules(rules_path)
        status = evaluate_artifact(rules["engagement_brief"], str(workspace_partial))
        assert status.state == "PARTIAL"
        assert len(status.missing) > 0

    def test_blocked(self, rules_path, workspace_blocked):
        rules = load_rules(rules_path)
        status = evaluate_artifact(rules["engagement_brief"], str(workspace_blocked))
        assert status.state == "BLOCKED"


class TestEvaluateAll:
    def test_returns_all_artifacts(self, rules_path, workspace_ready):
        rules = load_rules(rules_path)
        results = evaluate_all(rules, str(workspace_ready))
        assert "engagement_brief" in results
        assert "draft_glossary" in results


class TestStageCompletion:
    def test_full_completion(self, rules_path, workspace_ready):
        """Stage 0 with all files filled should be > 0%."""
        rules = load_rules(rules_path)
        pct = compute_stage_completion(0, rules, str(workspace_ready))
        assert pct > 0

    def test_empty_workspace(self, rules_path, workspace_blocked):
        """Stage 0 with no files should be 0%."""
        rules = load_rules(rules_path)
        pct = compute_stage_completion(0, rules, str(workspace_blocked))
        assert pct == 0
