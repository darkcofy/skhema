import os



class TestGnosisPipeline:
    def test_init_creates_workspace(self, tmp_path):
        """scaffold_workspace creates the expected ontology structure."""
        from gnosis.init import scaffold_workspace

        # Create minimal gnosis templates required by scaffold_workspace
        gnosis_templates = tmp_path / "src" / "gnosis" / "templates"
        gnosis_templates.mkdir(parents=True)
        (gnosis_templates / "workspace.yaml").write_text(
            'domain: "{{DOMAIN}}"\ninitialized: "{{DATE}}"\n'
        )
        for stage in ["00_scope", "01_language", "02_concepts",
                      "03_mappings", "04_behavior", "05_formalization"]:
            (gnosis_templates / stage).mkdir()

        (tmp_path / "clients").mkdir()

        client_dir = scaffold_workspace(str(tmp_path), "test-domain", domain="Test Domain")
        ontology_dir = os.path.join(client_dir, "ontology")

        assert os.path.isdir(os.path.join(ontology_dir, "00_scope"))
        assert os.path.isdir(os.path.join(ontology_dir, "05_formalization"))
        assert os.path.isfile(os.path.join(ontology_dir, "workspace.yaml"))

    def test_status_on_fresh_workspace(self, tmp_path):
        """compute_status returns stages and artifacts for a fresh workspace."""
        from gnosis.init import scaffold_workspace
        from gnosis.readiness import load_rules
        from gnosis.status import compute_status

        # Create minimal gnosis templates
        gnosis_templates = tmp_path / "src" / "gnosis" / "templates"
        gnosis_templates.mkdir(parents=True)
        (gnosis_templates / "workspace.yaml").write_text(
            'domain: "{{DOMAIN}}"\ninitialized: "{{DATE}}"\n'
        )
        for stage in ["00_scope", "01_language", "02_concepts",
                      "03_mappings", "04_behavior", "05_formalization"]:
            (gnosis_templates / stage).mkdir()

        (tmp_path / "clients").mkdir()

        client_dir = scaffold_workspace(str(tmp_path), "test-domain", domain="Test Domain")
        workspace_path = os.path.join(client_dir, "ontology")

        # Load actual rules from gnosis/rules/artifacts.yaml
        rules_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "src", "gnosis", "rules", "artifacts.yaml"
        )
        rules = load_rules(rules_path)

        status = compute_status(rules, workspace_path)
        assert isinstance(status, dict)
        assert "stages" in status
        assert "artifacts" in status
