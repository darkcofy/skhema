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
