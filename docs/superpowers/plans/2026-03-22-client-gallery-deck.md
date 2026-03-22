# Client Gallery & Deck Export Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-client folder structure, per-client HTML gallery with version history, and PDF/PPTX deck export.

**Architecture:** Client folders under `clients/<name>/` extend shared primitives. Render script gains `--client` flag with dual include search path. Gallery script generates self-contained HTML with inlined SVG thumbnails and git-based version history. Deck script exports to PDF (stdlib, Kroki PDF endpoint) and PPTX (optional python-pptx).

**Tech Stack:** Python 3 (stdlib), Kroki API (SVG + PDF endpoints), git CLI for history, optional python-pptx

---

## Phase 1: Client Structure & Render

### Task 0: Client Scaffolding & Gitignore

**Files:**
- Modify: `.gitignore`
- Create: `clients/.gitkeep`

- [ ] **Step 1: Update `.gitignore` for client rendered output and galleries**

Append to `.gitignore`:
```
# Client rendered output and generated galleries
clients/*/rendered/
clients/*/index.html
clients/*/*.pdf
clients/*/*.pptx
```

- [ ] **Step 2: Create clients directory**

```bash
mkdir -p clients && touch clients/.gitkeep
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore clients/.gitkeep
git commit -m "scaffold: add clients directory and gitignore patterns

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: Include Search Path in render.py

**Files:**
- Modify: `scripts/render.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Add search path tests**

Add to `tests/test_render.py`:

```python
class TestResolveIncludesSearchPath:
    """Test include resolution with search paths."""

    def test_search_path_fallback(self, tmp_path):
        """If not found relative to source, search paths are tried."""
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "common.puml").write_text("' shared content")
        source = "!include common.puml"
        result = resolve_includes(source, base_dir=str(tmp_path), search_paths=[str(shared)])
        assert "' shared content" in result

    def test_local_takes_priority(self, tmp_path):
        """Local file wins over search path."""
        shared = tmp_path / "shared"
        shared.mkdir()
        (shared / "item.puml").write_text("' shared version")
        (tmp_path / "item.puml").write_text("' local version")
        source = "!include item.puml"
        result = resolve_includes(source, base_dir=str(tmp_path), search_paths=[str(shared)])
        assert "' local version" in result
        assert "' shared version" not in result

    def test_search_path_order(self, tmp_path):
        """First search path wins when file exists in multiple."""
        path_a = tmp_path / "a"
        path_b = tmp_path / "b"
        path_a.mkdir()
        path_b.mkdir()
        (path_a / "item.puml").write_text("' from a")
        (path_b / "item.puml").write_text("' from b")
        source = "!include item.puml"
        result = resolve_includes(source, base_dir=str(tmp_path / "empty"), search_paths=[str(path_a), str(path_b)])
        assert "' from a" in result
```

