# Living Docs & Gallery Facelift: Design Spec

## Overview

Two enhancements to the arch-diagrams client tooling:

1. **Gallery facelift** — dark mode, better cards, hover preview modal, sticky sidebar nav, improved search
2. **Living docs deliverable** — new `scripts/docs.py` generates a self-contained HTML architecture handbook per client, combining rendered diagrams with hand-written markdown narrative

Both outputs are single self-contained HTML files with zero external dependencies.

**Audience:** Consulting clients (polished deliverable) and internal team (knowledge base + quick-browse gallery).

## Decisions

- **Single HTML file** for docs deliverable — no zip, no folder structure, just email one file
- **Markdown companions** alongside diagrams — one `.md` per diagram, `_overview.md` per section, `overview.md` per client
- **Lightweight client `client.yaml`** for metadata and section ordering (distinct from root `client.yaml` which describes shared domains/elements)
- **Simple regex markdown parser** — no dependencies, single-pass, no nested inline formatting. Covers headings/paragraphs/bold/italic/code/links/lists/blockquotes. Multi-line list items not supported — each `- ` or `1. ` line is one item
- **Gallery and docs are separate tools** — gallery for internal dev browsing, docs for client delivery
- **Demo client gets full showcase** — all 17 diagrams with companion prose, manifest, section overviews

## File Structure

```
clients/<name>/
├── client.yaml              # Client metadata + section ordering
├── docs/
│   ├── overview.md            # Client-level overview
│   ├── c4/
│   │   ├── _overview.md       # Section intro
│   │   ├── system-context.md  # Companion prose for system-context.puml
│   │   └── ...
│   ├── sequence/
│   │   ├── _overview.md
│   │   └── ...
│   ├── erd/
│   │   └── ...
│   └── deployment/
│       └── ...
├── diagrams/                  # (existing) .puml source files
├── rendered/                  # (existing, gitignored) .svg output
├── index.html                 # (existing, gitignored) dev gallery
└── <client>-architecture.html # (new, gitignored) docs deliverable
```

## Client Manifest (`client.yaml`)

**Note:** This is distinct from the root `manifest.yaml` which describes shared domains and elements (parsed by `scripts/manifest.py`). The client `client.yaml` uses a different, simpler schema and is parsed by a new `parse_client_yaml()` function — a simple line-based reader (same pattern as `manifest.py`) that reads key-value pairs and YAML-style list items. No PyYAML dependency.

```yaml
name: "NovaPay"
subtitle: "Digital Payments Platform"
accent_color: "#D97706"        # Optional, defaults to amber
sections:                      # Controls ordering in docs + gallery sidebar
  - c4
  - sequence
  - erd
  - deployment
```

The `parse_client_yaml()` function lives in `scripts/docs.py` and is also imported by `gallery.py` for sidebar ordering. When `client.yaml` is absent, both scripts fall back to auto-detecting sections from `rendered/` subdirectories, ordered by the existing `TYPE_ORDER` constant.

## Markdown Companion Format

### Diagram companion (`docs/c4/system-context.md`)

Plain markdown. No frontmatter, no metadata, no special syntax. Filename must match the `.puml` filename (minus extension).

```markdown
# System Context

The system context view shows NovaPay's position in the broader ecosystem.

**Key decisions:**
- Card network communication uses ISO 8583 for latency
- Regulatory reporting is push-based
```

### Section overview (`docs/c4/_overview.md`)

```markdown
C4 diagrams model the platform at four levels of abstraction...
```

### Client overview (`docs/overview.md`)

```markdown
NovaPay is a digital payments platform processing 2M+ transactions per day...
```

**Rules:**
- Filename must match the `.puml` filename (minus extension)
- `_overview.md` is reserved for section-level intros
- All files are optional — missing = diagram appears with auto-generated title
- Sweet spot: 2-5 paragraphs per diagram

## Gallery Facelift (`index.html`)

### Dark Mode Toggle

- Toggle button in the header (sun/moon icon, text label)
- Dark palette: `#1a1a2e` background, `#e2e8f0` text, `#2d2d44` cards
- Light palette: existing `#f9fafb` / white cards
- Preference persisted to `localStorage` under key `arch-diagrams-theme` (avoids collisions on `file://` origins)
- Diagrams keep a white background within cards so SVGs remain readable in dark mode

### Better Card Layout

- Cards: `360px` min-width, more padding
- Thumbnail height: `280px` (up from `200px`)
- Diagram name and type shown more prominently
- Animated badge gets a subtle CSS pulse animation

### Hover Preview Modal

- Replaces the existing `<a href>` link wrapping each card with a JS click handler
- Clicking a card opens a modal overlay with the full SVG expanded inline
- Diagram name as modal heading
- Close via Escape key, click-outside, or X button
- "Open in new tab" link inside the modal for raw SVG access (same URL as the old direct link)
- Vanilla CSS + JS, no dependencies

### Sticky Sidebar Navigation

