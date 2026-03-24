#!/usr/bin/env python3
"""Export client diagrams as a PDF or PowerPoint deck.

Usage:
    python scripts/deck.py --client acme               # PDF (default)
    python scripts/deck.py --client acme --pptx         # PowerPoint
"""
import argparse
import io
import os
import re
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pypdf import PdfWriter
from scripts.render import resolve_includes, render_plantuml, INCLUDE_RE

TYPE_ORDER = ["c4", "sequence", "erd", "deployment"]


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
    Excalidraw diagrams are excluded from output."""
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


def diagram_name(puml_path: str) -> str:
    """Convert filename to display name."""
    name = os.path.splitext(os.path.basename(puml_path))[0]
    return name.replace("-", " ").replace("_", " ").title()


def render_to_pdf(source: str) -> bytes:
    """Render PlantUML source to PDF via local binary."""
    return render_plantuml(source, fmt="pdf")


def render_to_png(source: str, scale: int = 2) -> bytes:
    """Render PlantUML source to PNG via local binary."""
    return render_plantuml(source, fmt="png")


COVER_HTML = """<!DOCTYPE html>
<html><head><style>
  body {{ font-family: sans-serif; display: flex; align-items: center;
         justify-content: center; height: 100vh; margin: 0;
         background: {accent}; color: white; text-align: center; }}
  h1 {{ font-size: 3em; margin: 0; }}
  p {{ font-size: 1.5em; opacity: 0.8; }}
</style></head><body>
  <div><h1>{name}</h1><p>{subtitle}</p></div>
</body></html>"""


def _svg_to_pdf(svg_bytes: bytes) -> bytes | None:
    """Convert SVG to PDF via wkhtmltopdf. Returns None if unavailable."""
    import subprocess
    html = (
        '<!DOCTYPE html><html><head><style>'
        'body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }'
        'img { max-width: 95%; max-height: 95%; }'
        '</style></head><body>'
        f'<img src="data:image/svg+xml;base64,{__import__("base64").b64encode(svg_bytes).decode()}">'
        '</body></html>'
    )
    try:
        result = subprocess.run(
            ["wkhtmltopdf", "--page-size", "A4", "--orientation", "Landscape", "-", "-"],
            input=html.encode(), capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    return None


def render_cover_page(client_name: str, subtitle: str = "",
                      accent_color: str = "#D97706") -> bytes | None:
    """Render cover page HTML to PDF via wkhtmltopdf. Returns None if unavailable."""
    import subprocess
    html = COVER_HTML.format(name=client_name, subtitle=subtitle, accent=accent_color)
    try:
        result = subprocess.run(
            ["wkhtmltopdf", "--page-size", "A4", "-", "-"],
            input=html.encode(), capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    return None


def ordered_diagrams(diagrams_dir: str, search_paths: list[str]) -> list[tuple[str, str]]:
    """Return ordered list of (puml_path, resolved_source) excluding excalidraw."""
    puml_files = discover_puml_files(diagrams_dir)
    ordered = order_by_type(puml_files, diagrams_dir)
    result = []
    for path in ordered:
        source = resolve_includes(
            open(path).read(),
            os.path.dirname(path),
            search_paths,
        )
        result.append((path, source))
    return result


def build_deck(client_name: str, diagrams_dir: str, search_paths: list[str],
               output_path: str, include_cover: bool = True,
               subtitle: str = "", accent_color: str = "#D97706",
               emit_pages: bool = False):
    """Build merged PDF deck from PlantUML diagrams."""
    writer = PdfWriter()

    if include_cover:
        cover = render_cover_page(client_name, subtitle, accent_color)
        if cover:
            writer.append(io.BytesIO(cover))

    pages_dir = output_path.replace(".pdf", "_pages") if emit_pages else None
    if pages_dir:
        os.makedirs(pages_dir, exist_ok=True)

    for puml_path, source in ordered_diagrams(diagrams_dir, search_paths):
        pdf_bytes = _svg_to_pdf(render_plantuml(source, fmt="svg"))
        if pdf_bytes is None:
            print(f"  Warning: could not convert {os.path.basename(puml_path)} to PDF, skipping",
                  file=sys.stderr)
            continue
        writer.append(io.BytesIO(pdf_bytes))
        if pages_dir:
            page_name = os.path.splitext(os.path.basename(puml_path))[0] + ".pdf"
            with open(os.path.join(pages_dir, page_name), "wb") as f:
                f.write(pdf_bytes)

    writer.write(output_path)
    writer.close()


def generate_pptx_deck(client_name: str, diagrams_dir: str, search_paths: list[str], output_path: str):
    """Generate a PowerPoint deck. Requires python-pptx."""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError:
        print("PowerPoint export requires python-pptx:", file=sys.stderr)
        print("  pip install python-pptx", file=sys.stderr)
        sys.exit(1)

    puml_files = order_by_type(discover_puml_files(diagrams_dir), diagrams_dir)
    if not puml_files:
        print("No .puml files found", file=sys.stderr)
        sys.exit(1)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    txBox = slide.shapes.add_textbox(Inches(2), Inches(2.5), Inches(9), Inches(2))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = client_name
    p.font.size = Pt(44)
    p.font.bold = True
    p2 = tf.add_paragraph()
    p2.text = "Architecture Diagrams"
    p2.font.size = Pt(24)

    # Diagram slides
    import tempfile
    for puml_path in puml_files:
        name = diagram_name(puml_path)
        print(f"  Rendering: {name}")
        source = open(puml_path).read()
        base_dir = os.path.dirname(puml_path)
        try:
            resolved = resolve_includes(source, base_dir=base_dir, search_paths=search_paths)
        except (ValueError, FileNotFoundError) as e:
            print(f"    SKIP: {e}", file=sys.stderr)
            continue
        try:
            png_data = render_to_png(resolved)
        except Exception as e:
            print(f"    SKIP: Kroki error: {e}", file=sys.stderr)
            continue

        slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
        # Add title
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
        txBox.text_frame.paragraphs[0].text = name
        txBox.text_frame.paragraphs[0].font.size = Pt(20)
        txBox.text_frame.paragraphs[0].font.bold = True
        # Add diagram image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_data)
            tmp_path = tmp.name
        try:
            slide.shapes.add_picture(tmp_path, Inches(0.5), Inches(1.2), width=Inches(12.3))
        finally:
            os.unlink(tmp_path)

    prs.save(output_path)
    print(f"PPTX -> {output_path} ({len(puml_files)} diagram(s))")


def main():
    parser = argparse.ArgumentParser(description="Export client diagrams as deck")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--pptx", action="store_true", help="PowerPoint output (needs python-pptx)")
    parser.add_argument("--pages", action="store_true", help="Also emit individual PDF pages alongside merged deck")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    diagrams_dir = os.path.join(client_dir, "diagrams")
    search_paths = [
        os.path.join(client_dir, "models"),
        os.path.join(root, "skhema", "models"),
        os.path.join(root, "skhema", "lib"),
    ]

    client_name = args.client.replace("-", " ").replace("_", " ").title()

    if args.pptx:
        output_path = os.path.join(client_dir, "deck.pptx")
        generate_pptx_deck(client_name, diagrams_dir, search_paths, output_path)
    else:
        output_path = os.path.join(client_dir, "deck.pdf")
        build_deck(client_name, diagrams_dir, search_paths, output_path, emit_pages=args.pages)
        print(f"PDF -> {output_path}")


if __name__ == "__main__":
    main()
