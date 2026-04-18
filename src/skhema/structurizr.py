"""Wrap the Structurizr CLI.

Exports C4 models from `workspace.dsl` to PlantUML (which skhema then renders).

Usage:
    python -m skhema.structurizr export --client meshco
    python -m skhema.structurizr validate --client meshco
    python -m skhema.structurizr view --client meshco      # opens Structurizr Lite

Requires `structurizr-cli` on PATH (or STRUCTURIZR_CLI env var pointing at the
launcher). The Docker image installs it; local users can follow
https://docs.structurizr.com/cli/installation.
"""
import argparse
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


def _get_structurizr_bin() -> str:
    """Get the structurizr CLI binary path from env var or PATH."""
    override = os.environ.get("STRUCTURIZR_CLI")
    if override:
        return override
    found = shutil.which("structurizr-cli") or shutil.which("structurizr")
    if found:
        return found
    # Inside the Docker image we install to /opt/structurizr-cli/structurizr.sh
    fallback = "/opt/structurizr-cli/structurizr.sh"
    if os.path.isfile(fallback):
        return fallback
    raise RuntimeError(
        "structurizr-cli not found on PATH. "
        "Install from https://docs.structurizr.com/cli/installation, "
        "or set STRUCTURIZR_CLI, or run inside the skhema Docker image."
    )


def workspace_path(client_dir: str) -> str:
    """Return the canonical workspace.dsl path for a client."""
    return os.path.join(client_dir, "workspace.dsl")


def export_plantuml(client_dir: str, output_subdir: str = "diagrams/exported") -> str:
    """Export workspace.dsl to PlantUML files.

    Output lands in `<client_dir>/<output_subdir>/` (default diagrams/exported/).
    Returns the output directory path.
    """
    dsl = workspace_path(client_dir)
    if not os.path.isfile(dsl):
        raise FileNotFoundError(f"No workspace.dsl at {dsl}")

    output_dir = os.path.join(client_dir, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    bin_path = _get_structurizr_bin()
    cmd = [
        bin_path,
        "export",
        "-workspace", dsl,
        "-format", "plantuml/c4plantuml",
        "-output", output_dir,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"structurizr-cli export failed:\n{result.stderr or result.stdout}"
        )
    return output_dir


def validate(client_dir: str) -> None:
    """Validate workspace.dsl. Raises on failure."""
    dsl = workspace_path(client_dir)
    if not os.path.isfile(dsl):
        raise FileNotFoundError(f"No workspace.dsl at {dsl}")

    bin_path = _get_structurizr_bin()
    cmd = [bin_path, "validate", "-workspace", dsl]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"structurizr-cli validation failed:\n{result.stderr or result.stdout}"
        )


def view(client: str) -> None:
    """Open Structurizr Lite in a browser, pointed at the given client workspace.

    Expects the structurizr-lite docker-compose service to be running:
        CLIENT=<client> docker compose up structurizr-lite
    """
    url = f"http://localhost:8080"
    print(f"Opening Structurizr Lite at {url}")
    print(f"(Make sure `CLIENT={client} docker compose up structurizr-lite` is running.)")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def find_repo_root() -> str:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "clients").is_dir():
            return str(parent)
    return os.getcwd()


def main():
    parser = argparse.ArgumentParser(
        description="Wrap the Structurizr CLI for client workspaces."
    )
    sub = parser.add_subparsers(dest="action", required=True)

    for action in ("export", "validate", "view"):
        p = sub.add_parser(action)
        p.add_argument("--client", required=True, help="Client name")

    args = parser.parse_args()

    root = find_repo_root()
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    try:
        if args.action == "export":
            out = export_plantuml(client_dir)
            print(f"Exported to {out}")
        elif args.action == "validate":
            validate(client_dir)
            print(f"OK: {workspace_path(client_dir)}")
        elif args.action == "view":
            view(args.client)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
