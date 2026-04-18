# System Overlaps

## Purpose
Document where multiple source systems represent the same real-world concept differently. These overlaps are where most data quality and integration problems hide.

## Session guide
With the source-to-canonical mapping in progress, look for overlaps:

1. Ask: "Which concept appears in more than one system?"
2. For each overlap: "How do these systems define it differently?"
3. Ask: "When they disagree, which system is right?"
4. Ask: "Are there known data quality issues at these overlap points?"

## Capture

For each overlap:
- Canonical concept involved
- Systems that represent it
- Key differences (schema, semantics, granularity)
- Known data quality issues
- Impact on the canonical model

## Example

> ## Transaction — Payment Gateway vs Billing Ledger
> - **Payment Gateway:** `transactions` table — one row per payment attempt, includes declined
> - **Billing Ledger:** `ledger_entries` table — one row per financial event, no declined transactions
> - **Key difference:** Gateway tracks payment state; ledger tracks money movement. Different granularity.
> - **Data quality:** Gateway has 2% orphan records with no matching ledger entry (timeout cases)
> - **Impact:** Canonical Transaction must include a `source` field to track provenance

## Completion criteria
- [ ] All multi-system concepts identified
- [ ] Differences documented for each overlap
- [ ] Source of truth designated for each concept
- [ ] Data quality issues noted where known
