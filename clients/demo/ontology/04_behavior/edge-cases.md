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

## Double-dip: refund issued then chargeback filed
- **Scenario:** Merchant refunds a transaction proactively, but the consumer also files a chargeback through their bank (not knowing the refund is in progress). The merchant loses the money twice.
- **Affects:** Transaction, Chargeback, Account
- **Current handling:** Fraud ops manually identifies double-dip cases by cross-referencing refund records with incoming chargebacks. If detected, they file a representment with the refund receipt as evidence. Success rate is ~70%.
- **Model impact:** Transaction needs a flag or relationship linking refunds to related chargebacks so double-dip detection can be automated. The Chargeback entity should reference any prior refunds on the same transaction.

## Partial capture with subsequent chargeback
- **Scenario:** Hotel authorizes $500 for a guest stay, captures $350 (partial capture for actual charges). Guest later disputes the $350 charge. The chargeback amount does not match the original authorization amount, causing reconciliation confusion.
- **Affects:** Transaction, Chargeback, SettlementBatch
- **Current handling:** Manual reconciliation by billing ops. The system correctly tracks partial captures as child transactions, but the chargeback system does not automatically link to the parent authorization.
- **Model impact:** Chargeback should reference the specific captured Transaction (child), not the authorization (parent). The parent-child transaction relationship must be traversable in both directions.

## Merchant deactivation with in-flight settlement batch
- **Scenario:** A merchant is deactivated for fraud while a settlement batch containing their transactions is already submitted to the acquirer. The funds arrive at NovaPay but cannot be paid out to the merchant.
- **Affects:** Merchant, SettlementBatch, Account, Payout
- **Current handling:** Funds are deposited into the merchant's NovaPay Account but the account is frozen. A hold is placed on all payouts. Finance manually reviews after 90 days and either refunds consumers or releases funds based on investigation outcome.
- **Model impact:** Account needs a "frozen" or "held" state separate from merchant deactivation. Payout needs a "blocked" status that indicates the merchant is suspended rather than a balance issue.

## Webhook endpoint down during critical event storm
- **Scenario:** A merchant's webhook endpoint goes down during a high-volume settlement period. Hundreds of webhook events queue up and retry. When the endpoint comes back, the merchant receives events out of order, causing their system to process settlements before authorizations.
- **Affects:** WebhookEvent, Transaction
- **Current handling:** Webhooks retry with exponential backoff (1s, 2s, 4s, 8s, ... up to 24h). Events include a sequence number, but most merchant implementations ignore it. NovaPay support manually re-sends events on request.
- **Model impact:** WebhookEvent needs a sequence_number and the merchant integration docs must specify that consumers should process events idempotently and handle out-of-order delivery. Consider adding a "batch replay" API endpoint.

## Multi-currency settlement with exchange rate fluctuation
- **Scenario:** Consumer in the UK pays GBP 100 for a transaction. At authorization time, the exchange rate is 1.27 USD/GBP, so the merchant expects $127. By settlement time (2 days later), the rate has moved to 1.25, and the merchant actually receives $125.
- **Affects:** Transaction, SettlementBatch, Account
- **Current handling:** The exchange rate is locked at authorization time for the consumer (they are always charged the authorized amount in their currency). The rate variance is absorbed by NovaPay as a cost of doing business. The merchant always receives the settlement_amount calculated at auth time.
- **Model impact:** Transaction correctly captures both consumer-side and merchant-side amounts with the exchange rate locked at auth. No model change needed, but the Billing Ledger needs to track the FX variance as a separate line item for finance reporting.

## Chargeback on a transaction older than 180 days
- **Scenario:** Card networks allow chargebacks up to 540 days after the transaction in certain fraud categories. A chargeback arrives for a transaction that is past the 180-day refund window and has already been archived from the gateway's hot storage.
- **Affects:** Chargeback, Transaction
- **Current handling:** Ops team manually retrieves the transaction from cold storage. The chargeback is processed against the merchant's current balance. If the merchant has been deactivated, the chargeback creates a negative balance that goes to collections.
- **Model impact:** Transaction records must be retrievable from archive for at least 540 days. Chargeback should not validate against the refund window (different rules apply). Account must support negative balances for this scenario.

## Example

> ## Partial refund on a split payment
> - **Scenario:** Consumer paid with two cards (60/40 split). Requests refund of 50% of the total.
> - **Affects:** Transaction, PaymentMethod, Refund
> - **Current handling:** Manual process — ops team splits the refund proportionally across both original transactions
> - **Model impact:** Refund needs a relationship to multiple source Transactions, not just one

## Completion criteria
- [x] At least 5 edge cases documented
- [x] Each linked to affected concepts and rules
- [x] Current handling described
- [x] Model impact assessed (does current model handle it?)
