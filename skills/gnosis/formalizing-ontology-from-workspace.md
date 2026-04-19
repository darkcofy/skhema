---
name: Formalising a canonical ontology from the gnosis workspace
description: Reads the complete gnosis workspace (concepts, stakeholders, glossary, synonyms, lifecycles, events, mappings) and produces a canonical ontology — the set of classes, their properties, and their relationships — that is the engagement's deliverable. Populates `05_formalization/ontology.yaml`. Use at gnosis stage 5 when stages 0-4 are substantially complete.
---

## When to use this skill

- You are at or near the end of an engagement. Stages 0-4 are substantially filled in.
- The client needs a canonical domain model as the engagement deliverable — something that can be signed off, loaded into a catalog, or driven into a data-platform schema registry.
- Terminology conflicts from stage 1 are mostly resolved (synonym-conflicts workshop has happened).
- You have stable lifecycles and events from stage 4 that can inform relationship cardinality.

Unlike the other gnosis skills, this is a **synthesis** skill, not extraction. You are not pulling concepts from raw transcripts — you are curating and promoting the best of what the workspace already contains. The LLM's job is to roll up prior stages into a coherent model; your job is to reject the rollup entries that aren't defensible and to settle the remaining ambiguities.

## Inputs

1. **`02_concepts/candidate-concepts.yaml`** — the pool of concepts to draw from.
2. **`01_language/glossary-seeds.csv`** — canonical definitions to reuse where they exist.
3. **`01_language/synonym-conflicts.yaml`** — check which terms are still unresolved. Do *not* promote a disputed term into a class.
4. **`04_behavior/lifecycle-states.yaml`** and **`04_behavior/events.yaml`** — lifecycles imply an entity with an `identifier` and a `status` property; events imply relationships.
5. **`03_mappings/source-to-canonical.csv`** — tells you which canonical concepts actually have source-system coverage (and are therefore real classes, not aspirational ones).
6. **(Optional)** `05_formalization/ontology.yaml` — for iterative refinement without starting over.

## Output format

YAML matching `05_formalization/ontology.yaml`. One entry per class.

```yaml
- name: Order
  definition: A customer's purchase intent — one basket at one time, across any channel.
  identifier: id
  properties:
    - id
    - customer_id
    - placed_at
    - status
    - total_amount
  relationships:
    - target: Customer
      type: belongs_to
      label: placed_by
      cardinality: N:1
    - target: Shipment
      type: has_many
      label: fulfilled_by
      cardinality: 1:N
    - target: Payment
      type: has_many
      label: paid_by
      cardinality: 1:N
  traces_to:
    - 02_concepts/candidate-concepts.yaml#Order
    - 04_behavior/lifecycle-states.yaml#Order
```

Required fields: `name` (PascalCase), `definition`, `identifier`, `properties` (≥1). Recommended: `relationships`, `traces_to`.

Semantics:

- `name` — must match a concept name in `candidate-concepts.yaml`. Invented names are rejected.
- `definition` — the canonical one-sentence definition. Pull from the glossary or the concept entry; refine if the glossary version is thin.
- `identifier` — the property that uniquely identifies an instance (usually `id`). Required — a class without an identifier can't be loaded into a catalog.
- `properties` — list of property names. Detailed types/required flags go in `05_formalization/properties.yaml` (out of scope for this skill).
- `relationships` — list of links to other classes.
  - `target` — class name in this ontology.
  - `type` — `has_one` / `has_many` / `belongs_to` / `references`.
  - `label` — the role name (`placed_by`, `fulfilled_by`, `parent_category`).
  - `cardinality` — `1:1` / `1:N` / `N:1` / `N:M`. Quote `"1:1"` in the YAML output — unquoted `1:1` is parsed as a sexagesimal integer by PyYAML. Gnosis accepts either form but the quoted version round-trips cleanly.
- `traces_to` — back-references to prior-stage artefacts. Optional but valuable for audit — answer the reviewer's question "where did this class come from?".

## Step-by-step

