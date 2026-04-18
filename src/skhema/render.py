#!/usr/bin/env python3
"""Render PlantUML diagrams via the local PlantUML binary.

Usage:
    python scripts/render.py <file.puml>              # Render single file to SVG
    python scripts/render.py <file.puml> --png         # Render single file to PNG
    python scripts/render.py <file.puml> --dry-run     # Print resolved source
    python scripts/render.py --all                     # Render all diagrams/
    python scripts/render.py --all --png               # Render all as PNG
"""
import argparse
import os
import re
import subprocess
import sys

DIAGRAMS_DIR = "diagrams"
RENDERED_DIR = "rendered"
INCLUDE_RE = re.compile(r"^\s*!include\s+(.+)\s*$", re.MULTILINE)


def resolve_includes(source: str, base_dir: str, search_paths: list[str] | None = None, seen: set | None = None) -> str:
    """Recursively inline local !include directives. Remote URLs are left untouched.

    Args:
        source: PlantUML source text
        base_dir: Directory to resolve relative includes from
        search_paths: Additional directories to search if include not found relative to base_dir
        seen: Set of already-included paths (circular detection)
    """
    if seen is None:
        seen = set()

    def replacer(match):
        path_str = match.group(1).strip()
        if path_str.startswith("http://") or path_str.startswith("https://"):
            return match.group(0)
        if path_str.startswith("<") and path_str.endswith(">"):
            return match.group(0)

        # Try relative to base_dir first
        full_path = os.path.normpath(os.path.join(base_dir, path_str))

        # If not found, try search paths
        if not os.path.isfile(full_path) and search_paths:
            for sp in search_paths:
                candidate = os.path.normpath(os.path.join(sp, path_str))
                if os.path.isfile(candidate):
                    full_path = candidate
                    break

        if full_path in seen:
            raise ValueError(f"Circular include detected: {full_path}")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Include file not found: {full_path}")
        seen.add(full_path)
        content = open(full_path).read()
        inc_dir = os.path.dirname(full_path)
        resolved = resolve_includes(content, base_dir=inc_dir, search_paths=search_paths, seen=seen)
        seen.discard(full_path)
        return resolved

    return INCLUDE_RE.sub(replacer, source)


def _get_plantuml_bin() -> str:
    """Get PlantUML binary path from env var."""
    return os.environ.get("PLANTUML_BIN", "plantuml")


def render_plantuml(source: str, fmt: str = "svg") -> bytes:
    """Render PlantUML source via local PlantUML binary."""
    plantuml_bin = _get_plantuml_bin()
    try:
        result = subprocess.run(
            [plantuml_bin, f"-t{fmt}", "-pipe"],
            input=source.encode("utf-8"),
            capture_output=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"PlantUML not found at '{plantuml_bin}'. "
            "Run via Docker or set PLANTUML_BIN."
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"PlantUML rendering failed:\n{result.stderr.decode('utf-8', errors='replace')}"
        )
    return result.stdout


def get_client_paths(root: str, client: str) -> tuple[str, str, list[str]]:
    """Return (diagrams_dir, rendered_dir, search_paths) for a client."""
    client_dir = os.path.join(root, "clients", client)
    if not os.path.isdir(client_dir):
        print(f"Client '{client}' not found in clients/", file=sys.stderr)
        sys.exit(1)
    diagrams_dir = os.path.join(client_dir, "diagrams")
    rendered_dir = os.path.join(client_dir, "rendered")
    search_paths = [
        os.path.join(client_dir, "models"),
        os.path.join(root, "src", "skhema", "models"),
        os.path.join(root, "src", "skhema", "lib"),
    ]
    return diagrams_dir, rendered_dir, search_paths


def find_all_diagrams(diagrams_path: str) -> list[str]:
    """Find all .puml files under the given diagrams directory."""
    results = []
    for dirpath, _, filenames in os.walk(diagrams_path):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results


def output_path(source_path: str, diagrams_dir: str, rendered_dir: str, fmt: str) -> str:
    """Compute output path mirroring diagrams structure into rendered dir."""
    rel = os.path.relpath(source_path, diagrams_dir)
    name = os.path.splitext(rel)[0] + f".{fmt}"
    return os.path.join(rendered_dir, name)


