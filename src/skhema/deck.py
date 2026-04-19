"""Export client diagrams as a self-contained Reveal.js HTML deck.

Usage:
    python -m skhema.deck --client acme                  # deck.html (default)
    python -m skhema.deck --client acme --pptx           # + deck.pptx
    python -m skhema.deck --client acme --theme dark     # theme variant
    python -m skhema.deck --client acme --no-notes       # strip speaker notes

The deck.html output is self-contained: Reveal.js JS/CSS and the skhema theme
are inlined. Open in any modern browser. For a PDF, append `?print-pdf` to
the URL and Save-as-PDF from the browser's print dialog.
"""
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from jinja2 import Environment, FileSystemLoader, select_autoescape

from skhema.render import resolve_includes, render_plantuml
from skhema.gallery import TYPE_LABELS, TYPE_ORDER, parse_client_yaml


class Diagram(NamedTuple):
    title: str
    svg_inline: str
    notes: str | None
    prose_html: str | None = None


class Section(NamedTuple):
    label: str
    diagrams: list[Diagram]


def discover_puml_files(diagrams_dir: str) -> list[str]:
    """Find all .puml files in the diagrams directory."""
    results = []
    for dirpath, _, filenames in os.walk(diagrams_dir):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results


def order_by_type(puml_files: list[str], diagrams_dir: str) -> list[str]:
    """Order files by type (c4 first, then sequence, etc.), alphabetical within type.
    Excalidraw diagrams are excluded from deck output."""

    def sort_key(path):
        rel = os.path.relpath(path, diagrams_dir)
        parts = rel.split(os.sep)
        dtype = parts[0] if len(parts) > 1 else "zzz"
        try:
            type_idx = TYPE_ORDER.index(dtype)
        except ValueError:
            type_idx = len(TYPE_ORDER)
        return (type_idx, rel)

    def is_excalidraw(path):
        rel = os.path.relpath(path, diagrams_dir)
        parts = rel.split(os.sep)
        return len(parts) > 1 and parts[0] == "excalidraw"

    return sorted([f for f in puml_files if not is_excalidraw(f)], key=sort_key)


def diagram_title(puml_path: str) -> str:
    """Convert filename to display title."""
    name = os.path.splitext(os.path.basename(puml_path))[0]
    return name.replace("-", " ").replace("_", " ").title()


def diagram_type(puml_path: str, diagrams_dir: str) -> str:
    """Return the top-level directory name as the diagram type."""
    rel = os.path.relpath(puml_path, diagrams_dir)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "other"


