# arch-diagrams

Version-controlled enterprise architecture diagrams using PlantUML + C4-PlantUML, rendered via Kroki API. Multi-client support with per-client HTML gallery, living docs handbook, and PDF/PPTX deck export.

## Quick Start

```bash
# Render shared diagrams
python scripts/render.py --all

# Render a client's diagrams (with animation)
python scripts/render.py --client demo --all --animate

# Generate client gallery (internal dev tool, dark mode + sidebar)
python scripts/gallery.py --client demo --title "NovaPay"

# Generate living docs handbook (single self-contained HTML, client-facing)
python scripts/docs.py --client demo

# Export PDF deck
python scripts/deck.py --client demo

# Export PowerPoint deck (requires: pip install python-pptx)
python scripts/deck.py --client demo --pptx

# Validate all files
python scripts/validate.py
```

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

# Create diagrams, then render
python scripts/render.py --client acme --all --animate

# Add optional docs for living handbook
mkdir -p clients/acme/docs/c4
echo 'name: "Acme Corp"' > clients/acme/client.yaml

# Generate outputs
python scripts/gallery.py --client acme
python scripts/docs.py --client acme
python scripts/deck.py --client acme
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/render.py` | Render PlantUML → SVG/PNG via Kroki API |
| `scripts/gallery.py` | Generate self-contained HTML gallery (dark mode, sidebar, modal preview) |
| `scripts/docs.py` | Generate self-contained HTML architecture handbook with prose + diagrams |
| `scripts/deck.py` | Export PDF deck (stdlib) or PPTX (requires python-pptx) |
| `scripts/animate.py` | Add marching-ant CSS animation to `~` arrows in SVGs |
| `scripts/validate.py` | Lint diagrams for inline definitions, hardcoded colours, duplicate IDs |

## Living Docs

The docs handbook is a "living document" — rerun `docs.py` after any diagram or prose change and the output reflects current state.

Companion markdown files are optional. If present, their content appears above the corresponding diagram. If absent, the diagram appears with an auto-generated title. Start with zero prose and add narrative where it matters.

Supported markdown: headings, paragraphs, bold, italic, inline code, links, lists, blockquotes, tables, fenced code blocks.

## Conventions

- Element IDs: `snake_case`
- File names: `kebab-case`
- Theme variables set BEFORE C4 include
- Elements defined ONCE in model layer, never in view files
- AI agents: read `manifest.yaml` first, then load relevant model files
- Client branches: `feat-<name>` naming convention
