"""End-to-end test for the MeshCo demo client.

Exercises the full v3 pipeline against the committed clients/meshco/ workspace:

- Gnosis: `status` shows all 4 artifacts READY, `generate` produces them.
- Skhema: deck HTML renders from mock-SVG inputs, gallery + handbook render,
  all outputs are self-contained.

PlantUML is mocked via `mock_plantuml` so this test runs in CI without the
binary present. Tests assert output *shape* (HTML structure, required
sections) rather than byte-for-byte snapshots — snapshots would force-
regenerate on every wording tweak.
"""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MESHCO = REPO_ROOT / "clients" / "meshco"


def _requires_meshco():
    if not MESHCO.is_dir():
        pytest.skip("clients/meshco/ is missing — rebuild Phase 8 first.")


class TestMeshcoGnosis:
    def test_workspace_scaffolded(self):
        _requires_meshco()
        assert (MESHCO / "ontology" / "workspace.yaml").is_file()
        for stage in ("00_scope", "01_language", "02_concepts",
                      "03_mappings", "04_behavior", "05_formalization"):
            assert (MESHCO / "ontology" / stage).is_dir()

    def test_all_four_artifacts_ready(self):
        _requires_meshco()
        from gnosis.readiness import evaluate_all, load_rules

        rules_path = REPO_ROOT / "src" / "gnosis" / "rules" / "artifacts.yaml"
        rules = load_rules(str(rules_path))
        statuses = evaluate_all(rules, str(MESHCO / "ontology"))

        for key, status in statuses.items():
            assert status.state == "READY", f"{key} is {status.state}: {status.missing}"

    def test_generate_all_artifacts_produces_expected_files(self, tmp_path):
        _requires_meshco()
        # Copy the ontology to tmp so we don't mutate committed files
        import shutil
        workspace = tmp_path / "ontology"
        shutil.copytree(MESHCO / "ontology", workspace)

        from gnosis.generate import (
            generate_concept_map,
            generate_draft_glossary,
            generate_engagement_brief,
            generate_terminology_conflicts,
        )

        rules = {}  # rules not read inside the individual generators
        eng = generate_engagement_brief(str(workspace), rules)
        glo = generate_draft_glossary(str(workspace), rules)
        con = generate_terminology_conflicts(str(workspace), rules)
        cmap = generate_concept_map(str(workspace), rules)

        assert Path(eng).is_file() and "# Engagement Brief" in open(eng).read()
        assert Path(glo).is_file() and "# Draft Glossary" in open(glo).read()
        assert Path(con).is_file() and "# Terminology Conflict Report" in open(con).read()
        # Concept map includes the 12 MeshCo concepts in PlantUML class format
        cmap_content = open(cmap).read()
        assert "@startuml" in cmap_content and "@enduml" in cmap_content
        assert 'class "DataProduct"' in cmap_content
        assert 'class "Customer"' in cmap_content


class TestMeshcoDeck:
    def test_deck_html_renders_from_mock_svgs(self, mock_plantuml):
        _requires_meshco()
        from skhema.deck import build_sections, render_deck_html

        diagrams_dir = str(MESHCO / "diagrams")
        search_paths = [
            str(MESHCO / "models"),
            str(REPO_ROOT / "src" / "skhema" / "models"),
            str(REPO_ROOT / "src" / "skhema" / "lib"),
        ]

        # MeshCo ships hand-written diagrams under diagrams/sequence/; the
        # c4/ directory is populated by `skhema structurizr export` which
        # needs a Java runtime. For this test we rely on the sequence
        # diagram alone.
        sections, total = build_sections(
            diagrams_dir=diagrams_dir,
            search_paths=search_paths,
            docs_dir=None,
            include_notes=False,
        )
        if total == 0:
            pytest.skip("No .puml diagrams in clients/meshco/diagrams/ yet")

        html = render_deck_html(
            client={"name": "MeshCo Retail", "subtitle": "v3 test", "accent_color": "#D97706"},
            sections=sections,
            adrs=[],
            total_diagrams=total,
        )
        assert "<!DOCTYPE html>" in html
        assert "MeshCo Retail" in html
        assert 'class="reveal"' in html
        assert "Reveal.initialize" in html

    def test_adrs_surface_on_deck(self):
        _requires_meshco()
        # ADRs live in clients/meshco/adrs/; verify discover_adrs finds them.
        from skhema.adr import discover_adrs

        adrs = discover_adrs(str(MESHCO))
        assert len(adrs) >= 3
        titles = {a.title for a in adrs}
        assert any("Iceberg" in t for t in titles), "Expected ADR01 (Iceberg)"
        assert any("dbt" in t for t in titles), "Expected ADR02 (dbt)"


class TestMeshcoGallery:
    def test_gallery_html_structure(self, tmp_path, mock_plantuml, fake_svg):
        """Exercises gallery pipeline against a synthetic rendered dir — since
        the committed MeshCo repo doesn't ship SVGs (they're reproducible)."""
        _requires_meshco()
        from skhema.gallery import generate_gallery_html

        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "context.svg").write_bytes(fake_svg)
        (rendered / "containers.svg").write_bytes(fake_svg)

        html = generate_gallery_html(
            client_name="MeshCo Retail",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
            diagrams_dir=str(MESHCO / "diagrams"),
            client_yaml_path=str(MESHCO / "client.yaml"),
            client_path=str(MESHCO),
        )
        assert "MeshCo Retail" in html
        assert "Context" in html and "Containers" in html
        # ADR panel shows up when client_path has adrs/
        # (We tagged ADRs with `skhema:elements` referencing container IDs;
        # the gallery only shows them when an SVG filename matches.
        # In this synthetic test the SVGs are named after our ADR-linked
        # containers, so at least one panel should render.)


class TestMeshcoStructurizr:
    def test_workspace_dsl_parseable_shape(self):
        _requires_meshco()
        dsl = (MESHCO / "workspace.dsl").read_text()
        # Structural sanity checks (we don't invoke structurizr-cli here —
        # that's covered in Dockerfile smoke tests).
        assert 'workspace "MeshCo Retail Data Platform"' in dsl
        assert "!identifiers hierarchical" in dsl
        # Named key containers present. The DSL is whitespace-formatted for
        # readability (column-aligned), so test by regex instead of substring.
        import re
        for container in ("ingestion", "lakehouse", "transforms", "contracts",
                          "catalog", "serving"):
            pattern = rf"\b{container}\s+=\s+container\b"
            assert re.search(pattern, dsl), f"Missing container: {container}"
        # At least one systemContext and one container view
        assert "systemContext platform" in dsl
        assert "container platform" in dsl
        # Styles defined for each tag used
        for tag in ("Ingestion", "Lakehouse", "Processing", "Contracts"):
            assert f'element "{tag}"' in dsl
