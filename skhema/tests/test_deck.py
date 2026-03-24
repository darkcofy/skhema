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


from unittest.mock import patch, MagicMock
import io


class TestBuildDeck:
    def test_produces_merged_pdf(self, tmp_path):
        from scripts.deck import build_deck

        # Create a minimal valid PDF bytes (1-page)
        from pypdf import PdfWriter
        single_page = PdfWriter()
        single_page.add_blank_page(width=612, height=792)
        buf = io.BytesIO()
        single_page.write(buf)
        fake_pdf = buf.getvalue()

        output = tmp_path / "deck.pdf"

        with patch("scripts.deck.render_plantuml", return_value=fake_pdf), \
             patch("scripts.deck.ordered_diagrams", return_value=[("a.puml", "@startuml\n@enduml"), ("b.puml", "@startuml\n@enduml")]):
            build_deck(
                client_name="Test",
                diagrams_dir=str(tmp_path),
                search_paths=[],
                output_path=str(output),
                include_cover=False,
            )

        assert output.exists()
        from pypdf import PdfReader
        reader = PdfReader(str(output))
        assert len(reader.pages) == 2

    def test_excludes_excalidraw(self, tmp_path):
        from scripts.deck import order_by_type
        files = [
            str(tmp_path / "c4" / "main.puml"),
            str(tmp_path / "excalidraw" / "sketch.puml"),
            str(tmp_path / "sequence" / "flow.puml"),
        ]
        for f in files:
            import os
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "w").close()
        ordered = order_by_type(files, str(tmp_path))
        types = [os.path.basename(os.path.dirname(f)) for f in ordered]
        assert "excalidraw" not in types
