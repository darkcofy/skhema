---
name: Detecting terminology synonyms and conflicts
description: Analyses a glossary and transcripts to identify synonyms, near-synonyms, and conflicting definitions of the same term across stakeholders. Produces entries for gnosis `01_language/synonym-conflicts.md`. Use after glossary extraction when you need to surface ambiguity before concept modelling.
---

## When to use this skill

- After `glossary-seeds.csv` has 10+ terms and you need to see where the business uses multiple words for the same thing (synonyms) or the same word for multiple things (homonyms).
- Before stage 2 concept modelling — unresolved terminology conflicts lead directly to corrupt concept models.
- Whenever two stakeholders in different meetings give you different definitions of the same term.

This skill does not *resolve* conflicts — resolution is a workshop decision between stakeholders. This skill *surfaces* them so the facilitator can bring them up.

## Inputs

1. **`01_language/glossary-seeds.csv`** — the glossary to analyse.
2. **Transcripts** — source material the glossary was drawn from, so you can check usage in context.
3. **(Optional)** An existing `synonym-conflicts.md` — for extending without duplicating.

## Output format

Structured YAML — one list entry per conflict. gnosis will validate the YAML, merge it into `01_language/synonym-conflicts.yaml` (the canonical source of truth), and render a human-readable `01_language/synonym-conflicts.md` view from the merged state. **Do not output free-form markdown** — the markdown file is now auto-generated from the YAML.

```yaml
- title: Customer / Account Holder / Buyer
  type: near-synonym          # synonym | near-synonym | homonym
  severity: high               # high | medium | low
  terms:
    - customer
    - account holder
    - buyer
  used_by:
    - term: customer
      speakers:
        - Alice Chen
        - Bob Murphy
    - term: account holder
      speakers:
        - Carol Singh
    - term: buyer
      speakers:
        - Dan Lee
  evidence:
    - quote: "Every transaction has a customer and a merchant"
      source: Alice Chen
      date: 2026-04-12
      polarity: same            # same | different
    - quote: "The account holder is who the card is registered to"
      source: Carol Singh
      date: 2026-04-13
      polarity: same
    - quote: "Corporate cards — the paying entity may differ from the account holder"
      source: Carol Singh
      date: 2026-04-13
      polarity: different
  proposed_canonical: customer
  rationale: Highest usage count across domains; clearest definition.
  open_questions:
    - Is an account holder always the same person as the paying customer? (Corporate cards.)
    - Does Carol's "registered to" imply a legal entity, not a person?

- title: Authorisation (payment flow vs consent)
  type: homonym
  severity: high
  terms:
    - authorisation
  used_by:
    - term: authorisation
      speakers:
        - Alice Chen
        - Carol Singh
  evidence:
    - quote: "Auth then capture"
      source: Alice Chen
      date: 2026-04-12
      polarity: different
    - quote: "They have to give us authorisation before we can debit"
      source: Carol Singh
      date: 2026-04-13
      polarity: different
  rationale: Alice means the card-network step; Carol means customer consent. Two concepts sharing one word.
  open_questions:
    - Which term gets renamed — the payment-flow one, the consent one, or both?
```

Required fields: `title`, `type`, `severity`, `terms` (≥1), `evidence` (at least one quote). Recommended: `used_by`, `proposed_canonical`, `rationale`, `open_questions`.

Each `evidence` entry must include `polarity` — `same` (evidence that the terms refer to the same thing) or `different` (evidence of distinct meanings or a homonym). This lets the markdown renderer group quotes under the right heading.

## Step-by-step

1. **Build a usage index.** For every term in the glossary, list which stakeholders used it (from transcripts).
2. **Find candidate synonyms.** Scan for terms where:
   - Definitions are highly similar in meaning.
   - The same stakeholder uses multiple terms interchangeably.
   - A stakeholder explicitly corrects another ("we don't call it X, we call it Y").
   - Two terms co-occur with the same related entities (e.g. both "customer" and "buyer" relate to "transaction" the same way).
3. **Find candidate homonyms.** Scan for terms where:
   - The same word appears with materially different definitions across stakeholders.
   - One stakeholder uses the word inconsistently (contextually shifts meaning).
4. **For each finding, write a conflict entry.** Include verbatim evidence quotes — don't paraphrase.
5. **Rate severity.**
   - `high` — concept is referenced by other concepts, or appears in scope; will break downstream modelling
   - `medium` — local ambiguity, affects a handful of artifacts
   - `low` — minor style variation, unlikely to cause issues
6. **Propose canonical (if clear).** When usage clearly favours one term (most senior speaker, highest frequency, tightest definition), name it. If not clear, leave it for the workshop.
7. **Do not attempt resolution.** Your output feeds a stakeholder discussion. The workshop decides the canonical term.

## Quality checks

- [ ] Every conflict entry has at least 2 verbatim evidence quotes from different speakers
- [ ] Severity is justified by the evidence (not "high" for a minor stylistic variation)
- [ ] Type is one of: synonym, near-synonym, homonym
- [ ] Speakers are attributed by name (matching `00_scope/stakeholders.yaml`)
- [ ] No conflicts that lack textual evidence (no speculation)
- [ ] Proposed canonical (if present) is one of the terms actually used, not an invented one

## Handoff to gnosis

Save your LLM output under `clients/<name>/transcripts/_drafts/` (date-stamped, e.g. `2026-05-09-synonyms-extraction.yaml`) and hand it to gnosis:

