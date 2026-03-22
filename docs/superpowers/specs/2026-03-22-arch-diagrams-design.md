# Architecture Diagrams-as-Code: Design Spec

## Overview

A version-controlled, AI-agent-friendly system for producing enterprise architecture diagrams using PlantUML + C4-PlantUML, rendered via the Kroki public API. No local installs required. Portable across locked-down machines.

## Decisions

- **Rendering:** Kroki public API (`POST https://kroki.io/plantuml/{format}`)
- **Diagram language:** PlantUML with C4-PlantUML library
- **Include strategy:** Option C — local relative includes for readability, render script inlines before POSTing to Kroki
- **Manifest format:** YAML
- **Rendered output:** Gitignored (reproducible from source)
- **Naming:** `snake_case` element IDs, `kebab-case` filenames
- **Scripts:** Python (portable on locked-down Windows)

## Repo Structure

```
arch-diagrams/
├── lib/
│   ├── theme.puml
│   └── macros.puml
├── models/
│   ├── consumers.puml
│   ├── ingestion.puml
│   ├── storage.puml
│   ├── processing.puml
│   ├── serving.puml
│   ├── governance.puml
│   ├── integration.puml
│   ├── security.puml
│   ├── iot.puml
│   ├── ml_platform.puml
│   └── genai.puml
├── diagrams/
│   ├── c4/
│   ├── sequence/
│   ├── erd/
│   └── deployment/
├── rendered/                   # gitignored
├── scripts/
│   ├── render.py
│   └── validate.py
├── templates/
│   ├── c4_context.puml
│   ├── c4_container.puml
│   ├── sequence.puml
│   └── erd.puml
├── prompts/
│   ├── diagram-agent.md
│   └── examples/
│       ├── good_c4_context.puml
│       └── bad_inline_defs.puml
├── manifest.yaml
├── .gitignore
└── README.md
```

## Three-Layer Architecture

### Foundation Layer (`lib/`)

**`lib/theme.puml`** — C4 colour variables set BEFORE the C4 include so they override defaults:

| Variable | Value | Purpose |
|---|---|---|
| `$PERSON_BG_COLOR` | `#FDE68A` | Warm yellow for persons |
| `$PERSON_FONT_COLOR` | `#333333` | Dark text |
| `$PERSON_BORDER_COLOR` | `#D97706` | Amber border |
| `$SYSTEM_BG_COLOR` | `#FEF3C7` | Light cream for systems |
| `$SYSTEM_FONT_COLOR` | `#333333` | Dark text |
| `$SYSTEM_BORDER_COLOR` | `#D97706` | Amber border |
| `$CONTAINER_BG_COLOR` | `#FEF3C7` | Light cream for containers |
| `$CONTAINER_FONT_COLOR` | `#333333` | Dark text |
| `$CONTAINER_BORDER_COLOR` | `#D97706` | Amber border |
| `$CONTAINER_DB_BG_COLOR` | `#FCD34D` | Deeper gold for databases |
| `$CONTAINER_DB_FONT_COLOR` | `#333333` | Dark text |
| `$CONTAINER_DB_BORDER_COLOR` | `#B45309` | Dark amber border |
| `$COMPONENT_BG_COLOR` | `#FEF9C3` | Pale yellow for components |
| `$COMPONENT_FONT_COLOR` | `#333333` | Dark text |
| `$COMPONENT_BORDER_COLOR` | `#CA8A04` | Gold border |
| `$EXTERNAL_PERSON_BG_COLOR` | `#F5F5F4` | Light stone for external persons |
| `$EXTERNAL_PERSON_FONT_COLOR` | `#666666` | Grey text |
| `$EXTERNAL_PERSON_BORDER_COLOR` | `#A8A29E` | Stone border |
| `$EXTERNAL_SYSTEM_BG_COLOR` | `#F5F5F4` | Light stone for external systems |
| `$EXTERNAL_SYSTEM_FONT_COLOR` | `#666666` | Grey text |
| `$EXTERNAL_SYSTEM_BORDER_COLOR` | `#A8A29E` | Stone border |
| `$EXTERNAL_CONTAINER_BG_COLOR` | `#F5F5F4` | Light stone for external containers |
| `$EXTERNAL_CONTAINER_FONT_COLOR` | `#666666` | Grey text |
| `$EXTERNAL_CONTAINER_BORDER_COLOR` | `#A8A29E` | Stone border |
| `$EXTERNAL_COMPONENT_BG_COLOR` | `#F5F5F4` | Light stone for external components |
| `$EXTERNAL_COMPONENT_FONT_COLOR` | `#666666` | Grey text |
| `$EXTERNAL_COMPONENT_BORDER_COLOR` | `#A8A29E` | Stone border |
| `$REL_TEXT_COLOR` | `#78716C` | Warm grey for arrow labels |
| `$REL_LINE_COLOR` | `#92400E` | Brown-amber for arrows |
| `$BOUNDARY_COLOR` | `#D97706` | Amber for boundaries |
| `$BOUNDARY_BG_COLOR` | `#FFFBEB` | Light cream for boundary fill |