- [ ] **Step 2: Run tests to see them fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_render.py -v
```

Expected: TypeError — `resolve_includes` doesn't accept `search_paths` yet.

- [ ] **Step 3: Add `search_paths` parameter to `resolve_includes`**

Modify `scripts/render.py` `resolve_includes()`:

```python
def resolve_includes(source: str, base_dir: str, search_paths: list[str] | None = None, seen: set | None = None) -> str:
    """Recursively inline local !include directives. Remote URLs are left untouched.

    Args:
        source: PlantUML source text
        base_dir: Directory to resolve relative includes from
        search_paths: Additional directories to search if include not found relative to base_dir
        seen: Set of already-included paths (circular detection)
    """
    if seen is None:
        seen = set()

    def replacer(match):
        path_str = match.group(1).strip()
        if path_str.startswith("http://") or path_str.startswith("https://"):
            return match.group(0)
        if path_str.startswith("<") and path_str.endswith(">"):
            return match.group(0)

        # Try relative to base_dir first
        full_path = os.path.normpath(os.path.join(base_dir, path_str))

        # If not found, try search paths
        if not os.path.isfile(full_path) and search_paths:
            for sp in search_paths:
                candidate = os.path.normpath(os.path.join(sp, path_str))
                if os.path.isfile(candidate):
                    full_path = candidate
                    break

        if full_path in seen:
            raise ValueError(f"Circular include detected: {full_path}")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Include file not found: {full_path}")
        seen.add(full_path)
        content = open(full_path).read()
        inc_dir = os.path.dirname(full_path)
        resolved = resolve_includes(content, base_dir=inc_dir, search_paths=search_paths, seen=seen)
        seen.discard(full_path)
        return resolved

    return INCLUDE_RE.sub(replacer, source)
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_render.py -v
```

Expected: All 8 tests PASS (5 existing + 3 new).

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py tests/test_render.py
git commit -m "feat: add search_paths to resolve_includes for client model fallback

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: --client Flag in render.py

**Files:**
- Modify: `scripts/render.py`

- [ ] **Step 1: Add `--client` argument and client-aware logic to `main()`**

Add argument:
```python
parser.add_argument("--client", help="Client name (looks in clients/<name>/diagrams/)")
```

Add helper to compute client paths:
```python
def get_client_paths(root: str, client: str) -> tuple[str, str, list[str]]:
    """Return (diagrams_dir, rendered_dir, search_paths) for a client."""
    client_dir = os.path.join(root, "clients", client)
    if not os.path.isdir(client_dir):
        print(f"Client '{client}' not found in clients/", file=sys.stderr)
        sys.exit(1)
    diagrams_dir = os.path.join(client_dir, "diagrams")
    rendered_dir = os.path.join(client_dir, "rendered")
    search_paths = [
        os.path.join(client_dir, "models"),
        os.path.join(root, "models"),
        os.path.join(root, "lib"),
    ]
    return diagrams_dir, rendered_dir, search_paths
```

Modify `find_all_diagrams` to accept a diagrams directory path:
```python
def find_all_diagrams(diagrams_path: str) -> list[str]:
    """Find all .puml files under the given diagrams directory."""
    results = []
    for dirpath, _, filenames in os.walk(diagrams_path):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results
```

Modify `output_path` to accept explicit dirs:
```python
def output_path(source_path: str, diagrams_dir: str, rendered_dir: str, fmt: str) -> str:
    """Compute output path mirroring diagrams structure into rendered dir."""
    rel = os.path.relpath(source_path, diagrams_dir)
    name = os.path.splitext(rel)[0] + f".{fmt}"
    return os.path.join(rendered_dir, name)
```

Modify `render_file` to accept `search_paths` and explicit dirs:
```python
def render_file(source_path: str, diagrams_dir: str, rendered_dir: str, fmt: str, dry_run: bool, animate: bool = False, search_paths: list[str] | None = None) -> bool:
```

Update `main()` to use client paths when `--client` is specified, otherwise use defaults (`diagrams/`, `rendered/`, no search paths).

- [ ] **Step 2: Run all tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add scripts/render.py
git commit -m "feat: add --client flag to render.py for multi-client support

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Create Sample Client & Smoke Test

**Files:**
- Create: `clients/demo/diagrams/c4/demo-platform.puml`
- Create: `clients/demo/models/legacy-erp.puml`

- [ ] **Step 1: Create demo client structure**

```bash
mkdir -p clients/demo/diagrams/c4 clients/demo/diagrams/sequence clients/demo/models
```

- [ ] **Step 2: Create a client-specific model**

Create `clients/demo/models/legacy-erp.puml`:

```plantuml
' ============================================================
' Domain: Demo Client — legacy systems
' ============================================================

!procedure $LegacyErp()
  System_Ext(legacy_erp, "Legacy ERP", "SAP R/3, on-prem")
!endprocedure
```

- [ ] **Step 3: Create a client diagram that uses both shared and client-specific models**

Create `clients/demo/diagrams/c4/demo-platform.puml`:

```plantuml
@startuml
!include ../../../../lib/theme.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
$ApplySkinparams()

!include ../../models/legacy-erp.puml
!include ../../../../models/ingestion.puml
!include ../../../../models/storage.puml

title Demo Client — Data Platform

$LegacyErp()
$BatchEtl()
$DataLake()
$DataWarehouse()

