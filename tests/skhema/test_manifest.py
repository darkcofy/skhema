"""Tests for the shared manifest parser."""
import os
import pytest
from skhema.manifest import parse_manifest


class TestParseManifest:
    def test_parses_domains(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  storage:
    file: models/storage.puml
    elements:
      data_lake:
        type: ContainerDb
        description: "Raw + curated zones"
      data_warehouse:
        type: ContainerDb
        description: "Dimensional models"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        assert "storage" in result
        assert len(result["storage"]) == 2

    def test_element_fields(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  consumers:
    file: models/consumers.puml
    elements:
      data_analyst:
        type: Person
        description: "Queries data via BI/SQL tools"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        elem = result["consumers"][0]
        assert elem["id"] == "data_analyst"
        assert elem["type"] == "Person"
        assert elem["description"] == "Queries data via BI/SQL tools"

    def test_multiple_domains(self, tmp_path):
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text("""version: "1.0"

domains:
  consumers:
    file: models/consumers.puml
    elements:
      data_analyst:
        type: Person
        description: "Queries data"
  storage:
    file: models/storage.puml
    elements:
      data_lake:
        type: ContainerDb
        description: "Raw zones"

diagrams: []
""")
        result = parse_manifest(str(manifest))
        assert len(result) == 2
        assert "consumers" in result
        assert "storage" in result

    def test_real_manifest(self):
        """Test against the actual project manifest."""
        manifest_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "manifest.yaml"
        )
        if not os.path.isfile(manifest_path):
            pytest.skip("No manifest.yaml in project root")
        result = parse_manifest(manifest_path)
        assert len(result) == 11  # 11 domains
        # Spot-check a known element
        storage_ids = [e["id"] for e in result["storage"]]
        assert "data_lake" in storage_ids
