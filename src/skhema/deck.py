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


_TITLE_ACRONYMS = {
    "Ai": "AI", "Aws": "AWS", "Bi": "BI", "Ci": "CI", "Cd": "CD",
    "Ml": "ML", "Sql": "SQL", "Api": "API", "Http": "HTTP", "Https": "HTTPS",
    "Mcp": "MCP", "Crm": "CRM", "Erp": "ERP", "Pos": "POS", "Etl": "ETL",
    "Genai": "GenAI", "Llm": "LLM", "Rag": "RAG", "Svg": "SVG", "Pdf": "PDF",
    "Html": "HTML", "Yaml": "YAML", "Dsl": "DSL", "Cdc": "CDC", "Slo": "SLO",
    "Sla": "SLA", "Pii": "PII", "Ui": "UI", "Wms": "WMS",
}


def _fix_acronyms(text: str) -> str:
    """Restore canonical acronym casing after `.title()` lower-cases them."""
    for bad, good in _TITLE_ACRONYMS.items():
        text = re.sub(rf"\b{re.escape(bad)}\b", good, text)
    return text


def diagram_title(puml_path: str) -> str:
    """Convert filename to a client-facing display title.

    Strips the `structurizr-` prefix that Structurizr's CLI auto-adds to
    every exported .puml — clients don't care which tool produced a diagram.
    Restores canonical casing for common acronyms (AI, AWS, SQL, …).
    """
    name = os.path.splitext(os.path.basename(puml_path))[0]
    if name.startswith("structurizr-"):
        name = name[len("structurizr-"):]
    return _fix_acronyms(name.replace("-", " ").replace("_", " ").title())


def diagram_type(puml_path: str, diagrams_dir: str) -> str:
    """Return the top-level directory name as the diagram type."""
    rel = os.path.relpath(puml_path, diagrams_dir)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "other"


def clean_svg_for_embed(svg_bytes: bytes) -> str:
    """Strip XML declarations, DOCTYPE, and any hardcoded sizing on the
    root <svg> tag so the SVG can be safely inlined into HTML and scaled by
    CSS via its viewBox.

    PlantUML embeds dimensions in THREE places on the root tag:
      1. width="..." and height="..." attributes
      2. style="width:...;height:...;..." declarations
      3. <svg> inner style tags (rare)

    We strip (1) and the size-only declarations in (2). The viewBox is
    preserved so the SVG scales proportionally inside whatever CSS box
    contains it.
    """
    svg = svg_bytes.decode("utf-8")
    svg = re.sub(r"<\?xml[^?]*\?>\s*", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)

    def _strip_root_size(match: re.Match) -> str:
        tag = match.group(0)
        # Remove width="..." and height="..." attrs
        tag = re.sub(r'\s+width="[^"]*"', "", tag)
        tag = re.sub(r'\s+height="[^"]*"', "", tag)
        # Remove width:...; and height:...; declarations inside style="..."
        def _clean_style(m: re.Match) -> str:
            value = m.group(1)
            value = re.sub(r"(?:^|;)\s*width\s*:\s*[^;\"]+;?", ";", value)
            value = re.sub(r"(?:^|;)\s*height\s*:\s*[^;\"]+;?", ";", value)
            value = re.sub(r";{2,}", ";", value).strip(";").strip()
            if not value:
                return ""
            return f' style="{value}"'
        tag = re.sub(r'\s+style="([^"]*)"', _clean_style, tag, count=1)
        return tag

    svg = re.sub(r"<svg\b[^>]*>", _strip_root_size, svg, count=1)
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


def _render_one(
    puml_path: str,
    diagrams_dir: str,
    search_paths: list[str],
    docs_dir: str | None,
    include_notes: bool,
) -> Diagram | None:
    source = open(puml_path).read()
    try:
        resolved = resolve_includes(
            source, os.path.dirname(puml_path), search_paths
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"  SKIP: {os.path.basename(puml_path)}: {e}", file=sys.stderr)
        return None

    try:
        svg_bytes = render_plantuml(resolved, fmt="svg")
    except Exception as e:
        print(f"  SKIP: {os.path.basename(puml_path)}: {e}", file=sys.stderr)
        return None

    dtype = diagram_type(puml_path, diagrams_dir)
    notes_md = (
        read_companion_notes(puml_path, dtype, docs_dir) if include_notes else None
    )
    prose_html = _markdown_to_html(notes_md) if notes_md else None
    return Diagram(
        title=diagram_title(puml_path),
        svg_inline=clean_svg_for_embed(svg_bytes),
        notes=notes_md,
        prose_html=prose_html,
    )


