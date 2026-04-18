"""End-to-end test for the deck pipeline (Reveal.js HTML)."""


class TestDeckPipeline:
    def test_produces_reveal_html_deck(self, mock_workspace, mock_plantuml):
        """Full pipeline: discover .puml -> render SVG -> emit deck.html."""
        from skhema.deck import build_sections, render_deck_html

        diagrams_dir = str(mock_workspace / "diagrams")
        sections, total = build_sections(
            diagrams_dir=diagrams_dir,
            search_paths=[],
            docs_dir=None,
            include_notes=False,
        )
        assert total > 0

        html = render_deck_html(
            client={"name": "Mock Client", "subtitle": "", "accent_color": "#D97706"},
            sections=sections,
            adrs=[],
            total_diagrams=total,
        )
        assert "Mock Client" in html
        assert 'class="reveal"' in html
        assert "Reveal.initialize" in html