def clean_svg_for_embed(svg_bytes: bytes) -> str:
    """Strip XML declarations and DOCTYPE so the SVG can be safely inlined into HTML."""
    svg = svg_bytes.decode("utf-8")
    svg = re.sub(r"<\?xml[^?]*\?>\s*", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
    return svg.strip()


def read_companion_notes(puml_path: str, dtype: str, docs_dir: str | None) -> str | None:
    """Look up optional companion markdown for a diagram.

    Searches in this order:
      1. `<docs_dir>/<dtype>/<stem>.md` — typed subdirectory (matches docs.py)
      2. `<docs_dir>/<stem>.md` — flat fallback

    Returns the raw markdown text, or None.
    """
    if not docs_dir or not os.path.isdir(docs_dir):
        return None
    stem = os.path.splitext(os.path.basename(puml_path))[0]
    for candidate in (
        os.path.join(docs_dir, dtype, f"{stem}.md"),
        os.path.join(docs_dir, f"{stem}.md"),
    ):
        if os.path.isfile(candidate):
            return open(candidate).read().strip()
    return None


def _markdown_to_html(md: str) -> str:
    """Render companion markdown for inline display via mistune."""
    import mistune
    return mistune.html(md)


def build_sections(
    diagrams_dir: str,
    search_paths: list[str],
    docs_dir: str | None = None,
    include_notes: bool = True,
) -> tuple[list[Section], int]:
    """Build the per-type sections for the deck, rendering each .puml to inline SVG."""
    puml_files = order_by_type(discover_puml_files(diagrams_dir), diagrams_dir)

    grouped: dict[str, list[Diagram]] = {}
    for puml_path in puml_files:
        source = open(puml_path).read()
        try:
            resolved = resolve_includes(
                source, os.path.dirname(puml_path), search_paths
            )
        except (ValueError, FileNotFoundError) as e:
            print(f"  SKIP: {os.path.basename(puml_path)}: {e}", file=sys.stderr)
            continue

        try:
            svg_bytes = render_plantuml(resolved, fmt="svg")
        except Exception as e:
            print(f"  SKIP: {os.path.basename(puml_path)}: {e}", file=sys.stderr)
            continue

        dtype = diagram_type(puml_path, diagrams_dir)
        notes_md = (
            read_companion_notes(puml_path, dtype, docs_dir) if include_notes else None
        )
        prose_html = _markdown_to_html(notes_md) if notes_md else None
        diagram = Diagram(
            title=diagram_title(puml_path),
            svg_inline=clean_svg_for_embed(svg_bytes),
            notes=notes_md,
            prose_html=prose_html,
        )
        grouped.setdefault(dtype, []).append(diagram)

    sections: list[Section] = []
    total = 0
    for dtype in TYPE_ORDER:
        if dtype in grouped and grouped[dtype]:
            label = TYPE_LABELS.get(dtype, dtype.title())
            sections.append(Section(label=label, diagrams=grouped[dtype]))
            total += len(grouped[dtype])
    return sections, total


def load_adrs(client_path: str) -> list[dict]:
    """Load ADRs for the client, if any."""
    adr_dir = os.path.join(client_path, "adrs")
    if not os.path.isdir(adr_dir):
        return []
    try:
        from skhema.adr import discover_adrs
    except ImportError:
        return []
    import mistune

    markdown = mistune.create_markdown(escape=False)
    adrs = []
    for adr in discover_adrs(client_path):
        body_html = markdown(adr.body) if getattr(adr, "body", None) else ""
        adrs.append({
            "number": adr.number,
            "title": adr.title,
            "status": adr.status,
            "body_html": body_html,
        })
    return adrs


def _vendor_dir() -> Path:
    return Path(__file__).parent / "vendor" / "reveal"


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates" / "deck"


def render_deck_html(
    client: dict,
    sections: list[Section],
    adrs: list[dict],
    total_diagrams: int,
) -> str:
    """Render the Reveal.js HTML deck via Jinja2."""
    vendor = _vendor_dir()
    reveal_js = (vendor / "reveal.min.js").read_text()
    reveal_css = (vendor / "reveal.min.css").read_text()
    theme_white_css = (vendor / "theme-white.min.css").read_text()

    tpl_dir = _templates_dir()
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Render theme.css first (it uses the accent colour from client.yaml)
    theme_tpl = env.get_template("theme.css")
    skhema_theme_css = theme_tpl.render(client=client)

    deck_tpl = env.get_template("deck.html.j2")
    return deck_tpl.render(
        client=client,
        sections=sections,
        adrs=adrs,
        total_diagrams=total_diagrams,
        generated_at=datetime.now(),
        reveal_js=reveal_js,
        reveal_css=reveal_css,
        theme_white_css=theme_white_css,
        skhema_theme_css=skhema_theme_css,
    )


def generate_pptx_deck(client_name: str, sections: list[Section], output_path: str) -> None:
    """Generate a PowerPoint deck from rendered sections. Requires python-pptx."""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError:
        print(
            "PowerPoint export requires python-pptx. Install with: uv pip install python-pptx",
            file=sys.stderr,
        )
        sys.exit(1)


    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    txBox = slide.shapes.add_textbox(Inches(2), Inches(2.5), Inches(9), Inches(2))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = client_name
    p.font.size = Pt(44)
    p.font.bold = True
    p2 = tf.add_paragraph()
    p2.text = "Architecture Diagrams"
    p2.font.size = Pt(24)

    # PPTX needs PNG, not SVG — re-render each diagram
    from skhema.render import resolve_includes  # noqa: F401 — already imported above

    for section in sections:
        for diagram in section.diagrams:
            # Section already rendered SVG; for PPTX we need PNG from the same source.
            # Re-render PNG would require original .puml source — we skip PPTX SVG embed
            # for now and use a simple text slide as placeholder. Real PNG round-trip
            # lives in Phase 10 when tests verify it.
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
            txBox.text_frame.paragraphs[0].text = diagram.title
            txBox.text_frame.paragraphs[0].font.size = Pt(20)
            txBox.text_frame.paragraphs[0].font.bold = True

    prs.save(output_path)
    print(f"PPTX -> {output_path}")


def find_repo_root() -> str:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "clients").is_dir():
            return str(parent)
    return os.getcwd()


def main():
    parser = argparse.ArgumentParser(
        description="Export client diagrams as a self-contained Reveal.js HTML deck.",
        epilog=(
            "\nTo export as PDF: open deck.html?print-pdf in any browser, "
            "then Print → Save as PDF (landscape, no margins)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--pptx", action="store_true", help="Also emit deck.pptx (needs python-pptx)")
    parser.add_argument("--theme", default="light", choices=["light", "dark"],
                        help="Colour theme (default: light)")
    parser.add_argument("--no-notes", action="store_true",
                        help="Strip speaker notes from companion markdown")
    args = parser.parse_args()

    root = find_repo_root()
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    diagrams_dir = os.path.join(client_dir, "diagrams")
    docs_dir = os.path.join(client_dir, "docs")
    search_paths = [
        os.path.join(client_dir, "models"),
        os.path.join(root, "src", "skhema", "models"),
        os.path.join(root, "src", "skhema", "lib"),
    ]

    client_yaml = os.path.join(client_dir, "client.yaml")
    client_config = parse_client_yaml(client_yaml)
    if not client_config.get("name"):
        client_config["name"] = args.client.replace("-", " ").replace("_", " ").title()

    sections, total = build_sections(
        diagrams_dir=diagrams_dir,
        search_paths=search_paths,
        docs_dir=docs_dir,
        include_notes=not args.no_notes,
    )
    if not sections:
        print(f"No diagrams found in {diagrams_dir}", file=sys.stderr)
        sys.exit(1)

    adrs = load_adrs(client_dir)

    html = render_deck_html(
        client=client_config,
        sections=sections,
        adrs=adrs,
        total_diagrams=total,
    )

    out_html = os.path.join(client_dir, "deck.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Deck -> {out_html}")
    print("       Open in any browser to present; append ?print-pdf and Save-as-PDF for a PDF copy.")

    if args.pptx:
        out_pptx = os.path.join(client_dir, "deck.pptx")
        generate_pptx_deck(client_config["name"], sections, out_pptx)


if __name__ == "__main__":
    main()
