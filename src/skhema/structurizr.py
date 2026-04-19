"""Wrap the Structurizr CLI.

Exports C4 models from `workspace.dsl` to PlantUML (which skhema then renders).
After export we post-process each `.puml` to inject an EY-palette C4-PlantUML
style block and to promote elements tagged `External` in the DSL to the
`System_Ext / Container_Ext / Person_Ext` macros. Structurizr's built-in
`plantuml/c4plantuml` exporter emits plain `System(...)` for externals with
an empty `$tags` value, so without this post-processing everything would
render in C4-PlantUML's default blue regardless of the DSL styles.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


_EY_STYLE_BLOCK = """
' ── skhema theme: EY-aligned palette (injected by skhema structurizr export) ──
UpdateElementStyle("person",             $bgColor="#FFE600", $fontColor="#2E2E38", $borderColor="#2E2E38")
UpdateElementStyle("external_person",    $bgColor="#747480", $fontColor="#FFFFFF", $borderColor="#2E2E38")
UpdateElementStyle("system",             $bgColor="#2E2E38", $fontColor="#FFE600", $borderColor="#FFE600")
UpdateElementStyle("external_system",    $bgColor="#747480", $fontColor="#FFFFFF", $borderColor="#2E2E38")
UpdateElementStyle("container",          $bgColor="#3A3A44", $fontColor="#FFFFFF", $borderColor="#FFE600")
UpdateElementStyle("external_container", $bgColor="#747480", $fontColor="#FFFFFF", $borderColor="#2E2E38")
UpdateElementStyle("component",          $bgColor="#FFE600", $fontColor="#2E2E38", $borderColor="#2E2E38")
UpdateElementStyle("external_component", $bgColor="#747480", $fontColor="#FFFFFF", $borderColor="#2E2E38")
UpdateRelStyle($lineColor="#2E2E38", $textColor="#2E2E38")
' ─────────────────────────────────────────────────────────────────────────────
"""


def _parse_external_ids(dsl_text: str) -> set[str]:
    """Find elements tagged `External` in the DSL.

    Returns both the DSL identifier and the name Structurizr would generate
    for the exported PlantUML macro (display-name with non-alphanumerics
    stripped: `"BI Platform"` → `BIPlatform`).
    """
    externals: set[str] = set()
    pattern = re.compile(
        r"(\w+)\s*=\s*(?:softwareSystem|container|person|component)\s+"
        r'"([^"]+)"[^{\n]*\{([^}]*?)\}',
        re.DOTALL,
    )
    for m in pattern.finditer(dsl_text):
        identifier = m.group(1)
        display = m.group(2)
        block = m.group(3)
        if re.search(r'\btags\s+"External"', block):
            externals.add(identifier)
            externals.add(re.sub(r"[^A-Za-z0-9]", "", display))
    return externals


def _inject_theme_and_externals(puml_text: str, external_ids: set[str]) -> str:
    """Insert the EY style block after the last `!include <C4/...>` line,
    and rewrite `System(/Container(/Person(` to `System_Ext(/…` where the
    element identifier matches an External tag from the DSL."""
    lines = puml_text.splitlines()
    insert_at = -1
    for i, line in enumerate(lines):
        if re.match(r"^\s*!include\s+<C4/", line):
            insert_at = i
    if insert_at >= 0:
        lines = lines[: insert_at + 1] + [_EY_STYLE_BLOCK] + lines[insert_at + 1 :]

    out: list[str] = []
    for line in lines:
        new = line
        if external_ids:
            for macro in ("System", "Container", "Person"):
                m = re.match(rf"^(\s*){macro}\(\s*(\w+)\s*,", new)
                if m and m.group(2) in external_ids:
                    new = re.sub(
                        rf"^(\s*){macro}\(",
                        rf"\1{macro}_Ext(",
                        new,
                        count=1,
                    )
                    break
        out.append(new)
    trailing = "\n" if puml_text.endswith("\n") else ""
    return "\n".join(out) + trailing


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


def export_plantuml(client_dir: str, output_subdir: str = "diagrams/c4/exported") -> str:
    """Export workspace.dsl to PlantUML files.

    Output lands in `<client_dir>/<output_subdir>/` (default diagrams/c4/exported/).
    The `c4/` parent directory matters: skhema's gallery/handbook/deck group
    diagrams by the first subdirectory under `diagrams/`, so exports must live
    under `c4/` to show up in the C4 Diagrams section.

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

    # Post-process: inject the EY palette + promote externals in every
    # exported .puml. Without this, C4-PlantUML's defaults (blue) win
    # because Structurizr strips DSL styles during export.
    dsl_text = open(dsl).read()
    external_ids = _parse_external_ids(dsl_text)
    for name in os.listdir(output_dir):
        if not name.endswith(".puml"):
            continue
        path = os.path.join(output_dir, name)
        with open(path) as f:
            content = f.read()
        with open(path, "w") as f:
            f.write(_inject_theme_and_externals(content, external_ids))

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
    url = "http://localhost:8080"
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
