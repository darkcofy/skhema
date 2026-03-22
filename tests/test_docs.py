"""Tests for the living docs generator."""
import os
import pytest
from scripts.docs import parse_markdown


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
        assert "<pre><code>" in html
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