Legend styling via skinparams:
- Background: `#FFFBEB`, Border: `#D97706`, Font: `#333333`

**`lib/macros.puml`** — Shared procedures:

| Procedure | Parameters | Purpose |
|---|---|---|
| `$LayoutLR()` | none | Force left-to-right layout direction |
| `$DomainBoundary($alias, $label)` | alias, label | Styled boundary wrapper for domain grouping |
| `$Note($alias, $text)` | alias, text | Styled note attached to an element |

### Model Layer (`models/`)

Each file defines C4 elements as `!procedure` blocks. Technology is parameterised. Elements defined ONCE, referenced everywhere via `!include`.

**11 domain files:**

| File | Elements |
|---|---|
| `consumers.puml` | `data_analyst` (Person), `data_engineer` (Person), `data_scientist` (Person), `business_user` (Person), `external_system` (System_Ext) |
| `ingestion.puml` | `api_gateway` (Container), `event_stream` (Container), `batch_etl` (Container), `cdc_pipeline` (Container), `file_drop` (Container) |
| `storage.puml` | `data_lake` (ContainerDb), `data_warehouse` (ContainerDb), `operational_db` (ContainerDb), `object_store` (ContainerDb), `cache_layer` (Container) |
| `processing.puml` | `elt_pipeline` (Container), `stream_processor` (Container), `orchestrator` (Container), `dbt_transform` (Container), `spark_job` (Container) |
| `serving.puml` | `bi_platform` (Container), `api_service` (Container), `ml_endpoint` (Container), `data_catalog` (Container), `report_dashboard` (Container) |
| `governance.puml` | `quality_engine` (Container), `access_control` (Container), `lineage_tracker` (Container), `master_data_svc` (Container), `policy_engine` (Container) |
| `integration.puml` | `esb` (Container), `message_broker` (Container), `webhook_handler` (Container), `rest_api` (Container), `graphql_endpoint` (Container) |
| `security.puml` | `identity_provider` (Container_Ext), `auth_gateway` (Container), `secrets_vault` (Container), `firewall` (Container_Ext), `certificate_mgr` (Container), `audit_log` (ContainerDb) |
| `iot.puml` | `edge_device` (Container_Ext), `edge_gateway` (Container), `telemetry_collector` (Container), `device_registry` (ContainerDb), `command_dispatcher` (Container) |
| `ml_platform.puml` | `feature_store` (ContainerDb), `model_registry` (ContainerDb), `training_infra` (Container), `experiment_tracker` (Container), `ml_pipeline` (Container) |
| `genai.puml` | `llm_gateway` (Container), `prompt_registry` (ContainerDb), `rag_pipeline` (Container), `vector_store` (ContainerDb), `eval_framework` (Container), `redteam_harness` (Container), `guardrails_engine` (Container), `agent_runtime` (Container), `feedback_collector` (Container) |

