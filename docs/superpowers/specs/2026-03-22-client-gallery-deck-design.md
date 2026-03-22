# Client Gallery & Deck Export: Design Spec

## Overview

Multi-client folder structure with per-client self-contained HTML gallery and slide deck export (PDF + optional PPTX). Each client is isolated — no cross-client visibility.

## Decisions

- **Client isolation:** Each client gets own models, diagrams, rendered output, manifest, gallery
- **Gallery:** Self-contained single HTML file per client with inlined SVG thumbnails
- **Deck:** PDF via Kroki PDF endpoint (stdlib-only), PPTX via python-pptx (optional)
- **No top-level client index** — confidentiality safe for consulting
- **Include resolution:** Client models searched first, then shared models

## Client Folder Structure

```
arch-diagrams/
├── lib/                              # Shared foundation (unchanged)
├── models/                           # Shared primitives (unchanged)
├── templates/                        # Shared templates (unchanged)
├── clients/
│   ├── acme/
│   │   ├── models/                   # Client-specific elements (optional, extends shared)
│   │   ├── diagrams/
│   │   │   ├── c4/
│   │   │   ├── sequence/
│   │   │   ├── erd/
│   │   │   ├── deployment/
│   │   │   └── excalidraw/
│   │   ├── rendered/                 # Client rendered output (gitignored)
│   │   ├── manifest.yaml             # Client-specific manifest (optional)
│   │   └── index.html                # Generated gallery (gitignored)
│   └── <other-client>/
│       └── ...                       # Same structure
├── scripts/
│   ├── gallery.py                    # Gallery generator (new)
│   ├── deck.py                       # Deck export (new)
│   ├── render.py                     # Modified: --client flag
│   └── ...
```

## Render Script Updates (`scripts/render.py`)

### New `--client` flag

```bash
python scripts/render.py --client acme --all              # Render all client diagrams
python scripts/render.py --client acme diagrams/c4/foo.puml  # Render one client diagram
python scripts/render.py --client acme --all --animate    # Render + animate
```

When `--client` is specified:
- Source files searched in `clients/<name>/diagrams/`
- Output written to `clients/<name>/rendered/` (mirroring subdirectory structure)
- Include resolution uses a search path: `clients/<name>/models/` first, then shared `models/`, then `lib/`

### Include Search Path

The `resolve_includes()` function gains an optional `search_paths` parameter:

```python
def resolve_includes(source: str, base_dir: str, search_paths: list[str] | None = None, seen: set | None = None) -> str:
```

When resolving a local `!include`:
1. Try relative to the source file's directory (existing behavior)
2. If not found, try each path in `search_paths` in order
3. First match wins

For client renders, search_paths = [`clients/<name>/models/`, `models/`, `lib/`]

This means client diagrams can write:
```plantuml
!include ../../lib/theme.puml                  ' resolves to shared lib/
!include ../../models/consumers.puml           ' resolves to shared models/
!include ../../models/acme-legacy.puml         ' resolves to clients/acme/models/ first
```

## Gallery Generator (`scripts/gallery.py`)

### Usage

```bash
python scripts/gallery.py --client acme
# -> clients/acme/index.html
```

### Output

Self-contained HTML file (`clients/acme/index.html`):
- No external assets — CSS, JS, and SVG thumbnails all inlined
- Portable: email it, drop it in SharePoint, open from any filesystem

### Page Structure

```
┌─────────────────────────────────────────┐
│  Client Name            Generated: date │
│  N diagrams                             │
├─────────────────────────────────────────┤
│  [Search/filter input]                  │
├─────────────────────────────────────────┤
│  C4 Diagrams (N)                        │
│  ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ thumb│ │ thumb│ │ thumb│            │
│  │      │ │      │ │      │            │
│  │ name │ │ name │ │ name │            │
│  └──────┘ └──────┘ └──────┘            │
├─────────────────────────────────────────┤
│  Sequence Diagrams (N)                  │
│  ┌──────┐ ┌──────┐                      │
│  │ ...  │ │ ...  │                      │
│  └──────┘ └──────┘                      │
├─────────────────────────────────────────┤
│  (ERD, Deployment, Excalidraw sections) │
└─────────────────────────────────────────┘
```

### Features

- **Grouped by type:** C4, Sequence, ERD, Deployment, Excalidraw. Empty sections hidden.
- **Thumbnails:** SVG content inlined directly in the HTML (not base64 — smaller, searchable)
- **Click behavior:** Opens full rendered SVG in a new browser tab (relative path link)
- **Animated indicator:** Small badge on diagrams that contain `~` markers
- **Text filter:** Vanilla JS, filters cards by diagram name. No dependencies.
- **Styling:** Inline CSS. Light grey background (`#f9fafb`), white cards with subtle shadow, yellow accent (`#D97706`) for headings and card borders on hover.

### Client Name Detection

Derived from the folder name. `clients/acme/` → "Acme" (title-cased). Override via `--title "Acme Corp"`.

### Error Handling

- If `clients/<name>/rendered/` is empty: "No rendered diagrams found. Run: python scripts/render.py --client <name> --all"
- If client folder doesn't exist: "Client '<name>' not found in clients/"

## Deck Export (`scripts/deck.py`)

### Usage

```bash
python scripts/deck.py --client acme               # PDF (default, no dependencies)
python scripts/deck.py --client acme --pptx         # PowerPoint (needs python-pptx)
# -> clients/acme/deck.pdf or clients/acme/deck.pptx
```

### PDF Mode (default, stdlib-only)

1. For each `.puml` file in `clients/<name>/diagrams/`, re-render via Kroki's PDF endpoint: `POST https://kroki.io/plantuml/pdf`
2. Resolve includes the same way as render.py (inline local, leave remote)
3. Each diagram becomes one PDF page
4. Concatenate pages into a single PDF
5. Add a title page (client name, date, diagram count) and table of contents

**PDF concatenation:** Basic binary append of PDF objects. For a simple implementation, use the fact that Kroki returns single-page PDFs — concatenate them using a minimal PDF writer that merges page trees. If this proves too complex for stdlib, fall back to generating individual PDFs in `clients/<name>/rendered/pdf/` and printing instructions to merge with an external tool.

### PowerPoint Mode (optional)

1. Check for `python-pptx`: `try: import pptx` — if missing, print install instructions and exit
2. For each diagram, render as PNG via Kroki (300 DPI equivalent: request larger dimensions)
3. One slide per diagram:
   - Landscape layout (13.33" x 7.5")
   - Diagram centered on slide
   - Title from diagram filename (kebab-case → Title Case)
4. First slide: title slide with client name + date
5. Save to `clients/<name>/deck.pptx`

### Ordering

Diagrams appear in the deck in this order:
1. C4 diagrams (alphabetical)
2. Sequence diagrams (alphabetical)
3. ERD diagrams (alphabetical)
4. Deployment diagrams (alphabetical)

Same ordering as the gallery.

## Repo Changes

```
scripts/gallery.py                # New: gallery generator
scripts/deck.py                   # New: deck export
scripts/render.py                 # Modified: --client flag, search_paths for includes
tests/test_gallery.py             # New
tests/test_deck.py                # New
.gitignore                        # Modified: add clients/*/rendered/ and clients/*/index.html
```

## Out of Scope

- Top-level client index/listing
- Client-specific theming (all clients use shared yellow/white theme for now)
- Diagram version history in the gallery
- Live auto-refresh on the gallery page
- Excalidraw files in the deck export (SVG/PlantUML only)
