---
name: Authoring Structurizr DSL for client workspaces
description: Guides the structuring of a client's `workspace.dsl` — people, software systems, containers, components, views, styles, and `!include` patterns. Use when starting a new skhema client or extending an existing workspace. Produces a well-formed Structurizr DSL file that the skhema CLI can `export` to PlantUML.
---

## When to use this skill

- New client — creating `clients/<name>/workspace.dsl` from scratch.
- Existing client — adding a new system/container/component.
- A peer has produced a DSL that feels messy and you want to align it with house style.

Do not use this skill to model something skhema's PlantUML layer handles (sequence diagrams, ERDs, deployment diagrams, Excalidraw sketches). Those stay as hand-written `.puml` files under `clients/<name>/diagrams/<type>/`. Structurizr is for C4 only.

## Inputs

1. **Concept model** — gnosis `02_concepts/candidate-concepts.yaml` (or equivalent).
2. **Stakeholders** — `00_scope/stakeholders.yaml` (for deciding who the Persons are on the L1 view).
3. **Source systems** — `00_scope/source-systems.yaml` (for External SoftwareSystem nodes).
4. **Architecture constraints** — any ADRs in `clients/<name>/adrs/`.

## Output

A single `clients/<name>/workspace.dsl` file. Structurizr Lite renders it live at `localhost:8080`; `skhema structurizr export --client <name>` produces PlantUML for the rest of the pipeline.

## Canonical workspace structure

```structurizr
workspace "MeshCo Retail Data Platform" "Architecture model for MeshCo's data mesh adoption." {

    !identifiers hierarchical

    model {
        // ─── People ───────────────────────────────────────────────
        dataAnalyst   = person "Data Analyst"   "Queries curated data via BI and SQL."
        platformTeam  = person "Platform Team"  "Runs shared infrastructure and catalog."
        domainTeam    = person "Domain Team"    "Owns one or more data products."

        // ─── External systems ─────────────────────────────────────
        pos       = softwareSystem "POS" "Point-of-sale transaction source." "External"
        erp       = softwareSystem "ERP" "Financial and inventory source of truth." "External"

        // ─── The system in focus ──────────────────────────────────
        platform = softwareSystem "MeshCo Data Platform" "Federated data platform supporting mesh-oriented data products." {

            ingestion = container "Ingestion" "CDC + event stream ingestion" "Debezium, Kafka" "Ingestion"
            lakehouse = container "Lakehouse" "Iceberg on S3 + Glue metastore" "Apache Iceberg, S3, Glue" "Lakehouse"
            dbt       = container "Transformations" "dbt silver/gold models" "dbt Core" "Processing"
            semantic  = container "Semantic Layer" "Business metrics and dimensions" "Cube, dbt Semantic Layer" "Semantic"
            catalog   = container "Data Catalog" "Discovery, lineage, contracts" "Unity Catalog" "Catalog"
            serving   = container "Serving" "BI, ML endpoints, operational APIs" "Various" "Serving"
        }

        // ─── Relationships ────────────────────────────────────────
        dataAnalyst -> platform.serving "Queries curated data"
        domainTeam -> platform.lakehouse "Publishes data products"
        platformTeam -> platform.catalog "Operates catalog + contracts"

        pos -> platform.ingestion "CDC via Debezium"
        erp -> platform.ingestion "Daily batch extract"

        platform.ingestion -> platform.lakehouse "Writes raw + bronze tables"
        platform.lakehouse -> platform.dbt "Materialises silver + gold"
        platform.dbt -> platform.semantic "Populates metrics"
        platform.dbt -> platform.catalog "Emits lineage + contracts"
        platform.semantic -> platform.serving "Feeds BI + APIs"
    }

    views {
        systemContext platform "context" {
            include *
            autolayout lr
        }

        container platform "containers" {
            include *
            autolayout lr
        }

        styles {
            element "Person" {
                shape person
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #8B8B8B
                color #ffffff
            }
            element "Ingestion"  { background #D97706 color #ffffff }
            element "Lakehouse"  { background #0369A1 color #ffffff }
            element "Processing" { background #059669 color #ffffff }
            element "Semantic"   { background #7C3AED color #ffffff }
            element "Catalog"    { background #DC2626 color #ffffff }
            element "Serving"    { background #4338CA color #ffffff }
        }
    }
}
```

