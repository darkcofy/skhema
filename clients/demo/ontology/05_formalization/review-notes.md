# Review Notes

## Purpose
Document decisions made during formalization, remaining open items, and feedback from reviewers. This is the audit trail for why the model looks the way it does.

## Session guide
During the formalization review:

1. Walk through each class with stakeholders
2. For each decision: "Why did we model it this way?"
3. For each open item: "What do we still need to resolve?"
4. Record dissenting opinions — they may prove important later

## Capture

## Decision: Model Chargeback as separate class (not Transaction subtype)
- **Rationale:** Chargebacks have a fundamentally different lifecycle, involve different stakeholders (fraud ops vs payments), and carry additional attributes (reason_code, evidence_due_by, fee_amount) that do not apply to normal transactions. Modeling as a subtype would pollute the Transaction class with nullable fields.
- **Dissent:** Finance team initially preferred a unified view for reporting. Addressed by planning a `financial_event` reporting view that joins Transactions, Chargebacks, and Refunds.
- **Date:** 2026-03-18

## Decision: Consumer is not a first-class entity
- **Rationale:** NovaPay does not own the consumer relationship — the merchant does. Consumers are only visible through tokenized PaymentMethods. Adding a Consumer entity would create PCI compliance challenges (storing consumer identity linked to payment data) with no clear business benefit.
- **Dissent:** Elena (Fraud Ops) wanted a Consumer entity for cross-merchant fraud pattern detection. Resolved by keeping consumer risk profiles internal to the Fraud Engine subdomain, not part of the canonical model.
- **Date:** 2026-03-19

## Decision: Use separate amount fields for multi-currency
- **Rationale:** Transaction carries both `amount` (consumer currency) and `settlement_amount` (merchant currency) rather than a single amount with currency conversion events. This matches how the Payment Gateway already works and avoids introducing a separate CurrencyConversion entity for what is fundamentally a property of the transaction.
- **Dissent:** Marcus (Payments Architect) noted that for domestic transactions, having two amount fields is redundant. Accepted as a minor overhead — the fields are simply equal for same-currency transactions.
- **Date:** 2026-03-20

## Decision: WebhookEvent as a domain entity (not just infrastructure)
- **Rationale:** Merchants depend on webhook delivery for their own reconciliation. Failed webhooks have direct business impact (merchant doesn't know a settlement landed). The event delivery lifecycle (pending -> delivered/failed/retrying) is a domain concern, not just an infrastructure concern.
- **Dissent:** Engineering initially argued webhooks are infrastructure. Overruled because merchant support tickets frequently involve webhook delivery issues, making it a first-class business concept.
- **Date:** 2026-03-21

## Decision: Parent-child transaction model for partial captures
- **Rationale:** Partial captures create child Transaction entities linked to the parent authorization via `parent_transaction_id`. This avoids complex amount-tracking on a single entity and cleanly handles scenarios where a $500 auth produces a $350 capture and a $150 void.
- **Dissent:** None. All stakeholders agreed this matches the gateway's existing behavior.
- **Date:** 2026-03-22

## Open item: Negative account balance handling
- **Owner:** Priya Sharma + Finance team
- **Deadline:** 2026-04-15
- **Description:** When a chargeback arrives for a deactivated merchant whose account balance is zero, the Account goes negative. The model supports this (available_balance is not constrained to >= 0), but the business process for recovering negative balances needs to be defined.

## Open item: Webhook event ordering guarantees
- **Owner:** Marcus Webb
- **Deadline:** 2026-04-01
- **Description:** The current model includes a `sequence_number` on WebhookEvent, but we have not defined whether merchants should expect strict ordering or handle out-of-order delivery. This affects both the model (whether sequence_number is advisory or authoritative) and the merchant integration docs.

## Reviewer feedback: Elena Rodriguez (Fraud Ops Lead)
- Reviewed all 12 classes on 2026-03-22
- Approved FraudCase and Chargeback models
- Requested: add a cross-reference between Chargeback and FraudCase (done — Chargeback.may_trigger relationship)
- Concern: FraudCase.transaction_ids should be a many-to-many relationship, not a simple list. Response: modeled as N:M in ontology.yaml.

## Reviewer feedback: David Kim (Merchant Integrations Lead)
- Reviewed Merchant, Account, Payout, FeeSchedule on 2026-03-22
- Approved all four classes
- Requested: add IntegrationTier enum (done)
- Noted: FeeSchedule should support time-bounded validity (effective_from/effective_to) for rate changes. Response: already included in properties.yaml.

## Example

> ## Decision: Model Refund as separate class (not Transaction subtype)
> - **Rationale:** Refunds have a different lifecycle, different auth flow, and different settlement timing. Modeling as a subtype would force shared attributes that don't apply.
> - **Dissent:** Finance team prefers unified view for reporting. Addressed by adding a `financial_event` view that combines both.
> - **Date:** 2026-03-20

## Completion criteria
- [x] All major modeling decisions documented with rationale
- [x] Open items listed with owners and deadlines
- [x] At least one review session completed
- [x] Reviewer feedback captured and addressed
