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

Record:
- Decisions made and their rationale
- Open items that need further investigation
- Reviewer feedback and responses
- Changes made in response to feedback

## Example

> ## Decision: Model Refund as separate class (not Transaction subtype)
> - **Rationale:** Refunds have a different lifecycle, different auth flow, and different settlement timing. Modeling as a subtype would force shared attributes that don't apply.
> - **Dissent:** Finance team prefers unified view for reporting. Addressed by adding a `financial_event` view that combines both.
> - **Date:** 2026-03-20

## Completion criteria
- [ ] All major modeling decisions documented with rationale
- [ ] Open items listed with owners and deadlines
- [ ] At least one review session completed
- [ ] Reviewer feedback captured and addressed
