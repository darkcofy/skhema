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

Gnosis has five top-level commands:

```bash
gnosis init <client> --domain "<domain>"      # scaffold a new ontology workspace
gnosis ingest <artifact> --from <file> ...    # validate + merge LLM extractions
gnosis status --client <client>               # stage completion + lint warnings
gnosis generate available --client <client>   # render ready artifacts (brief, glossary, concept map, …)
gnosis interview-kit --client <client> \
  --stakeholder "<name>"                      # deterministic per-stakeholder interview agenda
```

The day-to-day loop is **skill → LLM → ingest**: read a `skills/gnosis/*.md` playbook, apply it against your LLM of choice plus the raw material, save the output under `clients/<name>/transcripts/_drafts/`, then hand it to `gnosis ingest`. Gnosis validates the schema, runs semantic lint (non-blocking), merges into the workspace with `last_ingested` provenance, and regenerates `ontology/ingest-warnings.md`.

### The seven ingest artifacts

Each skill in `skills/gnosis/` pairs with a `gnosis ingest <artifact>` command. The skill tells the consultant what to prompt; the command enforces the contract on whatever the LLM returned.

| Artifact | Skill | Source | Target | Merge policy |
|---|---|---|---|---|
| `stakeholders` | `extracting-stakeholders.md` | YAML | `00_scope/stakeholders.yaml` | Compound key for TBDs; union interests + decision_rights |
| `glossary` | `extracting-glossary-terms.md` | CSV | `01_language/glossary-seeds.csv` | **Gentle** — curated definitions never clobbered; aliases unioned |
| `synonyms` | `detecting-terminology-synonyms.md` | YAML | `01_language/synonym-conflicts.{yaml,md}` | YAML canonical, markdown rendered; one-time backup of hand-authored `.md` |
| `concepts` | `extracting-concepts-from-transcripts.md` | YAML | `02_concepts/candidate-concepts.yaml` | Overwrite scalars; union source_quotes, related_to, open_questions |
| `mappings` | `mapping-source-systems-to-concepts.md` | CSV | `03_mappings/source-to-canonical.csv` | **Gentle** — curated mappings never clobbered; notes unioned |
| `behavior` | `extracting-events-and-lifecycles.md` | YAML (combined `lifecycles:` + `events:`) | `04_behavior/{lifecycle-states,events}.yaml` | Union states/transitions/carries; cross-file trigger ↔ event lint |
| `formalization` | `formalizing-ontology-from-workspace.md` | YAML | `05_formalization/ontology.yaml` | Overwrite scalars; union properties, relationships, traces_to |

Stages 0 → 5 progress from left to right, but in practice you'll iterate: a concepts ingest that raises `unknown_speaker` warnings sends you back to `stakeholders`; a formalization ingest that raises `unresolved_synonym_as_class` sends you back to `synonyms`. The warnings file is how the stages cross-reference each other.

### Running an ingest

```bash
# After applying skills/gnosis/extracting-concepts-from-transcripts.md to
# transcripts in Claude/Bedrock/ChatGPT, save the YAML output:
#   clients/meshco/transcripts/_drafts/2026-05-06-concepts-extraction.yaml

gnosis ingest concepts \
  --from clients/meshco/transcripts/_drafts/2026-05-06-concepts-extraction.yaml \
  --client meshco \
  --session 2026-05-06-week3-extraction \
  --interviewer alfred
```

Every ingest requires `--session` and `--interviewer` — these are stamped onto each merged entry as provenance so later you can trace which concepts came from which interview.

### Contract model

- **Hard schema** (refused — nothing is written): required fields, type checks, enum values, PascalCase / snake_case rules. Errors are collected and printed all at once.
- **Soft lint** (reported to `ontology/ingest-warnings.md`, non-blocking): unknown speakers, dangling references, low-confidence entries without open_questions, non-past-tense event names, transition triggers without matching events, relationship targets not in the ontology, etc.
- **Provenance** (required on every ingest): `--session` and `--interviewer` are stamped on each touched entry. Git supplies the rest of the history.

Fix warnings by editing the workspace (add the missing stakeholder, rename the dangling reference, …) or by correcting the source fixture and re-ingesting. `gnosis status` surfaces the current warning count after each run.

### Checking state and generating deliverables

```bash
gnosis status --client meshco                # stage %s + artifact readiness + lint warning count
gnosis generate available --client meshco    # render all READY artifacts (engagement brief, glossary, concept map, …)
```

### Generating per-stakeholder interview kits

`gnosis interview-kit` walks the current workspace and produces a markdown briefing for the next conversation — deterministic, no LLM involved. For each named stakeholder it pulls:

- **Open questions** from concepts where they're cited as a source
- **Low-confidence concepts** they contributed to (worth firming up)
- **Unresolved synonym conflicts** where their usage is on record
- **TBD stakeholders** they may be able to introduce

```bash
gnosis interview-kit --client meshco --stakeholder "Emma Ward"
# → generated/interview-kits/2026-05-12-emma-ward.md

gnosis interview-kit --client meshco    # omit --stakeholder to generate one per named stakeholder
```

Regenerate before every session to pick up any intervening ingests.

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
│   └── gnosis/            # Discovery: init, status, generate, ingest_*, interview_kit, readiness
├── skills/                # Dual-use methodology playbooks
│   ├── gnosis/            # 7 skills — one per ingest artifact (stakeholders, glossary, synonyms,
│   │                      #            concepts, mappings, events+lifecycles, formalization)
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
