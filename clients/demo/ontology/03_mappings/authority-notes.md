# Source of Truth / Authority Notes

## Purpose
For each canonical concept, record which system is the authoritative source and why. When systems disagree, the authority wins.

## Session guide
For each concept that appears in multiple systems:

1. Ask: "If these two systems disagree about [concept], which one is correct?"
2. Ask: "Why? Is it because of update timing, data quality, or ownership?"
3. Ask: "Are there exceptions where the non-authoritative system is actually more current?"

## Capture

## Transaction
- **Authority:** Payment Gateway
- **Why:** The gateway is the system that actually processes the payment. It has the most granular and up-to-date transaction state, including declines and voids that never reach the ledger.
- **Exception:** For post-settlement status (e.g., refund applied, chargeback deducted), the Billing Ledger is authoritative because the gateway does not track financial events that occur after capture.

## Merchant
- **Authority:** Merchant Portal
- **Why:** The portal is where merchants are onboarded, where their profile data is maintained, and where integration configuration lives. It is the only system with the full merchant lifecycle.
- **Exception:** For the 12 merchants created directly in the Billing Ledger during an incident, the ledger is the temporary authority until they are backfilled into the portal.

## SettlementBatch
- **Authority:** Billing Ledger
- **Why:** The ledger tracks the actual fund movement and reconciliation with the acquirer. The gateway knows which transactions were batched, but the ledger confirms whether funds actually settled.
- **Exception:** None. The ledger is always authoritative for settlement.

## Chargeback
- **Authority:** Billing Ledger (financial data) + Fraud Engine (investigation data)
- **Why:** Split authority because chargebacks span two concerns. The ledger is authoritative for amounts, fees, and financial resolution. The fraud engine is authoritative for risk scores, investigation status, and case outcomes.
- **Exception:** When a chargeback arrives outside the fraud workflow (~5% of cases), the ledger is the sole authority until a fraud case is retroactively created.

## FraudCase
- **Authority:** Fraud Engine
- **Why:** The fraud engine creates, manages, and resolves fraud investigations. No other system has visibility into the full case lifecycle.
- **Exception:** None. The fraud engine is always authoritative for fraud cases.

## FeeSchedule
- **Authority:** Merchant Portal
- **Why:** Fee schedules are configured during merchant onboarding and updated through the portal. The billing ledger reads fee schedules to calculate charges but does not modify them.
- **Exception:** None.

## PaymentMethod
- **Authority:** Payment Gateway (token vault)
- **Why:** The gateway's token vault is the system of record for payment method tokens. All other systems reference tokens but never store raw card data.
- **Exception:** None. PCI compliance mandates single-source management.

## Account
- **Authority:** Billing Ledger
- **Why:** The ledger maintains the running balance through double-entry bookkeeping. All debits and credits are recorded here first.
- **Exception:** None.

## Example

> ## Transaction
> - **Authority:** Payment Gateway
> - **Why:** Gateway is the system of record for payment state — it processes the transaction
> - **Exception:** For settlement status, the Billing Ledger is authoritative (gateway doesn't track post-settlement)

## Completion criteria
- [x] Every concept with multiple sources has a designated authority
- [x] Reasoning documented for each designation
- [x] Exceptions and caveats captured
- [x] Authority designations validated by system owners
