"""Tests for the Structurizr CLI wrapper module."""
import os
import pytest
from unittest.mock import patch, MagicMock

from skhema.structurizr import (
    _get_structurizr_bin,
    export_plantuml,
    validate,
    workspace_path,
)


class TestWorkspacePath:
    def test_workspace_path_joins_client_dir(self):
        assert workspace_path("/clients/meshco") == "/clients/meshco/workspace.dsl"


class TestBinaryResolution:
    def test_env_var_wins(self, monkeypatch):
        monkeypatch.setenv("STRUCTURIZR_CLI", "/custom/path/structurizr")
        assert _get_structurizr_bin() == "/custom/path/structurizr"

    def test_raises_when_missing(self, monkeypatch):
        monkeypatch.delenv("STRUCTURIZR_CLI", raising=False)
        with patch("skhema.structurizr.shutil.which", return_value=None), \
             patch("os.path.isfile", return_value=False):
            with pytest.raises(RuntimeError, match="structurizr-cli not found"):
                _get_structurizr_bin()

    def test_falls_back_to_docker_path(self, monkeypatch):
        monkeypatch.delenv("STRUCTURIZR_CLI", raising=False)
        with patch("skhema.structurizr.shutil.which", return_value=None), \
             patch("os.path.isfile", side_effect=lambda p: p == "/opt/structurizr-cli/structurizr.sh"):
            assert _get_structurizr_bin() == "/opt/structurizr-cli/structurizr.sh"


class TestExport:
    def test_missing_workspace_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No workspace.dsl"):
            export_plantuml(str(tmp_path))

    def test_invokes_cli_with_expected_args(self, tmp_path, monkeypatch):
        dsl = tmp_path / "workspace.dsl"
        dsl.write_text("workspace {}")
        monkeypatch.setenv("STRUCTURIZR_CLI", "/fake/structurizr")

        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            out = export_plantuml(str(tmp_path))

        assert os.path.isdir(out)
        cmd = mock_run.call_args[0][0]
        assert "/fake/structurizr" in cmd
        assert "export" in cmd
        assert str(dsl) in cmd
        assert "plantuml/c4plantuml" in cmd

    def test_propagates_cli_failure(self, tmp_path, monkeypatch):
        dsl = tmp_path / "workspace.dsl"
        dsl.write_text("workspace {}")
        monkeypatch.setenv("STRUCTURIZR_CLI", "/fake/structurizr")

        mock_result = MagicMock(returncode=1, stdout="", stderr="bad dsl")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="bad dsl"):
                export_plantuml(str(tmp_path))


class TestValidate:
    def test_missing_workspace_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No workspace.dsl"):
            validate(str(tmp_path))

    def test_happy_path(self, tmp_path, monkeypatch):
        dsl = tmp_path / "workspace.dsl"
        dsl.write_text("workspace {}")
        monkeypatch.setenv("STRUCTURIZR_CLI", "/fake/structurizr")

        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            validate(str(tmp_path))  # should not raise

    def test_validation_failure_raises(self, tmp_path, monkeypatch):
        dsl = tmp_path / "workspace.dsl"
        dsl.write_text("workspace { bad }")
        monkeypatch.setenv("STRUCTURIZR_CLI", "/fake/structurizr")

        mock_result = MagicMock(returncode=1, stdout="", stderr="syntax error")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="syntax error"):
                validate(str(tmp_path))
