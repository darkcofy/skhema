---
name: Extracting domain concepts from interview transcripts
description: Reads stakeholder interview transcripts, meeting notes, or process documentation and extracts candidate canonical concepts with definitions, relationships, and source citations. Use when starting gnosis stage 2 (concept modelling) or when unstructured interview material needs structuring into candidate-concepts.yaml. Output matches the gnosis `02_concepts/candidate-concepts.yaml` schema.
---

## When to use this skill

- You have transcripts from stakeholder interviews, kick-off meetings, SME working sessions, or recorded Slack threads.
- You are at or past gnosis stage 2 (concept modelling) and need to populate `candidate-concepts.yaml`.
- You want a starting list of *canonical* concepts the business actually talks about, with citations back to who said what.

Do **not** use this skill to propose concepts that aren't present in the source material. Your job is extraction, not invention.

## Inputs

1. **Transcripts or source documents** (markdown, plain text, SRT, VTT, Confluence exports). Multiple files is fine.
2. **Domain name** — one-line description of the business domain (e.g. "payment processing for a cross-border retailer").
3. **(Optional)** Existing `candidate-concepts.yaml` — so you can extend it without duplicating.
4. **(Optional)** `00_scope/stakeholders.yaml` — so you can map source quotes to people correctly.

## Output format

YAML matching the gnosis schema, appended to `02_concepts/candidate-concepts.yaml`:

```yaml
- name: Transaction
  domain: payments
  description: A single transfer of funds initiated by a customer against a payment method, subject to authorisation and capture.
  related_to:
    - PaymentMethod
    - Merchant
    - Settlement
  source_quotes:
    - quote: "Every transaction starts with an auth, then we capture later at EOD"
      source: Alice Chen (Payments Lead)
      date: 2026-04-12
    - quote: "A reversed transaction still keeps its original ID"
      source: Bob Murphy (Ops)
      date: 2026-04-13
  confidence: high          # high | medium | low
  open_questions:
    - Does a failed authorisation still count as a transaction?
```

Required fields: `name`, `domain`, `description`, `source_quotes` (at least one). Optional: `related_to`, `confidence`, `open_questions`.

## Step-by-step

1. **Skim the transcripts first.** Note the 5–10 terms that keep coming up. Don't write anything yet.
2. **Extract candidate concepts.** For each term that appears as a *thing the business reasons about* (not just a verb or a system name), create an entry:
   - Take the exact phrasing the stakeholder used as the `name`. Capitalise it (e.g. "Transaction", not "transaction").
   - Write a one-sentence `description` in the stakeholder's own voice — do not paraphrase into generic software-speak.
   - Capture **at least one** `source_quote` verbatim with attribution.
3. **Cluster relationships.** If two concepts frequently co-occur in the same sentence or stakeholders describe one as "part of" another, add them to `related_to`. Don't speculate — only add relationships that are visible in the source.
4. **Mark confidence.**
   - `high` — multiple stakeholders use the term consistently with the same meaning
   - `medium` — single stakeholder uses it, or usage is consistent but evidence is thin
   - `low` — meaning shifts between speakers, or you inferred boundaries from incomplete evidence
5. **Flag open questions.** When stakeholders disagree, or when you can tell the concept is load-bearing but its boundaries are fuzzy, add entries to `open_questions`. These feed synonym-conflicts.md and future interview agendas.
6. **Deduplicate.** If two candidate concepts look like the same thing with different names (e.g. "Customer" and "Account Holder"), keep them separate for now and flag it — the terminology-synonyms skill resolves these later, not this skill.

## Quality checks

- [ ] Every concept has at least one `source_quote` with attribution (name + date)
- [ ] No concept was invented — every `name` or `description` phrase is traceable to a transcript line
- [ ] Duplicates (case-insensitive, whitespace-insensitive) are absent
- [ ] `related_to` references use names that also exist elsewhere in the file (no dangling relationships)
- [ ] `confidence: low` entries have at least one `open_questions` item explaining the uncertainty
- [ ] Concept names are singular nouns (`Transaction`, not `Transactions` or `To transact`)
- [ ] Domain field matches one of the domains in `00_scope/engagement.md`

