"""Tests for the gallery generator."""
import os
import pytest
from scripts.gallery import (
    discover_diagrams,
    group_by_type,
    generate_gallery_html,
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