def render_file(source_path: str, diagrams_dir: str, rendered_dir: str, root: str, fmt: str, dry_run: bool, animate: bool = False, search_paths: list[str] | None = None, output_override: str | None = None) -> bool:
    """Render a single .puml file. Returns True on success."""
    print(f"Rendering: {os.path.relpath(source_path, root)}")
    source = open(source_path).read()
    base_dir = os.path.dirname(source_path)

    try:
        resolved = resolve_includes(source, base_dir=base_dir, search_paths=search_paths)
    except (ValueError, FileNotFoundError) as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False

    if dry_run:
        print(resolved)
        return True

    try:
        image_data = render_plantuml(resolved, fmt=fmt)
    except Exception as e:
        print(f"  ERROR: PlantUML rendering failed: {e}", file=sys.stderr)
        return False

    # Inject a white background rect into SVGs so viewers that ignore the
    # CSS background property still show a white canvas.
    if fmt == "svg":
        import re as _re
        svg_text = image_data.decode("utf-8")
        svg_text = _re.sub(
            r'(<svg\b[^>]*viewBox="0 0 (\d+) (\d+)"[^>]*>)',
            r'\1<rect width="\2" height="\3" fill="#FFFFFF"/>',
            svg_text,
            count=1,
        )
        image_data = svg_text.encode("utf-8")

    if output_override:
        out = os.path.abspath(output_override)
    else:
        out = output_path(source_path, diagrams_dir, rendered_dir, fmt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(image_data)
    print(f"  -> {os.path.relpath(out, root)}")

    if animate and fmt == "svg":
        from skhema.animate import animate_svg
        svg_content = open(out, "r").read()
        result, count = animate_svg(svg_content, return_count=True)
        if count > 0:
            with open(out, "w") as f:
                f.write(result)
            print(f"  Animated {count} arrow(s)")

    return True


def main():
    parser = argparse.ArgumentParser(description="Render PlantUML diagrams via local PlantUML binary")
    parser.add_argument("file", nargs="?", help="Path to .puml file")
    parser.add_argument("--all", action="store_true", help="Render all diagrams/")
    parser.add_argument("--client", help="Client name (looks in clients/<name>/diagrams/)")
    parser.add_argument("--png", action="store_true", help="Output PNG instead of SVG")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved source only")
    parser.add_argument("--animate", action="store_true", help="Add marching-ant animation to ~ arrows (SVG only)")
    parser.add_argument("--output", help="Explicit output path for rendered file")
    args = parser.parse_args()

    if not args.file and not args.all:
        parser.error("Provide a file path or use --all")

    if args.output and args.all:
        parser.error("--output cannot be used with --all")

    if args.animate and args.png:
        print("Warning: --animate is ignored with --png (SVG only)", file=sys.stderr)

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fmt = "png" if args.png else "svg"

    # Determine directories based on --client flag
    if args.client:
        diagrams_dir, rendered_dir, search_paths = get_client_paths(root, args.client)
    else:
        diagrams_dir = os.path.join(root, "skhema", DIAGRAMS_DIR)
        rendered_dir = os.path.join(root, RENDERED_DIR)
        search_paths = None

    if args.all:
        files = find_all_diagrams(diagrams_dir)
        if not files:
            print(f"No .puml files found in {os.path.relpath(diagrams_dir, root)}/")
            return
        failures = []
        for f in files:
            if not render_file(f, diagrams_dir, rendered_dir, root, fmt, args.dry_run, animate=args.animate, search_paths=search_paths):
                failures.append(f)
        if failures:
            print(f"\n{len(failures)} file(s) failed:", file=sys.stderr)
            for f in failures:
                print(f"  - {os.path.relpath(f, root)}", file=sys.stderr)
            sys.exit(1)
    else:
        source_path = os.path.abspath(args.file)
        if not os.path.isfile(source_path):
            print(f"File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        if not render_file(source_path, diagrams_dir, rendered_dir, root, fmt, args.dry_run, animate=args.animate, search_paths=search_paths, output_override=args.output):
            sys.exit(1)


if __name__ == "__main__":
    main()
