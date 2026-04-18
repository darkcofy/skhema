#!/usr/bin/env python3
"""Generate a self-contained HTML architecture handbook for a client.

Usage:
    python -m skhema.docs --client demo
    python -m skhema.docs --client demo --title "NovaPay"
    python -m skhema.docs --client demo --output novapay-v2.html
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from skhema.gallery import (
    TYPE_LABELS,
    TYPE_ORDER,
    diagram_name,
    discover_diagrams,
    group_by_type,
    parse_client_yaml,
)


def parse_markdown(md: str) -> str:
    """Convert markdown to HTML using mistune."""
    import mistune
    return mistune.html(md)


def _clean_svg(svg_content: str) -> str:
    return re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates" / "handbook"


def _read_md(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    return open(path).read()


def _build_diagram_block(
    svg_path: str,
    dtype: str,
    docs_dir: str,
    adr_map: dict,
) -> dict:
    name = diagram_name(svg_path)
    svg_inline = _clean_svg(open(svg_path).read())

    prose_html = None
    if os.path.isdir(docs_dir):
        stem = os.path.splitext(os.path.basename(svg_path))[0]
        companion_md = _read_md(os.path.join(docs_dir, dtype, f"{stem}.md"))
        if companion_md:
            prose_html = parse_markdown(companion_md)

    stem = os.path.splitext(os.path.basename(svg_path))[0]
    related = adr_map.get(stem, [])
    adrs = []
    for adr in related:
        adr_body = open(adr.path).read() if adr.path else ""
        adrs.append({
            "number": adr.number,
            "title": adr.title,
            "status": adr.status,
            "body_html": parse_markdown(adr_body),
        })

    return {
        "name": name,
        "svg_inline": svg_inline,
        "prose_html": prose_html,
        "adrs": adrs,
    }


def generate_docs_html(
    client_name: str,
    subtitle: str,
    rendered_dir: str,
    docs_dir: str,
    accent_color: str = "#D97706",
    section_order: list[str] | None = None,
    client_path: str | None = None,
) -> str:
    """Generate a self-contained HTML architecture handbook."""
    svg_files = discover_diagrams(rendered_dir)
    groups = group_by_type(svg_files, rendered_dir)
    total = len(svg_files)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    adr_map: dict = {}
    if client_path:
        from skhema.adr import discover_adrs
        for adr in discover_adrs(client_path):
            for elem_id in adr.elements:
                adr_map.setdefault(elem_id, []).append(adr)

    effective_order = section_order or [t for t in TYPE_ORDER if t in groups]

    overview_html = None
    if os.path.isdir(docs_dir):
        overview_md = _read_md(os.path.join(docs_dir, "overview.md"))
        if overview_md:
            overview_html = parse_markdown(overview_md)

    sections = []
    for dtype in effective_order:
        if dtype not in groups:
            continue

        section_overview_html = None
        if os.path.isdir(docs_dir):
            sec_overview_md = _read_md(os.path.join(docs_dir, dtype, "_overview.md"))
            if sec_overview_md:
                section_overview_html = parse_markdown(sec_overview_md)

        diagrams = [
            _build_diagram_block(svg, dtype, docs_dir, adr_map)
            for svg in groups[dtype]
        ]

        sections.append({
            "dtype": dtype,
            "label": TYPE_LABELS.get(dtype, dtype.title()),
            "overview_html": section_overview_html,
            "diagrams": diagrams,
        })

    tpl_dir = _templates_dir()
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )

    css_tpl = env.get_template("handbook.css")
    handbook_css = css_tpl.render(accent_color=accent_color)

    page_tpl = env.get_template("handbook.html.j2")
    return page_tpl.render(
        client_name=client_name,
        subtitle=subtitle,
        sections=sections,
        total_diagrams=total,
        generated_at=now,
        overview_html=overview_html,
        handbook_css=handbook_css,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate architecture handbook for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--title", help="Override client display name")
    parser.add_argument("--output", help="Output filename (relative to client dir)")
    args = parser.parse_args()

    from skhema._paths import find_repo_root
    root = find_repo_root()
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    rendered_dir = os.path.join(client_dir, "rendered")
    docs_dir = os.path.join(client_dir, "docs")
    if not os.path.isdir(rendered_dir) or not discover_diagrams(rendered_dir):
        print(f"No rendered diagrams found. Run: skhema render --client {args.client} --all", file=sys.stderr)
        sys.exit(1)

    config = parse_client_yaml(os.path.join(client_dir, "client.yaml"))
    client_name = args.title or config["name"] or args.client.replace("-", " ").replace("_", " ").title()
    subtitle = config.get("subtitle", "")
    accent_color = config.get("accent_color", "#D97706")
    section_order = config["sections"] if config["sections"] else None

    docs_html = generate_docs_html(
        client_name=client_name,
        subtitle=subtitle,
        rendered_dir=rendered_dir,
        docs_dir=docs_dir,
        accent_color=accent_color,
        section_order=section_order,
        client_path=client_dir,
    )

    out_name = args.output or f"{args.client}-architecture.html"
    out_path = os.path.join(client_dir, out_name)
    with open(out_path, "w") as f:
        f.write(docs_html)
    print(f"Docs -> {out_path}")


if __name__ == "__main__":
    main()
