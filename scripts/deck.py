#!/usr/bin/env python3
"""Export client diagrams as a PDF or PowerPoint deck.

Usage:
    python scripts/deck.py --client acme               # PDF (default)
    python scripts/deck.py --client acme --pptx         # PowerPoint
"""
import argparse
import os
import re
import sys
import time
import urllib.request
import urllib.error

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.render import resolve_includes, INCLUDE_RE

KROKI_BASE = "https://kroki.io/plantuml"
TYPE_ORDER = ["c4", "sequence", "erd", "deployment", "excalidraw"]


def discover_puml_files(diagrams_dir: str) -> list[str]:
    """Find all .puml files in the diagrams directory."""
    results = []
    for dirpath, _, filenames in os.walk(diagrams_dir):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results


def order_by_type(puml_files: list[str], diagrams_dir: str) -> list[str]:
    """Order files by type (c4 first, then sequence, etc.), alphabetical within type."""
    def sort_key(path):
        rel = os.path.relpath(path, diagrams_dir)
        parts = rel.split(os.sep)
        dtype = parts[0] if len(parts) > 1 else "zzz"
        try:
            type_idx = TYPE_ORDER.index(dtype)
        except ValueError:
            type_idx = len(TYPE_ORDER)
        return (type_idx, rel)
    return sorted(puml_files, key=sort_key)


def diagram_name(puml_path: str) -> str:
    """Convert filename to display name."""
    name = os.path.splitext(os.path.basename(puml_path))[0]
    return name.replace("-", " ").replace("_", " ").title()


def render_to_pdf(source: str) -> bytes:
    """Render PlantUML source to PDF via Kroki."""
    url = f"{KROKI_BASE}/pdf"
    data = source.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "text/plain",
        "User-Agent": "skhema/1.0",
    })
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    return b""


def render_to_png(source: str, scale: int = 2) -> bytes:
    """Render PlantUML source to high-res PNG via Kroki."""
    url = f"{KROKI_BASE}/png"
    data = source.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "text/plain",
        "User-Agent": "skhema/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def generate_pdf_deck(client_name: str, diagrams_dir: str, search_paths: list[str], output_path: str):
    """Generate a PDF deck by rendering each diagram via Kroki PDF endpoint."""
    puml_files = order_by_type(discover_puml_files(diagrams_dir), diagrams_dir)
    if not puml_files:
        print("No .puml files found", file=sys.stderr)
        sys.exit(1)

    pdf_pages = []
    rendered_names = []
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
            pdf_data = render_to_pdf(resolved)
            pdf_pages.append(pdf_data)
            rendered_names.append((puml_path, name))
        except Exception as e:
            print(f"    SKIP: Kroki error: {e}", file=sys.stderr)

    if not pdf_pages:
        print("No diagrams rendered successfully", file=sys.stderr)
        sys.exit(1)

    # Write individual PDFs (simple approach — one file per diagram)
    # A proper PDF merge requires a library; for now, save individual pages
    if len(pdf_pages) == 1:
        with open(output_path, "wb") as f:
            f.write(pdf_pages[0])
    else:
        # Save individual PDFs in a subdirectory
        pdf_dir = os.path.splitext(output_path)[0] + "_pages"
        os.makedirs(pdf_dir, exist_ok=True)
        for i, ((_puml_path, _name), pdf_data) in enumerate(zip(rendered_names, pdf_pages)):
            fname = os.path.splitext(os.path.basename(_puml_path))[0]
            page_path = os.path.join(pdf_dir, f"{i:02d}_{fname}.pdf")
            with open(page_path, "wb") as f:
                f.write(pdf_data)
        # Also write a simple HTML index for the PDF pages
        index = f"<html><head><title>{client_name} Deck</title></head><body>"
        index += f"<h1>{client_name} — Architecture Deck</h1><ol>"
        for i, (_puml_path, _name) in enumerate(rendered_names):
            fname = f"{i:02d}_{os.path.splitext(os.path.basename(_puml_path))[0]}.pdf"
            index += f'<li><a href="{fname}">{_name}</a></li>'
        index += "</ol></body></html>"
        with open(os.path.join(pdf_dir, "index.html"), "w") as f:
            f.write(index)
        output_path = pdf_dir

    print(f"PDF -> {output_path} ({len(pdf_pages)} diagram(s))")


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
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    diagrams_dir = os.path.join(client_dir, "diagrams")
    search_paths = [
        os.path.join(client_dir, "models"),
        os.path.join(root, "models"),
        os.path.join(root, "lib"),
    ]

    client_name = args.client.replace("-", " ").replace("_", " ").title()

    if args.pptx:
        output_path = os.path.join(client_dir, "deck.pptx")
        generate_pptx_deck(client_name, diagrams_dir, search_paths, output_path)
    else:
        output_path = os.path.join(client_dir, "deck.pdf")
        generate_pdf_deck(client_name, diagrams_dir, search_paths, output_path)


if __name__ == "__main__":
    main()
