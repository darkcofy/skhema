# Business Rules

## Purpose
Capture the invariants, constraints, and rules that govern how concepts behave. These are the "must always be true" and "must never happen" statements.

## Session guide
For each concept with a defined lifecycle:

1. Ask: "What must always be true about a [concept]?"
2. Ask: "What can never happen to a [concept]?"
3. Ask: "Are there timing constraints? (e.g., must happen within X days)"
4. Ask: "Are there amount or quantity limits?"
5. Ask: "What happens when a rule is violated?"

## Capture

For each rule:
- Rule statement (plain English)
- Which concepts it applies to
- What happens on violation
- Source (who told you this / where is it documented)

## Example

> ## Settlement batch closes at midnight UTC
> - **Applies to:** SettlementBatch, Transaction
> - **Rule:** All authorized transactions captured before midnight are included in that day's settlement batch. Transactions captured after midnight roll to the next batch.
> - **On violation:** N/A — enforced by system clock
> - **Source:** Payments architect, confirmed in gateway docs

## Completion criteria
- [ ] Rules captured for each concept with a lifecycle
- [ ] Each rule has a clear violation consequence
- [ ] Timing and threshold constraints documented
- [ ] Rules validated by domain expert
