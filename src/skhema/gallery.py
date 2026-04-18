#!/usr/bin/env python3
"""Generate a self-contained HTML gallery for a client's rendered diagrams.

Usage:
    python -m skhema.gallery --client acme
    python -m skhema.gallery --client acme --history 3
    python -m skhema.gallery --client acme --history 0
    python -m skhema.gallery --client acme --title "Acme Corp"
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TYPE_ORDER = ["c4", "sequence", "erd", "deployment", "excalidraw", "other"]
TYPE_LABELS = {
    "c4": "C4 Diagrams",
    "sequence": "Sequence Diagrams",
    "erd": "Entity Relationship Diagrams",
    "deployment": "Deployment Diagrams",
    "excalidraw": "Excalidraw Diagrams",
    "other": "Other Diagrams",
}


def parse_client_yaml(path: str) -> dict:
    """Parse client.yaml using PyYAML with defaults."""
    import yaml
    defaults = {"name": "", "subtitle": "", "accent_color": "#D97706", "sections": []}
    if not os.path.isfile(path):
        return defaults
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return {**defaults, **data}


def discover_diagrams(rendered_dir: str) -> list[str]:
    """Find all .svg files in the rendered directory."""
    results = []
    for dirpath, _, filenames in os.walk(rendered_dir):
        for f in sorted(filenames):
            if f.endswith(".svg"):
                results.append(os.path.join(dirpath, f))
    return results


def group_by_type(svg_paths: list[str], rendered_dir: str) -> dict[str, list[str]]:
    """Group SVG paths by diagram type (subdirectory name)."""
    groups: dict[str, list[str]] = {}
    for path in svg_paths:
        rel = os.path.relpath(path, rendered_dir)
        parts = rel.split(os.sep)
        dtype = parts[0] if len(parts) > 1 else "other"
        groups.setdefault(dtype, []).append(path)
    return groups


def get_history(source_puml: str, max_versions: int) -> list[dict]:
    """Get git history for a .puml source file.

    Returns list of {hash, date, message} dicts, most recent first.
    """
    if max_versions <= 0 or not os.path.isfile(source_puml):
        return []
    try:
        result = subprocess.run(
            ["git", "log", f"-{max_versions + 1}", "--format=%H|%ai|%s", "--", source_puml],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        entries = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                entries.append({"hash": parts[0], "date": parts[1], "message": parts[2]})
        return entries[1:max_versions + 1] if len(entries) > 1 else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def svg_to_source_path(svg_path: str, rendered_dir: str, diagrams_dir: str) -> str:
    """Map a rendered SVG back to its source .puml file."""
    rel = os.path.relpath(svg_path, rendered_dir)
    puml_rel = os.path.splitext(rel)[0] + ".puml"
    return os.path.join(diagrams_dir, puml_rel)


def diagram_name(svg_path: str) -> str:
    """Convert filename to display name: kebab-case -> Title Case."""
    name = os.path.splitext(os.path.basename(svg_path))[0]
    return name.replace("-", " ").replace("_", " ").title()


def _clean_svg(svg_content: str) -> str:
    """Strip XML declaration for safe inlining into HTML."""
    return re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates" / "gallery"


def _build_diagram_card(
    svg_path: str,
    dtype: str,
    rendered_dir: str,
    diagrams_dir: str | None,
    history: int,
    adr_map: dict,
) -> dict:
    """Build the render context for a single diagram card."""
    name = diagram_name(svg_path)
    svg_content = open(svg_path).read()
    svg_inline = _clean_svg(svg_content)
    rel_path = os.path.relpath(svg_path, os.path.dirname(rendered_dir))
    animated = "marching-ant" in svg_content

    versions = []
    if history > 0 and diagrams_dir:
        source = svg_to_source_path(svg_path, rendered_dir, diagrams_dir)
        for v in get_history(source, history):
            versions.append({
                "date_short": v["date"][:10],
                "message": v["message"][:60],
            })

    diagram_id = os.path.splitext(os.path.basename(svg_path))[0]
    related = adr_map.get(diagram_id, [])
    adrs = [
        {"number": a.number, "title": a.title, "status": a.status}
        for a in related
    ]

    return {
        "name": name,
        "svg_inline": svg_inline,
        "href": rel_path,
        "search_text": f"{name} {dtype}",
        "animated": animated,
        "history": versions,
        "adrs": adrs,
    }


def generate_gallery_html(
    client_name: str,
    rendered_dir: str,
    history: int = 3,
    diagrams_dir: str | None = None,
    client_yaml_path: str | None = None,
    client_path: str | None = None,
) -> str:
    """Generate a self-contained HTML gallery page."""
    svg_files = discover_diagrams(rendered_dir)
    groups = group_by_type(svg_files, rendered_dir)
    total = len(svg_files)

    adr_map: dict = {}
    if client_path:
        from skhema.adr import discover_adrs
        for adr in discover_adrs(client_path):
            for elem_id in adr.elements:
                adr_map.setdefault(elem_id, []).append(adr)

    config = parse_client_yaml(client_yaml_path) if client_yaml_path else {"sections": [], "accent_color": "#D97706"}
    accent_color = config.get("accent_color") or "#D97706"
    section_order = config["sections"] if config["sections"] else [t for t in TYPE_ORDER if t in groups]

    sections = []
    for dtype in section_order:
        if dtype not in groups:
            continue
        diagrams = [
            _build_diagram_card(svg, dtype, rendered_dir, diagrams_dir, history, adr_map)
            for svg in groups[dtype]
        ]
        sections.append({
            "dtype": dtype,
            "label": TYPE_LABELS.get(dtype, dtype.title()),
            "diagrams": diagrams,
        })

    tpl_dir = _templates_dir()
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )

    # Render CSS first (uses accent_color)
    css_tpl = env.get_template("gallery.css")
    gallery_css = css_tpl.render(accent_color=accent_color)

    js = (tpl_dir / "gallery.js").read_text()

    page_tpl = env.get_template("gallery.html.j2")
    return page_tpl.render(
        client_name=client_name,
        sections=sections,
        total_diagrams=total,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        gallery_css=gallery_css,
        gallery_js=js,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate HTML gallery for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--history", type=int, default=3, help="Number of historical versions (default: 3, 0 to disable)")
    parser.add_argument("--title", help="Override client display name")
    args = parser.parse_args()

    from skhema._paths import find_repo_root
    root = find_repo_root()
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    rendered_dir = os.path.join(client_dir, "rendered")
    diagrams_dir = os.path.join(client_dir, "diagrams")
    if not os.path.isdir(rendered_dir) or not discover_diagrams(rendered_dir):
        print(f"No rendered diagrams found. Run: skhema render --client {args.client} --all", file=sys.stderr)
        sys.exit(1)

    client_yaml = os.path.join(client_dir, "client.yaml")
    client_name = args.title or args.client.replace("-", " ").replace("_", " ").title()
    gallery_html = generate_gallery_html(
        client_name=client_name,
        rendered_dir=rendered_dir,
        history=args.history,
        diagrams_dir=diagrams_dir,
        client_yaml_path=client_yaml,
        client_path=client_dir,
    )

    out_path = os.path.join(client_dir, "index.html")
    with open(out_path, "w") as f:
        f.write(gallery_html)
    print(f"Gallery -> {out_path}")


if __name__ == "__main__":
    main()
