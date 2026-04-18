# Data Council kickoff — 2026-04-16

**Attendees:** Alice Chen (Head of Platform), Emma Ward (Finance), Carol Singh (Customer), domain leads, me (facilitating).

---

**Alice:** Thanks everyone. The goal today is to agree on the mesh model —
not the technology, the ownership model. We've been running a central data
team for six years. It works, but it doesn't scale. So we're moving to a
mesh.

**Me:** Can you define what mesh means for MeshCo specifically?

**Alice:** Five domains — customer, product, orders, inventory, fulfilment.
Each owns its data products. Platform team runs the shared infrastructure and
the contract governance. We stop funnelling everything through a single
central team.

**Carol:** And we finally get to own customer properly. Right now it's
scattered across POS, commerce, and CRM, and nobody's accountable.

**Emma:** For finance, the close is the big ask. Close is the monthly
process — we cut off the period, true up accruals, post journals back into
SAP. If data products have SLOs we can trust, I can automate half the
reconciliation.

**Me:** What are data products, in your words?

**Alice:** A data product is a first-class citizen — it has an owner, a
contract, an SLO, and a bill. If I'm consuming `customer.master_customer`,
I know who owns it, what it promises me, and what happens if it breaks.

**Emma:** "And a bill" — you're saying cost is attributed to the consumer?

**Alice:** Not at day one, but the platform will track consumption and
eventually yes, consumers pay. That changes the incentives.

**Carol:** I want to flag the customer / account holder / buyer language.
Sales Ops says "account holder" because Salesforce does. Product says
"buyer" from the commerce side. We need one word.

**Alice:** Customer. The mesh is B2C-centric for the current scope, so
customer wins.

**Carol:** Even for corporate accounts?

**Alice:** That's a separate concept — we can call it Account and keep it
distinct from Customer. Not in phase 1 scope.

**Me:** You said earlier every order has one customer — does that hold for
POS, where we don't always know who the customer is?

**Carol:** Good question. POS guest customers get a synthetic customer_id;
they're still a customer record, just a thin one.

**Alice:** Same on commerce for guest checkouts. Is_guest flag, light record,
upgraded if they register later.

---

**Decisions taken:**

- Five domains: customer, product, orders, inventory, fulfilment.
- Platform team runs shared infra and contract governance.
- Data products are first-class; contracts + SLOs required.
- "Customer" is the canonical term; "account holder" / "buyer" retire.

**Open questions parked:**

- B2B corporate case — Customer vs Account.
- Chargeback rate of cost attribution (phase 2).
- How domain teams coordinate breaking-change deprecation windows.
