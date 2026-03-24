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

## Transaction — Payment Gateway vs Billing Ledger vs Legacy ERP
- **Payment Gateway:** `transactions` table — one row per payment attempt, includes declined and voided transactions, tracks full lifecycle from initiation through capture
- **Billing Ledger:** `ledger_entries` table — one row per financial event (debit or credit), no declined transactions, only records that move money
- **Legacy ERP:** `payment_document` table — groups related payments into a single document, includes manual adjustments that have no gateway equivalent
- **Key difference:** Gateway tracks payment state (including failures); ledger tracks money movement (only successes); ERP groups multiple payments into documents. Different granularity at every level.
- **Data quality:** Gateway has ~2% orphan records with no matching ledger entry (timeout cases where capture succeeded at the network but the callback was lost). ERP has ~8% records that cannot be mapped to gateway transactions (manual entries, pre-gateway legacy data).
- **Impact:** Canonical Transaction uses the Payment Gateway as the primary source. Ledger entries are derived records. ERP data requires manual reconciliation during migration.

## Merchant — Merchant Portal vs Billing Ledger vs Legacy ERP
- **Merchant Portal:** `merchants` table — full merchant profile including legal name, DBA, MCC code, integration tier, onboarding status
- **Billing Ledger:** `merchant_accounts` table — financial view only: account balance, fee schedule reference, payout config
- **Legacy ERP:** `vendor_master` table — SAP vendor record with different ID scheme, limited to legal name and tax ID
- **Key difference:** Portal has the richest merchant data and is the onboarding system of record. Ledger only knows the financial relationship. ERP uses a completely different ID scheme and has stale data for ~15% of merchants who changed their legal details after migration.
- **Data quality:** 12 merchants exist in the ledger but not in the portal (created via direct DB insert during an incident). ERP vendor IDs require a translation table maintained by IT Ops; table is ~95% complete.
- **Impact:** Canonical Merchant uses the Merchant Portal as the primary source. The 12 ledger-only merchants must be backfilled into the portal before migration. ERP vendor-to-merchant mapping is a migration prerequisite.

## Chargeback — Fraud Engine vs Billing Ledger
- **Fraud Engine:** `fraud_cases` table — tracks the investigation side: risk scores, analyst notes, evidence, case outcome
- **Billing Ledger:** `chargeback_records` table — tracks the financial side: amounts, reason codes, fee deductions, settlement adjustments
- **Key difference:** Fraud Engine focuses on "is this fraud?" while Billing Ledger focuses on "how much money moved?" A single real-world chargeback appears as a FraudCase in the engine and a chargeback_record in the ledger, but they use different IDs and different status models.
- **Data quality:** ~5% of chargeback_records have no matching fraud_case (chargebacks that came in outside of fraud workflow, e.g., "product not received" disputes). Fraud Engine occasionally has cases that never received the final financial resolution from the ledger due to async processing delays.
- **Impact:** Canonical model keeps Chargeback and FraudCase as separate entities with a cross-reference. Reconciliation between the two systems should be automated as part of the new platform.

## Example

> ## Transaction — Payment Gateway vs Billing Ledger
> - **Payment Gateway:** `transactions` table — one row per payment attempt, includes declined
> - **Billing Ledger:** `ledger_entries` table — one row per financial event, no declined transactions
> - **Key difference:** Gateway tracks payment state; ledger tracks money movement. Different granularity.
> - **Data quality:** Gateway has 2% orphan records with no matching ledger entry (timeout cases)
> - **Impact:** Canonical Transaction must include a `source` field to track provenance

## Completion criteria
- [x] All multi-system concepts identified
- [x] Differences documented for each overlap
- [x] Source of truth designated for each concept
- [x] Data quality issues noted where known
