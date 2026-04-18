# Source of Truth / Authority Notes

## Purpose
For each canonical concept, record which system is the authoritative source and why. When systems disagree, the authority wins.

## Session guide
For each concept that appears in multiple systems:

1. Ask: "If these two systems disagree about [concept], which one is correct?"
2. Ask: "Why? Is it because of update timing, data quality, or ownership?"
3. Ask: "Are there exceptions where the non-authoritative system is actually more current?"

## Capture

For each concept:
- Canonical concept name
- Authoritative system
- Why it's authoritative
- Known exceptions or caveats

## Example

> ## Transaction
> - **Authority:** Payment Gateway
> - **Why:** Gateway is the system of record for payment state — it processes the transaction
> - **Exception:** For settlement status, the Billing Ledger is authoritative (gateway doesn't track post-settlement)

## Completion criteria
- [ ] Every concept with multiple sources has a designated authority
- [ ] Reasoning documented for each designation
- [ ] Exceptions and caveats captured
- [ ] Authority designations validated by system owners
