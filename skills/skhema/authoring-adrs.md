---
name: Authoring architecture decision records (ADRs)
description: Guides the structuring of ADRs in Nygard style, with skhema-specific cross-linking to C4 element IDs and gnosis concepts. Use when a non-trivial architectural decision needs to be recorded, or when reviewing existing ADRs for completeness. ADRs live in `clients/<name>/adrs/` and auto-surface in galleries, handbooks, and decks.
---

## When to use this skill

- A decision has been made with meaningful trade-offs and at least one serious alternative.
- Stakeholders might ask "why did we choose X?" six months from now.
- The decision affects more than one team, system, or deliverable.

Do **not** write an ADR for:
- A preference that has no consequences (e.g. tabs vs spaces).
- A decision with no viable alternative (there was nothing to decide).
- A temporary workaround you expect to revisit within a sprint.

## Inputs

1. **The decision itself** — what was chosen, and (most importantly) what alternatives were considered.
2. **Stakeholder context** — who made the call, when, under what constraints.
3. **Related concepts** — gnosis concept names the decision affects.
4. **Related elements** — C4 element IDs the decision shapes (from `workspace.dsl`).

## Output format

Markdown file at `clients/<name>/adrs/ADR<NN>-<kebab-title>.md`. Example: `adrs/ADR01-iceberg-for-lakehouse.md`.