Rel(legacy_erp, batch_etl, "~Exports data", "CSV/FTP")
Rel(batch_etl, data_lake, "~Loads to", "Parquet")
Rel(data_lake, data_warehouse, "Transforms", "dbt")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 4: Render the client diagram**

```bash
python -m scripts.render --client demo --all --animate
```

Expected:
```
Rendering: c4/demo-platform.puml
  -> clients/demo/rendered/c4/demo-platform.svg
  Animated 2 arrow(s)
```

- [ ] **Step 5: Open and verify**

```bash
xdg-open clients/demo/rendered/c4/demo-platform.svg
```

Expected: Yellow/white themed diagram with Legacy ERP (external, stone), shared primitives (yellow), 2 animated arrows.

- [ ] **Step 6: Commit**

```bash
git add clients/demo/
git commit -m "feat: add demo client with client-specific model and diagram

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 2: Gallery Generator

### Task 4: Gallery Script — Core HTML Generation

**Files:**
- Create: `scripts/gallery.py`
- Create: `tests/test_gallery.py`

- [ ] **Step 1: Write tests**

Create `tests/test_gallery.py`:

```python
"""Tests for the gallery generator."""
import os
import pytest
from scripts.gallery import (
    discover_diagrams,
    group_by_type,
    generate_gallery_html,
)


class TestDiscoverDiagrams:
    def test_finds_svg_files(self, tmp_path):
        rendered = tmp_path / "rendered"
        c4 = rendered / "c4"
        c4.mkdir(parents=True)
        (c4 / "diagram.svg").write_text("<svg></svg>")
        (c4 / "other.svg").write_text("<svg></svg>")
        result = discover_diagrams(str(rendered))
        assert len(result) == 2

    def test_ignores_non_svg(self, tmp_path):
        rendered = tmp_path / "rendered"
        rendered.mkdir()
        (rendered / "file.txt").write_text("not svg")
        result = discover_diagrams(str(rendered))
        assert len(result) == 0

    def test_empty_dir(self, tmp_path):
        rendered = tmp_path / "rendered"
        rendered.mkdir()
        result = discover_diagrams(str(rendered))
        assert len(result) == 0


class TestGroupByType:
    def test_groups_correctly(self):
        files = [
            "/r/c4/a.svg",
            "/r/c4/b.svg",
            "/r/sequence/c.svg",
            "/r/erd/d.svg",
        ]
        groups = group_by_type(files, "/r")
        assert len(groups["c4"]) == 2
        assert len(groups["sequence"]) == 1
        assert len(groups["erd"]) == 1

    def test_top_level_files(self):
        files = ["/r/orphan.svg"]
        groups = group_by_type(files, "/r")
        assert len(groups["other"]) == 1


