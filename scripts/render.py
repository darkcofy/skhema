#!/usr/bin/env python3
"""Render PlantUML diagrams via the Kroki public API.

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
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

KROKI_BASE = "https://kroki.io/plantuml"
DIAGRAMS_DIR = "diagrams"
RENDERED_DIR = "rendered"
INCLUDE_RE = re.compile(r"^\s*!include\s+(.+)\s*$", re.MULTILINE)


def resolve_includes(source: str, base_dir: str, seen: set | None = None) -> str:
    """Recursively inline local !include directives. Remote URLs are left untouched."""
    if seen is None:
        seen = set()

    def replacer(match):
        path_str = match.group(1).strip()
        if path_str.startswith("http://") or path_str.startswith("https://"):
            return match.group(0)
        if path_str.startswith("<") and path_str.endswith(">"):
            return match.group(0)
        full_path = os.path.normpath(os.path.join(base_dir, path_str))
        if full_path in seen:
            raise ValueError(f"Circular include detected: {full_path}")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Include file not found: {full_path}")
        seen.add(full_path)
        content = open(full_path).read()
        inc_dir = os.path.dirname(full_path)
        resolved = resolve_includes(content, base_dir=inc_dir, seen=seen)
        seen.discard(full_path)
        return resolved

    return INCLUDE_RE.sub(replacer, source)


def post_to_kroki(source: str, fmt: str = "svg") -> bytes:
    """POST resolved PlantUML source to Kroki and return the response bytes."""
    url = f"{KROKI_BASE}/{fmt}"
    data = source.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "text/plain",
        "User-Agent": "arch-diagrams/1.0 (PlantUML renderer)",
    })

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Retrying in {wait}s (HTTP {e.code})...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    return b""


def find_all_diagrams(root: str) -> list[str]:
    """Find all .puml files under the diagrams/ directory."""
    diagrams_path = os.path.join(root, DIAGRAMS_DIR)
    results = []
    for dirpath, _, filenames in os.walk(diagrams_path):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results


def output_path(source_path: str, root: str, fmt: str) -> str:
    """Compute output path mirroring diagrams/ structure into rendered/."""
    rel = os.path.relpath(source_path, os.path.join(root, DIAGRAMS_DIR))
    name = os.path.splitext(rel)[0] + f".{fmt}"
    return os.path.join(root, RENDERED_DIR, name)


def render_file(source_path: str, root: str, fmt: str, dry_run: bool, animate: bool = False) -> bool:
    """Render a single .puml file. Returns True on success."""
    print(f"Rendering: {os.path.relpath(source_path, root)}")
    source = open(source_path).read()
    base_dir = os.path.dirname(source_path)

    try:
        resolved = resolve_includes(source, base_dir=base_dir)
    except (ValueError, FileNotFoundError) as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False

    if dry_run:
        print(resolved)
        return True

    try:
        image_data = post_to_kroki(resolved, fmt)
    except Exception as e:
        print(f"  ERROR: Kroki request failed: {e}", file=sys.stderr)
        return False

    out = output_path(source_path, root, fmt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(image_data)
    print(f"  -> {os.path.relpath(out, root)}")

    if animate and fmt == "svg":
        from scripts.animate import animate_svg
        svg_content = open(out, "r").read()
        result, count = animate_svg(svg_content, return_count=True)
        if count > 0:
            with open(out, "w") as f:
                f.write(result)
            print(f"  Animated {count} arrow(s)")

    return True


def main():
    parser = argparse.ArgumentParser(description="Render PlantUML diagrams via Kroki API")
    parser.add_argument("file", nargs="?", help="Path to .puml file")
    parser.add_argument("--all", action="store_true", help="Render all diagrams/")
    parser.add_argument("--png", action="store_true", help="Output PNG instead of SVG")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved source only")
    parser.add_argument("--animate", action="store_true", help="Add marching-ant animation to ~ arrows (SVG only)")
    args = parser.parse_args()

    if not args.file and not args.all:
        parser.error("Provide a file path or use --all")

    if args.animate and args.png:
        print("Warning: --animate is ignored with --png (SVG only)", file=sys.stderr)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fmt = "png" if args.png else "svg"

    if args.all:
        files = find_all_diagrams(root)
        if not files:
            print("No .puml files found in diagrams/")
            return
        failures = []
        for f in files:
            if not render_file(f, root, fmt, args.dry_run, animate=args.animate):
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
        if not render_file(source_path, root, fmt, args.dry_run, animate=args.animate):
            sys.exit(1)


if __name__ == "__main__":
    main()
