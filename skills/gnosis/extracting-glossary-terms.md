---
name: Extracting glossary terms from transcripts and documents
description: Reads transcripts, docs, wiki pages, or onboarding materials and extracts candidate glossary terms with definitions and sources. Produces rows for gnosis `01_language/glossary-seeds.csv`. Use at gnosis stage 1 (language capture) before concept modelling, or whenever a previously-unknown term surfaces in a session.
---

## When to use this skill

- Early in an engagement when the team is still learning the client's language.
- After any stakeholder interview where new terms came up.
- When onboarding a new team member to a domain and you want a curated glossary.

The glossary is about **vocabulary** — terms the business uses. It is *not* the ontology (that comes at stage 2). A glossary term can be an informal shorthand, an acronym, a jargon phrase, or a noun — anything that a newcomer would need defined.

## Inputs

1. **Source material** — transcripts, onboarding docs, Confluence pages, Slack export, email threads, RFC PDFs.
2. **(Optional)** Existing `glossary-seeds.csv` — avoid duplicates.

## Output format

CSV with the following columns (matching `01_language/glossary-seeds.csv`):

```csv
term,definition,source,domain,aliases,notes
Transaction,"A single transfer of funds initiated by a customer, subject to authorisation and capture","Alice Chen, 2026-04-12 interview",payments,"txn, tx",
Chargeback,"A forced reversal initiated by the customer's bank when they dispute a transaction","Bob Murphy, 2026-04-13 interview",payments,,Different from refund
EOD,"End of day — the daily cut-off when transactions are captured and settled","Alice Chen, 2026-04-12 interview",payments,"end-of-day",
```

Required columns: `term`, `definition`, `source`. Optional: `domain`, `aliases` (comma-separated), `notes`.

## Step-by-step

1. **Read source material with a jargon-sensitive eye.** Flag anything that:
   - Is an acronym or initialism (EOD, PII, KYC, AML)
   - Has quotes around it when first introduced ("a so-called 'reversal'")
   - Is defined inline ("X, which is Y")
   - Gets corrected by a stakeholder ("we don't call it X, we call it Y")
   - Appears in a tone that suggests insider knowledge
2. **For each flagged phrase, write a row.**
   - `term` is the canonical phrasing (pick the one the most senior or most informed stakeholder uses).
   - `definition` is ONE sentence, in plain English, staying close to how the stakeholder described it. Do not go longer unless you genuinely have to.
   - `source` is `<speaker name>, <date> <context>` (e.g. "Alice Chen, 2026-04-12 interview").
   - `domain` is the domain from `00_scope/engagement.md` this term belongs to. Leave blank if cross-cutting.
   - `aliases` captures other phrasings used for the same term.
   - `notes` captures anything important that didn't fit the definition (e.g. "different from refund").
3. **Do not define terms you don't have evidence for.** If the transcript mentions "the Kovacs rule" once and no one explains it, add it with `definition` empty and `notes: Needs clarification from Alice` — don't invent a definition.
4. **Spot-check acronyms.** For every acronym, make sure the expansion is captured — either in `definition` or `aliases`.

## Quality checks

- [ ] Every row has `term`, `definition`, `source` populated (or `definition` blank + `notes` flag)
- [ ] Definitions are one sentence, stakeholder-voiced, not textbook-generic
- [ ] Acronyms include the full expansion
- [ ] No duplicates — the same term doesn't appear twice with different `source` values (merge into one row with multi-line `source`)
- [ ] Terms are singular (Transaction, not Transactions) unless the plural is semantically distinct
- [ ] CSV is valid (quoted values containing commas, no stray newlines inside unquoted fields)

## Examples

### Input

> "We track every transaction from auth to capture. EOD is when we close the batch — typically midnight UTC. If a card comes back declined we call that a soft decline, and if the acquirer rejects, that's a hard decline. Chargebacks are different, those come in from the bank side."

### Output

```csv
term,definition,source,domain,aliases,notes
Transaction,"A single transfer of funds tracked from authorisation through to capture","2026-04-12 Alice Chen interview",payments,"txn",
Authorisation,"The first step of a transaction where the card network confirms funds are available","2026-04-12 Alice Chen interview",payments,"auth",
Capture,"The point at which authorised funds are actually pulled from the customer's account","2026-04-12 Alice Chen interview",payments,,
EOD,"End of day — the daily batch close, typically midnight UTC","2026-04-12 Alice Chen interview",payments,"end-of-day",
Soft decline,"A card-side rejection of a transaction","2026-04-12 Alice Chen interview",payments,,
Hard decline,"An acquirer-side rejection of a transaction","2026-04-12 Alice Chen interview",payments,,
Chargeback,"A bank-initiated reversal of a transaction — distinct from a refund","2026-04-12 Alice Chen interview",payments,,Different from refund
```

## Anti-patterns

- **Textbook definitions.** "Authorisation: the process of verifying that a payer has sufficient credit available" is sanitised; the stakeholder's "the first step where the card network confirms funds" is the keeper.
- **Combining multiple terms into one row.** `soft_decline_or_hard_decline` is not a term; they're two separate terms.
- **Omitting sources.** A glossary without provenance is a wiki, not a discovery artefact. Every row needs `source`.
- **Defining terms for the client's domain from your own background.** If you know "chargeback" from prior payments work, great — but the definition you write must reflect *this* client's language, not generic knowledge.
- **Treating system names as glossary terms.** "Stripe", "Kafka", "RisingWave" are tools, not vocabulary. They belong in `00_scope/source-systems.yaml`.
