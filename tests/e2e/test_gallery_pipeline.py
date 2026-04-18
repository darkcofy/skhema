import os
import sys



class TestGalleryPipeline:
    def test_generates_html_from_workspace(self, mock_workspace, mock_rendered):
        from skhema.gallery import generate_gallery_html
        html = generate_gallery_html(
            client_name="Test", rendered_dir=str(mock_rendered),
            history=0, client_yaml_path=os.path.join(str(mock_workspace), "client.yaml"),
            client_path=str(mock_workspace))
        assert "<html" in html
        assert "Test" in html

    def test_invalid_client_yaml(self, tmp_path):
        from skhema.gallery import parse_client_yaml
        bad_yaml = tmp_path / "client.yaml"
        bad_yaml.write_text(": : : invalid")
        try:
            parse_client_yaml(str(bad_yaml))
        except Exception:
            pass

    def test_empty_rendered_dir(self, tmp_path):
        from skhema.gallery import discover_diagrams
        empty = tmp_path / "empty"
        empty.mkdir()
        assert discover_diagrams(str(empty)) == []
