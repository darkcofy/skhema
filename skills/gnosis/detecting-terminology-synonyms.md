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

Markdown with the following structure, appended to `01_language/synonym-conflicts.md`:

```markdown
## Synonym: Customer / Account Holder / Buyer

- **Terms used:** customer, account holder, buyer
- **Used by:**
  - "customer" — Alice Chen (Payments), Bob Murphy (Ops)
  - "account holder" — Carol Singh (Compliance)
  - "buyer" — Dan Lee (Product)
- **Evidence of same meaning:**
  - Alice: "Every transaction has a customer and a merchant"
  - Carol: "The account holder is who the card is registered to"
  - Dan: "Buyers pay, sellers receive"
- **Type:** synonym (candidate) — all three likely refer to the same entity but domain framing differs
- **Severity:** high — load-bearing concept, must be resolved before stage 2
- **Proposed canonical:** Customer (highest usage count, clearest definition)
- **Open questions:**
  - Is an account holder always the same person as the customer paying? (Corporate cards.)
  - Does the compliance definition ("registered to") imply a legal entity?

## Homonym: Authorisation

- **Terms used:** authorisation
- **Used by:**
  - Alice Chen uses it to mean "the first step of a transaction"
  - Carol Singh uses it to mean "a customer granting us permission to charge them"
- **Evidence of different meaning:**
  - Alice: "Auth then capture"
  - Carol: "They have to give us authorisation before we can debit"
- **Type:** homonym — same word, different concepts
- **Severity:** high — will create broken links if used ambiguously in the concept model
- **Proposed resolution:** `AuthorisationEvent` (Alice's) vs `PaymentAuthorisation` (Carol's), or rename one
```

Each conflict is an H2 section. Fields: Terms used, Used by, Evidence, Type (synonym / homonym / near-synonym), Severity (high/medium/low), Proposed canonical (if obvious), Open questions.

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
- [ ] Speakers are attributed by name + role
- [ ] No conflicts that lack textual evidence (no speculation)
- [ ] Proposed canonical (if present) is one of the terms actually used, not an invented one

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

```markdown
## Synonym: Customer / Account Holder / Buyer

- **Terms used:** customer, account holder, buyer
- **Used by:**
  - "customer" — Alice Chen (Payments Lead)
  - "account holder" — Carol Singh (Compliance)
  - "buyer" — Dan Lee (Product)
- **Evidence of same meaning:**
  - Alice (later): "When we say customer we mean the account holder really"
- **Evidence of possible distinction:**
  - Carol: "KYC checks focus on the account holder — we verify their ID" — suggests account holder is the *legal* person, which may differ from the paying customer in B2B/corporate-card scenarios
  - Dan: "buyer" comes from product framing and may include non-paying browsers
- **Type:** near-synonym (likely the same concept with domain-specific framing)
- **Severity:** high — core to most payment concepts; must resolve before stage 2
- **Proposed canonical:** Customer (payments + ops use it, Alice's aside confirms overlap)
- **Open questions:**
  - Corporate cards: is the paying entity different from the account holder?
  - Does "buyer" (Dan) include users who browse but never transact?
```

## Anti-patterns

- **Synthetic synonyms.** Don't group terms as synonyms based on Wikipedia or dictionary similarity — use the client's usage.
- **Ignoring intensity.** Not all synonym candidates are equal. A word one person used once versus a word that appears 30 times are weighted very differently.
- **Proposing resolution as if decided.** Output is *evidence for a workshop*, not a decree. Avoid "The canonical term is X." in favour of "Proposed canonical: X (highest usage count, clearest definition)".
- **Hiding conflicts because they look minor.** A "minor" terminology difference in a model that goes into production becomes a production incident three months later.
- **Omitting the open questions section.** If there's ambiguity (and there almost always is), surface it explicitly.
