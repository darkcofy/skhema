import os
import shutil
from unittest.mock import MagicMock, patch

import pytest


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
def mock_plantuml(fake_svg):
    """Mock the PlantUML subprocess call — returns fake_svg for all formats."""
    def side_effect(cmd, *args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = fake_svg
        result.stderr = b""
        return result

    with patch("skhema.render.subprocess.run", side_effect=side_effect) as mock:
        yield mock
