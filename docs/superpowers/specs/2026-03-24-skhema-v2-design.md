# Skhema v2 Design Spec

**Date:** 2026-03-24
**Scope:** Parser replacement, direct PlantUML rendering, PDF deck fix, Docker packaging, E2E tests, ADR linkage

---

## 1. Parser Replacement

### YAML — PyYAML

Replace all hand-rolled YAML parsing with `yaml.safe_load()`.

**Files affected:**

- `skhema/scripts/manifest.py` — rewrite `parse_manifest()` to `yaml.safe_load()`, drop line-by-line indentation tracking
- `gnosis/scripts/parsers.py` — `count_yaml_entries()` uses `yaml.safe_load()` + `len()`
- `gnosis/scripts/readiness.py` — `load_rules()` uses `yaml.safe_load()`, delete the entire `_safe_yaml_parse()` function (~90 lines of hand-rolled indentation parsing)
- `skhema/scripts/gallery.py` — `parse_client_yaml()` uses `yaml.safe_load()` with defaults dict merge: `{**defaults, **yaml.safe_load(f)}` where defaults provide `name=""`, `subtitle=""`, `accent_color="#D97706"`, `sections=[]`

Public API of each module stays the same — same function names, same return shapes. Callers don't change.

### Markdown — mistune

Replace regex-based markdown rendering with mistune.

**Files affected:**

- `skhema/scripts/docs.py` — replace regex `md_to_html()` with `mistune.html(text)`

Handles document fragments (no full document structure required). ~150 lines of hand-rolled parsing removed, ~20 lines of library calls added.

---

## 2. Rendering Backend — Direct PlantUML

Replace HTTP calls to Kroki with `subprocess.run()` calling the PlantUML native binary.

**File affected:** `skhema/scripts/render.py`

### Changes

- `post_to_kroki()` → `render_plantuml()` — calls `plantuml -t{fmt} -pipe < input > output`
- `-pipe` mode reads stdin, writes stdout — no temp files needed
- CLI format support: svg (default), png (via `--png`). PDF rendering is internal only, used by `deck.py` — not exposed as a CLI flag
- `resolve_includes()` stays as-is — skhema controls the search path (client models → shared models → lib), passes fully-resolved source to PlantUML

### Configuration

```bash
# Environment variable (set by Docker image at build time)
PLANTUML_BIN=/usr/local/bin/plantuml
```

Also supports `plantuml_bin` in `client.yaml`, taking precedence over env var.

### Error handling

- PlantUML exits non-zero on syntax errors, writes to stderr — capture and surface clearly
- Missing binary → fail fast: `"PlantUML not found. Run via Docker or set PLANTUML_BIN"`
- No retry logic needed (local process, not HTTP)

### What gets deleted

All Kroki-specific code: URL construction, HTTP POST, retry/backoff, User-Agent header. ~80 lines removed, ~40 lines added.

### What stays

`resolve_includes()`, `get_client_paths()`, `--animate` post-processing pipeline, CLI interface.

---

## 3. Export — True PDF Deck

**File affected:** `skhema/scripts/deck.py`

### New behavior

1. Render each PlantUML diagram to individual PDF via `render_plantuml(source, fmt="pdf")` internally
2. Order by type priority (c4 → sequence → erd → deployment). Excalidraw diagrams are excluded from PDF deck generation (not PlantUML, cannot be rendered via `-tpdf`)
3. Generate cover page: render a minimal HTML template (client name, subtitle, accent color, date) to PDF via `wkhtmltopdf --page-size A4 -`. Template is a string in `deck.py`, not an external file. If wkhtmltopdf is unavailable, skip cover page with a warning
4. Merge all into single `deck.pdf` via pypdf
5. `deck_pages/` only emitted with `--pages` flag (add to argparse)

```python
import io
from pypdf import PdfWriter

def build_deck(client, output_path, include_cover=True, emit_pages=False):
    writer = PdfWriter()
    if include_cover:
        cover_pdf = render_cover_page(client)
        if cover_pdf:
            writer.append(io.BytesIO(cover_pdf))
    for diagram in ordered_diagrams(client):
        pdf_bytes = render_plantuml(diagram, fmt="pdf")
        writer.append(io.BytesIO(pdf_bytes))
    writer.write(output_path)
    writer.close()
```

### CLI

```bash
skhema deck --client demo                  # → deck.pdf
skhema deck --client demo --pptx           # → deck.pptx
skhema deck --client demo --pages          # → deck.pdf + deck_pages/
```

PowerPoint path unchanged — uses python-pptx with PNG renders. python-pptx bundled in Docker image, not optional.

---

## 4. Docker Packaging

### Package structure

Skhema becomes a proper installable Python package. All `sys.path.insert()` and `PYTHONPATH` hacks in existing scripts are removed. Imports become standard package imports (e.g., `from skhema.scripts.animate import animate_svg`).

