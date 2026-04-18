import os
import sys



class TestAdrPipeline:
    def test_discovers_and_parses_adrs(self, mock_workspace):
        from skhema.adr import discover_adrs
        adrs = discover_adrs(str(mock_workspace))
        assert len(adrs) == 1
        assert adrs[0].number == 1
        assert "user" in adrs[0].elements
        assert "system" in adrs[0].elements
        assert "sample" in adrs[0].elements

    def test_adr_links_resolve_to_gallery(self, mock_workspace, mock_rendered):
        from skhema.gallery import generate_gallery_html
        html = generate_gallery_html(
            client_name="Test", rendered_dir=str(mock_rendered),
            history=0,
            client_yaml_path=os.path.join(str(mock_workspace), "client.yaml"),
            client_path=str(mock_workspace))
        assert "ADR01" in html

    def test_bad_link_tag_warns_not_crashes(self, tmp_path):
        from skhema.adr import parse_adr
        adr_file = tmp_path / "ADR99-bad.md"
        adr_file.write_text("# ADR99: Bad\n\n## Status\nAccepted\n\n<!-- skhema:elements -->\n")
        adr = parse_adr(str(adr_file))
        assert isinstance(adr.elements, list)

    def test_no_adrs_directory(self, tmp_path):
        from skhema.adr import discover_adrs
        assert discover_adrs(str(tmp_path)) == []
