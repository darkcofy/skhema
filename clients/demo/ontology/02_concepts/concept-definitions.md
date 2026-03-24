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

## Transaction
A single payment attempt initiated by a consumer against a merchant account. A Transaction has a lifecycle (initiated -> authorized -> captured -> settled or declined/refunded/disputed) and is the atomic unit of payment processing. Each Transaction is uniquely identified and immutable once created — state changes are tracked but previous states are never overwritten.

**Key attributes:** id, amount, currency, settlement_amount, settlement_currency, exchange_rate, status, created_at, authorized_at, captured_at, settled_at, payment_method_token, merchant_id, idempotency_key
**Common confusion:** A "transaction" in the Billing Ledger means a ledger entry (debit or credit), not a payment attempt. The canonical model uses "Transaction" exclusively for payment attempts and "LedgerEntry" for financial records.
**Related:** PaymentMethod, Merchant, SettlementBatch, Chargeback

## PaymentMethod
A tokenized representation of a consumer's payment instrument. The actual card number (PAN) is never stored — only a token referencing the vault. A PaymentMethod can be a credit card, debit card, bank account (ACH), or digital wallet. It persists across transactions for returning consumers.

**Key attributes:** token, type (card/bank/wallet), last_four, card_network, expiry_month, expiry_year, issuer_id, is_active
**Common confusion:** PaymentMethod is not the same as a payment — it is the instrument, not the act. A single PaymentMethod can be used for many Transactions.
**Related:** Transaction, Issuer

## Merchant
A business entity that has a contractual relationship with NovaPay to accept payments. A Merchant has a legal identity (legal name, tax ID, registration), a public-facing identity (DBA name, website), and a financial identity (Account, FeeSchedule). Merchants go through an onboarding lifecycle before they can process payments.

**Key attributes:** id, legal_name, dba_name, mcc_code, status (pending/active/suspended/deactivated), onboarded_at, integration_tier, website_url, country
**Common confusion:** "Merchant" and "merchant account" are not the same. The Merchant is the business entity; the Account is the financial construct that tracks their money.
**Related:** Account, FeeSchedule, Transaction, Payout, WebhookEvent

## SettlementBatch
A daily aggregation of captured transactions that are submitted together to the acquiring bank for fund transfer. Each batch has a cutoff time (midnight UTC), after which captured transactions roll to the next day's batch. The batch is the unit of reconciliation between NovaPay and the acquirer.

**Key attributes:** id, batch_date, acquirer_id, total_amount, transaction_count, status (open/submitted/processed/reconciled), submitted_at, reconciled_at
**Common confusion:** A SettlementBatch is not the same as a Payout. The batch settles funds from the card network to NovaPay; the Payout disburses funds from NovaPay to the merchant.
**Related:** Transaction, Acquirer

## Chargeback
A forced reversal of a previously settled transaction, initiated through the card network's dispute process. Chargebacks are fundamentally different from refunds: they are involuntary, carry financial penalties (chargeback fees), and involve a formal dispute workflow with evidence submission deadlines.

**Key attributes:** id, transaction_id, amount, reason_code, status (opened/evidence_due/representment/won/lost), opened_at, evidence_due_by, resolved_at, fee_amount
**Common confusion:** A chargeback is not a refund. Refunds are voluntary and merchant-initiated. Chargebacks are involuntary and issuer-initiated. A transaction that has been refunded can still receive a chargeback (double-dip scenario).
**Related:** Transaction, FraudCase, Issuer

## FraudCase
An investigation record created when the fraud engine's real-time risk scoring flags a transaction or behavioral pattern as suspicious. A FraudCase tracks the investigation from detection through resolution, including analyst notes, evidence gathered, and final outcome.

**Key attributes:** id, risk_score, trigger_type (transaction/pattern/manual), status (opened/investigating/escalated/resolved), outcome (confirmed_fraud/false_positive/inconclusive), opened_at, assigned_to, resolved_at
**Common confusion:** A FraudCase is not the same as a Chargeback. Many fraud cases never result in chargebacks (caught before the consumer complains), and some chargebacks have no associated fraud case (friendly fraud).
**Related:** Transaction, Merchant, Chargeback

