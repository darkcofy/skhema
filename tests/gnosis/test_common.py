"""Tests for the shared ingest helpers in gnosis._common."""
from __future__ import annotations

import datetime as _dt
import os

import yaml

from gnosis._common import (
    make_provenance,
    resolve_fixture_path,
    write_yaml_list,
)


class TestMakeProvenance:
    def test_shape(self):
        at = _dt.datetime(2026, 5, 10, 12, 34, 56, tzinfo=_dt.timezone.utc)
        p = make_provenance("sess-1", "alfred", at)
        assert p == {
            "session": "sess-1",
            "interviewer": "alfred",
            "at": "2026-05-10T12:34:56+00:00",
        }

    def test_microseconds_stripped(self):
        at = _dt.datetime(2026, 5, 10, 12, 34, 56, 789_000, tzinfo=_dt.timezone.utc)
        p = make_provenance("s", "al", at)
        assert "789" not in p["at"]


class TestWriteYamlList:
    def test_roundtrip_preserves_order(self, tmp_path):
        payload = [
            {"name": "Alpha", "rank": 1},
            {"name": "Bravo", "rank": 2},
        ]
        path = tmp_path / "out.yaml"
        write_yaml_list(payload, str(path))
        loaded = yaml.safe_load(open(path).read())
        assert loaded == payload

    def test_creates_parent_directory(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "out.yaml"
        write_yaml_list([{"k": "v"}], str(path))
        assert os.path.isfile(path)

    def test_block_style_output(self, tmp_path):
        path = tmp_path / "out.yaml"
        write_yaml_list([{"name": "Alpha", "aliases": ["a", "b"]}], str(path))
        text = open(path).read()
        # Block style should render list entries with `-`, not flow `[...]`.
        assert "- a" in text or "- name: Alpha" in text
        assert "[a, b]" not in text


class TestResolveFixturePath:
    def test_absolute_returned_asis(self, tmp_path):
        abs_path = str(tmp_path / "f.yaml")
        assert resolve_fixture_path(abs_path, str(tmp_path)) == abs_path

    def test_relative_resolved_against_root(self, tmp_path):
        (tmp_path / "sub").mkdir()
        f = tmp_path / "sub" / "f.yaml"
        f.write_text("[]")
        resolved = resolve_fixture_path("sub/f.yaml", str(tmp_path))
        assert resolved == str(f)

    def test_unresolved_returns_original(self, tmp_path):
        # If repo-relative doesn't exist, return the original string so the
        # downstream os.path.isfile check can surface the error.
        out = resolve_fixture_path("does/not/exist.yaml", str(tmp_path))
        assert out == "does/not/exist.yaml"
