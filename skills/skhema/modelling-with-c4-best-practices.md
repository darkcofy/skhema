---
name: Modelling with C4 best practices
description: Guides decisions on when to use C4 L1 (context) vs L2 (container) vs L3 (component) vs L4 (code); naming, boundaries, relationship labels, and data-platform-specific patterns. Use when onboarding a new architect or reviewing a client's workspace for quality. Pairs with authoring-structurizr-dsl when actually writing the model.
---

## When to use this skill

- Reviewing an architect's first pass at a client model.
- Teaching the C4 mental model to a colleague.
- Deciding whether to add L3 components to an already-complex workspace.
- Unsure whether something is a container or a component.

## The C4 mental model (fast recap)

- **L1 — System Context.** The system you own, who uses it, what external systems it talks to. Audience: execs, partners. Count: one per engagement.
- **L2 — Containers.** The deployable/runnable parts of your system (process, service, database, browser app, SPA). Audience: everyone technical. Count: one per system, usually 5–15 containers.
- **L3 — Components.** The modules inside *one* container. Audience: the team working on that container. Count: only for containers worth drilling into, usually 0–3 views per engagement.
- **L4 — Code.** Class diagrams. Audience: nobody in consulting, usually. Skip.

The progression is not "we always draw all four". It's "we always draw L1 and L2; we drill into L3 only where it helps".

## Picking the right level

| If you find yourself modelling... | It's at level... |
|---|---|
| "Our customers and their SSO provider" | L1 — these are external actors |
| "Our platform vs SAP vs Salesforce" | L1 — platform is the focus, others are external systems |
| "The ingestion pipeline and the lakehouse" | L2 — these are containers inside the platform |
| "The Kafka topic name" | L2 property (technology field) or event catalogue (separate artifact), not a diagram |
| "The parser class inside the validator module" | L4 — don't bother |
| "The three logical modules of our RAG service" | L3 — component view for the RAG container |

## Data-platform-specific patterns

Data platforms have recurring shapes. Lean on these to avoid modelling from scratch.

### The "lakehouse medallion" pattern

One container per zone — not one container per table. Bronze, silver, gold are *logical layers* of the same lakehouse container (annotated with `"technology"` including medallion language) unless you run them as separately-deployed processes.

### The "producer / consumer / platform team" tri-actor pattern

For data-mesh engagements, L1 typically shows:
- A **domain team** (producer) publishing data products
- A **consuming team** or **analyst** reading them
- A **platform team** running shared infrastructure

Don't model individual humans. "Data Analyst" is a role; "Alice Chen" is not.

### The "CDC ingestion" container pattern

Debezium / RisingWave / Fivetran live as a single `Ingestion` container, not split by source. One relationship from each External Source → Ingestion; one outbound to the lakehouse.

### The "catalog + observability" pattern

Data catalog, lineage tracker, quality engine often share traffic shapes. In L1 they collapse into one "Governance" or "Catalog" container. In L3 (for that container) you split them out.

## Naming conventions

- **Containers:** noun phrases describing *responsibility*, not technology.
  - Good: `Ingestion`, `Lakehouse`, `Semantic Layer`, `Transformations`
  - Bad: `Kafka`, `Snowflake`, `dbt Cluster`, `Spark Jobs`
- **People:** role, not person.
  - Good: `Data Analyst`, `Platform Team`
  - Bad: `Alice`, `Platform guys`
- **External systems:** the thing's canonical name as the client knows it.
  - Good: `POS`, `ERP`, `Salesforce`
  - Bad: `the till system`, `the CRM thing`
- **Relationships:** verb phrase from A's perspective.
  - Good: `Publishes events`, `Queries curated data`, `Subscribes to change log`
  - Bad: `uses`, `talks to`, `API`

## Boundaries: what's inside vs outside

The **system in focus** is the one your engagement is scoped to. Everything else is external — even if your client also owns it, even if you wrote it yourself last year.

Red flags:
- Multiple `softwareSystem` nodes all owned by the client and all in focus — probably means the scope is unclear, not that you need multiple systems.
- A container that's really an external service — if you can't deploy it, it's not a container.

## When to add L3 components

Add an L3 component view for a container **only if** at least one of:

- The container is complex enough that its internal structure drives the conversation (e.g. a RAG pipeline with retriever + ranker + generator + guardrails).
- There's an ADR that depends on the internal structure (e.g. "we chose BM25 + reranker over pure vector search").
- The audience includes the team that builds *that specific container* and would benefit from seeing its internals.

If none apply, skip L3. A decked-out workspace with eight component views nobody reads is worse than a three-view workspace people understand.

## Common anti-patterns (see and fix)

- **Deployment creep in L2.** Someone added "Kubernetes cluster" and "VPC" as containers. These belong in deployment diagrams (`deploymentNode`), not container views.
- **Database-per-container.** Modelling every Postgres and Redis as its own container makes L2 unreadable. Only split DBs out as containers if they're independently owned/deployed.
- **Person = individual human.** "Alice Chen" is not a C4 person. Her *role* ("Payments Lead") is. If you need to note individuals, put them in `stakeholders.yaml`, not the C4 model.
- **External-external relationships.** A line between two external systems that don't touch your system in focus is noise. Remove.
- **"Uses" labels.** If every relationship says "uses", the labels are doing nothing. Force yourself to write verb phrases.
- **Orphaned containers.** A container with no inbound and no outbound relationships is either wrong or forgotten. Either connect it or delete it.
- **Tagless elements.** Without tags, styling is per-element and unmaintainable. Tag early.

## Review checklist

Use this when reviewing an architect's workspace:

- [ ] Exactly one `softwareSystem` in focus, clearly named
- [ ] 5–15 containers (not 2, not 30)
- [ ] Every container tagged with an architectural layer
- [ ] Every container has a technology value with real tool names
- [ ] Every relationship has a verb-phrase label
- [ ] L1 has 2–5 external systems + 2–5 people — not 20 of each
- [ ] L3 views exist only for containers that warrant them
- [ ] No deployment-layer concepts mixed into container views
- [ ] Styles are tag-based
- [ ] `skhema structurizr validate` passes
- [ ] Exporting to PlantUML succeeds

## Examples

### Fix a too-granular container view

**Before** (15 containers, too narrow):

```
ingestionKafka, ingestionCDC, ingestionSFTP, rawBucket, bronzeBucket,
silverBucket, goldBucket, dbtRunner, airflowDAG, airflowScheduler,
airflowWebserver, snowflakeWarehouse, lookerDashboard, lookerQueryEngine,
dataCatalog
```

**After** (7 containers, responsibility-level):

```
ingestion          (Kafka + CDC + SFTP collapsed)
lakehouse          (raw/bronze/silver/gold are layers within)
transformations    (dbt + Airflow)
warehouse          (Snowflake — deliberately split from lakehouse)
bi                 (Looker)
catalog            (data catalog, lineage)
serving            (API layer if present; otherwise omit)
```

### Fix a vendor-named container

**Before:** `snowflake = container "Snowflake" "Managed warehouse" "Snowflake"`

**After:** `warehouse = container "Warehouse" "Dimensional model + aggregates for BI" "Snowflake"`

Name by responsibility; keep technology in the technology field.
