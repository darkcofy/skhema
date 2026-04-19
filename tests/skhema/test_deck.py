"""Tests for the deck export script (Reveal.js HTML deck)."""
import os


from skhema.deck import (
    Diagram,
    Section,
    clean_svg_for_embed,
    diagram_title,
    diagram_type,
    discover_puml_files,
    order_by_type,
    render_deck_html,
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
        assert types == ["c4", "c4", "sequence", "erd"]

    def test_excludes_excalidraw(self, tmp_path):
        files = [
            str(tmp_path / "c4" / "main.puml"),
            str(tmp_path / "excalidraw" / "sketch.puml"),
            str(tmp_path / "sequence" / "flow.puml"),
        ]
        for f in files:
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "w").close()
        ordered = order_by_type(files, str(tmp_path))
        types = [os.path.basename(os.path.dirname(f)) for f in ordered]
        assert "excalidraw" not in types


class TestHelpers:
    def test_diagram_title_converts_filename(self):
        assert diagram_title("/d/c4/data-platform-container.puml") == "Data Platform Container"

    def test_diagram_type_returns_top_dir(self, tmp_path):
        path = tmp_path / "diagrams" / "c4" / "context.puml"
        path.parent.mkdir(parents=True)
        path.touch()
        assert diagram_type(str(path), str(tmp_path / "diagrams")) == "c4"

    def test_clean_svg_strips_xml_decl(self):
        raw = b'<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "..">\n<svg><rect/></svg>'
        cleaned = clean_svg_for_embed(raw)
        assert "<?xml" not in cleaned
        assert "<!DOCTYPE" not in cleaned
        assert cleaned.startswith("<svg>")

    def test_clean_svg_strips_root_width_height_attrs(self):
        raw = b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect/></svg>'
        cleaned = clean_svg_for_embed(raw)
        assert 'width="1200"' not in cleaned
        assert 'height="800"' not in cleaned
        assert 'viewBox="0 0 1200 800"' in cleaned

    def test_clean_svg_strips_size_from_style_attr(self):
        # PlantUML embeds dimensions in style="" — they override CSS sizing.
        raw = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'style="width:1452px;height:754px;background:#FFFFFF;" '
            b'viewBox="0 0 1452 754"><rect/></svg>'
        )
        cleaned = clean_svg_for_embed(raw)
        assert "width:1452px" not in cleaned
        assert "height:754px" not in cleaned
        # Non-size style declarations (background) are preserved
        assert "background:#FFFFFF" in cleaned
        # viewBox is preserved — it's what CSS scaling depends on
        assert 'viewBox="0 0 1452 754"' in cleaned


class TestRenderDeckHtml:
    def test_produces_reveal_html(self):
        sections = [
            Section(
                label="C4 Diagrams",
                diagrams=[
                    Diagram(title="Context", svg_inline="<svg><rect/></svg>", notes=None),
                ],
            ),
        ]
        html = render_deck_html(
            client={"name": "Test Co", "subtitle": "v1", "accent_color": "#D97706"},
            sections=sections,
            adrs=[],
            total_diagrams=1,
        )
        assert "<!DOCTYPE html>" in html
        assert 'class="reveal"' in html
        assert "Test Co" in html
        assert "Context" in html
        assert "<svg><rect/></svg>" in html
        # Reveal.js is inlined (no CDN references)
        assert "Reveal.initialize" in html

    def test_cover_uses_accent_color(self):
        html = render_deck_html(
            client={"name": "Foo", "subtitle": "", "accent_color": "#123456"},
            sections=[],
            adrs=[],
            total_diagrams=0,
        )
        assert "#123456" in html

    def test_adrs_render_when_present(self):
        html = render_deck_html(
            client={"name": "Foo", "subtitle": "", "accent_color": "#D97706"},
            sections=[],
            adrs=[
                {"number": 1, "title": "Pick Postgres", "status": "Accepted", "body_html": "<p>Because.</p>"},
            ],
            total_diagrams=0,
        )
        assert "ADR01: Pick Postgres" in html
        assert "status-accepted" in html
        assert "<p>Because.</p>" in html

    def test_self_contained_no_external_script_or_link_tags(self):
        html = render_deck_html(
            client={"name": "X", "subtitle": "", "accent_color": "#D97706"},
            sections=[],
            adrs=[],
            total_diagrams=0,
        )
        # No external <script src="..."> or <link href="..."> — everything inlined.
        # Reveal.js source may contain https:// references in comments and CSS url()
        # calls, which is fine as long as no runtime external fetch happens.
        assert "<script src=" not in html
        assert '<link rel="stylesheet"' not in html
        assert '<link href=' not in html