## FeeSchedule
A merchant-specific pricing configuration that determines what fees are charged for each transaction type. Fee schedules vary by merchant tier, transaction volume, and card type. They include per-transaction fees (flat + percentage), monthly fees, chargeback fees, and refund processing fees.

**Key attributes:** id, merchant_id, effective_from, effective_to, per_txn_flat_fee, per_txn_percentage, monthly_fee, chargeback_fee, refund_fee, tier
**Common confusion:** FeeSchedule defines the rates; actual fee amounts are calculated per-transaction and recorded in the Billing Ledger. The schedule is the template, not the invoice.
**Related:** Merchant

## Acquirer
The bank or financial institution that maintains NovaPay's merchant processing relationship with the card networks. The acquirer receives settlement batches, submits them to the card network, and transfers funds to NovaPay. NovaPay may work with multiple acquirers for redundancy and geographic coverage.

**Key attributes:** id, name, bank_id, supported_networks, supported_currencies, settlement_schedule, is_active
**Common confusion:** The acquirer is NovaPay's bank, not the merchant's bank. Funds flow: Issuer -> Card Network -> Acquirer -> NovaPay -> Merchant.
**Related:** SettlementBatch, Merchant

## Issuer
The bank that issued the consumer's payment card. The issuer authorizes transactions, places holds on cardholder funds, and initiates chargebacks on behalf of cardholders. NovaPay does not interact with issuers directly — communication goes through the card network.

**Key attributes:** id, name, bank_id, country, supported_networks
**Common confusion:** Issuer is not the same as acquirer. The issuer represents the consumer's side; the acquirer represents the merchant's side.
**Related:** PaymentMethod, Chargeback

## Account
A financial account within NovaPay that tracks a merchant's running balance. Every settlement adds funds, every payout deducts funds, and every fee reduces the balance. The Account is the single source of truth for "how much does NovaPay owe this merchant?"

**Key attributes:** id, merchant_id, currency, available_balance, pending_balance, total_settled, total_paid_out, created_at
**Common confusion:** This is NovaPay's internal account, not the merchant's bank account. The merchant's external bank account is just a payout destination.
**Related:** Merchant, Payout

## Payout
A disbursement of accumulated settled funds from a merchant's NovaPay Account to their registered external bank account. Payouts can be scheduled (daily, weekly, monthly) or manual. Each payout reduces the merchant's available balance.

**Key attributes:** id, merchant_id, account_id, amount, currency, status (pending/processing/completed/failed), scheduled_at, completed_at, bank_account_last_four
**Common confusion:** Payout is not the same as settlement. Settlement is funds arriving at NovaPay from the card network. Payout is funds leaving NovaPay to the merchant.
**Related:** Account, Merchant

## WebhookEvent
An asynchronous notification delivered to a merchant's registered HTTP endpoint when a significant event occurs (e.g., transaction settled, chargeback opened, payout completed). Webhook events are idempotent, signed for verification, and retried with exponential backoff on failure.

**Key attributes:** id, event_type, merchant_id, endpoint_url, payload, status (pending/delivered/failed/retrying), created_at, delivered_at, retry_count
**Common confusion:** A WebhookEvent is not the same as the domain event that triggered it. The domain event is internal; the WebhookEvent is the external notification delivered to the merchant.
**Related:** Transaction, Merchant

## Example

> ## Transaction
> A single payment attempt initiated by a consumer against a merchant account. A transaction has a lifecycle (initiated -> authorized -> captured -> settled or declined) and is the atomic unit of payment processing. Partial captures are modeled as separate transactions linked to the original authorization.
>
> **Key attributes:** amount, currency, status, timestamp, payment method
> **Common confusion:** A "transaction" in the billing system refers to a ledger entry, not a payment attempt. We use "Transaction" exclusively for payment attempts.
> **Related:** PaymentMethod, Merchant, SettlementBatch

## Completion criteria
- [x] Every candidate concept has a detailed definition
- [x] Definitions reviewed by at least one domain expert
- [x] Edge cases and common confusions documented
- [x] Key attributes listed for each concept
