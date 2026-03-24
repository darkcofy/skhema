# Domain Boundaries

## Purpose
Define where this domain starts and stops, and how it relates to adjacent domains. Clear boundaries prevent scope creep and help identify integration points.

## Session guide
After identifying candidate concepts, map the boundaries:

1. Ask: "Which of these concepts are fully ours to define?"
2. Ask: "Which concepts do we share with other domains?"
3. Ask: "Where do we consume data from other domains vs produce data for them?"
4. Draw a simple boundary diagram: inside vs outside vs shared.

## Capture

**Core Payments (we own):** Transaction, PaymentMethod, SettlementBatch, Acquirer, Issuer, WebhookEvent
These concepts are fully defined and governed by the payments domain. The Payment Gateway is the system of record.

**Merchant Management (we own):** Merchant, Account, Payout, FeeSchedule
These concepts are owned by the partner engineering / merchant domain. The Merchant Portal is the system of record. While they interact heavily with core payments, their lifecycle and governance are independent.

**Fraud Detection (we own):** FraudCase, Chargeback
These concepts are owned by the risk & compliance domain. The Fraud Engine is the system of record for FraudCase; chargebacks flow through both the Fraud Engine and the Billing Ledger.

**Shared (co-owned):**
- **Merchant** is shared between core payments and merchant management. Core payments references Merchant for routing and fee lookup; merchant management owns the full lifecycle (onboarding, activation, suspension).
- **Transaction** is shared between core payments and fraud detection. Core payments owns the payment lifecycle; fraud detection reads transactions for risk scoring and links them to fraud cases.

**External (referenced but not owned):**
- **Consumer/Cardholder** — not modeled as a first-class entity. Referenced only through tokenized PaymentMethod. Consumer identity is owned by the card networks and issuing banks.
- **Product/SKU** — not part of the payments domain. Some merchants send line-item data, but we treat it as opaque metadata.
- **Employee/Agent** — fraud case assignment references internal employees, but HR/identity is not part of this model.

**Integration points:**
- We receive merchant onboarding data from the KYC/compliance service (external to this domain)
- We publish TransactionSettled and TransactionRefunded events to the Billing Ledger
- We query real-time risk scores from the Fraud Engine during authorization
- We send webhook events to merchant endpoints for async notifications
- We receive chargeback notifications from the card network via the acquirer
- The Legacy ERP provides historical data for migration but will not receive data from the canonical model

## Example

> **Core (we own):** Transaction, SettlementBatch, PaymentMethod, FeeSchedule
> **Shared (co-owned):** Merchant (shared with onboarding domain), Account (shared with billing)
> **External (referenced):** Customer (owned by CRM), Product (owned by catalog)
> **Integration points:**
> - We receive merchant data from the onboarding service
> - We publish settlement events to the billing ledger
> - We query customer risk scores from the fraud engine

## Completion criteria
- [x] All candidate concepts classified as core / shared / external
- [x] Shared concepts have identified co-owners
- [x] Integration points listed with data flow direction
- [x] Boundary validated by stakeholders from adjacent domains
