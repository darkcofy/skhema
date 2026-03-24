# skhema

*Architecture deliverables as code.*

Skhema is a Git-friendly toolkit for consultants and technical architects who need to turn diagram source into client-ready architecture outputs — and a guided workflow for capturing domain knowledge into structured, reviewable models.

Two products, one workspace:

- **skhema** — turns PlantUML/C4 source into a self-contained HTML gallery, living architecture handbook, and presentation deck
- **gnosis** — guides you through a structured domain discovery workflow, from stakeholder interviews to a formal domain model

Both tools share a `clients/` directory, so a single engagement workspace holds diagrams, domain knowledge, and generated deliverables side by side.

## Why skhema?

Architecture work ends up fragmented across diagram files, slide decks, notes, and hand-written docs.

Skhema keeps those outputs connected:

- Write and version diagrams as code
- Reuse shared architecture models across engagements
- Isolate each client's work in its own workspace
- Regenerate docs and presentations as the architecture evolves
- Capture domain knowledge through a guided, staged workflow

Instead of maintaining separate files, docs, and decks, skhema keeps them connected. Instead of blank-page domain modeling, gnosis gives you structured worksheets and readiness-aware artifact generation.

## Who this is for

Skhema is designed for:

- Architecture consultants
- Solutions architects
- Platform and enterprise architecture teams
- Technical teams that prefer reviewable, text-first workflows

It is not a drag-and-drop diagram editor, a collaborative whiteboard, or a hosted documentation platform.

## Quick start

### Diagrams (skhema)

```bash
skhema init acme
skhema demo acme
```

This scaffolds a client workspace and generates:

- `clients/acme/index.html` — interactive diagram gallery
- `clients/acme/acme-architecture.html` — living architecture handbook
- `clients/acme/deck.pdf` — stakeholder presentation

### Domain knowledge (gnosis)

```bash
gnosis init acme --domain "Order Management"
gnosis status --client acme
gnosis generate available --client acme
```

This scaffolds a guided ontology workspace and generates:

- `clients/acme/ontology/00_scope/` through `05_formalization/` — guided worksheets
- `clients/acme/ontology/generated/` — glossary, conflict reports, concept maps

## Installation

### Docker (recommended)

```bash
docker compose build
docker compose run skhema skhema help
docker compose run skhema gnosis help
```

All dependencies (PlantUML, graphviz, weasyprint) are bundled. Mount your `clients/` directory and go.

```bash
docker compose run skhema skhema demo acme
```

### Local

**Requirements:** Python 3.13+, Git, uv, PlantUML binary, graphviz.

```bash
git clone <repo-url> ~/skhema
cd ~/skhema
uv sync
echo 'export PATH="$HOME/skhema/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc
```

Set `PLANTUML_BIN` if PlantUML is not on your PATH.

Verify:

```bash
skhema help
gnosis help
```

## skhema CLI reference

### `skhema init` — Scaffold a new client

```bash
skhema init acme
skhema init acme-corp   # "acme-corp" → "Acme Corp"
```

Creates `clients/<name>/` with `client.yaml`, `docs/overview.md`, and empty diagram directories.

### `skhema render` — Render diagrams

```bash
skhema render --client acme --all --animate    # All client diagrams with animation
skhema render --client acme --all --png        # PNG instead of SVG
skhema render diagrams/c4/example.puml         # Single file
skhema render file.puml --output out.svg       # Explicit output path
skhema render file.puml --dry-run              # Print resolved source only
```

### `skhema gallery` — Generate HTML gallery

```bash
skhema gallery --client acme
skhema gallery --client acme --title "Acme Corp" --history 5
```

Output: `clients/acme/index.html` — self-contained HTML with dark mode, sidebar nav, modal preview, search/filter.

### `skhema docs` — Generate living docs handbook

```bash
skhema docs --client acme
skhema docs --client acme --title "Acme Corp" --output acme-v2.html
```

Output: `clients/acme/acme-architecture.html` — self-contained HTML with cover page, table of contents, companion prose, inlined SVG diagrams. Print-friendly.

### `skhema deck` — Export PDF or PowerPoint

```bash
skhema deck --client acme              # Merged PDF deck
skhema deck --client acme --pptx       # PowerPoint
skhema deck --client acme --pages      # PDF + individual pages
```

### `skhema adr` — Architecture Decision Records

```bash
skhema adr --client acme              # List all ADRs with linked elements and concepts
skhema adr --client acme --coverage   # Show elements without ADR coverage
```

ADRs live in `clients/<name>/adrs/` as standard markdown files (e.g. `ADR01-event-driven-ingestion.md`). Link them to diagram elements and gnosis concepts with HTML comment tags:

