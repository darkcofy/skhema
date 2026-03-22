# Living Docs & Gallery Facelift Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-contained HTML architecture handbook generator (`docs.py`) and upgrade the gallery with dark mode, sidebar nav, modal preview, and improved cards.

**Architecture:** Gallery facelift modifies `gallery.py` CSS/JS/HTML structure. New `docs.py` imports shared utilities from `gallery.py`, adds a markdown parser + doc assembly. Demo client gets full companion prose. Both produce single self-contained HTML files.

**Tech Stack:** Python 3 (stdlib), vanilla CSS/JS, regex-based markdown parser

---

## Phase 1: Foundation

### Task 0: Gitignore Update & Client YAML Parser

**Files:**
- Modify: `.gitignore`
- Modify: `scripts/gallery.py`
- Modify: `tests/test_gallery.py`

- [ ] **Step 1: Update `.gitignore`**

Change:
```
clients/*/index.html
```
To:
```
clients/*/*.html
```

- [ ] **Step 2: Write `parse_client_yaml` tests**

Add to `tests/test_gallery.py`:

```python
from scripts.gallery import parse_client_yaml


class TestParseClientYaml:
    def test_parses_name_and_sections(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: "Acme"\nsubtitle: "Platform"\nsections:\n  - c4\n  - sequence\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["name"] == "Acme"
        assert result["subtitle"] == "Platform"
        assert result["sections"] == ["c4", "sequence"]

    def test_optional_accent_color(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: "X"\naccent_color: "#FF0000"\nsections:\n  - erd\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["accent_color"] == "#FF0000"

    def test_defaults_when_missing(self, tmp_path):
        result = parse_client_yaml(str(tmp_path / "nonexistent.yaml"))
        assert result["name"] == ""
        assert result["sections"] == []
        assert result["accent_color"] == "#D97706"

    def test_no_quotes_in_values(self, tmp_path):
        yaml_file = tmp_path / "client.yaml"
        yaml_file.write_text('name: Acme Corp\nsubtitle: Data Platform\nsections:\n  - c4\n')
        result = parse_client_yaml(str(yaml_file))
        assert result["name"] == "Acme Corp"
```

- [ ] **Step 3: Run tests to see them fail**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_gallery.py::TestParseClientYaml -v
```

Expected: ImportError — `parse_client_yaml` doesn't exist yet.

- [ ] **Step 4: Implement `parse_client_yaml` in `gallery.py`**

Add after the `TYPE_LABELS` dict:

```python
def parse_client_yaml(path: str) -> dict:
    """Parse a client.yaml file. Returns dict with name, subtitle, accent_color, sections.

    Uses line-based parsing (no PyYAML dependency). Returns defaults if file missing.
    """
    defaults = {"name": "", "subtitle": "", "accent_color": "#D97706", "sections": []}
    if not os.path.isfile(path):
        return defaults
    result = dict(defaults)
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
```

- [ ] **Step 5: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_gallery.py -v
```

Expected: All tests PASS (8 existing + 4 new = 12).

- [ ] **Step 6: Commit**

