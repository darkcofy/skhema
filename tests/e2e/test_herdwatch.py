"""End-to-end test for the Herdwatch client workspace.

Marked `local_only` — Herdwatch is real client data and must not run in CI.
Run locally with: `pytest -m local_only`.

This test assumes the user has rebuilt `clients/herdwatch/` using the v3
stack (workspace.dsl + gnosis ontology). If the client doesn't exist,
the test is skipped with a message.
"""
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERDWATCH_DIR = REPO_ROOT / "clients" / "herdwatch"


pytestmark = pytest.mark.local_only


def _requires_herdwatch():
    if not HERDWATCH_DIR.is_dir():
        pytest.skip(
            "Herdwatch client not present locally — "
            "rebuild with v3 stack (workspace.dsl + gnosis init) to run this test."
        )


class TestHerdwatchWorkspace:
    def test_workspace_dsl_exists(self):
        _requires_herdwatch()
        assert (HERDWATCH_DIR / "workspace.dsl").is_file(), \
            "Expected clients/herdwatch/workspace.dsl (Structurizr DSL)"

    def test_ontology_scaffolded(self):
        _requires_herdwatch()
        ontology = HERDWATCH_DIR / "ontology"
        assert ontology.is_dir()
        for stage in ("00_scope", "01_language", "02_concepts",
                      "03_mappings", "04_behavior", "05_formalization"):
            assert (ontology / stage).is_dir(), f"Missing stage dir: {stage}"

    def test_client_yaml_valid(self):
        _requires_herdwatch()
        import yaml
        with open(HERDWATCH_DIR / "client.yaml") as f:
            data = yaml.safe_load(f) or {}
        assert data.get("name"), "client.yaml must have a name"
        assert data.get("accent_color"), "client.yaml must have an accent_color"
