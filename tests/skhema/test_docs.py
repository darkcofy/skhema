"""Tests for the living docs generator."""
import os
import pytest
from skhema.docs import generate_docs_html, parse_markdown


class TestParseMarkdown:
    def test_headings(self):
        md = "# Title\n## Subtitle\n### H3\n#### H4"
        html = parse_markdown(md)
        assert "<h1>Title</h1>" in html
        assert "<h2>Subtitle</h2>" in html
        assert "<h3>H3</h3>" in html
        assert "<h4>H4</h4>" in html

    def test_paragraphs(self):
        md = "First paragraph.\n\nSecond paragraph."
        html = parse_markdown(md)
        assert "<p>First paragraph.</p>" in html
        assert "<p>Second paragraph.</p>" in html

    def test_bold_and_italic(self):
        md = "This is **bold** and *italic* text."
        html = parse_markdown(md)
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_inline_code(self):
        md = "Use `git status` to check."
        html = parse_markdown(md)
        assert "<code>git status</code>" in html

    def test_links(self):
        md = "See [docs](https://example.com) for details."
        html = parse_markdown(md)
        assert '<a href="https://example.com">docs</a>' in html

    def test_bullet_list(self):
        md = "Items:\n\n- Alpha\n- Beta\n- Gamma"
        html = parse_markdown(md)
        assert "<ul>" in html
        assert "<li>Alpha</li>" in html
        assert "<li>Gamma</li>" in html

    def test_numbered_list(self):
        md = "Steps:\n\n1. First\n2. Second\n3. Third"
        html = parse_markdown(md)
        assert "<ol>" in html
        assert "<li>First</li>" in html

    def test_blockquote(self):
        md = "> This is a quote\n> with two lines"
        html = parse_markdown(md)
        assert "<blockquote>" in html
        assert "This is a quote" in html

    def test_fenced_code_block(self):
        md = "Example:\n\n```bash\ngit status\ngit diff\n```"
        html = parse_markdown(md)
        assert "<pre><code" in html
        assert "git status" in html

    def test_table(self):
        md = "| Name | Role |\n|------|------|\n| Alice | Dev |\n| Bob | Ops |"
        html = parse_markdown(md)
        assert "<table>" in html
        assert "<th>Name</th>" in html
        assert "<td>Alice</td>" in html
        assert "<td>Ops</td>" in html

    def test_empty_input(self):
        assert parse_markdown("") == ""
        assert parse_markdown("  \n  \n") == ""


class TestGenerateDocsHtml:
    def test_returns_html_with_client_name(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        html = generate_docs_html(
            client_name="TestCo",
            subtitle="Platform",
            rendered_dir=str(tmp_path / "rendered"),
            docs_dir=str(tmp_path / "docs"),
        )
        assert "<!DOCTYPE html>" in html
        assert "TestCo" in html
        assert "Platform" in html

    def test_inlines_svg(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "arch.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "<circle" in html

    def test_includes_companion_prose(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs" / "c4"
        docs.mkdir(parents=True)
        (docs / "test.md").write_text("# Test Diagram\n\nThis shows the **test** architecture.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "<strong>test</strong>" in html
        assert "Test Diagram" in html

    def test_includes_section_overview(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs" / "c4"
        docs.mkdir(parents=True)
        (docs / "_overview.md").write_text("C4 diagrams show containers and components.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "C4 diagrams show containers and components." in html

    def test_includes_client_overview(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "overview.md").write_text("# NovaPay\n\nA payments platform.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(docs))
        assert "A payments platform." in html

    def test_missing_docs_dir_still_works(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "nodocs"))
        assert "<!DOCTYPE html>" in html
        assert "Test" in html

    def test_has_table_of_contents(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "Table of Contents" in html or "toc" in html.lower()

    def test_print_friendly(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "@media print" in html


class TestDocsAdrIntegration:
    def test_docs_includes_adr_subsection(self, tmp_path):
        from skhema.docs import generate_docs_html

        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "main.svg").write_text("<svg>diagram</svg>")

        docs = tmp_path / "docs" / "c4"
        docs.mkdir(parents=True)
        (docs / "overview.md").write_text("# Overview\nThis is the overview.")

        adrs = tmp_path / "adrs"
        adrs.mkdir()
        (adrs / "ADR01-test.md").write_text(
            "# ADR01: Test Decision\n\n## Status\nAccepted\n\n"
            "## Context\nContext here.\n\n## Decision\nDecision here.\n\n"
            "<!-- skhema:elements main -->\n"
        )

        html = generate_docs_html(
            client_name="Test",
            subtitle="",
            rendered_dir=str(tmp_path / "rendered"),
            docs_dir=str(tmp_path / "docs"),
            client_path=str(tmp_path),
        )
        assert "Architectural Decisions" in html
        assert "ADR01" in html
        assert "Test Decision" in html