Entry points defined in `pyproject.toml`:

```toml
[project.scripts]
skhema = "skhema.cli:main"
gnosis = "gnosis.cli:main"
```

The `bin/skhema` and `bin/gnosis` bash wrappers are kept for non-installed usage but are not the primary path.

### Dockerfile (multi-stage, optimized)

```dockerfile
# Stage 1: build
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/skhema
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-editable
COPY . .

# Stage 2: runtime
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# PlantUML native binary (GraalVM-compiled, no JRE needed)
ADD https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-linux-amd64-v1.2024.8 \
    /usr/local/bin/plantuml
RUN chmod +x /usr/local/bin/plantuml

COPY --from=builder /opt/skhema /opt/skhema
COPY --from=builder /opt/skhema/.venv /opt/skhema/.venv

ENV PATH="/opt/skhema/.venv/bin:/opt/skhema/bin:$PATH"
ENV PLANTUML_BIN=/usr/local/bin/plantuml
WORKDIR /workspace
```

**Note on PlantUML version:** v1.2024.8 is pinned because it has a verified native binary release with `-pipe` support. Not all PlantUML releases ship native binaries — verify the release URL before bumping.

### pyproject.toml

```toml
[project]
name = "skhema"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "PyYAML",
    "mistune",
    "pypdf",
    "python-pptx",
]

[project.scripts]
skhema = "skhema.cli:main"
gnosis = "gnosis.cli:main"
```

### Package manager: uv

- `uv sync` for local dev
- `uv.lock` committed to repo for reproducible builds

### Size optimizations

| Technique | Effect |
|---|---|
| Multi-stage build | No uv/build tools in final image |
| PlantUML native binary | No JRE (~150-200MB saved) |
| `--no-install-recommends` | Skips suggested packages |
| `python:3.13-slim` | ~600MB smaller than full image |
| Single apt layer + cache cleanup | No dangling cache |
| `.dockerignore` | Excludes .git, clients, __pycache__ |

Estimated final image: ~150-200MB.

### .dockerignore

```
.git
clients
**/__pycache__
**/*.pyc
*.egg-info
```

### Usage

```bash
docker run -v ./clients:/workspace/clients skhema render --client demo --all
docker run -v ./clients:/workspace/clients skhema deck --client demo
docker run -v ./clients:/workspace/clients gnosis status --client demo

# Or via compose
docker compose run skhema render --client demo --all
```

### docker-compose.yml

```yaml
services:
  skhema:
    build: .
    volumes:
      - ./clients:/workspace/clients
```

### Non-Docker usage

Still supported — Python 3.13 + PlantUML binary + wkhtmltopdf locally, then `uv sync && bin/skhema`.

### Migration note

This release removes Kroki HTTP rendering entirely. Users currently running `skhema render` without Docker need to install the PlantUML native binary and set `PLANTUML_BIN`. Docker is now the primary distribution path.

---

## 5. E2E Tests

### Structure

```
tests/
  e2e/
    test_render_pipeline.py
    test_gallery_pipeline.py
    test_docs_pipeline.py
    test_deck_pipeline.py
    test_validate_pipeline.py
    test_gnosis_pipeline.py
    test_adr_pipeline.py
    conftest.py
    fixtures/
      mock_workspace/           # minimal client.yaml, 1-2 .puml sources, adrs/, docs/
      mock_rendered/            # pre-rendered SVG + PDF for downstream tests
```

### Fixture contents

`mock_workspace/` contains:
- `client.yaml` — minimal valid config (name, accent_color, sections)
- `diagrams/c4/sample.puml` — one simple C4 context diagram
- `diagrams/sequence/sample.puml` — one sequence diagram
- `docs/c4/overview.md` — companion prose for the C4 diagram
- `adrs/ADR01-sample-decision.md` — one ADR with skhema:elements and gnosis:concepts tags
- `ontology/workspace.yaml` — minimal gnosis workspace

`mock_rendered/` contains:
- `c4/sample.svg` — pre-rendered SVG (valid SVG, minimal content)
- `c4/sample.pdf` — pre-rendered PDF (valid single-page PDF)

### Mocking approach

- Mock `subprocess.run` for PlantUML — return pre-built SVG/PNG/PDF fixtures
- Real PyYAML, mistune, pypdf — fast and deterministic, no reason to mock
- Real filesystem via `tmp_path` pytest fixtures with scaffolded workspace

### Coverage