```bash
git add .gitignore scripts/gallery.py tests/test_gallery.py
git commit -m "feat: add parse_client_yaml and broaden gitignore for client HTML

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 2: Gallery Facelift

### Task 1: Gallery Dark Mode & Improved Cards

**Files:**
- Modify: `scripts/gallery.py` (CSS + HTML structure)
- Modify: `tests/test_gallery.py`

- [ ] **Step 1: Write tests for dark mode and card improvements**

Add to `tests/test_gallery.py`:

```python
class TestGalleryDarkMode:
    def test_dark_mode_toggle_present(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "theme-toggle" in html
        assert "arch-diagrams-theme" in html

    def test_dark_mode_css_present(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "#1a1a2e" in html  # dark background
        assert "#2d2d44" in html  # dark card background

    def test_card_thumb_height_280(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "280px" in html

    def test_animated_badge_has_pulse(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>.marching-ant{}</style></svg>')
        html = generate_gallery_html("X", str(tmp_path / "rendered"), history=0)
        assert "pulse" in html
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_gallery.py::TestGalleryDarkMode -v
```

Expected: AssertionError failures.

- [ ] **Step 3: Replace `GALLERY_CSS` constant**

Replace the `GALLERY_CSS` constant in `scripts/gallery.py` with:

```python
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
/* Modal */
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
.modal-overlay.active { display: flex; }
.modal { background: var(--card-bg); border-radius: 12px; max-width: 90vw; max-height: 90vh; overflow: auto; padding: 24px; position: relative; }
.modal h3 { margin: 0 0 8px; color: var(--heading); }
.modal .modal-close { position: absolute; top: 12px; right: 16px; background: none; border: none; font-size: 24px; cursor: pointer; color: var(--meta); }
.modal .modal-close:hover { color: var(--text); }
.modal .modal-link { display: inline-block; margin-bottom: 16px; color: var(--accent); font-size: 13px; }
.modal svg { max-width: 100%; background: #fff; border-radius: 8px; padding: 16px; }
/* Responsive */
.hamburger { display: none; background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text); padding: 8px; }
@media (max-width: 768px) {
  .sidebar { display: none; position: fixed; top: 0; left: 0; z-index: 900; height: 100vh; width: 280px; }
  .sidebar.open { display: block; }
  .hamburger { display: block; }
}
"""
```

- [ ] **Step 4: Replace `GALLERY_JS` constant**

Replace the `GALLERY_JS` constant in `scripts/gallery.py` with:

```python
GALLERY_JS = """
// Theme toggle
function initTheme() {
  const saved = localStorage.getItem('arch-diagrams-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.setAttribute('data-theme', 'dark');
  updateToggleLabel();
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('arch-diagrams-theme', next);
  updateToggleLabel();
}
function updateToggleLabel() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = dark ? '☀ Light' : '☾ Dark';
}

// Filter
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

// Modal
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
function closeModal() {
  document.getElementById('modal').classList.remove('active');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// Sidebar scroll tracking
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

// Hamburger
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
}

// Init
initTheme();
document.addEventListener('DOMContentLoaded', () => { initScrollTracking(); filterCards(); });
"""
```

- [ ] **Step 5: Update `generate_gallery_html` to use new layout**

Replace the `generate_gallery_html` function in `scripts/gallery.py`. The key changes:
1. Flex layout: `.header` on top, then `.layout` with `.sidebar` + `.content`
2. Cards use `onclick="openModal(this)"` + `data-href` instead of `<a>` wrapping
3. Sidebar nav with section links and count badges
4. Modal overlay at the bottom of the body
5. Type label shown on each card
6. Read `client.yaml` for section ordering when available

```python
def generate_gallery_html(
    client_name: str,
    rendered_dir: str,
    history: int = 3,
    diagrams_dir: str | None = None,
    client_yaml_path: str | None = None,
) -> str:
    """Generate a self-contained HTML gallery page."""
    svg_files = discover_diagrams(rendered_dir)
    groups = group_by_type(svg_files, rendered_dir)
    total = len(svg_files)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Determine section order
    config = parse_client_yaml(client_yaml_path) if client_yaml_path else {"sections": [], "accent_color": "#D97706"}
    section_order = config["sections"] if config["sections"] else [t for t in TYPE_ORDER if t in groups]

    # Build sidebar nav
    nav_html = ""
    for dtype in section_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        count = len(groups[dtype])
        nav_html += f'<div class="nav-section"><a href="#section-{dtype}">{html.escape(label)} <span class="badge">{count}</span></a></div>'

    # Build cards
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
            section_cards.append(
                f'<div class="card" data-name="{html.escape(search_text)}" data-href="{html.escape(rel_path)}" onclick="openModal(this)">'
                f'<div class="thumb">{svg_inline}</div>'
                f'<div class="info"><span class="name">{html.escape(name)}</span>{badge}'
                f'<div class="type-label">{html.escape(type_label_text)}</div></div>'
                f'{history_html}</div>'
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
  <div><button class="hamburger" onclick="toggleSidebar()">☰</button><button class="theme-toggle" id="themeToggle" onclick="toggleTheme()">☾ Dark</button></div>
</div>
<div class="layout">
  <aside class="sidebar">
    <div class="search"><input type="text" id="search" placeholder="Filter diagrams..." oninput="filterCards()"><div class="match-count" id="matchCount">{total} diagrams</div></div>
    <nav>{nav_html}</nav>
  </aside>
  <main class="content">{"".join(cards_html)}</main>
</div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal"><button class="modal-close" onclick="closeModal()">✕</button><h3 id="modalTitle"></h3><a class="modal-link" id="modalLink" target="_blank">Open in new tab</a><div id="modalSvg"></div></div>
</div>
<script>{GALLERY_JS}</script>
</body></html>"""
```

- [ ] **Step 6: Update `main()` to pass `client_yaml_path`**

In gallery.py's `main()`, after computing `client_dir`, add:

```python
    client_yaml = os.path.join(client_dir, "client.yaml")
```

And update the `generate_gallery_html` call to pass `client_yaml_path=client_yaml`.

- [ ] **Step 7: Run all tests**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_gallery.py -v
```

Expected: All 12 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/gallery.py tests/test_gallery.py
git commit -m "feat: gallery facelift — dark mode, sidebar nav, modal preview, improved cards

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 3: Living Docs Script

### Task 2: Markdown Parser

**Files:**
- Create: `scripts/docs.py`
- Create: `tests/test_docs.py`

- [ ] **Step 1: Write markdown parser tests**

Create `tests/test_docs.py`:

```python
"""Tests for the living docs generator."""
import os
import pytest
from scripts.docs import parse_markdown


class TestParseMarkdown:
    def test_headings(self):
        md = "# Title\n## Subtitle\n### H3\n#### H4"
        html = parse_markdown(md)
        assert "<h1>Title</h1>" in html
        assert "<h2>Subtitle</h2>" in html
        assert "<h3>H3</h3>" in html
        assert "<h4>H4</h4>" in html

    def test_paragraphs(self):
        md = "First paragraph.\n\nSecond paragraph."
        html = parse_markdown(md)
        assert "<p>First paragraph.</p>" in html
        assert "<p>Second paragraph.</p>" in html

    def test_bold_and_italic(self):
        md = "This is **bold** and *italic* text."
        html = parse_markdown(md)
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_inline_code(self):
        md = "Use `git status` to check."
        html = parse_markdown(md)
        assert "<code>git status</code>" in html

    def test_links(self):
        md = "See [docs](https://example.com) for details."
        html = parse_markdown(md)
        assert '<a href="https://example.com">docs</a>' in html

    def test_bullet_list(self):
        md = "Items:\n\n- Alpha\n- Beta\n- Gamma"
        html = parse_markdown(md)
        assert "<ul>" in html
        assert "<li>Alpha</li>" in html
        assert "<li>Gamma</li>" in html

    def test_numbered_list(self):
        md = "Steps:\n\n1. First\n2. Second\n3. Third"
        html = parse_markdown(md)
        assert "<ol>" in html
        assert "<li>First</li>" in html

    def test_blockquote(self):
        md = "> This is a quote\n> with two lines"
        html = parse_markdown(md)
        assert "<blockquote>" in html
        assert "This is a quote" in html

    def test_fenced_code_block(self):
        md = "Example:\n\n```bash\ngit status\ngit diff\n```"
        html = parse_markdown(md)
        assert "<pre><code>" in html
        assert "git status" in html

    def test_table(self):
        md = "| Name | Role |\n|------|------|\n| Alice | Dev |\n| Bob | Ops |"
        html = parse_markdown(md)
        assert "<table>" in html
        assert "<th>Name</th>" in html
        assert "<td>Alice</td>" in html
        assert "<td>Ops</td>" in html

    def test_empty_input(self):
        assert parse_markdown("") == ""
        assert parse_markdown("  \n  \n") == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_docs.py::TestParseMarkdown -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `parse_markdown` in `scripts/docs.py`**

Create `scripts/docs.py` with the markdown parser:

```python
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

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gallery import (
    discover_diagrams,
    group_by_type,
    diagram_name,
    parse_client_yaml,
    TYPE_ORDER,
    TYPE_LABELS,
)


def parse_markdown(md: str) -> str:
    """Convert markdown text to HTML. Single-pass, no nested inline formatting."""
    if not md or not md.strip():
        return ""

    lines = md.split("\n")
    result = []
    i = 0

    def inline(text):
        """Apply inline formatting: bold, italic, code, links."""
        text = html_mod.escape(text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(html_mod.escape(lines[i]))
                i += 1
            i += 1  # skip closing ```
            code = "\n".join(code_lines)
            cls = f' class="language-{lang}"' if lang else ""
            result.append(f"<pre><code{cls}>{code}</code></pre>")
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m:
            level = len(m.group(1))
            text = inline(m.group(2))
            result.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        # Table
        if "|" in stripped and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1].strip()):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2  # skip header + separator
            rows = []
            while i < len(lines) and "|" in lines[i].strip():
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            header_html = "".join(f"<th>{inline(h)}</th>" for h in headers)
            rows_html = ""
            for row in rows:
                cells_html = "".join(f"<td>{inline(c)}</td>" for c in row)
                rows_html += f"<tr>{cells_html}</tr>"
            result.append(f"<table><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                bq_lines.append(inline(lines[i].strip()[2:]))
                i += 1
            result.append(f"<blockquote><p>{'<br>'.join(bq_lines)}</p></blockquote>")
            continue

        # Bullet list
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline(lines[i].strip()[2:])}</li>")
                i += 1
            result.append(f"<ul>{''.join(items)}</ul>")
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                items.append(f"<li>{inline(text)}</li>")
                i += 1
            result.append(f"<ol>{''.join(items)}</ol>")
            continue

        # Paragraph (collect consecutive non-blank, non-special lines)
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#") and not lines[i].strip().startswith("```") and not lines[i].strip().startswith("> ") and not lines[i].strip().startswith("- ") and not re.match(r'^\d+\.\s', lines[i].strip()):
            para_lines.append(inline(lines[i].strip()))
            i += 1
        if para_lines:
            result.append(f"<p>{' '.join(para_lines)}</p>")

    return "\n".join(result)
```

- [ ] **Step 4: Run parser tests**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_docs.py::TestParseMarkdown -v
```

Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/docs.py tests/test_docs.py
git commit -m "feat: add markdown parser for living docs

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Doc Assembly & HTML Generation

**Files:**
- Modify: `scripts/docs.py`
- Modify: `tests/test_docs.py`

- [ ] **Step 1: Write doc assembly tests**

Add to `tests/test_docs.py`:

```python
from scripts.docs import generate_docs_html, parse_markdown


class TestGenerateDocsHtml:
    def test_returns_html_with_client_name(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        html = generate_docs_html(
            client_name="TestCo",
            subtitle="Platform",
            rendered_dir=str(tmp_path / "rendered"),
            docs_dir=str(tmp_path / "docs"),
        )
        assert "<!DOCTYPE html>" in html
        assert "TestCo" in html
        assert "Platform" in html

    def test_inlines_svg(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "arch.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "<circle" in html

    def test_includes_companion_prose(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs" / "c4"
        docs.mkdir(parents=True)
        (docs / "test.md").write_text("# Test Diagram\n\nThis shows the **test** architecture.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "<strong>test</strong>" in html
        assert "Test Diagram" in html

    def test_includes_section_overview(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs" / "c4"
        docs.mkdir(parents=True)
        (docs / "_overview.md").write_text("C4 diagrams show containers and components.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "C4 diagrams show containers and components." in html

    def test_includes_client_overview(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "overview.md").write_text("# NovaPay\n\nA payments platform.")
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(docs))
        assert "A payments platform." in html

    def test_missing_docs_dir_still_works(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "nodocs"))
        assert "<!DOCTYPE html>" in html
        assert "Test" in html  # auto-generated title from filename

    def test_has_table_of_contents(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "Table of Contents" in html or "toc" in html.lower()

    def test_print_friendly(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_docs_html("X", "", str(tmp_path / "rendered"), str(tmp_path / "docs"))
        assert "@media print" in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_docs.py::TestGenerateDocsHtml -v
```

Expected: ImportError — `generate_docs_html` doesn't exist yet.

- [ ] **Step 3: Implement `generate_docs_html`**

Add to `scripts/docs.py` after the `parse_markdown` function:

```python
DOCS_CSS = """
:root { --accent: {accent_color}; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, Georgia, serif; margin: 0; padding: 0; color: #1a1a2e; line-height: 1.7; }
.cover { max-width: 800px; margin: 60px auto; text-align: center; padding: 40px 20px; }
.cover h1 { font-size: 36px; color: var(--accent); margin-bottom: 8px; }
.cover .subtitle { font-size: 20px; color: #78716C; }
.cover .meta { font-size: 14px; color: #a1a1aa; margin-top: 16px; }
.toc { max-width: 800px; margin: 0 auto 40px; padding: 0 20px; }
.toc h2 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 6px; }
.toc ol { padding-left: 20px; }
.toc a { color: #1a1a2e; text-decoration: none; }
.toc a:hover { color: var(--accent); }
.overview { max-width: 800px; margin: 0 auto 40px; padding: 0 20px; }
.doc-section { max-width: 900px; margin: 0 auto 60px; padding: 0 20px; }
.doc-section h2 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 8px; font-size: 28px; }
.section-overview { color: #555; margin-bottom: 24px; }
.diagram-block { margin-bottom: 48px; padding-bottom: 24px; border-bottom: 1px solid #e5e7eb; }
.diagram-block:last-child { border-bottom: none; }
.diagram-block h3 { color: #333; font-size: 22px; margin-bottom: 8px; }
.diagram-block .prose { margin-bottom: 20px; }
.diagram-block .prose p { margin: 0 0 12px; }
.diagram-block .prose ul, .diagram-block .prose ol { margin: 0 0 12px; padding-left: 24px; }
.diagram-block .prose blockquote { border-left: 3px solid var(--accent); padding: 8px 16px; margin: 12px 0; color: #555; }
.diagram-block .prose table { border-collapse: collapse; margin: 12px 0; width: 100%; }
.diagram-block .prose th, .diagram-block .prose td { border: 1px solid #d1d5db; padding: 8px 12px; text-align: left; }
.diagram-block .prose th { background: #f9fafb; font-weight: 600; }
.diagram-block .prose pre { background: #f3f4f6; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
.diagram-block .prose code { background: #f3f4f6; padding: 2px 5px; border-radius: 3px; font-size: 13px; }
.diagram-block .prose pre code { background: none; padding: 0; }
.diagram-svg { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; text-align: center; margin-top: 16px; }
.diagram-svg svg { max-width: 100%; height: auto; }
.footer { max-width: 800px; margin: 40px auto; padding: 20px; text-align: center; color: #a1a1aa; font-size: 13px; border-top: 1px solid #e5e7eb; }
@media print {
  .doc-section { page-break-before: always; }
  .diagram-svg { break-inside: avoid; }
  .diagram-svg svg { max-height: 70vh; }
  body { font-size: 11pt; }
}
"""


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

    if section_order is None:
        section_order = [t for t in TYPE_ORDER if t in groups]

    css = DOCS_CSS.replace("{accent_color}", accent_color)

    # Client overview
    overview_html = ""
    overview_path = os.path.join(docs_dir, "overview.md")
    if os.path.isfile(overview_path):
        overview_html = f'<div class="overview">{parse_markdown(open(overview_path).read())}</div>'

    # TOC
    toc_items = []
    for dtype in section_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())
        toc_items.append(f'<li><a href="#doc-{dtype}">{html_mod.escape(label)}</a></li>')
    toc_html = f'<div class="toc"><h2>Table of Contents</h2><ol>{"".join(toc_items)}</ol></div>' if toc_items else ""

    # Sections
    sections_html = []
    for dtype in section_order:
        if dtype not in groups:
            continue
        label = TYPE_LABELS.get(dtype, dtype.title())

        # Section overview
        section_overview = ""
        overview_file = os.path.join(docs_dir, dtype, "_overview.md")
        if os.path.isfile(overview_file):
            section_overview = f'<div class="section-overview">{parse_markdown(open(overview_file).read())}</div>'

        # Diagrams
        diagrams_html = []
        for svg_path in groups[dtype]:
            name = diagram_name(svg_path)
            svg_content = open(svg_path).read()
            svg_inline = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()

            # Companion prose
            prose_html = ""
            base = os.path.splitext(os.path.basename(svg_path))[0]
            prose_path = os.path.join(docs_dir, dtype, f"{base}.md")
            if os.path.isfile(prose_path):
                prose_html = f'<div class="prose">{parse_markdown(open(prose_path).read())}</div>'

            diagrams_html.append(
                f'<div class="diagram-block"><h3>{html_mod.escape(name)}</h3>'
                f'{prose_html}'
                f'<div class="diagram-svg">{svg_inline}</div></div>'
            )

        sections_html.append(
            f'<div class="doc-section" id="doc-{dtype}"><h2>{html_mod.escape(label)}</h2>'
            f'{section_overview}{"".join(diagrams_html)}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(client_name)} — Architecture Handbook</title>
<style>{css}</style></head>
<body>
<div class="cover"><h1>{html_mod.escape(client_name)}</h1>
<div class="subtitle">{html_mod.escape(subtitle)}</div>
<div class="meta">Generated {now} — {total} diagram(s)</div></div>
{toc_html}
{overview_html}
{"".join(sections_html)}
<div class="footer">Generated {now} by arch-diagrams</div>
</body></html>"""
```

- [ ] **Step 4: Run doc assembly tests**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/test_docs.py -v
```

Expected: All 19 tests PASS (11 parser + 8 assembly).

- [ ] **Step 5: Add `main()` to `scripts/docs.py`**

Add at the bottom of `scripts/docs.py`:

```python
def main():
    parser = argparse.ArgumentParser(description="Generate architecture handbook for a client")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--title", help="Override client display name")
    parser.add_argument("--output", help="Output filename (relative to client dir)")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
```

- [ ] **Step 6: Run all tests**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/docs.py tests/test_docs.py
git commit -m "feat: add living docs generator with markdown parser and doc assembly

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 4: Demo Client Showcase

### Task 4: Demo Client Manifest & Overview

**Files:**
- Create: `clients/demo/client.yaml`
- Create: `clients/demo/docs/overview.md`

- [ ] **Step 1: Create `clients/demo/client.yaml`**

```yaml
name: "NovaPay"
subtitle: "Digital Payments Platform — Architecture Documentation"
accent_color: "#D97706"
sections:
  - c4
  - sequence
  - erd
  - deployment
```

- [ ] **Step 2: Create `clients/demo/docs/overview.md`**

```markdown
# NovaPay Platform

NovaPay is a digital payments platform processing 2M+ transactions per day across UK and EU markets. The platform enables consumer-to-merchant payments via mobile app, web checkout, and NFC, with real-time fraud detection and automated compliance reporting.

**Scope of this document:**
- Core payment processing (authorization, capture, settlement, refunds)
- Real-time fraud detection and case management
- Merchant management (onboarding, payouts, disputes)
- Analytics and data platform
- Production infrastructure and disaster recovery

**Key architectural principles:**
- Event-driven: Kafka as the backbone for async communication between services
- Double-entry ledger: Every financial movement is recorded as a balanced debit/credit pair
- Client isolation: Each client's data and configuration are fully separated
- Stdlib-first: Minimal external dependencies for portability
```

- [ ] **Step 3: Commit**

```bash
git add clients/demo/client.yaml clients/demo/docs/overview.md
git commit -m "feat: add demo client manifest and overview

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Demo C4 Companion Docs

**Files:**
- Create: `clients/demo/docs/c4/_overview.md`
- Create: `clients/demo/docs/c4/system-context.md`
- Create: `clients/demo/docs/c4/container-overview.md`
- Create: `clients/demo/docs/c4/payment-engine-components.md`
- Create: `clients/demo/docs/c4/fraud-detection.md`
- Create: `clients/demo/docs/c4/analytics-platform.md`
- Create: `clients/demo/docs/c4/merchant-portal.md`
- Create: `clients/demo/docs/c4/demo-platform.md`

- [ ] **Step 1: Create C4 section overview and all 7 companion files**

Create `clients/demo/docs/c4/_overview.md`:
```markdown
C4 diagrams model the NovaPay platform at multiple levels of abstraction. Start with the system context for the big picture, then drill into container and component views for implementation detail. Animated arrows (marked with `~` in PlantUML) indicate data flows that are particularly important for understanding system behavior.
```

Create `clients/demo/docs/c4/system-context.md`:
```markdown
# System Context

The system context view shows NovaPay's position in the broader financial ecosystem. Three user personas interact with the platform: consumers (via mobile app), merchants (via portal/API), and compliance officers (internal).

**Key integrations:**
- **Card Networks** (Visa/Mastercard): ISO 8583 protocol for authorization — chosen over REST for latency-critical payment flows
- **Core Banking** (COBOL mainframe): Settlement via SFTP/MQ — batch-oriented, runs nightly
- **Regulator Portal** (FCA/PSD2): Push-based compliance reporting via API and SFTP
```

Create `clients/demo/docs/c4/container-overview.md`:
```markdown
# Container Overview

The container view decomposes the NovaPay platform into its core services. The architecture follows an event-driven pattern with Kafka as the central message backbone.

**Payment flow:** Mobile App → Payment Engine → Fraud Detector (risk check) → Card Network (authorization) → Ledger (recording) → Kafka (event bus) → Notification Service + Webhook Engine

**Data stores:**
- PostgreSQL (operational DB) for transactional data
- Redis (cache layer) for fraud feature lookups and idempotency
- Kafka for event streaming between services

**Key design decision:** The Ledger Service is implemented in Rust for correctness guarantees around double-entry bookkeeping. All other services use Java/Spring Boot, Go, or Python depending on their I/O vs. compute profile.
```

Create `clients/demo/docs/c4/payment-engine-components.md`:
```markdown
# Payment Engine Components

The Payment Engine is the core orchestrator for the transaction lifecycle. It handles four distinct phases: authorization, capture, refund, and settlement.

**Component responsibilities:**

| Component | Responsibility | Protocol |
|-----------|---------------|----------|
| Auth Handler | Processes incoming authorization requests | REST |
| Capture Handler | Converts authorized transactions to captured | Internal |
| Refund Handler | Full and partial refund processing | REST |
| Settlement Handler | Batches nightly clearing files | SFTP |
| Routing Engine | Selects optimal card processor and route | Internal |
| Idempotency Store | Prevents duplicate transaction processing | Redis |

**Critical path:** Auth Handler → Routing Engine → Card Network takes < 200ms p99. The idempotency store adds ~1ms overhead but prevents costly duplicate authorizations.
```

Create `clients/demo/docs/c4/fraud-detection.md`:
```markdown
# Fraud Detection System

Real-time fraud scoring with a dual approach: configurable rules and ML-based scoring running in parallel for every transaction.

**Scoring pipeline:**
1. Transaction arrives at Scoring API
2. Rule Engine evaluates velocity counters, geo anomalies, and amount thresholds (Redis-backed, < 5ms)
3. ML Scorer runs ONNX inference using features from the Feature Store (< 20ms)
4. Combined score = max(rule_score, ml_score)
5. Decision: ALLOW (< 0.5), ALLOW_WITH_REVIEW (0.5–0.8), or BLOCK (> 0.8)

**Model details:**
- Gradient boosted trees trained on 18 months of labeled transaction data
- Retrained weekly with automated evaluation against precision@95% recall threshold
- AUC-ROC target: > 0.96
```

Create `clients/demo/docs/c4/analytics-platform.md`:
```markdown
# Analytics Platform

The analytics platform follows a medallion architecture pattern with real-time and batch ingestion paths converging in a shared data lake.

**Data flow:**
- **Real-time path:** Kafka → Stream Processor → Data Lake (raw zone, Parquet)
- **Batch path:** Batch ETL → Data Lake (daily extracts from operational systems)
- **Transform:** Data Lake → dbt → Data Warehouse (Snowflake, dimensional models)
- **Serve:** Data Warehouse → BI Platform (dashboards and reports)

**Data quality:** Great Expectations runs validation checks after every dbt transformation. Failures block promotion to the serving layer. OpenLineage tracks end-to-end data lineage for audit and debugging.
```

Create `clients/demo/docs/c4/merchant-portal.md`:
```markdown
# Merchant Portal Components

The Merchant Portal is a React SPA backed by a Node.js BFF (backend-for-frontend) that aggregates data from multiple internal services.

**Key modules:**
- **Transaction Viewer** — search, filter, and export transaction history with real-time status updates
- **Payout Manager** — configure payout schedules, manage bank accounts, and track payout status
- **Dispute Manager** — handle chargebacks, upload evidence, and track resolution deadlines

**Authentication:** SSO via OIDC to the Identity Provider. The BFF validates JWTs through the Auth Gateway. All merchant data access is scoped by `merchant_id` — no cross-tenant visibility.
```

Create `clients/demo/docs/c4/demo-platform.md`:
```markdown
# Data Platform Overview

A simplified view showing how client-specific legacy systems integrate with the shared data platform primitives. The Legacy ERP exports data via CSV/FTP to the Batch ETL layer, which loads it into the Data Lake as Parquet files. dbt transforms the data into the Data Warehouse for analytics consumption.
```

- [ ] **Step 2: Commit**

```bash
git add clients/demo/docs/c4/
git commit -m "docs: add C4 companion prose for demo client (7 diagrams + overview)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Demo Sequence, ERD & Deployment Companion Docs

**Files:**
- Create: 4 sequence `.md` files + `_overview.md`
- Create: 3 ERD `.md` files + `_overview.md`
- Create: 3 deployment `.md` files + `_overview.md`

- [ ] **Step 1: Create sequence section**

Create `clients/demo/docs/sequence/_overview.md`:
```markdown
Sequence diagrams trace key transaction flows through the system, showing the exact order of service interactions. These are particularly useful for understanding latency-critical paths and error handling branches.
```

Create `clients/demo/docs/sequence/payment-flow.md`:
```markdown
# Payment Processing Flow

The happy-path payment flow from consumer tap to merchant webhook. The entire authorization path completes in < 500ms.

**Key observations:**
- Fraud check happens *before* card network authorization — blocking a fraudulent transaction is cheaper than reversing one
- The Kafka event bus decouples the notification and webhook delivery from the payment path — payment confirmation returns to the consumer immediately
- Settlement runs as a separate T+1 batch process
```

Create `clients/demo/docs/sequence/refund-flow.md`:
```markdown
# Refund Processing

Refund flow initiated by a merchant through the portal. Supports both full and partial refunds.

**Validations:** The Payment Engine checks that the original transaction exists and the refund amount does not exceed the captured amount. Refunds against uncaptured (auth-only) transactions are rejected — those should be voided instead.

**Ledger impact:** Every refund creates a reversal entry in the ledger, maintaining the double-entry invariant.
```

Create `clients/demo/docs/sequence/merchant-onboarding.md`:
```markdown
# Merchant Onboarding

The onboarding flow handles identity verification and KYC/AML compliance checks. The Compliance Service performs automated screening against sanctions lists and PEP databases, plus document verification.

**Two outcomes:**
- **Approved:** Merchant account is activated, API keys are provisioned, and a welcome email is sent with getting-started documentation
- **Rejected:** Merchant is notified of the specific issue (e.g., document mismatch) and given clear next steps for resubmission
```

Create `clients/demo/docs/sequence/fraud-realtime-check.md`:
```markdown
# Real-Time Fraud Check

Detailed view of the parallel rule + ML scoring pipeline that runs for every transaction.

**Performance budget:** Total scoring latency must stay under 50ms p99. Rules and ML scoring run in parallel (`par` block) to stay within budget. The Feature Store is optimized for online serving with < 5ms read latency.

**Escalation thresholds:**

| Score Range | Decision | Action |
|-------------|----------|--------|
| < 0.5 | ALLOW | Transaction proceeds normally |
| 0.5 – 0.8 | ALLOW_WITH_REVIEW | Transaction proceeds, case created for manual review |
| > 0.8 | BLOCK | Transaction declined, urgent case created |
```

- [ ] **Step 2: Create ERD section**

Create `clients/demo/docs/erd/_overview.md`:
```markdown
Entity relationship diagrams document the core data models. These map directly to PostgreSQL schemas in the operational database. All tables use UUIDs as primary keys and `timestamptz` for temporal columns.
```

Create `clients/demo/docs/erd/core-transactions.md`:
```markdown
# Core Transaction Data Model

The central transaction model linking merchants, consumers, payment methods, transactions, refunds, and ledger entries.

**Key relationships:**
- A transaction belongs to exactly one merchant and one consumer
- A transaction uses exactly one payment method (card, bank, or wallet)
- Refunds are always linked to a parent transaction — orphan refunds are not allowed
- Ledger entries provide the audit trail: every status change (auth → capture → settle) creates a new entry

**Status lifecycle:** `CREATED → AUTHORIZED → CAPTURED → SETTLED` (happy path) or `→ REFUNDED` / `→ FAILED` at any point.
```

Create `clients/demo/docs/erd/merchant-management.md`:
```markdown
# Merchant Management Data Model

Covers the merchant lifecycle: contacts, bank accounts, API keys, payout schedules, and disputes.

**API key design:** Keys are environment-scoped (TEST vs LIVE) with granular permissions stored as JSONB. The actual key is never stored — only a hash. The `prefix` field (e.g., `npk_live_`) allows quick identification without exposing the secret.

**Payout schedules** link to a specific bank account and support DAILY, WEEKLY, or MONTHLY frequency with configurable minimum payout amounts.
```

Create `clients/demo/docs/erd/fraud-cases.md`:
```markdown
# Fraud Case Data Model

The fraud investigation data model tracks scores, rules, cases, and ML model metadata.

**Score → Case flow:** Not every scored transaction generates a case. Cases are only created when the combined score exceeds the REVIEW or BLOCK threshold. Each case links back to the original fraud score for full traceability.

**Model versioning:** The `fraud_models` table tracks model performance metrics (AUC-ROC, precision@95%) so the team can compare production models against candidates before promoting a new version.
```

- [ ] **Step 3: Create deployment section**

Create `clients/demo/docs/deployment/_overview.md`:
```markdown
Deployment diagrams show how the platform runs in production, including infrastructure topology, CI/CD pipeline, and disaster recovery architecture. All infrastructure runs on AWS across two regions.
```

Create `clients/demo/docs/deployment/production-infra.md`:
```markdown
# Production Infrastructure

The production environment runs on AWS eu-west-1 with EKS (Kubernetes) for container orchestration. Services are deployed across multiple availability zones for resilience.

**Key infrastructure:**
- **ALB + CloudFront** — TLS termination and edge caching for static assets
- **EKS Cluster** — runs all application services with per-service pod scaling
- **Aurora PostgreSQL** — Multi-AZ for automatic failover, handles all transactional data
- **ElastiCache Redis** — cluster mode enabled for fraud feature serving and caching
- **MSK Kafka** — 3-broker cluster for event streaming

**DR:** Asynchronous replication to eu-central-1 with Aurora read replicas and Kafka MirrorMaker 2.
```

Create `clients/demo/docs/deployment/cicd-pipeline.md`:
```markdown
# CI/CD Pipeline

Fully automated pipeline from developer push to production deployment.

**Stages:**
1. **Build & Test** — unit tests, integration tests, SAST (Snyk), DAST (ZAP)
2. **Package** — Docker images pushed to ECR, Helm charts to S3
3. **Staging** — automatic deployment to staging EKS cluster
4. **Production** — manual promotion gate, then rolling deployment to production EKS

**Security:** Every build runs Snyk for dependency vulnerabilities and ZAP for dynamic security scanning against the staging environment. Failed security checks block promotion to production.
```

Create `clients/demo/docs/deployment/disaster-recovery.md`:
```markdown
# Disaster Recovery Architecture

Active-passive DR across two AWS regions with Route 53 health-check failover.

**Recovery targets:**
- **RTO: 15 minutes** — scale standby pods, promote Aurora replica, update Route 53 routing
- **RPO: < 1 minute** — Aurora async replication lag is typically under 30 seconds

**Replication:**

| Component | Method | Target |
|-----------|--------|--------|
| Aurora PostgreSQL | Async replication | eu-central-1 read replica |
| MSK Kafka | MirrorMaker 2 | eu-central-1 topic sync |
| S3 | Cross-region replication | eu-central-1 bucket |

**Failover procedure is documented in the team runbook and tested quarterly.**
```

- [ ] **Step 4: Commit**

```bash
git add clients/demo/docs/sequence/ clients/demo/docs/erd/ clients/demo/docs/deployment/
git commit -m "docs: add sequence, ERD, and deployment companion prose for demo client

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Smoke Test — Generate All Outputs

**Files:**
- None created (uses existing demo client + new scripts)

- [ ] **Step 1: Generate the facelifted gallery**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m scripts.gallery --client demo --history 0 --title "NovaPay"
```

Expected: `clients/demo/index.html` created.

- [ ] **Step 2: Verify gallery features**

```bash
python3 -c "
html = open('clients/demo/index.html').read()
assert 'theme-toggle' in html, 'Missing dark mode toggle'
assert '#1a1a2e' in html, 'Missing dark mode CSS'
assert 'sidebar' in html, 'Missing sidebar'
assert 'modal' in html, 'Missing modal'
assert '280px' in html, 'Missing improved card height'
assert 'pulse' in html, 'Missing pulse animation'
cards = html.count('class=\"card\"')
print(f'Gallery: {cards} cards, dark mode, sidebar, modal — OK')
print(f'Size: {len(html)//1024}KB')
"
```

- [ ] **Step 3: Generate the living docs**

```bash
python3 -m scripts.docs --client demo
```

Expected: `clients/demo/demo-architecture.html` created.

- [ ] **Step 4: Verify docs features**

```bash
python3 -c "
html = open('clients/demo/demo-architecture.html').read()
assert '<!DOCTYPE html>' in html
assert 'NovaPay' in html, 'Missing client name'
assert 'Digital Payments Platform' in html, 'Missing subtitle'
assert 'Table of Contents' in html, 'Missing TOC'
assert '<svg' in html, 'Missing inlined SVGs'
assert '<strong>' in html, 'Missing parsed markdown bold'
assert '<table>' in html, 'Missing parsed tables'
assert '@media print' in html, 'Missing print CSS'
# Check all sections present
for section in ['C4 Diagrams', 'Sequence Diagrams', 'Entity Relationship', 'Deployment']:
    assert section in html, f'Missing section: {section}'
print('Docs: all sections, prose, SVGs, TOC, print CSS — OK')
print(f'Size: {len(html)//1024}KB')
"
```

- [ ] **Step 5: Re-generate PDF deck**

```bash
python3 -m scripts.deck --client demo
```

Expected: `clients/demo/deck.pdf` created.

- [ ] **Step 6: Run full test suite**

```bash
cd /home/alfred/code/arch-diagrams && python3 -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit demo client content** (manifest + docs are tracked; generated HTML and PDF are gitignored)

```bash
git status
```

Verify no generated files are staged. All markdown docs and `client.yaml` should already be committed in previous tasks.