1. **Start from the concepts list, not from scratch.** Open `candidate-concepts.yaml` and list every concept with `confidence: high` that has source-system coverage in `source-to-canonical.csv`. These are your strongest class candidates.
2. **For each candidate, check the synonym-conflict status.** If the concept's name appears as a term in an unresolved `synonym-conflicts.yaml` entry, do not promote it to a class yet. Flag it in `review-notes.md` and park it.
3. **Pull the canonical definition.** Check the glossary for the term. If the glossary definition exists and is good, use it. Otherwise use the concept's `description`. If both are weak, write a new one drawing on source quotes — and note in `traces_to` where the new definition came from.
4. **Pick the identifier.** For most entities, `id` is fine. Check `source-to-canonical.csv` for rows where `canonical_concept = <class>` and `canonical_property = id` to confirm the identifier has source coverage.
5. **List properties from mapping coverage.** Every distinct `canonical_property` in `source-to-canonical.csv` for this class is a property. Add lifecycle `status` if the class has a lifecycle entry. Don't invent properties that have no source mapping.
6. **Derive relationships from events and mappings.**
   - Every `foreign_key` mapping in `source-to-canonical.csv` implies a `belongs_to` relationship on the source side and a `has_many` on the target side.
   - Every event with `entity: X` and carries including `<other_entity>_id` implies a relationship.
   - Every lifecycle transition trigger implies an event, which implies a relationship.
7. **Add `traces_to` generously.** The formalisation's credibility rests on traceability. A class without `traces_to` looks invented; one with three pointers looks inevitable.
8. **Stop when you've covered the stage-0 outcomes.** Don't promote every concept — only the ones that support the `engagement.md` outcomes. Concepts below the line stay in `candidate-concepts.yaml` as discovery residue.

## Quality checks

- [ ] Every class `name` matches a concept in `candidate-concepts.yaml`
- [ ] No class name is listed as a term in an unresolved `synonym-conflicts.yaml` entry
- [ ] Every class has `identifier` set
- [ ] Every `relationships[].target` is another class in this ontology
- [ ] Every `properties` entry has source coverage (there's at least one row in `source-to-canonical.csv` mapping to it) — or is explicitly noted as derived/computed
- [ ] `traces_to` cites at least one prior-stage file
- [ ] Class count is sensible (typically 10–20 for a mid-sized engagement — if you have 50, you're over-modelling)

## Handoff to gnosis

Save your LLM output under `clients/<name>/transcripts/_drafts/` (date-stamped, e.g. `2026-05-12-formalization.yaml`) and hand it to gnosis:

```bash
gnosis ingest formalization \
  --from clients/meshco/transcripts/_drafts/2026-05-12-formalization.yaml \
  --client meshco \
  --session 2026-05-12-week5-formalization \
  --interviewer alfred
```

What gnosis enforces when you run this:

**Hard schema (refused if violated — nothing is written):**

- Each class has `name` (PascalCase), `definition`, `identifier`, and `properties` (≥1)
- `relationships`, if set, each have `target` (PascalCase), `type` ∈ {has_one, has_many, belongs_to, references}, `label`, `cardinality` ∈ {1:1, 1:N, N:1, N:M}
- No duplicate class `name` within a single ingest

**Soft lint (reported to `ontology/ingest-warnings.md`, non-blocking):**

- `class_without_candidate_concept` — class `name` doesn't match any concept in `02_concepts/candidate-concepts.yaml`. Suggests formalisation drifted from discovery vocabulary.
- `unresolved_synonym_as_class` — class name appears as a term in a `synonym-conflicts.yaml` entry that isn't closed (no `proposed_canonical` set). Formalising disputed terms is how you ship a model nobody agrees with.
- `relationship_target_unknown` — a relationship's `target` isn't a class in this ontology (in the current batch or the existing file). Catches dangling relationships.
- `missing_identifier_property` — the declared `identifier` isn't listed in `properties`. Classes must have their identifier among their properties.

**Merge behaviour:** classes are keyed by `name` (case-insensitive). Re-ingesting an existing class overwrites scalar fields (`definition`, `identifier`) and unions `properties`, `relationships` (dedup by `target+type`), and `traces_to`. Every merged entry carries a `last_ingested` block.

## Anti-patterns

- **Promoting aspirational concepts.** If a concept has no source coverage in `source-to-canonical.csv`, it isn't a class — it's a wish. Keep it in `candidate-concepts.yaml` until mapping lands.
- **Promoting disputed terms.** Formalising "Customer" when the synonym workshop didn't close the Customer / Account Holder / Buyer conflict ships a fight with the deliverable.
- **Inventing properties.** If `properties` includes `fraud_score` but no row in `source-to-canonical.csv` maps anything to `fraud_score`, the property is phantom. Remove it or document how it's derived.
- **Over-modelling.** The engagement brief defined outcomes; the ontology serves them. If you have classes nobody will consume, cut them.
- **Skipping `traces_to`.** A formalisation with no back-pointers to concepts/glossary/mappings can't be defended in a review.
- **Inconsistent cardinality.** If `Order → has_many Shipment` then `Shipment → belongs_to Order` (cardinality 1:N and N:1 respectively). Do the inverse by hand and cross-check.
