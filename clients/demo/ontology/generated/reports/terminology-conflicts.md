# Terminology Conflict Report

*Auto-generated from synonym-conflicts.md.*

# Synonym and Terminology Conflicts

## Purpose
List terms that appear to mean the same thing, or the same term used to mean different things. These must be resolved before concepts can be formalized.

## Session guide
After completing stakeholder interviews, cross-reference terms:

1. Compare terms across stakeholders — where do definitions overlap or clash?
2. For each conflict, ask: "Which meaning should be canonical?"
3. Do not force resolution yet — just capture the conflict clearly.

## Capture

## "Customer" vs "Merchant" vs "Account Holder"
- **Product team (Priya)**: "customer" = the merchant (the business paying us for payment processing)
- **Fraud ops (Elena)**: "customer" = the consumer (the cardholder making a purchase)
- **Partner engineering (David)**: "customer" = always the merchant; consumers are "cardholders"
- **Billing (Ledger system)**: "account holder" = the entity receiving invoices (always the merchant)
- **Status**: resolved
- **Resolution**: Use "merchant" for the business entity and "cardholder" or "consumer" for the person making a purchase. Retire "customer" from the canonical model entirely to avoid ambiguity.

## "Auth" vs "Authorization" vs "Pre-auth" vs "Approval"
- **Product (Priya)**: "auth" = the step where we check the card and reserve funds
- **Engineering (Marcus)**: "pre-auth" = the same thing; "auth" is ambiguous (could mean authentication)
- **Fraud ops (Elena)**: "approval" = a transaction that passed risk scoring; different from card authorization
- **Status**: resolved
- **Resolution**: Canonical term is "authorization" (full word). "Pre-auth" is acceptable as an alias. "Approval" is reserved for fraud risk decisions only. "Auth" is deprecated in docs to avoid confusion with authentication.

## "Refund" vs "Reversal" vs "Chargeback"
- **Product (Priya)**: "refund" = merchant-initiated return of funds; "chargeback" = bank-initiated forced reversal
- **Engineering (Marcus)**: "reversal" = any undo operation (includes voids, refunds, and chargebacks)
- **Fraud ops (Elena)**: "chargeback" = specifically the financial penalty after a lost dispute; "reversal" = generic
- **Billing Ledger**: uses "credit" for all money-back operations regardless of trigger
- **Status**: resolved
- **Resolution**: Three distinct canonical terms: "refund" (merchant-initiated, voluntary), "chargeback" (issuer-initiated, forced via dispute process), "void" (cancellation of an auth before capture). "Reversal" is retired as too vague. "Credit" is a ledger-level term only.

## "Settlement" — gateway vs ledger meaning
- **Gateway (Marcus)**: "settlement" = the batch file sent to the acquirer at end of day
- **Billing Ledger**: "settlement" = the completed fund transfer from acquirer to merchant account
- **Product (Priya)**: uses "settlement" interchangeably for both meanings
- **Status**: resolved
- **Resolution**: "Settlement batch" = the gateway-side batch processing. "Settlement" = the completed fund transfer. Context determines which is meant, but in the canonical model, SettlementBatch is the entity representing the batch, and the settlement event is when funds arrive.

## Example

> ## "Customer" vs "Merchant" vs "Account Holder"
> - **Sales team**: "customer" = the business that signs up (i.e., the merchant)
> - **Support team**: "customer" = the end consumer making a purchase
> - **Billing**: "account holder" = whoever receives the invoice (could be either)
> - **Status**: unresolved
> - **Notes**: Need to distinguish the merchant (B2B relationship) from the consumer (B2C)

## Completion criteria
- [x] All known synonym groups listed
- [x] Each conflict has attributed definitions from specific stakeholders
- [x] Resolution status marked for each
- [x] At least one conflict has a proposed resolution

