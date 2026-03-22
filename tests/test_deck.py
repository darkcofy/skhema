"""Tests for the deck export script."""
import os
import pytest
from scripts.deck import (
    discover_puml_files,
    order_by_type,
)


class TestDiscoverPumlFiles:
    def test_finds_puml(self, tmp_path):
        diagrams = tmp_path / "diagrams" / "c4"
        diagrams.mkdir(parents=True)
        (diagrams / "a.puml").write_text("@startuml\n@enduml")
        (diagrams / "b.puml").write_text("@startuml\n@enduml")
        result = discover_puml_files(str(tmp_path / "diagrams"))
        assert len(result) == 2

    def test_ignores_non_puml(self, tmp_path):
        diagrams = tmp_path / "diagrams"
        diagrams.mkdir()
        (diagrams / "readme.md").write_text("not puml")
        result = discover_puml_files(str(diagrams))
        assert len(result) == 0


class TestOrderByType:
    def test_orders_correctly(self):
        files = [
            "/d/sequence/a.puml",
            "/d/c4/b.puml",
            "/d/erd/c.puml",
            "/d/c4/a.puml",
        ]
        ordered = order_by_type(files, "/d")
        types = [os.path.relpath(f, "/d").split(os.sep)[0] for f in ordered]
        # c4 first, then sequence, then erd (matches TYPE_ORDER)
        assert types == ["c4", "c4", "sequence", "erd"]