| Test | Validates |
|---|---|
| render_pipeline | Include resolution → subprocess call → output file written |
| gallery_pipeline | client.yaml parsed → diagrams discovered → HTML with sections, search, dark mode |
| docs_pipeline | Prose parsed → inlined with diagrams → print-friendly HTML |
| deck_pipeline | Diagrams ordered → individual PDFs → merged single deck.pdf with cover |
| validate_pipeline | Inline defs detected, duplicate IDs caught, manifest sync |
| gnosis_pipeline | Workspace scaffolded → templates present → status computes → artifacts generate |
| adr_pipeline | ADRs parsed → links extracted → references in gallery + docs |

### Malformed input tests (in each pipeline file)

- Invalid YAML in client.yaml → clear error
- Missing required fields → clear error
- Empty diagrams directory → graceful skip
- Broken PlantUML syntax → subprocess stderr surfaced
- ADR with bad link tags → warning, not crash

### Running

```bash
uv run pytest tests/              # unit + e2e, mocked PlantUML
uv run pytest tests/e2e/          # just e2e
PLANTUML_LIVE=1 uv run pytest     # real PlantUML for local validation
```

---

## 6. ADR Linkage

### Directory structure

```
clients/demo/
  adrs/
    ADR01-event-driven-ingestion.md
    ADR02-postgres-over-dynamodb.md
    template.md                      # scaffolded by skhema init --adrs
```

### ADR format

Standard ADR markdown with link tags as HTML comments:

```markdown
# ADR01: Event-Driven Ingestion

## Status
Accepted

## Context
Payment events need low-latency processing...

## Decision
Use Kafka for event ingestion.

<!-- skhema:elements payment_events, kafka_cluster -->
<!-- gnosis:concepts Event, PaymentReceived -->

## Consequences
- Requires Kafka ops expertise
- Enables real-time dashboards
```

Link tags are HTML comments — invisible in any markdown viewer, ADRs stay portable.

### New module: `skhema/scripts/adr.py`

```python
@dataclass
class ADR:
    number: int
    title: str
    status: str          # Accepted, Deprecated, Superseded
    path: Path
    elements: list[str]  # from skhema:elements tag
    concepts: list[str]  # from gnosis:concepts tag

def discover_adrs(client_path) -> list[ADR]:
    """Scan adrs/ directory, return parsed ADRs."""

def parse_adr(path) -> ADR:
    """Extract title, status via mistune (render body to HTML for docs integration).
    Extract link tags via regex on raw text (HTML comments are not structured markdown)."""

def resolve_links(adrs, manifest) -> dict[str, list[ADR]]:
    """Map element IDs → ADRs that reference them. Warn on invalid IDs."""

def resolve_concept_links(adrs, workspace) -> dict[str, list[ADR]]:
    """Map gnosis concepts → ADRs. Validate against ontology."""
```

### Integration into existing outputs

| Output | Change |
|---|---|
| gallery.py | Diagram detail panel gets "Related Decisions" list — ADR title + status |
| docs.py | Each section gets "Architectural Decisions" subsection with relevant ADRs inlined |
| gnosis status | Shows concepts with/without ADR rationale as coverage metric |

### CLI

```bash
skhema adr --client demo              # list ADRs with link summary
skhema adr --client demo --coverage   # elements/concepts without ADR coverage
skhema init --client new --adrs       # scaffold adrs/ with template.md
```

ADR coverage check lives exclusively on `skhema adr --coverage`, not on `validate`.

### What this is NOT

- Not an ADR authoring tool — reads markdown files
- Not enforcing a template — link tags are the only requirement for linkage
- No approval workflow — status is informational, git is the audit trail

---

## 7. NovaPay Demo Updates

All new features are demonstrated in the existing `clients/demo/` (NovaPay) workspace:

- **ADRs:** Add 3-5 ADRs to `clients/demo/adrs/` covering key NovaPay architecture decisions, with `skhema:elements` and `gnosis:concepts` link tags referencing existing elements and concepts
- **Gallery:** Regenerate `index.html` showing ADR linkage in diagram detail panels
- **Living docs:** Regenerate `demo-architecture.html` with ADR subsections
- **Deck:** Regenerate `deck.pdf` as a true merged PDF with cover page
- **gnosis status:** Show ADR coverage in status output

---

## Out of Scope

- `skhema/scripts/generate_excalidraw_lib.py` — no changes needed (reads manifest.yaml which now uses PyYAML, but the module's public API is unchanged)
- Incremental builds / caching
- Output safety / HTML sanitization
- Observability / verbose mode
- Config validation / schema enforcement (beyond what PyYAML gives for free)

---

## Dependencies Summary

| Package | Purpose |
|---|---|
| PyYAML | Config/manifest parsing |
| mistune | Markdown rendering |
| pypdf | PDF merging for deck |
| python-pptx | PowerPoint export |

## System Dependencies (Docker image)

| Binary | Purpose |
|---|---|
| PlantUML native (GraalVM) | Diagram rendering, no JRE |
| wkhtmltopdf | HTML → PDF for cover pages |
