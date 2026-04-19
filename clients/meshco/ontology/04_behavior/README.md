# Stage 4: Behavior & Constraints — not yet populated

Stage 4 captures dynamic behaviour: lifecycles, state machines,
domain events, and business rules. For MeshCo that would include the
Order lifecycle (initiated → authorised → captured → refunded/disputed),
the Contract lifecycle (draft → published → deprecated → retired),
and events like `ContractBreakDetected`, `OrderAbandoned`, etc.

This demo stops at stage 2. Stage 4 is scaffolded but intentionally
empty to keep the demo focused.

To populate: apply the
`skills/gnosis/extracting-events-and-lifecycles.md` skill against
stakeholder interviews and process documentation.

Expected files (when populated):

- `lifecycle-states.yaml` — state machines per entity
- `events.yaml` — domain events with triggers, payloads, consumers
- `business-rules.md` — invariants and constraints
- `edge-cases.md` — known exceptions and how they're handled
