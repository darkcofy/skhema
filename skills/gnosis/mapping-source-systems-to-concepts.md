---
name: Mapping source-system fields to canonical concepts
description: Reads source-system schemas, data dictionaries, or sample extracts and produces rows for gnosis `03_mappings/source-to-canonical.csv`. Each row captures how a field in an operational system maps to a property on a canonical concept. Use at gnosis stage 3 (system mapping) once candidate concepts from stage 2 are stable.
---

## When to use this skill

- Candidate concepts from stage 2 are reasonably stable — you have canonical names the business agrees on.
- You have access to source-system artefacts: DDL exports, Confluence schema pages, ERD diagrams, sample CSV extracts, dbt source YAMLs.
- You need to produce the data-engineering crosswalk that will drive ingestion work.

This skill is where consultants burn the most time on real engagements. The LLM genuinely helps: it can read long DDL files, compare field names, propose canonical matches, and flag ambiguous cases far faster than by hand. Your job is to review, correct the confidence levels, and resolve the ambiguities.

## Inputs

1. **Source material** — DDL exports, data dictionaries, sample CSVs, dbt `sources.yml`, Confluence schema pages, ERDs. The more structured the source material, the cleaner the extraction.
2. **`02_concepts/candidate-concepts.yaml`** — the canonical vocabulary. Every `canonical_concept` value in your output must resolve against this file.
3. **(Optional)** `00_scope/source-systems.yaml` — the registered source systems. `source_system` values should match the `id` or `name` of a registered system.
4. **(Optional)** Existing `source-to-canonical.csv` — extend without duplicating.

## Output format

CSV matching `03_mappings/source-to-canonical.csv`. One row per source field.

```csv
source_system,source_entity,source_field,canonical_concept,canonical_property,mapping_type,confidence,notes
pos,transactions,txn_id,Transaction,id,direct,high,Primary key in POS; canonical identifier
pos,transactions,customer_ref,Customer,id,foreign_key,high,FK into POS customers table
pos,transactions,amount_cents,Transaction,amount,transform,high,"Amount in minor units — divide by 100 for canonical Money type"
commerce,orders,order_uuid,Order,id,direct,high,
erp,purchase_orders,po_number,,,ambiguous,low,"ERP 'purchase order' is a different concept from customer Order — flag for stakeholder workshop"
```

Required columns: `source_system`, `source_entity`, `source_field`, `canonical_concept`, `canonical_property`, `mapping_type`, `confidence`. Optional: `notes`.

Column semantics:

- `source_system` — kebab-case, ideally matching an id in `00_scope/source-systems.yaml` (e.g. `pos`, `commerce`, `erp`, `salesforce`).
- `source_entity` — the table, collection, or endpoint (e.g. `transactions`, `orders`, `customers`).
- `source_field` — the column, attribute, or JSON path.
- `canonical_concept` — the PascalCase concept name from `candidate-concepts.yaml`. May be left empty when the mapping is ambiguous, but `mapping_type` must then be `ambiguous` or `unmapped` and `notes` must explain.
- `canonical_property` — the property on the canonical concept. Use `id` for the concept's primary identifier.
- `mapping_type` — one of: `direct` (1:1), `transform` (needs a conversion), `foreign_key` (points at another concept), `derived` (computed from multiple fields), `ambiguous` (not yet resolved), `unmapped` (no canonical equivalent exists).
- `confidence` — `high` / `medium` / `low`. Low confidence entries must have `notes` explaining the uncertainty.
- `notes` — anything important: transforms, caveats, discrepancies, open questions for the next stakeholder conversation.

## Step-by-step

1. **Inventory the source systems first.** Before mapping, list the systems and their major entities. Cross-check against `00_scope/source-systems.yaml` — add anything missing as an open question.
2. **For each source entity, walk its fields.** For every field:
   - Is this the entity's primary key? → map to `<Concept>.id`, `mapping_type: direct`, `confidence: high`.
   - Does the field name match a concept property? → direct mapping.
   - Does the field name suggest a relationship (ends in `_id`, `_ref`, `_fk`)? → `mapping_type: foreign_key`, `canonical_property: id` on the referenced concept.
   - Does the field need conversion (unit, timezone, enum decode)? → `mapping_type: transform`, describe the transform in `notes`.
   - No obvious canonical? → `mapping_type: ambiguous` or `unmapped`, `confidence: low`, flag in `notes`.
3. **Pay attention to overloaded names.** `order` in ERP (purchase order) and `order` in commerce (customer order) are different concepts. Don't auto-match on name alone; check the stage-2 synonym conflicts.
4. **Flag authority conflicts.** If two systems both claim to be the source-of-truth for the same canonical property (e.g. customer email from Salesforce vs commerce), map both rows and add a note — authority resolution goes in `03_mappings/authority-notes.md`, not here.
5. **Low-confidence entries get `notes`.** A low-confidence row without an explanation is useless to the next reviewer. If you're not sure, say why.

