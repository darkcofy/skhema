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

## Authorization expires after 7 calendar days
- **Applies to:** Transaction
- **Rule:** An authorized transaction must be captured within 7 calendar days. After 7 days, the authorization hold is released by the issuing bank and the transaction must be re-authorized or voided.
- **On violation:** Gateway automatically voids expired authorizations during nightly cleanup. Merchant receives a webhook notification of the void.
- **Source:** Marcus Webb (Payments Architect); confirmed in Visa and Mastercard network rules

## Settlement batch closes at midnight UTC
- **Applies to:** SettlementBatch, Transaction
- **Rule:** All captured transactions received before midnight UTC are included in that day's settlement batch. Transactions captured after midnight roll to the next day's batch. Only one batch per acquirer per day.
- **On violation:** N/A — enforced by system clock and batch scheduler. No manual override is possible.
- **Source:** Marcus Webb (Payments Architect); confirmed in acquirer integration docs

## Refund cannot exceed original transaction amount
- **Applies to:** Transaction
- **Rule:** The total of all refunds against a transaction must not exceed the original captured amount. Partial refunds are allowed. Multiple partial refunds are allowed as long as the sum does not exceed the original.
- **On violation:** Gateway rejects the refund request with error code `refund_amount_exceeds_original`. Merchant sees an error in the portal.
- **Source:** Priya Sharma (Product Owner); enforced at gateway level

## Refund window is 180 days from settlement
- **Applies to:** Transaction
- **Rule:** Refunds can only be issued within 180 days of the transaction's settlement date. After 180 days, the merchant must issue a manual credit outside the payment system.
- **On violation:** Gateway rejects the refund request with error code `refund_window_expired`. Merchant must contact support for manual resolution.
- **Source:** Card network rules (Visa, Mastercard); confirmed by Marcus Webb

## Chargeback evidence must be submitted within 14 days
- **Applies to:** Chargeback
- **Rule:** When a chargeback is opened, the merchant has 14 calendar days to submit representment evidence. If evidence is not submitted by the deadline, the chargeback is automatically ruled in the cardholder's favor.
- **On violation:** Chargeback auto-resolves as lost. Merchant is charged the chargeback fee plus the disputed amount. WebhookEvent sent to merchant.
- **Source:** Elena Rodriguez (Fraud Ops Lead); deadline set by card network rules

## Merchant must pass KYC before processing payments
- **Applies to:** Merchant
- **Rule:** A merchant in "pending" status cannot process any transactions. The Payment Gateway blocks all authorization requests for non-active merchants. KYC verification, identity checks, and underwriting must be completed first.
- **On violation:** Gateway returns error code `merchant_not_active`. Transaction is not created.
- **Source:** David Kim (Merchant Integrations Lead); regulatory requirement

## Payout requires minimum available balance
- **Applies to:** Payout, Account
- **Rule:** A payout can only be initiated if the merchant's available balance exceeds the payout amount plus a reserve buffer (currently $100 or 5% of monthly volume, whichever is greater). The reserve protects against pending chargebacks.
- **On violation:** Payout is rejected with status "insufficient_balance". Merchant notified via webhook and portal.
- **Source:** Priya Sharma (Product Owner) + Finance team; configured per-merchant in Account settings

## Example

> ## Settlement batch closes at midnight UTC
> - **Applies to:** SettlementBatch, Transaction
> - **Rule:** All authorized transactions captured before midnight are included in that day's settlement batch. Transactions captured after midnight roll to the next batch.
> - **On violation:** N/A — enforced by system clock
> - **Source:** Payments architect, confirmed in gateway docs

## Completion criteria
- [x] Rules captured for each concept with a lifecycle
- [x] Each rule has a clear violation consequence
- [x] Timing and threshold constraints documented
- [x] Rules validated by domain expert