## Step-by-step

1. **Workspace header.** `workspace "<ClientName> <Topic>" "<one-line description>"`. Enable `!identifiers hierarchical` so referring to nested elements uses dotted names (`platform.ingestion`).
2. **Model people first.** Each Person has a name and a one-line description of what they do. Use title case for display names.
3. **Model external systems.** These are the things *outside* the platform boundary — source systems, consumer systems, third-party APIs. Tag them `"External"` so the style applies.
4. **Model the system in focus.** One `softwareSystem` with a clear boundary. Name it after the platform, not the company.
5. **Model containers inside.** Each container: `<ID> = container "<Display>" "<description>" "<technology>" "<tag>"`. Prefer one container per *domain of responsibility*, not one per microservice.
6. **Only model components when needed.** L3 component diagrams for one specific container at a time. Most client decks never need L3.
7. **Write relationships explicitly.** `producer -> consumer "<verb phrase>"`. Use present-tense action verbs. Omit technology from the relationship label unless it's genuinely important.
8. **Define views.** Minimum: `systemContext` (L1) + `container` (L2) for the focus system. Add `component` views only for containers worth drilling into.
9. **Use `autolayout lr` or `tb`** on every view. Hand-positioning is a trap.
10. **Define styles last.** Tag your containers and style-by-tag, not by individual element. One colour per architectural layer is a strong convention.

## Quality checks

- [ ] Workspace description is one line, not a paragraph
- [ ] All identifiers are lowercase and hierarchical
- [ ] External systems are tagged `"External"`
- [ ] Containers carry a `"technology"` value (real tech names — `Apache Iceberg`, not `database`)
- [ ] Every relationship has a verb-phrase label
- [ ] Every view has `autolayout`
- [ ] Styles are tag-based, not per-element
- [ ] No emojis in element names (they break PlantUML export)
- [ ] `skhema structurizr validate --client <name>` passes
- [ ] `skhema structurizr export --client <name>` produces non-empty `.puml` files

## Examples

### Adding a new container to an existing workspace

**Before:** the platform has ingestion, lakehouse, dbt, serving — but someone added ML endpoints recently.

```structurizr
platform = softwareSystem "MeshCo Data Platform" {
    ingestion = container "Ingestion" ...
    lakehouse = container "Lakehouse" ...
    dbt       = container "Transformations" ...
    serving   = container "Serving" ...

    // Added:
    mlPlatform = container "ML Platform" "Feature store, model registry, serving" "SageMaker, Feast" "MLPlatform"

    // New relationships:
    dbt       -> mlPlatform "Populates feature store"
    mlPlatform -> serving    "Exposes model endpoints"
}

views {
    // ...add style for new tag
    styles {
        // ...
        element "MLPlatform" { background #DB2777 color #ffffff }
    }
}
```

## Anti-patterns

- **Workspace = one big blob.** Multiple concurrent product lines should be multiple systems, not multiple containers in one system.
- **Naming containers after vendors.** Your container is "Lakehouse", not "Snowflake". Technology lives in the `"technology"` field.
- **Adding every system the company runs.** The model in focus is the *one* system you're engaged on. External systems are peripheral.
- **Component views for every container.** Most client audiences want L1 + L2. L3 is for deep-dive sessions only.
- **Hand-positioned layouts.** Do not use `position` coordinates. `autolayout` is good enough; aesthetic tweaks are a rabbit hole.
- **Skipping relationship labels.** "A -> B" with no label is unreadable. Always say what A does to B.
- **Mixing modelling and deployment.** Deployment views (node, deploymentNode) are separate; don't stuff them into container views.