```markdown
<!-- skhema:elements payment_events, kafka_cluster -->
<!-- gnosis:concepts Event, PaymentReceived -->
```

Linked ADRs appear automatically in gallery diagram panels and living docs sections.

### `skhema validate` — Lint diagrams

```bash
skhema validate
```

Checks for: inline element definitions, hardcoded colours, duplicate element IDs.

### `skhema demo` — Regenerate all outputs

```bash
skhema demo         # Demo client
skhema demo acme    # Specific client
```

Runs render + gallery + docs + deck in sequence.

## gnosis CLI reference

### `gnosis init` — Scaffold a domain workspace

```bash
gnosis init acme --domain "Order Management"
```

Creates `clients/acme/ontology/` with guided worksheets for 6 stages of domain discovery. Each file includes facilitator instructions, session guides, capture formats, examples, and completion criteria.

### `gnosis status` — Show progress and readiness

```bash
gnosis status --client acme
gnosis status --client acme --validate
```

Shows stage completion percentages, artifact readiness (READY / PARTIAL / BLOCKED), and suggested next steps. The `--validate` flag adds structural checks.

### `gnosis generate` — Generate artifacts

```bash
gnosis generate available --client acme       # All ready artifacts
gnosis generate engagement_brief --client acme # Specific artifact
```

Generates artifacts that current evidence supports:

| Artifact | Stage | Output |
|----------|-------|--------|
| Engagement brief | 0 | `generated/reports/engagement-brief.md` |
| Draft glossary | 1 | `generated/glossary/draft-glossary.md` |
| Terminology conflict report | 1 | `generated/reports/terminology-conflicts.md` |
| Concept map | 2 | `generated/diagrams/concept-map.puml` + SVG |

## The gnosis workflow

Gnosis guides you through a fixed sequence of domain discovery stages:

| Stage | Goal | Key files |
|-------|------|-----------|
| 0. Setup | Define scope, stakeholders, systems | engagement.md, stakeholders.yaml |
| 1. Language | Capture terminology from stakeholders | glossary-seeds.csv, synonym-conflicts.md |
| 2. Concepts | Identify canonical concepts and relationships | candidate-concepts.yaml, concept-definitions.md |
| 3. Mappings | Map concepts to source systems | source-to-canonical.csv, authority-notes.md |
| 4. Behavior | Capture lifecycles, events, rules | lifecycle-states.yaml, business-rules.md |
| 5. Formalization | Produce a structured domain model | ontology.yaml, properties.yaml, enums.yaml |

Each file is a guided worksheet — not an empty blob, but a facilitator guide with session instructions, capture formats, examples, and completion checkboxes. Artifacts unlock as readiness improves.

Run `gnosis status` to see where you are and what to do next.

## Repository structure

```
skhema/                     # repo root
├── bin/
│   ├── skhema              # diagramming CLI
│   └── gnosis              # domain knowledge CLI
├── clients/                # shared client directory
│   └── <client>/
│       ├── client.yaml     # shared metadata
│       ├── diagrams/       # skhema: diagram source
│       ├── adrs/           # skhema: architecture decision records
│       ├── ontology/       # gnosis: domain worksheets + generated artifacts
│       ├── models/         # skhema: client-specific model overrides
│       ├── docs/           # skhema: companion prose
│       └── rendered/       # skhema: rendered SVGs (gitignored)
├── skhema/                 # diagramming product
│   ├── scripts/            # Python modules
│   ├── lib/                # theme, macros
│   ├── models/             # shared C4 element definitions
│   └── templates/          # diagram scaffolds
├── gnosis/                 # domain knowledge product
│   ├── scripts/            # Python modules
│   ├── templates/          # worksheet templates
│   └── rules/              # readiness rules (YAML)
├── manifest.yaml           # skhema element registry
└── README.md
```

### Include resolution (skhema)

When rendering with `--client`, includes are resolved in order:
1. Relative to the source file
2. `clients/<name>/models/`
3. `skhema/models/` (shared)
4. `skhema/lib/` (shared)

## Living docs

The docs handbook is a living document — rerun `skhema docs` after any diagram or prose change and the output reflects current state.

Companion markdown files are optional. If present, their content appears above the corresponding diagram. If absent, the diagram appears with an auto-generated title.

## Conventions

- Element IDs: `snake_case`
- File names: `kebab-case`
- Theme variables set BEFORE C4 include
- Elements defined ONCE in model layer, never in view files
- AI agents: read `manifest.yaml` first, then load relevant model files

## Current limitations

- Rendering requires a local PlantUML binary (bundled in Docker image)
- PDF deck export uses weasyprint for SVG-to-PDF conversion
- Gnosis artifact generation is deterministic template-based — no LLM inference
