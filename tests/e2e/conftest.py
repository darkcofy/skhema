import io
import os
import shutil
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_workspace(tmp_path):
    """Copy mock workspace fixtures to tmp_path and return path."""
    fixtures = os.path.join(os.path.dirname(__file__), "fixtures", "mock_workspace")
    dest = tmp_path / "client"
    shutil.copytree(fixtures, dest)
    return dest


@pytest.fixture
def mock_rendered(tmp_path):
    """Copy mock rendered fixtures to tmp_path and return path."""
    fixtures = os.path.join(os.path.dirname(__file__), "fixtures", "mock_rendered")
    dest = tmp_path / "rendered"
    shutil.copytree(fixtures, dest)
    return dest


@pytest.fixture
def fake_svg():
    return b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'


@pytest.fixture
def fake_pdf():
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture
def mock_plantuml(fake_svg, fake_pdf):
    def side_effect(cmd, *args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if isinstance(cmd, list) and any("-tpdf" in c for c in cmd):
            result.stdout = fake_pdf
        elif isinstance(cmd, list) and any("-tpng" in c for c in cmd):
            result.stdout = fake_svg
        else:
            result.stdout = fake_svg
        result.stderr = b""
        return result

    with patch("skhema.render.subprocess.run", side_effect=side_effect) as mock:
        yield mock
