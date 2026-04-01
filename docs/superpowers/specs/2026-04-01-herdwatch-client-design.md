# Herdwatch skhema Client — Design Spec

**Date:** 2026-04-01
**Status:** Approved

## Goal

Create a `herdwatch` client in skhema that documents the Herdwatch Data Layer architecture from system context (L1) down to code/schema level (L4) using C4 diagrams.

## Scope

The **data layer** is the system boundary. Everything outside it — mobile app, enterprise webapp, Mission Control ERP, customer support agents, analysts, Power BI — are external actors.

### Data Layer Components

| Component | Technology | Description |
|-----------|-----------|-------------|
| Raw Layer | RisingWave CDC | MySQL (5 regions: IE, UK, US, AU, Global) → CDC sources → regional tables → unions → Iceberg sinks → S3/Glue `raw_layer` |
| SQLMesh | SQLMesh (Python/SQL) | Bronze, silver, gold transformations on top of raw layer |
| StarRocks (legacy) | Managed MVs (`manage_mv` script) | Current serving layer — materialized views with manual management |
| StarRocks (future) | CTAS (CREATE TABLE AS SELECT) | New serving pattern replacing managed MVs |
| Soda | Soda Core (YAML) | Data quality checks and alerting |
| Infrastructure | K8s, S3, Glue Catalog | Deployment and storage infrastructure |

### External Actors

**Source side:**
- 5 Regional MySQL DBs (IE, UK, US, AU, Global)
- Herdwatch Mobile App → MySQL
- Enterprise Webapp → MySQL
- Mission Control (internal ERP) → MySQL

**Consumer side:**
- Data Engineers (operate pipelines)
- Data Analysts (query StarRocks)
- Customer Support Agents (query data)
- Power BI (dashboards/reporting)

## Approach: Hybrid Manual + SQLPrism

- **L1 (System Context) and L2 (Container):** Hand-crafted PlantUML/C4 — architectural narrative and framing
- **L3 (Component) and L4 (Code/Schema):** Manual for all components except SQLMesh
- **SQLMesh L3 and L4:** SQLPrism-assisted — extract real model graph, schemas, column lineage from the codebase and transform into PlantUML

SQLPrism only applies to the SQLMesh layer. RisingWave, StarRocks, Soda, and Infrastructure are Python/YAML/config — not indexable by SQLPrism.

## Diagram Inventory

### L1 — System Context (1 diagram, manual)

| File | Description |
|------|-------------|
| `c4/system-context.puml` | Herdwatch Data Layer as system boundary, all external actors around it |

### L2 — Container Overview (1 diagram, manual)

| File | Description |
|------|-------------|
| `c4/container-overview.puml` | Inside the data layer: Raw Layer, SQLMesh (bronze/silver/gold), StarRocks, Soda, Infrastructure |

### L3 — Component (6 diagrams, 1 SQLPrism-assisted)

| File | Description | Method |
|------|-------------|--------|
| `c4/component-raw-layer.puml` | CDC sources, regional tables, unions, strip-tz views, Iceberg sinks | Manual |
| `c4/component-sqlmesh.puml` | Bronze, silver, gold models and dependencies | SQLPrism-assisted |
| `c4/component-starrocks-managed-mv.puml` | Legacy: managed MVs, refresh scripts, dependency management | Manual |
| `c4/component-starrocks-ctas.puml` | Future: CTAS pattern, scheduling, data flow from gold | Manual |
| `c4/component-soda.puml` | Quality checks, dashboards, alerting | Manual |
| `c4/component-infrastructure.puml` | K8s cluster, S3 buckets, Glue catalog, networking | Manual |

### L4 — Code/Schema (9 diagrams, 3 SQLPrism-assisted)

| File | Description | Method |
|------|-------------|--------|
| `erd/raw-layer-tables.puml` | 49 CDC table schemas, regional structure, union schema | Manual |
| `erd/sqlmesh-bronze.puml` | Bronze model schemas | SQLPrism |
| `erd/sqlmesh-silver.puml` | Silver model schemas | SQLPrism |
| `erd/sqlmesh-gold.puml` | Gold model schemas | SQLPrism |
| `lineage/sqlmesh-lineage.puml` | Full model lineage graph (bronze→silver→gold) | SQLPrism |
| `erd/starrocks-managed-mv.puml` | Legacy MV definitions, source mappings, refresh topology | Manual |
| `erd/starrocks-ctas.puml` | CTAS table schemas, source queries | Manual |
| `erd/soda-checks.puml` | Quality check definitions, coverage map | Manual |
| `deployment/infrastructure.puml` | K8s pods, S3 bucket layout, Glue databases, IAM roles | Manual |

**Total: 17 diagrams** (8 C4 + 6 ERD + 1 lineage + 1 deployment + 1 Soda coverage)

## Client File Structure

```
clients/herdwatch/
├── client.yaml
├── diagrams/
│   ├── c4/
│   │   ├── system-context.puml              # L1
│   │   ├── container-overview.puml          # L2
│   │   ├── component-raw-layer.puml         # L3
│   │   ├── component-sqlmesh.puml           # L3 (SQLPrism)
│   │   ├── component-starrocks-managed-mv.puml  # L3 legacy
│   │   ├── component-starrocks-ctas.puml    # L3 future
│   │   ├── component-soda.puml              # L3
│   │   └── component-infrastructure.puml    # L3
│   ├── erd/
│   │   ├── raw-layer-tables.puml            # L4
│   │   ├── sqlmesh-bronze.puml              # L4 (SQLPrism)
│   │   ├── sqlmesh-silver.puml              # L4 (SQLPrism)
│   │   ├── sqlmesh-gold.puml                # L4 (SQLPrism)
│   │   ├── starrocks-managed-mv.puml        # L4
│   │   ├── starrocks-ctas.puml              # L4
│   │   └── soda-checks.puml                 # L4
│   ├── lineage/
│   │   └── sqlmesh-lineage.puml             # L4 (SQLPrism)
│   └── deployment/
│       └── infrastructure.puml              # L4
├── models/
│   ├── herdwatch-actors.puml                # External actor macros
│   ├── herdwatch-data-layer.puml            # Core system element macros
│   └── herdwatch-infra.puml                 # Infrastructure element macros
├── docs/
│   └── overview.md                          # Scope, principles, key decisions
└── rendered/                                # gitignored: SVG/PNG outputs
```

No ontology directory — diagrams and docs only.

## Gitignore Coverage

Already handled by existing `.gitignore` patterns:
- `clients/*/rendered/` — SVG/PNG outputs
- `clients/*/*.html` — gallery and docs HTML
- `clients/*/*.pdf` — deck PDF
- `clients/*/*.pptx` — PowerPoint
- `clients/*/deck_pages/` — slide pages

Source files (`.puml`, `.yaml`, `.md`, models) are tracked in git.

## Implementation Order

1. Scaffold client (`skhema init herdwatch`) and configure `client.yaml`
2. Create model files (actors, data-layer, infra macros)
3. L1 — `system-context.puml`
4. L2 — `container-overview.puml`
5. L3 — Component diagrams (6 diagrams, start with raw layer)
6. Index `dp-svc-hwlake-bronze/sqlmesh` with SQLPrism
7. L4 — ERD, lineage, and deployment diagrams (9 diagrams)
8. Write `docs/overview.md`
9. Render all and generate gallery/docs