DOM layout changes from single-column to flex:
```html
<div class="layout">
  <aside class="sidebar">...</aside>
  <main class="content">...</main>
</div>
```
The `.header` moves above `.layout`. The existing `.section` and `.card` elements live inside `.content`.

- Left sidebar, `240px` wide
- Collapsible sections: C4, Sequence, ERD, Deployment (from `client.yaml` if present, else `TYPE_ORDER` fallback)
- Count badge per section (e.g., "C4 (7)")
- Click section to scroll; current section highlighted via intersection observer
- Collapses to hamburger menu on screens < `768px`
- Search input lives in the sidebar (always visible)
- Shows match count: "3 of 17 diagrams"

### Filter Upgrade

- Filters both cards AND sidebar section items
- Matches on diagram name and type (existing `data-name` attribute)

## Living Docs Deliverable (`scripts/docs.py`)

### Usage

```bash
python scripts/docs.py --client demo                          # Generate docs
python scripts/docs.py --client demo --title "NovaPay"        # Override name
python scripts/docs.py --client demo --output novapay-v2.html # Custom filename (relative to client dir)
```

### Output

Single self-contained HTML file at `clients/<name>/<name>-architecture.html` (or custom `--output` path).

### Page Structure

1. **Cover section** — client name, subtitle (from manifest), generation date, diagram count, table of contents
2. **Overview** — from `docs/overview.md` (if exists)
3. **Sections** — one per diagram type, in `client.yaml` order
   - Section heading + overview from `docs/<type>/_overview.md` (if exists)
   - For each diagram (alphabetical within section):
     - Companion prose from `docs/<type>/<diagram-name>.md` (if exists)
     - Inlined SVG
     - Auto-generated title from filename (kebab-case → Title Case)
4. **Footer** — generation timestamp, "Generated by arch-diagrams"

### Styling

- Light, professional theme — white background, clean system fonts
- Accent color from `client.yaml` (default: `#D97706`)
- Print-friendly CSS: `@media print` with page breaks between sections, SVGs scale to fit A4
- Responsive: reads well on laptop, tablet, or printed

### Markdown Parser

Regex-based, ~60 lines, covering:
- Headings (`#` through `####`)
- Paragraphs
- Bold (`**text**`), italic (`*text*`), inline code (`` `text` ``)
- Links (`[text](url)`)
- Bullet lists (`- item`) and numbered lists (`1. item`)
- Blockquotes (`> text`)

No tables, images, or fenced code blocks needed for architectural prose.

### Error Handling

- Missing `client.yaml`: use defaults (client name from folder, auto-detect sections from `rendered/` subdirectories)
- Missing `docs/` directory: all diagrams appear with auto-generated titles, no prose
- Missing `rendered/` directory: error with message to run `render.py` first
- Missing individual `.md` files: silently skip, diagram appears without prose

## .gitignore Update

Change:
```
clients/*/index.html
```

To:
```
clients/*/*.html
```

This covers both `index.html` (gallery) and `*-architecture.html` (docs).

## Demo Client Showcase

The existing demo client gets extended to be a complete reference example:

### New files

- `clients/demo/client.yaml`
- `clients/demo/docs/overview.md`
- `clients/demo/docs/c4/_overview.md` + one `.md` per C4 diagram (7 files)
- `clients/demo/docs/sequence/_overview.md` + one `.md` per sequence diagram (4 files)
- `clients/demo/docs/erd/_overview.md` + one `.md` per ERD diagram (3 files)
- `clients/demo/docs/deployment/_overview.md` + one `.md` per deployment diagram (3 files)

Total: 22 new markdown files + 1 manifest

### Generated outputs (all gitignored)

- `clients/demo/index.html` — facelifted gallery with dark mode, sidebar, modal
- `clients/demo/demo-architecture.html` — full docs deliverable with all prose
- `clients/demo/deck.pdf` — PDF deck (existing feature, re-rendered as part of showcase)

## Shared Utilities

`gallery.py` and `docs.py` share logic: `discover_diagrams`, `group_by_type`, `diagram_name`, `parse_client_yaml`. These live in `docs.py` (as the more general script) and are imported by `gallery.py`. This avoids duplication without introducing a third module.

## Repo Changes

```
scripts/gallery.py             # Modified: dark mode, sidebar, modal, better cards
scripts/docs.py                # New: living docs generator
tests/test_gallery.py          # Modified: tests for new gallery features
tests/test_docs.py             # New: tests for markdown parser and doc assembly
.gitignore                     # Modified: clients/*/*.html
clients/demo/client.yaml     # New
clients/demo/docs/             # New: 22 markdown files
```

## Out of Scope

- Client-specific accent colors in gallery (gallery uses shared theme)
- Automatic PDF generation from docs.html (use browser print for now)
- Excalidraw diagram support in docs (handled separately)
- Version history in docs deliverable (gallery-only feature)
- Markdown features beyond the basics (tables, images, code blocks)
- Multi-language support