### View Layer (`diagrams/`)

Thin files that:
1. Set theme variables (from `lib/theme.puml`)
2. Include C4 library
3. Include required model files
4. Call element procedures
5. Define only relationships and layout

Organised by diagram type: `c4/`, `sequence/`, `erd/`, `deployment/`.

**C4 library file per diagram type:**

| Diagram type | C4 include required |
|---|---|
| `c4_context` | `C4_Context.puml` |
| `c4_container` | `C4_Container.puml` (transitively includes Context) |
| `c4_component` | `C4_Component.puml` (transitively includes Container) |
| `sequence` | Standard PlantUML (no C4 include) |
| `erd` | Standard PlantUML (no C4 include) |
| `deployment` | `C4_Deployment.puml` |

View files must include the deepest C4 library file needed by any of their model includes.

## Render Script (`scripts/render.py`)

1. Accept single file or `--all` for batch
2. Read `.puml` source
3. Recursively resolve local `!include` paths by inlining file content (walks relative paths from source file directory)
4. Leave remote `!include` URLs untouched (Kroki resolves those)
5. Detect circular includes and error
6. POST resolved source to `https://kroki.io/plantuml/{format}`
7. Save to `rendered/{subdir}/{name}.{svg|png}` (mirrors `diagrams/` directory structure)
8. Default SVG, `--png` flag for PNG
9. `--dry-run` flag to print resolved source without POSTing
10. Retry with exponential backoff (3 attempts) on transient HTTP errors (429, 503)
11. `--all` mode: continue-on-error, report failures at end
12. Non-zero exit on any failure

Usage:
```bash
python scripts/render.py diagrams/c4/data_platform_context.puml
python scripts/render.py diagrams/c4/data_platform_context.puml --png
python scripts/render.py --all
```

## Validation Script (`scripts/validate.py`)

| Rule | Checks |
|---|---|
| No inline element definitions in views | `Container(`, `Person(`, `ContainerDb(` etc. in `diagrams/` files |
| No hardcoded colours | Hex codes outside `lib/theme.puml` |
| No duplicate element IDs | Same ID in multiple model files |
| Missing includes | Elements used but not traced to an `!include` |
| Manifest sync | Model file elements match `manifest.yaml` entries |
| Theme ordering | View files must set theme vars before C4 include |

Returns non-zero on failure. Can be wired into pre-commit or CI.

## Manifest Schema (`manifest.yaml`)

```yaml
version: "1.0"
domains:
  <domain_name>:
    file: models/<domain_name>.puml
    elements:
      <element_id>:
        type: <C4 type>  # Person, Container, ContainerDb, System_Ext, etc.
        description: "<short description>"

diagrams:
  - path: diagrams/<type>/<name>.puml
    title: "<diagram title>"
    type: <c4_context|c4_container|sequence|erd|deployment>
    includes_domains: [<domain1>, <domain2>]
```

## Agent Prompt (`prompts/diagram-agent.md`)

Rules for any AI agent working in this repo:

1. Read `manifest.yaml` first before generating anything
2. Three-layer discipline: views include models, models define elements, lib provides styling
3. Reuse existing elements — never redefine
4. New elements go to model layer + update manifest
5. Local relative includes for human readability
6. `snake_case` element IDs, `kebab-case` filenames
7. Theme variables before C4 include — always

## Templates (`templates/`)

| File | Purpose |
|---|---|
| `c4_context.puml` | System context starter |
| `c4_container.puml` | Container view starter |
| `sequence.puml` | Sequence diagram starter |
| `erd.puml` | ERD starter |

Each includes: theme block, C4 include, placeholder model includes, commented guidance, `LAYOUT_WITH_LEGEND()`.

## Out of Scope (for now)

- Self-hosted Kroki (Option C infra)
- RAG-based context management (start with manifest stuffing)
- CI/CD pipeline
- EY branding (generic palette for now)
- Confluence/Jira plugin integration
