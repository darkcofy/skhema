# Engagement Brief

*Auto-generated from ontology workspace scope files.*

## Scope

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

## Stakeholders

| Name | Role |
|------|------|
| Priya Sharma | Product Owner |
| Marcus Webb | Payments Architect |
| Elena Rodriguez | Fraud Operations Lead |
| David Kim | Merchant Integrations Lead |

## Success Criteria

# Success Criteria

## Purpose
Define measurable outcomes that tell you whether this engagement succeeded. These criteria should be revisited at the end of each stage.

## Session guide
After the kickoff session (engagement.md), ask the sponsor:

1. "If we deliver everything you hope for, what specifically will be different?"
2. "What would a 'minimum viable' outcome look like — the least we could deliver that's still useful?"
3. "What would make you say this effort was a waste of time?"

## Capture

## Canonical glossary adopted by 2+ teams
Verified by teams referencing the glossary in API design docs and Confluence pages. Target: payments, partner engineering, and fraud ops all using the same term definitions within 30 days of delivery.
**Pass/fail:** At least 2 teams include glossary links in new design documents.

## Mapping matrix covers 90%+ of source entities
Every entity in Payment Gateway, Billing Ledger, and Merchant Portal mapped to the canonical model. Measured by entity count vs source system inventory.
**Pass/fail:** Source-to-canonical mapping CSV covers >= 90% of identified source entities.

## Zero undefined terms in new API contracts
All new API endpoints use terms from the canonical glossary. Verified by contract review during PR approvals.
**Pass/fail:** Next 3 API design reviews pass with zero "what does this field mean?" questions.

## Minimum viable outcome
At minimum, a shared glossary of 25+ terms and a concept map with 10+ entities that the payments team can use as a reference during the Legacy ERP migration planning.

## Legacy ERP migration unblocked
The mapping matrix from Legacy ERP entities to canonical model is complete enough for the data engineering team to begin writing migration scripts.
**Pass/fail:** Data engineering confirms they can map 80%+ of active ERP entities using the deliverables.

## Example
> - **Canonical glossary adopted by 2+ teams** — verified by teams referencing it in design docs.
> - **Mapping matrix covers 80%+ of source entities** — measured by entity count vs source inventory.
> - **Zero undefined terms in new API contracts** — verified by contract review.

## Completion criteria
- [x] At least 3 success criteria defined
- [x] Each criterion has a measurable pass/fail definition
- [x] Minimum viable outcome identified