```bash
gnosis ingest synonyms \
  --from clients/meshco/transcripts/_drafts/2026-05-09-synonyms-extraction.yaml \
  --client meshco \
  --session 2026-05-09-week3-synonyms \
  --interviewer alfred
```

What gnosis enforces when you run this:

**Hard schema (refused if violated — nothing is written):**

- Each entry has `title`, `type` ∈ {synonym, near-synonym, homonym}, `severity` ∈ {high, medium, low}, and non-empty `terms`
- Each `evidence` quote has `quote`, `source`, ISO `date`, and `polarity` ∈ {same, different}
- No duplicate `title` within a single ingest

**Soft lint (reported to `ontology/ingest-warnings.md`, non-blocking):**

- `insufficient_evidence` — fewer than 2 distinct sources in the evidence list. Cross-speaker corroboration is the point of this artefact; single-speaker conflicts are weak signal.
- `unknown_speaker_in_evidence` — an evidence source that looks like a person name but doesn't match any stakeholder in `00_scope/stakeholders.yaml`. Team-like sources (e.g. "Sales Ops", "Platform Team") are intentionally skipped.
- `proposed_canonical_not_in_terms` — if you set `proposed_canonical`, it must be one of the listed `terms`. Otherwise you've invented a canonical that isn't in use, which defeats the purpose.

**Writeout behaviour:**

- Canonical source of truth: `01_language/synonym-conflicts.yaml` (merged across ingests)
- Rendered view: `01_language/synonym-conflicts.md` — always regenerated from the YAML, never hand-edit post-ingest
- First-ingest grace: if a hand-authored `synonym-conflicts.md` exists without a `.yaml` peer, it is renamed to `synonym-conflicts.md.pre-ingest` (idempotent, one-time). Your prior content is preserved for reference — migrate it into the YAML by re-running the LLM extraction against it or by hand.

**Merge behaviour:** conflicts are keyed by `title` (case-insensitive). Re-ingesting an existing title unions the `terms`, `evidence` (dedup by quote+source), `used_by` (merging speaker lists within each term), and `open_questions`. Scalar fields (`type`, `severity`, `proposed_canonical`, `rationale`) are overwritten from the new entry. Every merged entry carries a `last_ingested` block for provenance.

## Examples

### Input (glossary excerpt)

```csv
term,definition,source
Customer,"The person paying","Alice Chen"
Account Holder,"The person registered against the payment method","Carol Singh"
Buyer,"Party on the purchase side of a transaction","Dan Lee"
```

### Input (transcripts)

```
Alice: "Every transaction has a customer and a merchant."
Carol: "KYC checks focus on the account holder — we verify their ID."
Dan: "Our product tracks buyers and sellers."
Alice (later): "When we say customer we mean the account holder really."
```

### Output

```yaml
- title: Customer / Account Holder / Buyer
  type: near-synonym
  severity: high
  terms:
    - customer
    - account holder
    - buyer
  used_by:
    - term: customer
      speakers: [Alice Chen]
    - term: account holder
      speakers: [Carol Singh]
    - term: buyer
      speakers: [Dan Lee]
  evidence:
    - quote: "When we say customer we mean the account holder really"
      source: Alice Chen
      date: 2026-04-14
      polarity: same
    - quote: "KYC checks focus on the account holder — we verify their ID"
      source: Carol Singh
      date: 2026-04-13
      polarity: different
    - quote: "Our product tracks buyers and sellers"
      source: Dan Lee
      date: 2026-04-15
      polarity: different
  proposed_canonical: customer
  rationale: Payments + ops use it; Alice's aside confirms overlap with account holder.
  open_questions:
    - Corporate cards — is the paying entity different from the account holder?
    - Does "buyer" (Dan) include users who browse but never transact?
```

When gnosis renders this to `synonym-conflicts.md`, the output looks like:

```markdown
## Near-synonym: Customer / Account Holder / Buyer

- **Terms used:** customer, account holder, buyer
- **Used by:**
  - "customer" — Alice Chen
  - "account holder" — Carol Singh
  - "buyer" — Dan Lee
- **Evidence of same meaning:**
  - Alice Chen (2026-04-14): "When we say customer we mean the account holder really"
- **Evidence of different meaning:**
  - Carol Singh (2026-04-13): "KYC checks focus on the account holder — we verify their ID"
  - Dan Lee (2026-04-15): "Our product tracks buyers and sellers"
- **Type:** near-synonym
- **Severity:** high
- **Proposed canonical:** customer — Payments + ops use it; Alice's aside confirms overlap with account holder.
- **Open questions:**
  - Corporate cards — is the paying entity different from the account holder?
  - Does "buyer" (Dan) include users who browse but never transact?
```

## Anti-patterns

- **Synthetic synonyms.** Don't group terms as synonyms based on Wikipedia or dictionary similarity — use the client's usage.
- **Ignoring intensity.** Not all synonym candidates are equal. A word one person used once versus a word that appears 30 times are weighted very differently.
- **Proposing resolution as if decided.** Output is *evidence for a workshop*, not a decree. Avoid "The canonical term is X." in favour of "Proposed canonical: X (highest usage count, clearest definition)".
- **Hiding conflicts because they look minor.** A "minor" terminology difference in a model that goes into production becomes a production incident three months later.
- **Omitting the open questions section.** If there's ambiguity (and there almost always is), surface it explicitly.
