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

Define:
- Core domain concepts (fully owned)
- Shared concepts (co-owned with other domains)
- External concepts (referenced but not owned)
- Integration points (where data flows across boundaries)

## Example

> **Core (we own):** Transaction, SettlementBatch, PaymentMethod, FeeSchedule
> **Shared (co-owned):** Merchant (shared with onboarding domain), Account (shared with billing)
> **External (referenced):** Customer (owned by CRM), Product (owned by catalog)
> **Integration points:**
> - We receive merchant data from the onboarding service
> - We publish settlement events to the billing ledger
> - We query customer risk scores from the fraud engine

## Completion criteria
- [ ] All candidate concepts classified as core / shared / external
- [ ] Shared concepts have identified co-owners
- [ ] Integration points listed with data flow direction
- [ ] Boundary validated by stakeholders from adjacent domains
