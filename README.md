# skhema

*Consulting deliverables as code.*

A dual-product toolkit for consultant architects who need to turn messy client engagements into reproducible, shareable, reviewable artifacts — and a skills library that makes the methodology itself the force multiplier.

Two products, one workspace, one skills library:

- **gnosis** *(headliner)* — guided domain-discovery workflow with readiness gates. Captures stakeholder interviews, canonical terminology, and domain ontology through six staged worksheets. Deterministic plumbing (scaffold, status, generate); extraction handled by [skills](skills/) executed against whichever LLM you have access to.
- **skhema** *(supporting)* — deliverable packager. Consumes PlantUML (hand-written *or* exported from [Structurizr DSL](https://structurizr.com)) and produces a polished self-contained HTML gallery, living architecture handbook, and Reveal.js presentation deck for client hand-off.
- **skills** *(force multiplier)* — a [dual-use library](skills/README.md) of SKILL.md playbooks covering gnosis extraction (transcripts → structured worksheets) and skhema authoring (Structurizr DSL, C4 best practices, Reveal decks, ADRs, living docs). Read as a human playbook, or apply with any LLM (Claude, ChatGPT, Gemini, Cursor, Ollama) — the methodology is the product.

Both tools share a `clients/` directory, so a single engagement workspace holds the Structurizr model, domain knowledge, skills, and generated deliverables side by side.

## Why this exists

Architecture consulting ends up fragmented across diagram tools, slide decks, interview notes, and hand-written docs. Each engagement re-invents structure. Reviews are unrepeatable. Methodology walks out the door when people change roles.

skhema keeps it connected and repeatable:

- Structurizr DSL as the source of truth for C4 models (mature, cross-engine, battle-tested)
- Gnosis's readiness-gated staged worksheets for domain discovery (the missing piece in every consulting toolkit)
- Jinja2-templated outputs that look professional without custom design work
- A **skills library** that captures the methodology in a form both humans and LLMs can execute
- Clean separation: Python for deterministic plumbing, Markdown SKILL.md files for the judgement-heavy work

## Positioning

| | Does C4 modelling | Domain discovery | Client-ready HTML/PDF hand-off | Dual-use methodology library |
|---|---|---|---|---|
| **Structurizr** | ✅ (best in class — owned here) | ❌ | ⚠️ functional, not pretty | ❌ |
| **arc42** | — (template only) | ❌ | ⚠️ template | ❌ |
| **Backstage** | ❌ (internal portal, not client) | ❌ | ❌ | ❌ |
| **skhema + gnosis** | — (delegates to Structurizr) | ✅ | ✅ | ✅ |

Use Structurizr for modelling. Use gnosis for discovery. Use skhema to package the output for client hand-off. Use skills as the methodology playbook.

## Who this is for

- Big-4 and independent architecture consultants running data / platform / enterprise engagements
- Solutions architects producing client-facing deliverables
- Anyone who has ever emailed a ZIP of diagrams to a partner and felt embarrassed

It is **not**:

- A drag-and-drop diagram editor
- A collaborative whiteboard
- A hosted SaaS documentation platform
- An AI product (there's no LLM code in this repo — skills work with whichever LLM you bring)

## Quick start

### Docker (recommended)

```bash
docker compose build

# Live model review in your browser
CLIENT=meshco docker compose up structurizr-lite
# → open http://localhost:8080

# One-shot generate all deliverables
docker compose run skhema skhema structurizr export --client meshco
docker compose run skhema skhema render --client meshco --all --animate
docker compose run skhema skhema gallery --client meshco
docker compose run skhema skhema docs --client meshco
docker compose run skhema skhema deck --client meshco
```

Outputs land in `clients/meshco/`:

- `index.html` — diagram gallery with search, filter, and ADR cross-references
- `meshco-architecture.html` — living architecture handbook
- `deck.html` — self-contained Reveal.js presentation (responsive, keyboard-nav, speaker notes)
- `ontology/generated/` — engagement brief, glossary, terminology conflicts, concept map

For a PDF of the deck: open `deck.html?print-pdf` in any browser, Cmd+P, Save as PDF.

### Local

```bash
git clone <repo-url> ~/skhema && cd ~/skhema
uv sync

# skhema / gnosis are now on PATH as proper entry points
skhema --help
gnosis --help
```

Requires Python 3.11+, PlantUML binary on PATH (or `PLANTUML_BIN` env var), and graphviz. For Structurizr export you also need `structurizr-cli` (or use the Docker image).

## Gnosis workflow

```bash
gnosis init meshco --domain "Retail Data Mesh"
# Fill in the six stages — either by hand, or by applying skills to transcripts
# with your LLM of choice:
#   • skills/gnosis/extracting-concepts-from-transcripts.md
#   • skills/gnosis/extracting-glossary-terms.md
#   • skills/gnosis/detecting-terminology-synonyms.md
#   • skills/gnosis/extracting-stakeholders.md
#   • skills/gnosis/extracting-events-and-lifecycles.md

gnosis status --client meshco       # See stage completion + artifact readiness
gnosis generate available --client meshco   # Produce all READY artifacts
```

## Skhema workflow

```bash
skhema structurizr export --client meshco    # Structurizr DSL → PlantUML
skhema render --client meshco --all --animate  # PlantUML → SVG
skhema gallery --client meshco                # SVGs → gallery.html
skhema docs --client meshco                    # SVGs + prose → handbook.html
skhema deck --client meshco                    # SVGs → Reveal.js deck.html
skhema adr --client meshco                     # List ADRs + coverage
skhema validate                                # Lint conventions
```

## Repository layout

```
skhema/
├── src/
│   ├── skhema/            # Packaging: render, gallery, docs, deck, adr, structurizr
│   └── gnosis/            # Discovery: init, status, generate, readiness
├── skills/                # Dual-use methodology playbooks
│   ├── gnosis/            # 5 extraction skills
│   ├── skhema/            # 5 authoring skills
│   └── README.md          # Dual-use explanation + portability table
├── clients/
│   └── meshco/            # Public demo client (MeshCo Retail Data Mesh)
│       ├── workspace.dsl  # Structurizr DSL — source of truth
│       ├── ontology/      # Gnosis workspace
│       ├── adrs/          # Architecture decision records
│       ├── docs/          # Companion prose for the handbook
│       └── diagrams/      # Hand-written .puml (sequence, ERD, deployment)
├── manifest.yaml          # Reference catalogue — 2026 data-arch vocabulary
├── Dockerfile             # Python + PlantUML + Structurizr CLI + graphviz
├── docker-compose.yml     # skhema + structurizr-lite services
└── pyproject.toml         # Python package config
```

Private client workspaces (real EY / previous-employer data) live locally under `clients/<name>/` and are gitignored. Only `clients/meshco/` is committed.

## Skills library

The skills are the differentiator. Each file in [`skills/`](skills/) is two things at once:

- **A human-readable best-practices playbook** — methodology for a consultant to apply by hand.
- **An LLM-executable instruction file** — point any LLM at it plus your raw material, get structured output.

Skills follow the [Anthropic SKILL.md format](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md). Works natively in Claude Code; adapter-compatible with Cursor, Windsurf, Cline, ChatGPT Custom GPTs, and Gemini Gems. See [`skills/README.md`](skills/README.md) for the portability table.

## Conventions

- Element IDs: `snake_case`
- Filenames: `kebab-case`
- Client workspaces: `clients/<kebab-case-client>/`
- ADRs: `ADR<NN>-<kebab-title>.md` with `<!-- skhema:elements -->` and `<!-- gnosis:concepts -->` tags
- Structurizr DSL: `clients/<name>/workspace.dsl` (Lite convention)

## Development

```bash
uv sync                         # install everything
uv run pytest tests/            # 217 unit + e2e tests (local_only skipped)
uv run pytest tests/ -m local_only   # run real-client tests (Herdwatch)
uv run ruff check src/ tests/
uv run mypy src/
```

Tests are designed to run without PlantUML installed — the e2e suite mocks the binary. Full pipeline end-to-end runs against the `meshco` client in CI via the Dockerfile.

## Status

v3 — gnosis-led pivot. Previous v1/v2 positioning as "architecture diagrams as code" has been retired; Structurizr owns that space. See the design spec in your local `docs/superpowers/specs/` (gitignored) for the full v3 rationale.

## License

Apache 2.0 — see [LICENSE](LICENSE).
