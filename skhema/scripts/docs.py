#!/usr/bin/env python3
"""Generate a self-contained HTML architecture handbook for a client.

Usage:
    python scripts/docs.py --client demo
    python scripts/docs.py --client demo --title "NovaPay"
    python scripts/docs.py --client demo --output novapay-v2.html
"""
import argparse
import html as html_mod
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gallery import (
    discover_diagrams,
    group_by_type,
    diagram_name,
    parse_client_yaml,
    TYPE_ORDER,
    TYPE_LABELS,
)


DOCS_CSS = """
:root { --accent: {accent_color}; }
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', system-ui, Arial, sans-serif;
  margin: 0; padding: 0;
  color: #1a1a1a; background: #fff; line-height: 1.6;
}
a { color: var(--accent); }

/* Cover */
.cover {
  padding: 80px 40px 60px;
  border-bottom: 3px solid var(--accent);
}
.cover h1 { font-size: 2.6rem; margin: 0 0 8px; color: #111; }
.cover .subtitle { font-size: 1.2rem; color: #555; margin: 0 0 24px; }
.cover .meta { font-size: 0.9rem; color: #777; }

/* TOC */
.toc {
  padding: 40px 40px 32px;
  border-bottom: 1px solid #e5e7eb;
}
.toc h2 { font-size: 1.3rem; margin: 0 0 16px; color: #333; }
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc ul li { margin-bottom: 6px; }
.toc ul li a { color: var(--accent); text-decoration: none; font-size: 0.95rem; }
.toc ul li a:hover { text-decoration: underline; }

/* Overview */
.overview {
  padding: 32px 40px;
  border-bottom: 1px solid #e5e7eb;
}

/* Doc section */
.doc-section {
  padding: 40px 40px 32px;
  border-bottom: 1px solid #e5e7eb;
}
.doc-section h2 {
  font-size: 1.6rem; margin: 0 0 24px;
  color: #111;
  border-bottom: 2px solid var(--accent);
  padding-bottom: 8px;
}
.section-overview { margin-bottom: 32px; color: #444; }

/* Diagram block */
.diagram-block { margin-bottom: 48px; }
.diagram-block h3 { font-size: 1.15rem; color: #333; margin: 0 0 12px; }
.diagram-svg {
  width: 100%; overflow: auto;
  border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 16px; background: #fafafa;
  margin-bottom: 16px;
}
.diagram-svg svg { max-width: 100%; height: auto; display: block; }
.prose { color: #444; font-size: 0.95rem; }
.prose h1, .prose h2, .prose h3, .prose h4 { color: #222; margin-top: 1.2em; }
.prose p { margin: 0 0 12px; }
.prose ul, .prose ol { margin: 0 0 12px; padding-left: 24px; }
.prose code { background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
.prose pre { background: #f3f4f6; padding: 14px 16px; border-radius: 6px; overflow: auto; }
.prose pre code { background: none; padding: 0; }
.prose blockquote {
  border-left: 4px solid var(--accent);
  margin: 0 0 12px; padding: 8px 16px;
  color: #555; background: #fffbeb;
}
.prose table { border-collapse: collapse; width: 100%; margin-bottom: 12px; font-size: 0.92rem; }
.prose th { background: #f3f4f6; border: 1px solid #d1d5db; padding: 8px 12px; text-align: left; }
.prose td { border: 1px solid #d1d5db; padding: 8px 12px; }
.prose tr:nth-child(even) td { background: #f9fafb; }

/* Footer */
.footer {
  padding: 24px 40px;
  margin-top: 40px;
  border-top: 1px solid #e5e7eb;
  font-size: 0.82rem; color: #999;
}

/* Print */
@media print {
  body { font-size: 11pt; }
  .cover { padding: 40px 20px 30px; border-bottom: 2pt solid var(--accent); }
  .cover h1 { font-size: 2rem; }
  .toc, .overview, .doc-section, .footer { padding: 20px; }
  .doc-section { page-break-before: always; }
  .diagram-block { margin-bottom: 32px; }
  .diagram-block h3 { break-after: avoid; page-break-after: avoid; }
  .diagram-svg { break-inside: avoid; page-break-inside: avoid; border: 1pt solid #ccc; background: #fff; }
  .diagram-svg svg { max-width: 100%; max-height: 480pt; }
  .prose h1, .prose h2, .prose h3, .prose h4 { break-after: avoid; page-break-after: avoid; }
  .prose p { orphans: 4; widows: 4; }
  .prose li { orphans: 3; widows: 3; }
  .prose table { break-inside: avoid; page-break-inside: avoid; }
  .prose blockquote { break-inside: avoid; page-break-inside: avoid; }
  .prose pre { break-inside: avoid; page-break-inside: avoid; }
  .prose ul, .prose ol { orphans: 3; widows: 3; }
  .section-overview { break-inside: avoid; page-break-inside: avoid; }
  h2 { break-after: avoid; page-break-after: avoid; }
  a { color: inherit; text-decoration: none; }
}
"""