def build_sections(
    diagrams_dir: str,
    search_paths: list[str],
    docs_dir: str | None = None,
    include_notes: bool = True,
    narrative: list[dict] | None = None,
) -> tuple[list[Section], int]:
    """Build deck sections.

    If `narrative` is provided (from client.yaml), it's a list of
    `{label, diagrams: [path, ...]}` dicts that drives section order,
    section labels, and per-section diagram order explicitly. Diagrams
    are referenced by their path relative to `diagrams_dir` (without the
    `.puml` extension — both forms accepted).

    When `narrative` is absent, we fall back to the type-based grouping
    with a within-type "story" ordering for C4 (landscape → context →
    containers → components → dynamic).
    """
    all_puml = discover_puml_files(diagrams_dir)

    if narrative:
        return _build_from_narrative(
            narrative, all_puml, diagrams_dir, search_paths, docs_dir, include_notes
        )

    # Default: group by type, with improved within-type ordering for C4.
    puml_files = order_by_type(all_puml, diagrams_dir)
    grouped: dict[str, list[Diagram]] = {}
    for puml_path in _reorder_c4_story(puml_files, diagrams_dir):
        diagram = _render_one(
            puml_path, diagrams_dir, search_paths, docs_dir, include_notes
        )
        if diagram is None:
            continue
        grouped.setdefault(diagram_type(puml_path, diagrams_dir), []).append(diagram)

    sections: list[Section] = []
    total = 0
    for dtype in TYPE_ORDER:
        if dtype in grouped and grouped[dtype]:
            label = TYPE_LABELS.get(dtype, dtype.title())
            sections.append(Section(label=label, diagrams=grouped[dtype]))
            total += len(grouped[dtype])
    return sections, total


# Within the C4 section we tell the story from the outside in:
# landscape → context → containers → L3 components → dynamic views.
_C4_STORY_ORDER = [
    "landscape",
    "context",
    "containers",
    "components",   # any L3 view ending in -components
]


def _reorder_c4_story(puml_files: list[str], diagrams_dir: str) -> list[str]:
    """Reorder the C4 section so L0→L1→L2→L3→dynamic reads as a story."""
    c4_files: list[str] = []
    other_files: list[str] = []
    for path in puml_files:
        if diagram_type(path, diagrams_dir) == "c4":
            c4_files.append(path)
        else:
            other_files.append(path)

    def c4_key(path: str) -> tuple[int, str]:
        stem = os.path.splitext(os.path.basename(path))[0]
        normalised = stem.replace("structurizr-", "")
        for idx, anchor in enumerate(_C4_STORY_ORDER):
            if anchor in normalised:
                return (idx, normalised)
        # Dynamic views and anything else go after components
        return (len(_C4_STORY_ORDER), normalised)

    c4_files.sort(key=c4_key)
    return c4_files + other_files


def _build_from_narrative(
    narrative: list[dict],
    all_puml: list[str],
    diagrams_dir: str,
    search_paths: list[str],
    docs_dir: str | None,
    include_notes: bool,
) -> tuple[list[Section], int]:
    """Build sections from an explicit narrative config.

    `narrative` is a list of {label, diagrams: [...]} dicts. Each diagram
    reference is a path relative to `diagrams_dir`, with or without the
    `.puml` extension. Unknown references are warned about but don't
    abort the build.
    """
    # Index every .puml by path-relative-to-diagrams_dir, with and without .puml
    by_rel: dict[str, str] = {}
    for full in all_puml:
        rel = os.path.relpath(full, diagrams_dir)
        by_rel[rel] = full
        by_rel[os.path.splitext(rel)[0]] = full

    sections: list[Section] = []
    total = 0
    consumed: set[str] = set()
    for block in narrative:
        label = block.get("label") or block.get("section") or "Section"
        diagrams_spec = block.get("diagrams", [])
        diagrams: list[Diagram] = []
        for ref in diagrams_spec:
            full = by_rel.get(ref.strip())
            if not full:
                print(f"  NARRATIVE: unknown diagram '{ref}' — skipping", file=sys.stderr)
                continue
            diagram = _render_one(
                full, diagrams_dir, search_paths, docs_dir, include_notes
            )
            if diagram is None:
                continue
            diagrams.append(diagram)
            consumed.add(full)
        if diagrams:
            sections.append(Section(label=label, diagrams=diagrams))
            total += len(diagrams)

    # Any .puml not referenced by the narrative gets appended under
    # "More diagrams" so nothing silently vanishes.
    leftovers = [p for p in all_puml if p not in consumed]
    if leftovers:
        extras: list[Diagram] = []
        for puml_path in _reorder_c4_story(leftovers, diagrams_dir):
            diagram = _render_one(
                puml_path, diagrams_dir, search_paths, docs_dir, include_notes
            )
            if diagram:
                extras.append(diagram)
        if extras:
            sections.append(Section(label="More diagrams", diagrams=extras))
            total += len(extras)

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
        narrative=client_config.get("narrative"),
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
