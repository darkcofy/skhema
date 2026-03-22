# arch-diagrams

Version-controlled enterprise architecture diagrams using PlantUML + C4-PlantUML, rendered via Kroki API.

## Quick Start

```bash
# Render a single diagram
python scripts/render.py diagrams/c4/data-platform-container.puml

# Render all diagrams
python scripts/render.py --all

# Validate all files
python scripts/validate.py

# Dry-run (see resolved source without rendering)
python scripts/render.py diagrams/c4/data-platform-container.puml --dry-run
```

## Architecture

Three-layer system:

- **`lib/`** — Foundation layer: theme colours, macros, shared styling
- **`models/`** — Model layer: reusable C4 element definitions (one file per domain)
- **`diagrams/`** — View layer: thin files that compose models into specific views

See `docs/superpowers/specs/2026-03-22-arch-diagrams-design.md` for full design spec.

## Conventions

- Element IDs: `snake_case`
- File names: `kebab-case`
- Theme variables set BEFORE C4 include
- Elements defined ONCE in model layer, never in view files
- AI agents: read `manifest.yaml` first, then load relevant model files