class TestGenerateGalleryHtml:
    def test_returns_html_string(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        html = generate_gallery_html(
            client_name="Test Client",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
        )
        assert "<!DOCTYPE html>" in html
        assert "Test Client" in html

    def test_contains_svg_content(self, tmp_path):
        rendered = tmp_path / "rendered" / "c4"
        rendered.mkdir(parents=True)
        (rendered / "test.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect fill="red"/></svg>')
        html = generate_gallery_html(
            client_name="Acme",
            rendered_dir=str(tmp_path / "rendered"),
            history=0,
        )
        assert "<rect" in html

    def test_sections_by_type(self, tmp_path):
        rendered = tmp_path / "rendered"
        (rendered / "c4").mkdir(parents=True)
        (rendered / "sequence").mkdir(parents=True)
        (rendered / "c4" / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        (rendered / "sequence" / "b.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        html = generate_gallery_html("X", str(rendered), history=0)
        assert "C4" in html
        assert "Sequence" in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_gallery.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/gallery.py`**

```python
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
            section_cards.append(
                f'<div class="card" data-name="{html.escape(name)}">'
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
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_gallery.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/gallery.py tests/test_gallery.py
git commit -m "feat: add gallery generator with type grouping and version history

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Gallery Smoke Test

**Files:**
- None created (uses demo client from Task 3)

- [ ] **Step 1: Generate gallery for demo client**

```bash
python -m scripts.gallery --client demo --history 0
```

Expected: `clients/demo/index.html` created.

- [ ] **Step 2: Open and verify**

```bash
xdg-open clients/demo/index.html
```

Expected: HTML page with "Demo" header, C4 section with one diagram card, SVG thumbnail visible, search filter works.

- [ ] **Step 3: Verify self-contained**

```bash
python -c "
html_content = open('clients/demo/index.html').read()
assert '<!DOCTYPE html>' in html_content
assert '<svg' in html_content  # SVG inlined
assert 'Demo' in html_content
print('Self-contained: OK')
print(f'Size: {len(html_content)} bytes')
"
```

- [ ] **Step 4: Commit** (nothing to commit — gallery is gitignored)

Gallery verified.

---

## Phase 3: Deck Export

### Task 6: Deck Script — PDF Mode

**Files:**
- Create: `scripts/deck.py`
- Create: `tests/test_deck.py`

- [ ] **Step 1: Write tests**

Create `tests/test_deck.py`:

```python
"""Tests for the deck export script."""
import os
import pytest
from scripts.deck import (
    discover_puml_files,
    order_by_type,
)


class TestDiscoverPumlFiles:
    def test_finds_puml(self, tmp_path):
        diagrams = tmp_path / "diagrams" / "c4"
        diagrams.mkdir(parents=True)
        (diagrams / "a.puml").write_text("@startuml\n@enduml")
        (diagrams / "b.puml").write_text("@startuml\n@enduml")
        result = discover_puml_files(str(tmp_path / "diagrams"))
        assert len(result) == 2

    def test_ignores_non_puml(self, tmp_path):
        diagrams = tmp_path / "diagrams"
        diagrams.mkdir()
        (diagrams / "readme.md").write_text("not puml")
        result = discover_puml_files(str(diagrams))
        assert len(result) == 0


class TestOrderByType:
    def test_orders_correctly(self):
        files = [
            "/d/sequence/a.puml",
            "/d/c4/b.puml",
            "/d/erd/c.puml",
            "/d/c4/a.puml",
        ]
        ordered = order_by_type(files, "/d")
        types = [os.path.relpath(f, "/d").split(os.sep)[0] for f in ordered]
        # c4 first, then erd, then sequence
        assert types == ["c4", "c4", "erd", "sequence"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_deck.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/deck.py`**

```python
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
        "User-Agent": "arch-diagrams/1.0",
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
        "User-Agent": "arch-diagrams/1.0",
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
        for i, (puml_path, pdf_data) in enumerate(zip(puml_files, pdf_pages)):
            name = os.path.splitext(os.path.basename(puml_path))[0]
            page_path = os.path.join(pdf_dir, f"{i:02d}_{name}.pdf")
            with open(page_path, "wb") as f:
                f.write(pdf_data)
        # Also write a simple HTML index for the PDF pages
        index = f"<html><head><title>{client_name} Deck</title></head><body>"
        index += f"<h1>{client_name} — Architecture Deck</h1><ol>"
        for i, puml_path in enumerate(puml_files):
            name = diagram_name(puml_path)
            fname = f"{i:02d}_{os.path.splitext(os.path.basename(puml_path))[0]}.pdf"
            index += f'<li><a href="{fname}">{name}</a></li>'
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
    from pptx.util import Emu
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
```

- [ ] **Step 4: Run tests**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/test_deck.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/deck.py tests/test_deck.py
git commit -m "feat: add deck export script with PDF and PPTX modes

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Deck Smoke Test

**Files:**
- None created (uses demo client)

- [ ] **Step 1: Generate PDF deck**

```bash
python -m scripts.deck --client demo
```

Expected: `clients/demo/deck.pdf` or `clients/demo/deck_pages/` created.

- [ ] **Step 2: Verify PDF output**

```bash
ls -la clients/demo/deck*
```

Expected: PDF file(s) present.

- [ ] **Step 3: Run full test suite**

```bash
cd /home/alfred/code/arch-diagrams && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit** (nothing to commit — deck output is gitignored)

Deck verified.
