# Concept Definitions

## Purpose
Provide detailed definitions for each candidate concept. These go beyond the one-liner in candidate-concepts.yaml to capture nuance, edge cases, and the "why" behind each concept.

## Session guide
For each candidate concept, run a 15-minute deep-dive with the relevant domain expert:

1. Ask: "In your own words, what is a [concept]?"
2. Ask: "What makes one [concept] different from another?"
3. Ask: "What can happen to a [concept] over its lifetime?"
4. Ask: "Can you give me an example of a tricky or edge-case [concept]?"

## Capture

For each concept, record:
- Full definition (2-3 sentences)
- Key distinguishing attributes
- Common confusions or edge cases
- Related concepts

## Example

> ## Transaction
> A single payment attempt initiated by a consumer against a merchant account. A transaction has a lifecycle (initiated -> authorized -> captured -> settled or declined) and is the atomic unit of payment processing. Partial captures are modeled as separate transactions linked to the original authorization.
>
> **Key attributes:** amount, currency, status, timestamp, payment method
> **Common confusion:** A "transaction" in the billing system refers to a ledger entry, not a payment attempt. We use "Transaction" exclusively for payment attempts.
> **Related:** PaymentMethod, Merchant, SettlementBatch

## Completion criteria
- [ ] Every candidate concept has a detailed definition
- [ ] Definitions reviewed by at least one domain expert
- [ ] Edge cases and common confusions documented
- [ ] Key attributes listed for each concept
