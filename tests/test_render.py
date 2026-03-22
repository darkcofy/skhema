"""Tests for the render script's include resolution logic."""
import os
import tempfile
import pytest

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
