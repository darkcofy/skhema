"""Tests for client detection and workspace path resolution."""
import os
import pytest

from gnosis.client import detect_client, resolve_workspace


@pytest.fixture
def repo_with_one_client(tmp_path):
    """Repo with one client that has client.yaml."""
    clients_dir = tmp_path / "clients" / "acme"
    clients_dir.mkdir(parents=True)
    (clients_dir / "client.yaml").write_text('name: "Acme"\n')
    return tmp_path


@pytest.fixture
def repo_with_two_clients(tmp_path):
    """Repo with two clients."""
    for name in ["acme", "beta"]:
        d = tmp_path / "clients" / name
        d.mkdir(parents=True)
        (d / "client.yaml").write_text(f'name: "{name}"\n')
    return tmp_path


@pytest.fixture
def repo_with_no_clients(tmp_path):
    """Repo with clients dir but no valid clients."""
    (tmp_path / "clients").mkdir()
    (tmp_path / "clients" / ".gitkeep").touch()
    return tmp_path


class TestDetectClient:
    def test_single_client_auto_detected(self, repo_with_one_client):
        name = detect_client(str(repo_with_one_client), client_arg=None)
        assert name == "acme"

    def test_explicit_client_arg(self, repo_with_two_clients):
        name = detect_client(str(repo_with_two_clients), client_arg="beta")
        assert name == "beta"

    def test_multiple_clients_no_arg_raises(self, repo_with_two_clients):
        with pytest.raises(SystemExit):
            detect_client(str(repo_with_two_clients), client_arg=None)

    def test_no_clients_raises(self, repo_with_no_clients):
        with pytest.raises(SystemExit):
            detect_client(str(repo_with_no_clients), client_arg=None)

    def test_nonexistent_client_raises(self, repo_with_one_client):
        with pytest.raises(SystemExit):
            detect_client(str(repo_with_one_client), client_arg="nonexistent")


class TestResolveWorkspace:
    def test_returns_ontology_path(self, repo_with_one_client):
        ws = resolve_workspace(str(repo_with_one_client), "acme")
        assert ws == os.path.join(str(repo_with_one_client), "clients", "acme", "ontology")