## Quality checks

- [ ] Every row has `source_system`, `source_entity`, `source_field`, `mapping_type`, `confidence`
- [ ] Every `canonical_concept` (where present) matches a name in `candidate-concepts.yaml`
- [ ] Every `confidence: low` row has a `notes` entry explaining the uncertainty
- [ ] No duplicate `(source_system, source_entity, source_field)` triples
- [ ] `mapping_type: ambiguous` or `unmapped` rows have empty `canonical_concept` and explanatory `notes`
- [ ] Primary-key rows use `canonical_property: id`
- [ ] Field-name-only matches have been sanity-checked against field semantics, not just names

## Handoff to gnosis

Save your LLM output under `clients/<name>/transcripts/_drafts/` (date-stamped, e.g. `2026-05-11-mappings-extraction.csv`) and hand it to gnosis:

```bash
gnosis ingest mappings \
  --from clients/meshco/transcripts/_drafts/2026-05-11-mappings-extraction.csv \
  --client meshco \
  --session 2026-05-11-week4-mappings \
  --interviewer alfred
```

What gnosis enforces when you run this:

**Hard schema (refused if violated — nothing is written):**

- Header contains `source_system`, `source_entity`, `source_field`, `canonical_concept`, `canonical_property`, `mapping_type`, `confidence`; only `notes` allowed as an extra
- Every row has non-empty `source_system`, `source_entity`, `source_field`
- `mapping_type` is one of `direct`, `transform`, `foreign_key`, `derived`, `ambiguous`, `unmapped`
- `confidence` is one of `high`, `medium`, `low`
- No duplicate `(source_system, source_entity, source_field)` triples within a single ingest

**Soft lint (reported to `ontology/ingest-warnings.md`, non-blocking):**

- `unknown_canonical_concept` — `canonical_concept` is set but doesn't match any concept in `02_concepts/candidate-concepts.yaml`. Catches LLM hallucinations and drift from the agreed vocabulary.
- `low_confidence_without_notes` — `confidence: low` with empty `notes`. Low-confidence mappings need an explanation or they're useless to the next reviewer.
- `ambiguous_without_notes` — `mapping_type: ambiguous` or `unmapped` with empty `notes`. An ambiguity without an explanation is an unclosed loop.

**Merge behaviour (gentle, like glossary):** mappings are keyed by the `(source_system, source_entity, source_field)` triple. New rows are appended. Existing rows are **not clobbered** — the `notes` field is unioned (new lines appended if different) and everything else stays as curated. If you want to revise an existing mapping, edit the CSV by hand. Rationale: stage-3 mappings are validated against real data samples; LLM re-extractions can introduce regressions.

Per-row provenance sits in the `notes` column when important (e.g. "2026-05-11: confidence lowered after schema review with Bob"). No sidecar provenance file.

## Examples

### Input (DDL excerpt)

```sql
CREATE TABLE pos.transactions (
  txn_id         VARCHAR(64) PRIMARY KEY,
  customer_ref   VARCHAR(64) NOT NULL,
  amount_cents   INTEGER NOT NULL,
  card_last4     VARCHAR(4),
  captured_at    TIMESTAMP
);
```

### Output

```csv
source_system,source_entity,source_field,canonical_concept,canonical_property,mapping_type,confidence,notes
pos,transactions,txn_id,Transaction,id,direct,high,Primary key in POS
pos,transactions,customer_ref,Customer,id,foreign_key,high,FK into POS customers table
pos,transactions,amount_cents,Transaction,amount,transform,high,"Minor units — divide by 100 for canonical Money"
pos,transactions,card_last4,PaymentMethod,last4,direct,medium,"Not on all rows (cash transactions are NULL) — may need separate PaymentMethod resolution"
pos,transactions,captured_at,Transaction,captured_at,direct,high,UTC
```

## Anti-patterns

- **Name-only matching.** `customer_id` in one system and `customer_id` in another may mean different things (Salesforce account vs POS customer). Check semantics.
- **Inventing canonical concepts.** If a source field has no canonical equivalent, mark it `unmapped` with a note — don't invent a concept. The concepts skill's job is inventing concepts.
- **Low-confidence without notes.** This is the single most common extraction failure mode. A row saying `confidence: low, notes: ""` tells the next reviewer nothing.
- **Mapping a field to a concept you haven't confirmed.** If `candidate-concepts.yaml` doesn't have `Shipment` yet, don't map to it — add an open question instead, and pick it up after the next concepts ingest.
- **Conflating entities.** `pos.transactions` and `commerce.orders` may both map to `Order`, but they're different source entities. Don't collapse them into one row.
- **Mapping transforms without documenting them.** `amount_cents → amount` is a transform (divide by 100) — say so in `notes`. An unqualified `transform` is a ticking bomb.
