"""Tests for the SVG arrow animation post-processor."""
import os
import xml.etree.ElementTree as ET
import pytest
from skhema.animate import animate_svg, MARCHING_ANT_CSS

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "sample-link-groups.svg"
)
NS = "{http://www.w3.org/2000/svg}"


def parse_animated(svg_content: str) -> ET.Element:
    """Parse animated SVG string into an Element."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return ET.fromstring(svg_content)


class TestAnimateSvg:
    def test_returns_string(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        assert isinstance(result, str)

    def test_injects_style_element(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        styles = root.findall(f"{NS}style")
        assert len(styles) >= 1
        assert "marching-ant" in styles[0].text

    def test_animated_path_gets_class(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk1 has ~Streams — its path should have marching-ant class
        lnk1 = root.find(f".//{NS}g[@id='lnk1']")
        path = lnk1.find(f"{NS}path")
        assert "marching-ant" in (path.get("class") or "")

    def test_static_path_unchanged(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk2 has Queries (no ~) — its path should NOT have the class
        lnk2 = root.find(f".//{NS}g[@id='lnk2']")
        path = lnk2.find(f"{NS}path")
        assert "marching-ant" not in (path.get("class") or "")

    def test_tilde_stripped_from_text(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        lnk1 = root.find(f".//{NS}g[@id='lnk1']")
        texts = [t.text or "" for t in lnk1.findall(f"{NS}text")]
        for t in texts:
            assert "~" not in t

    def test_multiple_animated_links(self):
        source = open(FIXTURE_PATH).read()
        result = animate_svg(source)
        root = parse_animated(result)
        # lnk1 and lnk3 should both be animated
        for lnk_id in ["lnk1", "lnk3"]:
            g = root.find(f".//{NS}g[@id='{lnk_id}']")
            path = g.find(f"{NS}path")
            assert "marching-ant" in (path.get("class") or ""), f"{lnk_id} not animated"

    def test_no_markers_returns_unchanged(self):
        """SVG with no ~ markers should be returned with no style injected."""
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><g id="lnk1"><path d="M0 0" fill="none" style="stroke:#666;"/><text>Normal</text></g></svg>'
        result = animate_svg(svg)
        assert "marching-ant" not in result

    def test_plantuml_pi_stripped(self):
        source = open(FIXTURE_PATH).read()
        assert "<?plantuml" in source  # fixture has it
        result = animate_svg(source)
        assert "<?plantuml" not in result

    def test_returns_count(self):
        source = open(FIXTURE_PATH).read()
        result, count = animate_svg(source, return_count=True)
        assert count == 2  # lnk1 and lnk3
