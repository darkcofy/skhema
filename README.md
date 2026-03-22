# skhema

*σχῆμα — "form, shape, figure"*

Architecture diagrams as code for consulting engagements. PlantUML + C4-PlantUML rendered via Kroki API, with multi-client isolation, self-contained HTML gallery, living docs handbook, and PDF/PPTX deck export.

## Installation

**Requirements:** Python 3.10+ and Git. No pip dependencies (except optional `python-pptx` for PowerPoint export).

### Linux / macOS

```bash
git clone <repo-url> ~/skhema
echo 'export PATH="$HOME/skhema/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc
```

### macOS (alternative — symlink)

```bash
git clone <repo-url> ~/skhema
ln -s ~/skhema/bin/skhema /usr/local/bin/skhema
```

### Windows (Git Bash / WSL)

```bash
git clone <repo-url> ~/skhema
echo 'export PATH="$HOME/skhema/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell / CMD)

```powershell
git clone <repo-url> C:\skhema
# Add C:\skhema\bin to your system PATH via:
# Settings → System → About → Advanced system settings → Environment Variables
# Or run the scripts directly: python C:\skhema\scripts\render.py --all
```

### Verify

```bash
skhema help
```

## Quick Start

```bash
# Generate everything for the demo client (render + gallery + docs + deck)
skhema demo

# Or step by step:
skhema render --client demo --all --animate
skhema gallery --client demo
skhema docs --client demo
skhema deck --client demo
```

## CLI Reference

### `skhema render` — Render diagrams

```bash
# Render all shared diagrams
skhema render --all

# Render a single shared diagram
skhema render diagrams/c4/data-platform-container.puml

# Render all client diagrams with animation
skhema render --client acme --all --animate

# Render a single client diagram
skhema render --client acme clients/acme/diagrams/c4/system-context.puml

# Render as PNG instead of SVG
skhema render --client acme --all --png

# Dry-run (print resolved PlantUML source without rendering)
skhema render --client acme clients/acme/diagrams/c4/system-context.puml --dry-run
```

### `skhema gallery` — Generate HTML gallery

```bash
# Generate gallery for a client
skhema gallery --client acme

# Override the display title
skhema gallery --client acme --title "Acme Corp"

# Include version history (default: 3 versions, 0 to disable)
skhema gallery --client acme --history 5
skhema gallery --client acme --history 0
```

Output: `clients/acme/index.html` — self-contained HTML with dark mode toggle, sidebar nav, modal preview, search/filter.

### `skhema docs` — Generate living docs handbook

```bash
# Generate architecture handbook
skhema docs --client acme

# Override the display title
skhema docs --client acme --title "Acme Corp"

# Custom output filename
skhema docs --client acme --output acme-v2.html
```

Output: `clients/acme/acme-architecture.html` — self-contained HTML with cover page, table of contents, companion prose, inlined SVG diagrams. Print-friendly.

### `skhema deck` — Export PDF or PowerPoint deck

```bash
# PDF deck (no dependencies)
skhema deck --client acme

# PowerPoint deck (requires: pip install python-pptx)
skhema deck --client acme --pptx
```

Output: `clients/acme/deck.pdf` (single diagram) or `clients/acme/deck_pages/` (multiple diagrams).

### `skhema validate` — Lint diagrams

```bash
skhema validate
```

Checks for: inline element definitions, hardcoded colours, duplicate element IDs.

### `skhema demo` — Regenerate demo client

```bash
# Regenerate everything for the demo client
skhema demo

# Regenerate for a different client
skhema demo acme
```

Runs render (with animation) + gallery + docs + deck in sequence.

## Architecture

Three-layer system with multi-client extension:

- **`lib/`** — Foundation layer: theme colours, macros, shared styling
- **`models/`** — Model layer: reusable C4 element definitions (one file per domain)
- **`diagrams/`** — View layer: thin files that compose models into specific views
- **`clients/<name>/`** — Client layer: per-client diagrams, models, docs, and generated output

See `docs/superpowers/specs/2026-03-22-arch-diagrams-design.md` for the base design spec.

## Client Structure

Each client is isolated — no cross-client visibility. Shared models are inherited automatically.

```
clients/<name>/
├── client.yaml          # Metadata: name, subtitle, accent color, section order
├── docs/
│   ├── overview.md      # Client-level intro (optional)
│   ├── c4/
│   │   ├── _overview.md # Section intro (optional)
│   │   └── *.md         # Per-diagram companion prose (optional)
│   ├── sequence/
│   ├── erd/
│   └── deployment/
├── models/              # Client-specific model overrides (searched before shared models/)
├── diagrams/            # Client diagram source (.puml)
├── rendered/            # Rendered SVGs (gitignored)
├── index.html           # Gallery (gitignored)
└── <name>-architecture.html  # Living docs handbook (gitignored)
```

### Include Resolution

When rendering with `--client`, includes are resolved in order:
1. Relative to the source file
2. `clients/<name>/models/`
3. `models/` (shared)
4. `lib/` (shared)

### Adding a New Client

```bash
mkdir -p clients/acme/diagrams/c4 clients/acme/models

# Create diagrams, then generate everything
skhema render --client acme --all --animate
skhema gallery --client acme
skhema docs --client acme
skhema deck --client acme

# Or all at once
skhema demo acme
```

## Living Docs

The docs handbook is a "living document" — rerun `skhema docs` after any diagram or prose change and the output reflects current state.

Companion markdown files are optional. If present, their content appears above the corresponding diagram. If absent, the diagram appears with an auto-generated title. Start with zero prose and add narrative where it matters.

Supported markdown: headings, paragraphs, bold, italic, inline code, links, lists, blockquotes, tables, fenced code blocks.

## Conventions

- Element IDs: `snake_case`
- File names: `kebab-case`
- Theme variables set BEFORE C4 include
- Elements defined ONCE in model layer, never in view files
- AI agents: read `manifest.yaml` first, then load relevant model files
- Client branches: `feat-<name>` naming convention