def parse_markdown(md: str) -> str:
    """Convert markdown to HTML using mistune."""
    import mistune
    return mistune.html(md)


def generate_docs_html(
    client_name: str,
    subtitle: str,
    rendered_dir: str,
    docs_dir: str,
    accent_color: str = "#D97706",
    section_order: list[str] | None = None,
) -> str:
    """Generate a self-contained HTML architecture handbook."""
    svg_files = discover_diagrams(rendered_dir)
    groups = group_by_type(svg_files, rendered_dir)
    total = len(svg_files)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    effective_order = section_order or [t for t in TYPE_ORDER if t in groups]

    # Build cover
    subtitle_html = f'<p class="subtitle">{html_mod.escape(subtitle)}</p>' if subtitle else ""
    cover_html = (
        f'<section class="cover">'
        f'<h1>{html_mod.escape(client_name)}</h1>'
        f'{subtitle_html}'
        f'<p class="meta">Generated {now} &mdash; {total} diagram(s)</p>'
        f'</section>'
    )

    # Build TOC
    toc_items = ""
    for dtype in effective_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        toc_items += f'<li><a href="#section-{dtype}">{html_mod.escape(label)}</a></li>'
    toc_html = (
        f'<nav class="toc" id="toc">'
        f'<h2>Table of Contents</h2>'
        f'<ul>{toc_items}</ul>'
        f'</nav>'
    )

    # Client overview
    overview_html = ""
    if os.path.isdir(docs_dir):
        overview_path = os.path.join(docs_dir, "overview.md")
        if os.path.isfile(overview_path):
            with open(overview_path) as f:
                md_content = f.read()
            overview_html = f'<section class="overview"><div class="prose">{parse_markdown(md_content)}</div></section>'

    # Build sections
    sections_html = []
    for dtype in effective_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())

        # Section _overview.md
        section_overview_html = ""
        if os.path.isdir(docs_dir):
            sec_overview_path = os.path.join(docs_dir, dtype, "_overview.md")
            if os.path.isfile(sec_overview_path):
                with open(sec_overview_path) as f:
                    sec_md = f.read()
                section_overview_html = (
                    f'<div class="section-overview prose">{parse_markdown(sec_md)}</div>'
                )

        # Individual diagrams
        diagrams_html = ""
        for svg_path in groups[dtype]:
            name = diagram_name(svg_path)
            with open(svg_path) as f:
                svg_content = f.read()
            svg_inline = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()

            # Companion prose
            prose_html = ""
            if os.path.isdir(docs_dir):
                stem = os.path.splitext(os.path.basename(svg_path))[0]
                companion_path = os.path.join(docs_dir, dtype, f"{stem}.md")
                if os.path.isfile(companion_path):
                    with open(companion_path) as f:
                        companion_md = f.read()
                    prose_html = f'<div class="prose">{parse_markdown(companion_md)}</div>'

            diagrams_html += (
                f'<div class="diagram-block">'
                f'<h3>{html_mod.escape(name)}</h3>'
                f'<div class="diagram-svg">{svg_inline}</div>'
                f'{prose_html}'
                f'</div>'
            )

        sections_html.append(
            f'<section class="doc-section" id="section-{dtype}">'
            f'<h2>{html_mod.escape(label)}</h2>'
            f'{section_overview_html}'
            f'{diagrams_html}'
            f'</section>'
        )

    footer_html = (
        f'<footer class="footer">Generated by skhema on {now}</footer>'
    )

    css = DOCS_CSS.replace("{accent_color}", accent_color)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(client_name)} — Architecture Handbook</title>
<style>{css}</style>
</head>
<body>
{cover_html}
{toc_html}
{overview_html}
{"".join(sections_html)}
{footer_html}
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate architecture handbook for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--title", help="Override client display name")
    parser.add_argument("--output", help="Output filename (relative to client dir)")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    rendered_dir = os.path.join(client_dir, "rendered")
    docs_dir = os.path.join(client_dir, "docs")
    if not os.path.isdir(rendered_dir) or not discover_diagrams(rendered_dir):
        print(f"No rendered diagrams found. Run: python scripts/render.py --client {args.client} --all", file=sys.stderr)
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
    )

    out_name = args.output or f"{args.client}-architecture.html"
    out_path = os.path.join(client_dir, out_name)
    with open(out_path, "w") as f:
        f.write(docs_html)
    print(f"Docs -> {out_path}")


if __name__ == "__main__":
    main()
