#!/usr/bin/env python3
"""Generate a self-contained HTML gallery for a client's rendered diagrams.

Usage:
    python scripts/gallery.py --client acme
    python scripts/gallery.py --client acme --history 3
    python scripts/gallery.py --client acme --history 0
    python scripts/gallery.py --client acme --title "Acme Corp"
"""
import argparse
import html
import os
import re
import subprocess
import sys
from datetime import datetime

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """Parse a client.yaml file. Returns dict with name, subtitle, accent_color, sections."""
    defaults = {"name": "", "subtitle": "", "accent_color": "#D97706", "sections": []}
    if not os.path.isfile(path):
        return defaults
    result = dict(defaults)
    result["sections"] = []
    in_sections = False
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "sections:":
                in_sections = True
                continue
            if in_sections:
                if stripped.startswith("- "):
                    result["sections"].append(stripped[2:].strip())
                else:
                    in_sections = False
            if not in_sections and ":" in stripped and not stripped.endswith(":"):
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in result:
                    result[key] = val
    return result


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
        # Skip the first entry (current version), return previous versions
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


GALLERY_CSS = """
body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f9fafb; color: #333; }
.header { max-width: 1200px; margin: 0 auto 30px; }
.header h1 { color: #92400E; margin-bottom: 5px; }
.header .meta { color: #78716C; font-size: 14px; }
.search { max-width: 1200px; margin: 0 auto 20px; }
.search input { width: 100%; padding: 10px 16px; border: 2px solid #D97706; border-radius: 8px; font-size: 16px; outline: none; box-sizing: border-box; }
.search input:focus { border-color: #92400E; }
.section { max-width: 1200px; margin: 0 auto 40px; }
.section h2 { color: #92400E; border-bottom: 2px solid #D97706; padding-bottom: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.card { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: box-shadow 0.2s, border-color 0.2s; border: 2px solid transparent; cursor: pointer; }
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-color: #D97706; }
.card a { text-decoration: none; color: inherit; display: block; }
.card .thumb { width: 100%; height: 200px; overflow: hidden; background: #fff; display: flex; align-items: center; justify-content: center; padding: 10px; box-sizing: border-box; }
.card .thumb svg { max-width: 100%; max-height: 100%; }
.card .info { padding: 12px 16px; border-top: 1px solid #f3f4f6; }
.card .info .name { font-weight: 600; font-size: 14px; }
.card .info .badge { display: inline-block; font-size: 11px; background: #FDE68A; color: #92400E; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }
.history { padding: 0 16px 12px; }
.history summary { font-size: 12px; color: #78716C; cursor: pointer; }
.history .version { font-size: 12px; color: #78716C; padding: 4px 0; border-top: 1px solid #f3f4f6; }
.history .version .date { font-weight: 600; }
.hidden { display: none; }
"""

GALLERY_JS = """
function filterCards() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(c => {
    const name = c.dataset.name.toLowerCase();
    c.classList.toggle('hidden', !name.includes(q));
  });
  document.querySelectorAll('.section').forEach(s => {
    const visible = s.querySelectorAll('.card:not(.hidden)').length;
    s.style.display = visible ? '' : 'none';
  });
}
"""


def generate_gallery_html(
    client_name: str,
    rendered_dir: str,
    history: int = 3,
    diagrams_dir: str | None = None,
) -> str:
    """Generate a self-contained HTML gallery page."""
    svg_files = discover_diagrams(rendered_dir)
    groups = group_by_type(svg_files, rendered_dir)
    total = len(svg_files)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cards_html = []
    for dtype in TYPE_ORDER:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        section_cards = []
        for svg_path in groups[dtype]:
            name = diagram_name(svg_path)
            svg_content = open(svg_path).read()
            # Strip XML declaration for inline embedding
            svg_inline = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()
            rel_path = os.path.relpath(svg_path, os.path.dirname(rendered_dir))

            # Check for animated arrows
            has_animation = "marching-ant" in svg_content

            # Get history if available
            history_html = ""
            if history > 0 and diagrams_dir:
                source = svg_to_source_path(svg_path, rendered_dir, diagrams_dir)
                versions = get_history(source, history)
                if versions:
                    ver_items = ""
                    for v in versions:
                        date_short = v["date"][:10]
                        msg = html.escape(v["message"][:60])
                        ver_items += f'<div class="version"><span class="date">{date_short}</span> — {msg}</div>'
                    history_html = f'<details class="history"><summary>{len(versions)} previous version(s)</summary>{ver_items}</details>'

            badge = '<span class="badge">animated</span>' if has_animation else ""
            search_text = f"{name} {dtype}"
            section_cards.append(
                f'<div class="card" data-name="{html.escape(search_text)}">'
                f'<a href="{html.escape(rel_path)}" target="_blank">'
                f'<div class="thumb">{svg_inline}</div>'
                f'<div class="info"><span class="name">{html.escape(name)}</span>{badge}</div>'
                f'</a>{history_html}</div>'
            )

        cards_html.append(
            f'<div class="section"><h2>{html.escape(label)} ({len(groups[dtype])})</h2>'
            f'<div class="grid">{"".join(section_cards)}</div></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(client_name)} — Architecture Diagrams</title>
<style>{GALLERY_CSS}</style></head>
<body>
<div class="header"><h1>{html.escape(client_name)}</h1><p class="meta">Generated {now} — {total} diagram(s)</p></div>
<div class="search"><input type="text" id="search" placeholder="Filter diagrams..." oninput="filterCards()"></div>
{"".join(cards_html)}
<script>{GALLERY_JS}</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate HTML gallery for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--history", type=int, default=3, help="Number of historical versions (default: 3, 0 to disable)")
    parser.add_argument("--title", help="Override client display name")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    rendered_dir = os.path.join(client_dir, "rendered")
    diagrams_dir = os.path.join(client_dir, "diagrams")
    if not os.path.isdir(rendered_dir) or not discover_diagrams(rendered_dir):
        print(f"No rendered diagrams found. Run: python scripts/render.py --client {args.client} --all", file=sys.stderr)
        sys.exit(1)

    client_name = args.title or args.client.replace("-", " ").replace("_", " ").title()
    gallery_html = generate_gallery_html(
        client_name=client_name,
        rendered_dir=rendered_dir,
        history=args.history,
        diagrams_dir=diagrams_dir,
    )

    out_path = os.path.join(client_dir, "index.html")
    with open(out_path, "w") as f:
        f.write(gallery_html)
    print(f"Gallery -> {out_path}")


if __name__ == "__main__":
    main()