## Handoff to gnosis

Save your LLM output under `clients/<name>/transcripts/_drafts/` (date-stamped, e.g. `2026-05-06-concepts-extraction.yaml`) and then hand it to gnosis for validation and merge:

```bash
gnosis ingest concepts \
  --from clients/meshco/transcripts/_drafts/2026-05-06-concepts-extraction.yaml \
  --client meshco \
  --session 2026-05-06-week3-extraction \
  --interviewer alfred
```

What gnosis enforces when you run this:

**Hard schema (refused if violated — nothing is written):**

- Each entry has `name` (PascalCase), `domain`, `description` (≥ 20 chars), and at least one `source_quote`
- Each `source_quote` has non-empty `quote`, `source`, and an ISO `date`
- `confidence`, if set, is one of `high` / `medium` / `low`

**Soft lint (reported to `ontology/ingest-warnings.md`, non-blocking):**

- `unknown_speaker` — a `source_quote.source` that doesn't resolve to a stakeholder in `00_scope/stakeholders.yaml`
- `dangling_related_to` — a `related_to` entry that isn't an existing concept or another concept in the same ingest
- `low_confidence_missing_questions` — `confidence: low` without at least one `open_questions` entry

Fix warnings by editing the workspace (add the missing stakeholder, rename the dangling reference, add an open question) and re-running the ingest, or by correcting the source YAML and re-ingesting. `gnosis status` will show the warning count after each run.

Merges are **additive by name (case-insensitive)**: `source_quotes`, `related_to`, and `open_questions` are unioned across ingests; `description` / `domain` / `confidence` are overwritten from the new entry. Every merged entry carries a `last_ingested` block recording the session, interviewer, and timestamp — so later you can trace who sourced which concept in which session.

## Examples

### Input (transcript excerpt)

```
Alice Chen (Payments Lead, 2026-04-12):
"A transaction is really a flow — the customer hits pay, we send an
authorisation to the card network, and assuming that passes we capture
the funds at end of day. Each transaction sits against one payment
method, and a merchant is the counterparty."

Bob Murphy (Ops, 2026-04-13):
"When customers dispute a transaction, we call that a chargeback. It's
different from a refund — a refund is us choosing to reverse, a
chargeback is the customer's bank forcing it."
```

### Output

```yaml
- name: Transaction
  domain: payments
  description: A flow initiated by a customer paying, consisting of an authorisation step followed by end-of-day capture, tied to one payment method and one merchant.
  related_to:
    - PaymentMethod
    - Merchant
    - Chargeback
    - Refund
  source_quotes:
    - quote: "A transaction is really a flow — the customer hits pay, we send an authorisation to the card network, and assuming that passes we capture the funds at end of day"
      source: Alice Chen (Payments Lead)
      date: 2026-04-12
  confidence: high

- name: Chargeback
  domain: payments
  description: A forced reversal initiated by the customer's bank when they dispute a transaction; distinct from a refund, which is merchant-initiated.
  related_to:
    - Transaction
    - Refund
  source_quotes:
    - quote: "A chargeback is the customer's bank forcing it"
      source: Bob Murphy (Ops)
      date: 2026-04-13
  confidence: high
  open_questions:
    - Does a chargeback close the original transaction, or create a new linked record?
```

## Anti-patterns

- **Inventing concepts that aren't in the transcripts.** If the transcript mentions "fraud case" but not "fraud investigator", you do not create a "FraudInvestigator" concept just because it feels logical.
- **Paraphrasing away the stakeholder's voice.** The description for "Transaction" should carry the flavour of how Alice described it, not a sanitised textbook definition.
- **Merging concepts based on vibes.** "Customer" and "Account Holder" may well be synonyms, but deciding that is the synonym-detection skill's job — here, keep them separate and flag.
- **Dropping source quotes to save space.** Every concept without a source quote is unverifiable.
- **Creating relationships that aren't textually supported.** `Transaction related_to Merchant` is fine if a stakeholder said so; `Transaction related_to FraudCase` just because it seems plausible is not.
- **Extracting system names as concepts.** "Stripe" is a vendor, "Debezium" is a tool — neither is a domain concept. "Payment method" and "Transaction" are.
