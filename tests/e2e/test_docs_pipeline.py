import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "skhema"))


class TestDocsPipeline:
    def test_generates_docs_with_prose(self, mock_workspace, mock_rendered):
        from scripts.docs import generate_docs_html
        html = generate_docs_html(
            client_name="Test", subtitle="Test Docs",
            rendered_dir=str(mock_rendered),
            docs_dir=os.path.join(str(mock_workspace), "docs"),
            client_path=str(mock_workspace))
        assert "<html" in html
        assert "System Overview" in html

    def test_docs_with_adr_subsections(self, mock_workspace, mock_rendered):
        from scripts.docs import generate_docs_html
        html = generate_docs_html(
            client_name="Test", subtitle="",
            rendered_dir=str(mock_rendered),
            docs_dir=os.path.join(str(mock_workspace), "docs"),
            client_path=str(mock_workspace))
        assert "ADR01" in html
