# Engagement Scope

## Purpose
Define the business area this ontology effort covers. This is the anchor document — everything else flows from the scope you set here.

## Session guide
Run this as a 60-minute kickoff session with the project sponsor and 1-2 key stakeholders.

1. Ask the stakeholder: "What business domain are we trying to model?"
2. Ask: "What decisions should this work support? What will you do differently once we have a shared model?"
3. Ask: "What is explicitly out of scope? What adjacent areas should we avoid pulling in?"
4. Ask: "Which systems hold the data we care about?"
5. Ask: "What would 'done' look like for this engagement?"

Capture answers below in the stakeholder's language — do not rephrase or formalize yet.

## domain
NovaPay's core digital payments platform — from payment initiation through settlement, including merchant onboarding and fraud detection.

## outcomes
1. A canonical entity model for the payments domain that all teams can reference when building APIs and integrations.
2. A shared glossary of payment terms adopted by product, engineering, and operations.
3. A mapping matrix linking every source system entity to the canonical model, enabling clean data migration from the Legacy ERP.
4. Clear domain boundaries between core payments, fraud detection, and merchant management.

## out_of_scope
- Consumer-facing mobile app UX (separate product domain)
- Internal HR and employee management systems
- Physical point-of-sale terminal hardware management
- Marketing and customer acquisition workflows
- Tax calculation and regulatory reporting (handled by finance domain)

## systems
- Payment Gateway (primary transaction processor)
- Merchant Portal (merchant self-service and onboarding)
- Fraud Engine (real-time risk scoring and case management)
- Billing Ledger (financial reconciliation and settlement)
- Legacy ERP (being sunset — historical data migration source)

## Example
> **domain:** Order management for e-commerce platform — from cart through fulfillment.
> **outcomes:** 1. Canonical entity model for data migration. 2. Shared glossary for cross-team alignment. 3. Mapping matrix from legacy ERP to new platform.
> **out_of_scope:** Payment processing (separate domain), warehouse logistics, customer support workflows.

## Completion criteria
- [x] In-scope domain described in 1-2 sentences
- [x] At least 3 target outcomes listed
- [x] Out-of-scope areas explicitly named
- [x] Initial systems list included (even if rough)
