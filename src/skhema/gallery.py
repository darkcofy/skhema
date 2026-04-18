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
from datetime import datetime

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
:root {
  --bg: #f9fafb; --text: #333; --card-bg: #fff; --card-border: transparent;
  --card-hover: #D97706; --heading: #92400E; --accent: #D97706;
  --meta: #78716C; --border: #f3f4f6; --input-bg: #fff;
  --sidebar-bg: #fff; --sidebar-border: #e5e7eb;
}
[data-theme="dark"] {
  --bg: #1a1a2e; --text: #e2e8f0; --card-bg: #2d2d44; --card-border: #3d3d5c;
  --card-hover: #D97706; --heading: #FDE68A; --accent: #D97706;
  --meta: #a1a1aa; --border: #3d3d5c; --input-bg: #2d2d44;
  --sidebar-bg: #16162a; --sidebar-border: #2d2d44;
}
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, Arial, sans-serif; margin: 0; padding: 0; background: var(--bg); color: var(--text); }
.header { max-width: 1400px; margin: 0 auto; padding: 20px 20px 0; display: flex; justify-content: space-between; align-items: center; }
.header h1 { color: var(--heading); margin: 0 0 5px; }
.header .meta { color: var(--meta); font-size: 14px; }
.theme-toggle { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 8px 14px; cursor: pointer; color: var(--text); font-size: 14px; }
.theme-toggle:hover { border-color: var(--accent); }
.layout { display: flex; max-width: 1400px; margin: 0 auto; min-height: calc(100vh - 80px); }
.sidebar { width: 240px; flex-shrink: 0; padding: 20px; position: sticky; top: 0; height: 100vh; overflow-y: auto; border-right: 1px solid var(--sidebar-border); background: var(--sidebar-bg); }
.sidebar .search input { width: 100%; padding: 8px 12px; border: 2px solid var(--accent); border-radius: 6px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--text); }
.sidebar .search input:focus { border-color: var(--heading); }
.sidebar .match-count { font-size: 12px; color: var(--meta); margin-top: 6px; }
.sidebar nav { margin-top: 16px; }
.sidebar .nav-section { margin-bottom: 4px; }
.sidebar .nav-section a { display: flex; justify-content: space-between; padding: 8px 12px; border-radius: 6px; color: var(--text); text-decoration: none; font-size: 14px; font-weight: 500; }
.sidebar .nav-section a:hover, .sidebar .nav-section a.active { background: var(--card-bg); color: var(--accent); }
.sidebar .nav-section .badge { background: var(--accent); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.content { flex: 1; padding: 20px; min-width: 0; }
.section { margin-bottom: 40px; }
.section h2 { color: var(--heading); border-bottom: 2px solid var(--accent); padding-bottom: 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; }
.card { background: var(--card-bg); border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: box-shadow 0.2s, border-color 0.2s; border: 2px solid var(--card-border); cursor: pointer; }
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-color: var(--card-hover); }
.card .thumb { width: 100%; height: 280px; overflow: hidden; background: #fff; display: flex; align-items: center; justify-content: center; padding: 12px; }
.card .thumb svg { max-width: 100%; max-height: 100%; }
.card .info { padding: 12px 16px; border-top: 1px solid var(--border); }
.card .info .name { font-weight: 600; font-size: 15px; }
.card .info .type-label { font-size: 12px; color: var(--meta); margin-top: 2px; }
.card .info .badge { display: inline-block; font-size: 11px; background: #FDE68A; color: #92400E; padding: 2px 6px; border-radius: 4px; margin-left: 6px; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.history { padding: 0 16px 12px; }
.history summary { font-size: 12px; color: var(--meta); cursor: pointer; }
.history .version { font-size: 12px; color: var(--meta); padding: 4px 0; border-top: 1px solid var(--border); }
.history .version .date { font-weight: 600; }
.hidden { display: none; }
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
.modal-overlay.active { display: flex; }
.modal { background: var(--card-bg); border-radius: 12px; max-width: 90vw; max-height: 90vh; overflow: auto; padding: 24px; position: relative; }
.modal h3 { margin: 0 0 8px; color: var(--heading); }
.modal .modal-close { position: absolute; top: 12px; right: 16px; background: none; border: none; font-size: 24px; cursor: pointer; color: var(--meta); }
.modal .modal-close:hover { color: var(--text); }
.modal .modal-link { display: inline-block; margin-bottom: 16px; color: var(--accent); font-size: 13px; }
.modal svg { max-width: 100%; background: #fff; border-radius: 8px; padding: 16px; }
.hamburger { display: none; background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text); padding: 8px; }
@media (max-width: 768px) {
  .sidebar { display: none; position: fixed; top: 0; left: 0; z-index: 900; height: 100vh; width: 280px; }
  .sidebar.open { display: block; }
  .hamburger { display: block; }
}
"""

GALLERY_JS = """
function initTheme() {
  const saved = localStorage.getItem('skhema-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.setAttribute('data-theme', 'dark');
  updateToggleLabel();
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('skhema-theme', next);
  updateToggleLabel();
}
function updateToggleLabel() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = dark ? '\\u2600 Light' : '\\u263e Dark';
}
function filterCards() {
  const q = document.getElementById('search').value.toLowerCase();
  let total = 0, shown = 0;
  document.querySelectorAll('.card').forEach(c => {
    total++;
    const match = c.dataset.name.toLowerCase().includes(q);
    c.classList.toggle('hidden', !match);
    if (match) shown++;
  });
  document.querySelectorAll('.section').forEach(s => {
    const visible = s.querySelectorAll('.card:not(.hidden)').length;
    s.style.display = visible ? '' : 'none';
  });
  const mc = document.getElementById('matchCount');
  if (mc) mc.textContent = q ? shown + ' of ' + total + ' diagrams' : total + ' diagrams';
}
function openModal(card) {
  const modal = document.getElementById('modal');
  const svg = card.querySelector('.thumb').innerHTML;
  const name = card.querySelector('.name').textContent;
  const href = card.dataset.href;
  document.getElementById('modalTitle').textContent = name;
  document.getElementById('modalSvg').innerHTML = svg;
  document.getElementById('modalLink').href = href;
  modal.classList.add('active');
}
function closeModal() { document.getElementById('modal').classList.remove('active'); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
function initScrollTracking() {
  const sections = document.querySelectorAll('.section');
  const navLinks = document.querySelectorAll('.nav-section a');
  if (!sections.length || !navLinks.length) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navLinks.forEach(l => l.classList.remove('active'));
        const id = e.target.id;
        const link = document.querySelector('.nav-section a[href=\"#' + id + '\"]');
        if (link) link.classList.add('active');
      }
    });
  }, { threshold: 0.1 });
  sections.forEach(s => observer.observe(s));
}
function toggleSidebar() { document.querySelector('.sidebar').classList.toggle('open'); }
initTheme();
document.addEventListener('DOMContentLoaded', () => { initScrollTracking(); filterCards(); });
"""


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
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    element_adr_map: dict = {}
    if client_path:
        from skhema.adr import discover_adrs
        adrs = discover_adrs(client_path)
        for adr in adrs:
            for elem_id in adr.elements:
                element_adr_map.setdefault(elem_id, []).append(adr)

    config = parse_client_yaml(client_yaml_path) if client_yaml_path else {"sections": [], "accent_color": "#D97706"}
    section_order = config["sections"] if config["sections"] else [t for t in TYPE_ORDER if t in groups]

    nav_html = ""
    for dtype in section_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        count = len(groups[dtype])
        nav_html += f'<div class="nav-section"><a href="#section-{dtype}">{html.escape(label)} <span class="badge">{count}</span></a></div>'

    cards_html = []
    for dtype in section_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        section_cards = []
        for svg_path in groups[dtype]:
            name = diagram_name(svg_path)
            svg_content = open(svg_path).read()
            svg_inline = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()
            rel_path = os.path.relpath(svg_path, os.path.dirname(rendered_dir))
            has_animation = "marching-ant" in svg_content

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
            type_label_text = TYPE_LABELS.get(dtype, dtype.title())

            diagram_id = os.path.splitext(os.path.basename(svg_path))[0]
            related_adrs = element_adr_map.get(diagram_id, [])
            adr_html = ""
            if related_adrs:
                adr_html = '<div class="adr-panel"><h4>Architectural Decisions</h4><ul>'
                for adr in related_adrs:
                    adr_html += f'<li>ADR{adr.number:02d}: {html.escape(adr.title)} ({html.escape(adr.status)})</li>'
                adr_html += '</ul></div>'

            section_cards.append(
                f'<div class="card" data-name="{html.escape(search_text)}" data-href="{html.escape(rel_path)}" onclick="openModal(this)">'
                f'<div class="thumb">{svg_inline}</div>'
                f'<div class="info"><span class="name">{html.escape(name)}</span>{badge}'
                f'<div class="type-label">{html.escape(type_label_text)}</div></div>'
                f'{history_html}{adr_html}</div>'
            )

        cards_html.append(
            f'<div class="section" id="section-{dtype}"><h2>{html.escape(label)} ({len(groups[dtype])})</h2>'
            f'<div class="grid">{"".join(section_cards)}</div></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(client_name)} — Architecture Diagrams</title>
<style>{GALLERY_CSS}</style></head>
<body>
<div class="header">
  <div><h1>{html.escape(client_name)}</h1><p class="meta">Generated {now} — {total} diagram(s)</p></div>
  <div><button class="hamburger" onclick="toggleSidebar()">&#9776;</button><button class="theme-toggle" id="themeToggle" onclick="toggleTheme()">&#9790; Dark</button></div>
</div>
<div class="layout">
  <aside class="sidebar">
    <div class="search"><input type="text" id="search" placeholder="Filter diagrams..." oninput="filterCards()"><div class="match-count" id="matchCount">{total} diagrams</div></div>
    <nav>{nav_html}</nav>
  </aside>
  <main class="content">{"".join(cards_html)}</main>
</div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal"><button class="modal-close" onclick="closeModal()">&#10005;</button><h3 id="modalTitle"></h3><a class="modal-link" id="modalLink" target="_blank">Open in new tab</a><div id="modalSvg"></div></div>
</div>
<script>{GALLERY_JS}</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate HTML gallery for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--history", type=int, default=3, help="Number of historical versions (default: 3, 0 to disable)")
    parser.add_argument("--title", help="Override client display name")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    client_dir = os.path.join(root, "clients", args.client)
    if not os.path.isdir(client_dir):
        print(f"Client '{args.client}' not found in clients/", file=sys.stderr)
        sys.exit(1)

    rendered_dir = os.path.join(client_dir, "rendered")
    diagrams_dir = os.path.join(client_dir, "diagrams")
    if not os.path.isdir(rendered_dir) or not discover_diagrams(rendered_dir):
        print(f"No rendered diagrams found. Run: python scripts/render.py --client {args.client} --all", file=sys.stderr)
        sys.exit(1)

    client_yaml = os.path.join(client_dir, "client.yaml")
    client_name = args.title or args.client.replace("-", " ").replace("_", " ").title()
    gallery_html = generate_gallery_html(
        client_name=client_name,
        rendered_dir=rendered_dir,
        history=args.history,
        diagrams_dir=diagrams_dir,
        client_yaml_path=client_yaml,
    )

    out_path = os.path.join(client_dir, "index.html")
    with open(out_path, "w") as f:
        f.write(gallery_html)
    print(f"Gallery -> {out_path}")


if __name__ == "__main__":
    main()
