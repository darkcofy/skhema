"""Client detection and workspace path resolution.

A client is a subdirectory of clients/ that contains a client.yaml file.
"""
import os
import sys


def find_repo_root() -> str:
    """Find the repository root by walking up from this file's location.

    Looks for the 'clients' directory as the marker.
    """
    # Walk up from both __file__ (src install) AND CWD (package install).
    import itertools
    from pathlib import Path as _P
    starts = [_P(__file__).resolve(), _P.cwd().resolve()]
    for parent in itertools.chain.from_iterable(
        [[s, *s.parents] for s in starts]
    ):
        if (parent / "clients").is_dir():
            return str(parent)
    print("Error: could not find repository root (no clients/ directory found)", file=sys.stderr)
    sys.exit(1)


def list_clients(root: str) -> list[str]:
    """List all valid client names (directories with client.yaml)."""
    clients_dir = os.path.join(root, "clients")
    if not os.path.isdir(clients_dir):
        return []
    return sorted(
        name for name in os.listdir(clients_dir)
        if os.path.isfile(os.path.join(clients_dir, name, "client.yaml"))
    )


def detect_client(root: str, client_arg: str | None) -> str:
    """Detect or validate the client name.

    If client_arg is provided, validate it exists.
    If not, auto-detect if exactly one client exists.
    """
    clients = list_clients(root)

    if client_arg:
        if client_arg not in clients:
            print(f"Error: client '{client_arg}' not found. Available: {', '.join(clients) or 'none'}", file=sys.stderr)
            sys.exit(1)
        return client_arg

    if len(clients) == 0:
        print("Error: no clients found in clients/. Run 'gnosis init <name>' first.", file=sys.stderr)
        sys.exit(1)

    if len(clients) == 1:
        return clients[0]

    print(f"Error: multiple clients found ({', '.join(clients)}). Use --client <name>.", file=sys.stderr)
    sys.exit(1)


def resolve_workspace(root: str, client: str) -> str:
    """Return the ontology workspace path for a client."""
    return os.path.join(root, "clients", client, "ontology")
