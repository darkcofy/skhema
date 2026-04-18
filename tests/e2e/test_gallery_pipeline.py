"""End-to-end test for the gallery pipeline (Jinja2 + Reveal-style SVG embed)."""
import os

import pytest


class TestGalleryPipeline:
    def test_generates_html_from_workspace(self, mock_workspace, mock_rendered):
        from skhema.gallery import generate_gallery_html

        html = generate_gallery_html(
            client_name="Test",
            rendered_dir=str(mock_rendered),
            history=0,
            client_yaml_path=os.path.join(str(mock_workspace), "client.yaml"),
            client_path=str(mock_workspace),
        )

        # Structural asserts — was previously just substring `"<html"`.
        assert html.startswith("<!DOCTYPE html>"), "Gallery output must start with HTML doctype"
        assert '<html lang="en">' in html
        assert "<title>Test — Architecture Diagrams</title>" in html
        # Sidebar nav + main grid present
        assert 'class="sidebar"' in html
        assert 'class="grid"' in html
        # Inlined JS + CSS (no external refs)
        assert '<script>' in html
        assert '<style>' in html
        assert '<script src=' not in html
        assert '<link rel="stylesheet"' not in html

    def test_invalid_client_yaml_raises_rather_than_passing_silently(self, tmp_path):
        """Replaces the previous `try/except: pass` non-test. Real assertion."""
        from skhema.gallery import parse_client_yaml

        bad_yaml = tmp_path / "client.yaml"
        bad_yaml.write_text(": : : invalid")

        with pytest.raises(Exception):
            parse_client_yaml(str(bad_yaml))

    def test_empty_rendered_dir_returns_empty_list(self, tmp_path):
        from skhema.gallery import discover_diagrams

        empty = tmp_path / "empty"
        empty.mkdir()
        assert discover_diagrams(str(empty)) == []

    def test_missing_client_yaml_returns_defaults(self, tmp_path):
        from skhema.gallery import parse_client_yaml

        defaults = parse_client_yaml(str(tmp_path / "does-not-exist.yaml"))
        assert defaults["accent_color"] == "#D97706"
        assert defaults["sections"] == []
        assert defaults["name"] == ""
