"""Tests for the gallery generator."""
import os
import pytest
from skhema.gallery import (
    discover_diagrams,
    group_by_type,
    generate_gallery_html,
    parse_client_yaml,
)


class TestDiscoverDiagrams:
    def test_finds_svg_files(self, tmp_path):
        rendered = tmp_path / "rendered"
        c4 = rendered / "c4"
        c4.mkdir(parents=True)
        (c4 / "diagram.svg").write_text("<svg></svg>")
        (c4 / "other.svg").write_text("<svg></svg>")
        result = discover_diagrams(str(rendered))
        assert len(result) == 2

    def test_ignores_non_svg(self, tmp_path):
        rendered = tmp_path / "rendered"
        rendered.mkdir()
        (rendered / "file.txt").write_text("not svg")
        result = discover_diagrams(str(rendered))
        assert len(result) == 0

    def test_empty_dir(self, tmp_path):
        rendered = tmp_path / "rendered"
        rendered.mkdir()
        result = discover_diagrams(str(rendered))
        assert len(result) == 0


class TestGroupByType:
    def test_groups_correctly(self):
        files = [
            "/r/c4/a.svg",
            "/r/c4/b.svg",
            "/r/sequence/c.svg",
            "/r/erd/d.svg",
        ]
        groups = group_by_type(files, "/r")
        assert len(groups["c4"]) == 2
        assert len(groups["sequence"]) == 1
        assert len(groups["erd"]) == 1

    def test_top_level_files(self):
        files = ["/r/orphan.svg"]
        groups = group_by_type(files, "/r")
        assert len(groups["other"]) == 1


class TestGenerateGalleryHtml:
    def test_returns_html_string(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        html = generate_gallery_html(
            client_name="Test Client",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
        )
        assert "<!DOCTYPE html>" in html
        assert "Test Client" in html

    def test_contains_svg_content(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect fill="red"/></svg>')
        html = generate_gallery_html(
            client_name="Acme",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
        )
        assert "<rect" in html

    def test_sections_by_type(self, tmp_path):
        rendered = tmp_path / "rendered"
        (rendered / "c4").mkdir(parents=True)
        (rendered / "sequence").mkdir(parents=True)
        (rendered / "c4" / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        (rendered / "sequence" / "b.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(rendered), history=0)
        assert "C4" in html
        assert "Sequence" in html


class TestParseClientYaml:
    def test_parses_name_and_sections(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: "Acme"\nsubtitle: "Platform"\nsections:\n  - c4\n  - sequence\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["name"] == "Acme"
        assert result["subtitle"] == "Platform"
        assert result["sections"] == ["c4", "sequence"]

    def test_optional_accent_color(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: "X"\naccent_color: "#FF0000"\nsections:\n  - erd\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["accent_color"] == "#FF0000"

    def test_defaults_when_missing(self, tmp_path):
        result = parse_client_yaml(str(tmp_path / "nonexistent.yaml"))
        assert result["name"] == ""
        assert result["sections"] == []
        assert result["accent_color"] == "#D97706"

    def test_no_quotes_in_values(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: Acme Corp\nsubtitle: Data Platform\nsections:\n  - c4\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["name"] == "Acme Corp"


class TestGalleryAdrIntegration:
    def test_gallery_shows_adr_links(self, tmp_path):
        from skhema.gallery import generate_gallery_html

        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "main.svg").write_text("<svg></svg>")

        adrs = tmp_path / "adrs"
        adrs.mkdir()
        (adrs / "ADR01-test.md").write_text(
            "# ADR01: Test Decision\n\n## Status\nAccepted\n\n"
            "## Decision\nDo the thing.\n\n"
            "<!-- skhema:elements main -->\n"
        )

        client_yaml = tmp_path / "client.yaml"
        client_yaml.write_text("name: Test\naccent_color: '#D97706'\nsections:\n  - c4\n")

        html = generate_gallery_html(
            client_name="Test",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
            client_yaml_path=str(client_yaml),
            client_path=str(tmp_path),
        )
        assert "ADR01" in html
        assert "Test Decision" in html


class TestGalleryDarkMode:
    def test_dark_mode_toggle_present(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "theme-toggle" in html
        assert "skhema-theme" in html

    def test_dark_mode_css_present(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "#1a1a2e" in html
        assert "#2d2d44" in html

    def test_card_thumb_height_280(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "280px" in html

    def test_animated_badge_has_pulse(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>.marching-ant{}</style></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "pulse" in html
