"""Tests for the gnosis init command — workspace scaffolding."""
import os
import pytest

from gnosis.init import scaffold_workspace


@pytest.fixture
def repo_root(tmp_path):
    """Create a minimal repo structure with gnosis templates."""
    # Create clients dir (marker for repo root)
    (tmp_path / "clients").mkdir()

    # Create gnosis templates dir with workspace.yaml
    templates = tmp_path / "src" / "gnosis" / "templates"
    templates.mkdir(parents=True)
    (templates / "workspace.yaml").write_text(
        'domain: "{{DOMAIN}}"\ninitialized: "{{DATE}}"\n'
    )

    # Create a stage template directory with a sample file
    scope = templates / "00_scope"
    scope.mkdir()
    (scope / "engagement.md").write_text(
        "# {{CLIENT}} Engagement\n\n## domain\n{{DOMAIN}}\n"
    )
    (scope / "stakeholders.yaml").write_text(
        "# Stakeholders for {{CLIENT}}\n"
    )

    return tmp_path


class TestScaffoldWorkspace:
    def test_creates_client_dir(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        assert os.path.isdir(client_dir)

    def test_creates_client_yaml(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        client_yaml = os.path.join(client_dir, "client.yaml")
        assert os.path.isfile(client_yaml)
        content = open(client_yaml).read()
        assert 'name: "Acme Corp"' in content

    def test_creates_ontology_workspace(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        ontology = os.path.join(client_dir, "ontology")
        assert os.path.isdir(ontology)
        assert os.path.isfile(os.path.join(ontology, "workspace.yaml"))

    def test_workspace_yaml_substitution(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp", domain="Payments")
        ws = os.path.join(client_dir, "ontology", "workspace.yaml")
        content = open(ws).read()
        assert "Payments" in content
        assert "{{DOMAIN}}" not in content
        assert "{{DATE}}" not in content

    def test_template_files_copied(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        engagement = os.path.join(client_dir, "ontology", "00_scope", "engagement.md")
        assert os.path.isfile(engagement)
        content = open(engagement).read()
        assert "Acme Corp" in content
        assert "{{CLIENT}}" not in content

    def test_generated_dirs_created(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        gen = os.path.join(client_dir, "ontology", "generated")
        assert os.path.isdir(os.path.join(gen, "reports"))
        assert os.path.isdir(os.path.join(gen, "glossary"))
        assert os.path.isdir(os.path.join(gen, "diagrams"))

    def test_stage_dirs_created(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        ontology = os.path.join(client_dir, "ontology")
        for stage in ["00_scope", "01_language", "02_concepts",
                       "03_mappings", "04_behavior", "05_formalization"]:
            assert os.path.isdir(os.path.join(ontology, stage))

    def test_duplicate_client_exits(self, repo_root):
        scaffold_workspace(str(repo_root), "acme-corp")
        with pytest.raises(SystemExit):
            scaffold_workspace(str(repo_root), "acme-corp")

    def test_domain_defaults_to_display_name(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp")
        client_yaml = os.path.join(client_dir, "client.yaml")
        content = open(client_yaml).read()
        assert 'domain: "Acme Corp"' in content

    def test_custom_domain(self, repo_root):
        client_dir = scaffold_workspace(str(repo_root), "acme-corp", domain="E-Commerce")
        client_yaml = os.path.join(client_dir, "client.yaml")
        content = open(client_yaml).read()
        assert 'domain: "E-Commerce"' in content
