# Edge Cases and Exceptions

## Purpose
Document the weird, rare, and troublesome scenarios that don't fit neatly into the happy path. These are the cases that break assumptions and reveal gaps in the model.

## Session guide
After documenting lifecycles and business rules:

1. Ask: "What's the weirdest case you've seen with [concept]?"
2. Ask: "When does the normal flow break down?"
3. Ask: "Are there cases where the rules are bent or overridden?"
4. Ask: "What keeps you up at night about this domain?"

## Capture

For each edge case:
- Scenario description
- Which concepts/rules it affects
- How it's currently handled
- Whether the model accounts for it

## Example

> ## Partial refund on a split payment
> - **Scenario:** Consumer paid with two cards (60/40 split). Requests refund of 50% of the total.
> - **Affects:** Transaction, PaymentMethod, Refund
> - **Current handling:** Manual process — ops team splits the refund proportionally across both original transactions
> - **Model impact:** Refund needs a relationship to multiple source Transactions, not just one

## Completion criteria
- [ ] At least 5 edge cases documented
- [ ] Each linked to affected concepts and rules
- [ ] Current handling described
- [ ] Model impact assessed (does current model handle it?)
