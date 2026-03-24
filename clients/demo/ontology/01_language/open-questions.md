# Open Questions

## Purpose
Track questions that come up during language capture and concept modeling that cannot be answered yet. These are the known unknowns — things that need stakeholder input, research, or decisions before the model can progress.

## Session guide
This file accumulates throughout the engagement. After each session:

1. Review notes for unanswered questions
2. Add them here with context on why they matter
3. Assign an owner if possible
4. Revisit at the start of each new session

## Capture

## Should partial captures be modeled as separate transactions or as a property of the original?
- **Why it matters**: Determines whether a single authorization can produce multiple Transaction entities or if we track partial capture amounts as attributes on one Transaction
- **Who can answer**: Marcus Webb (Payments Architect) + Priya Sharma (Product Owner)
- **Status**: answered
- **Resolution**: Modeled as separate Transaction entities linked to the original authorization via a `parent_transaction_id` reference. This matches how the Payment Gateway already tracks them and avoids complex amount-tracking logic on a single entity.

## How should we model multi-currency transactions where the consumer pays in one currency and the merchant settles in another?
- **Why it matters**: Affects whether Transaction has one amount field or two (consumer amount + settlement amount), and whether currency conversion is a property or a separate event
- **Who can answer**: Marcus Webb (Payments Architect) + Billing Ledger team
- **Status**: answered
- **Resolution**: Transaction carries both `amount` (consumer currency) and `settlement_amount` (merchant currency) with an `exchange_rate` property. The conversion is not a separate entity — it is captured at authorization time and locked in.

## Do we need to model the consumer/cardholder as a first-class entity?
- **Why it matters**: Currently consumers only exist as properties on transactions (card number, token). If we model Consumer as an entity, it changes the relationship graph significantly and has PCI implications for data storage.
- **Who can answer**: Priya Sharma (Product Owner) + Elena Rodriguez (Fraud Ops Lead)
- **Status**: answered
- **Resolution**: No. Consumers are not first-class entities in the canonical model. We reference them only through tokenized payment methods. The Fraud Engine maintains its own consumer risk profiles, but those are internal to the fraud subdomain and not part of the canonical payments model.

## What happens to in-flight transactions when a merchant is deactivated?
- **Why it matters**: Determines edge case handling for the Merchant lifecycle and whether Transaction needs a "merchant_deactivated" terminal state
- **Who can answer**: David Kim (Merchant Integrations Lead) + Priya Sharma
- **Status**: answered
- **Resolution**: Authorized-but-uncaptured transactions are voided automatically. Already-captured transactions proceed to settlement normally. New transactions are blocked at the gateway level. No new terminal state needed — existing void and settlement states cover it.

## Example

> ## Is a chargeback a type of refund or a separate concept?
> - **Why it matters**: Determines whether we model one entity with subtypes or two distinct entities
> - **Who can answer**: Payments architect + Fraud ops lead
> - **Status**: open
> - **Notes**: Finance treats them the same in reporting, but ops handles them via completely different workflows

## Completion criteria
- [x] All known open questions captured
- [x] Each question has a "why it matters" explanation
- [x] At least one question has an assigned owner
- [x] Questions reviewed and updated after each session