Standard structure (Michael Nygard's template, skhema-extended):

```markdown
# ADR01: Iceberg for the lakehouse table format

<!-- skhema:elements lakehouse, catalog -->
<!-- gnosis:concepts DataProduct, LineageEdge -->

**Status:** Accepted
**Date:** 2026-04-18
**Deciders:** Alice Chen (Platform Lead), Bob Murphy (Data Engineering), MeshCo Data Council

## Context

MeshCo is adopting a data-mesh model requiring open, durable, cross-engine table formats for its lakehouse layer. Incumbent options include Delta Lake, Apache Hudi, and Apache Iceberg. We need ACID guarantees, time travel for audit, and interoperability with Snowflake, Databricks, and ad-hoc Trino queries.

## Decision

Use **Apache Iceberg** as the canonical table format for all lakehouse data. Use AWS Glue as the metastore, with a migration path to Apache Polaris when it matures.

## Alternatives considered

### Delta Lake
- Pros: Strong Databricks support, mature tooling, Snowflake reads Delta natively.
- Cons: Commercial roots with Databricks create vendor-gravity concerns for a mesh architecture; community-owned Delta Lake spec lags.

### Apache Hudi
- Pros: Best-in-class upsert performance; streaming-native.
- Cons: Smaller community, fewer third-party integrations, MeshCo workload is append-dominant.

## Consequences

- Iceberg's hidden partitioning removes partition-management toil from consumer code.
- Snowflake's Iceberg support becomes the primary cross-engine consumption path — validate at scale in PoC phase.
- Catalog choice (Glue → Polaris) remains a separately-recorded decision (see ADR-04).
- Time-travel queries enable regulatory-audit scenarios not currently supported.
- Migration cost from existing Parquet tables: ~4 engineer-weeks estimated.

## Links

- [Iceberg spec](https://iceberg.apache.org/spec/)
- Related: ADR04 (Catalog choice)
- Supersedes: ADR00 (initial "raw Parquet" decision)
```

Required sections: Context, Decision, Consequences. Alternatives considered is *strongly* recommended — without it, an ADR is a write-up, not a decision record.

## The comment-tag contract

Two HTML comments at the top of the file link this ADR to the rest of skhema/gnosis:

```markdown
<!-- skhema:elements <comma-separated element IDs from workspace.dsl> -->
<!-- gnosis:concepts <comma-separated concept names from candidate-concepts.yaml> -->
```

skhema's gallery, handbook, and deck auto-render this ADR next to every diagram that contains one of the tagged elements, and next to every concept entry that matches. The tags are a soft contract — missing ones don't break the build, but without them the ADR is invisible to downstream artifacts.

## Step-by-step

1. **Pick the next ADR number.** Scan `clients/<name>/adrs/` for existing `ADR<NN>-*.md` files; take the next integer. Zero-pad to two digits.
2. **Write the title.** One line, noun phrase, capturing the *decision* (not the problem). "Iceberg for the lakehouse" — good. "How to choose a table format" — bad.
3. **Add the comment tags.** Open `workspace.dsl` and list the element IDs this ADR touches. Open `candidate-concepts.yaml` and list the concept names.
4. **Fill in metadata.** Status is one of: Proposed, Accepted, Deprecated, Superseded. Date is today (ISO). Deciders is names + roles.
5. **Context — three to five sentences.** State the problem and the constraints. Do not describe the decision here; this is background only.
6. **Decision — one sentence + bullets.** Lead with the chosen option. Use bullets for supporting conditions.
7. **Alternatives considered — one H3 per option.** Each with Pros and Cons bullets. Dry, factual. This is the most important section and the one most commonly skipped.
8. **Consequences — bullets of follow-on effects.** Include both positive ("enables X") and negative ("migration cost of Y weeks") consequences. Don't editorialise.
9. **Links.** Any relevant URLs, related ADRs, supersession chain.

## Quality checks

- [ ] Title is the *decision*, not the question
- [ ] Status is one of the four standard values
- [ ] Date is in YYYY-MM-DD ISO format
- [ ] Deciders list includes names + roles
- [ ] Context does not state the decision
- [ ] Alternatives considered section has at least one alternative with pros and cons
- [ ] Consequences include at least one negative or trade-off — not just upside
- [ ] Comment tags (`skhema:elements`, `gnosis:concepts`) present even if lists are empty (`<!-- skhema:elements -->` flags "nothing yet")
- [ ] ADR file is `ADR<NN>-<kebab-title>.md` (zero-padded)
- [ ] `skhema adr --client <name>` lists the ADR without errors

## Examples

### Minimal-good ADR

```markdown
# ADR02: dbt for the transformation layer

<!-- skhema:elements dbt, catalog -->
<!-- gnosis:concepts DataProduct, DimensionalModel -->

**Status:** Accepted
**Date:** 2026-04-18
**Deciders:** Alice Chen (Platform Lead), Dave Kim (Analytics Engineering)

## Context

We need a SQL-centric transformation framework that supports testing, documentation, lineage, and cross-team contribution. Analytics Engineering uses dbt already; data engineering was considering SQLMesh.

## Decision

Adopt **dbt Core** for the silver and gold layers of the lakehouse.

## Alternatives considered

### SQLMesh
- Pros: Stronger Python integration, virtual environments for dev/staging, model-level versioning.
- Cons: Smaller community, steeper learning curve for existing dbt-trained team.

## Consequences

- Existing dbt skills carry over; onboarding new analytics engineers is faster.
- We lose out on SQLMesh's virtual environment ergonomics; we'll revisit in 18 months.
- dbt's OSS catalog integration is good enough; no separate catalog tool needed for lineage.
```

## Anti-patterns

- **Writing the ADR after implementation is done.** ADRs work when they're the *decision artifact*, not a retrospective write-up. Write during the decision.
- **No alternatives.** An ADR with no "Alternatives considered" section looks like a decree, not a decision. Even if the alternative is "do nothing", state it.
- **Only listing upsides.** Every real decision has a trade-off. If your Consequences section has no negative bullet, you haven't thought hard enough.
- **Vague status.** "Status: In Progress" isn't standard. Use Proposed / Accepted / Deprecated / Superseded.
- **Overlong Context.** If Context goes more than 6 sentences, you're writing an essay. Move detail into Links.
- **Missing comment tags.** An ADR that doesn't connect to the C4 model or the ontology will be invisible in the rendered artifacts. Add the tags even if empty.
- **Paragraph ADRs.** Walls of prose read worse than bulleted alternatives/consequences. Use structure.
