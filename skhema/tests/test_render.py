"""Tests for the render script's include resolution logic."""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from scripts.render import resolve_includes


class TestResolveIncludes:
    """Test local !include inlining."""

    def test_no_includes(self):
        source = "@startuml\nPerson(a, 'A', 'desc')\n@enduml"
        result = resolve_includes(source, base_dir="/tmp")
        assert result == source

    def test_remote_include_left_untouched(self):
        source = "!include https://example.com/C4_Context.puml\nPerson(a, 'A', 'desc')"
        result = resolve_includes(source, base_dir="/tmp")
        assert "https://example.com/C4_Context.puml" in result

    def test_local_include_inlined(self, tmp_path):
        inc_file = tmp_path / "inc.puml"
        inc_file.write_text("' included content\n!define FOO bar")
        source = f"!include inc.puml\nPerson(a, 'A', 'desc')"
        result = resolve_includes(source, base_dir=str(tmp_path))
        assert "' included content" in result
        assert "!define FOO bar" in result
        assert "!include inc.puml" not in result

    def test_nested_local_includes(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.puml").write_text("' leaf content")
        (tmp_path / "a.puml").write_text("!include sub/b.puml")
        source = "!include a.puml\nDone"
        result = resolve_includes(source, base_dir=str(tmp_path))
        assert "' leaf content" in result
        assert "!include" not in result.replace("!include https", "")

    def test_circular_include_raises(self, tmp_path):
        (tmp_path / "a.puml").write_text("!include b.puml")
        (tmp_path / "b.puml").write_text("!include a.puml")
        source = "!include a.puml"
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_includes(source, base_dir=str(tmp_path))


class TestResolveIncludesSearchPath:
    """Test include resolution with search paths."""

    def test_search_path_fallback(self, tmp_path):
        """If not found relative to source, search paths are tried."""
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "common.puml").write_text("' shared content")
        source = "!include common.puml"
        result = resolve_includes(source, base_dir=str(tmp_path), search_paths=[str(shared)])
        assert "' shared content" in result

    def test_local_takes_priority(self, tmp_path):
        """Local file wins over search path."""
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "item.puml").write_text("' shared version")
        (tmp_path / "item.puml").write_text("' local version")
        source = "!include item.puml"
        result = resolve_includes(source, base_dir=str(tmp_path), search_paths=[str(shared)])
        assert "' local version" in result
        assert "' shared version" not in result

    def test_search_path_order(self, tmp_path):
        """First search path wins when file exists in multiple."""
        path_a = tmp_path / "a"
        path_b = tmp_path / "b"
        path_a.mkdir()
        path_b.mkdir()
        (path_a / "item.puml").write_text("' from a")
        (path_b / "item.puml").write_text("' from b")
        source = "!include item.puml"
        result = resolve_includes(source, base_dir=str(tmp_path / "empty"), search_paths=[str(path_a), str(path_b)])
        assert "' from a" in result


class TestRenderPlantUml:
    def test_renders_svg_via_subprocess(self):
        from scripts.render import render_plantuml
        fake_svg = b"<svg>test</svg>"
        mock_result = MagicMock()
        mock_result.stdout = fake_svg
        mock_result.returncode = 0

        with patch("scripts.render.subprocess.run", return_value=mock_result) as mock_run:
            result = render_plantuml("@startuml\nA -> B\n@enduml", fmt="svg")

        assert result == fake_svg
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "-tsvg" in call_args[0][0]

    def test_raises_on_plantuml_error(self):
        from scripts.render import render_plantuml
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"Syntax Error line 2"

        with patch("scripts.render.subprocess.run", return_value=mock_result):
            try:
                render_plantuml("@startuml\nbad syntax\n@enduml")
                assert False, "Should have raised"
            except RuntimeError as e:
                assert "Syntax Error" in str(e)

    def test_missing_plantuml_binary(self):
        from scripts.render import render_plantuml
        with patch("scripts.render.subprocess.run", side_effect=FileNotFoundError()):
            try:
                render_plantuml("@startuml\nA -> B\n@enduml")
                assert False, "Should have raised"
            except RuntimeError as e:
                assert "PlantUML not found" in str(e)
