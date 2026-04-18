# Concept definitions — MeshCo

Authoritative prose definitions for each candidate concept. The YAML in
`candidate-concepts.yaml` is the index; this file holds the full definitions,
examples, and known edge cases.

## Capture

## Customer

A person or organisation that transacts with MeshCo.

**Canonical identifier:** `customer_id` — a stable UUID assigned once at
golden-record creation and never reused. Stored in the customer-domain
`master_customer` data product.

**Identity resolution:** multiple source systems have their own identifiers
(POS customer number, Salesforce account ID, commerce email) which are merged
into one golden record via the identity-resolution service. Merges are
recorded; splits are (currently) a manual ops process.

**Edge cases:**

- B2B corporate orders: the Account (the entity billed) and the Customer (the
  person who places the order) may differ. Open question — may require splitting
  into Customer and Account as distinct concepts.
- Guest checkouts on commerce: create a lightweight Customer record with
  `is_guest = true` and no verified identity; promoted to a full record when
  the guest later registers.

## Order

A customer's purchase intent — one basket of one or more products at one point
in time, across any channel (POS till, commerce web, commerce app).

**Canonical identifier:** `order_id` — UUID per order, generated at order
creation. POS and commerce systems each have their own native IDs, mapped to
this canonical ID by the orders-domain ingestion.

**Distinct from:** ERP's `PurchaseOrder` (supplier-side). The two share the
word "order" but mean different things — see `synonym-conflicts.md`.

**Edge cases:**

- Abandoned carts: captured as Orders in state `abandoned`, never reach
  `captured`.
- Order splits: an order can be fulfilled as multiple shipments (common for
  split-stock orders).

## DataProduct

A curated, owned, SLO-backed dataset exposed to consumers via a versioned
contract. The unit of ownership, governance, and consumption in the mesh.

**Required attributes** (from the platform team's publishing checklist):

- Owner (a Domain)
- Contract version
- At least three SLOs: freshness, completeness, accuracy
- A published schema
- Column-level lineage back to its sources

**Example data products:**

- `customer.master_customer` — the golden-record customer view
- `orders.transactional_orders` — unified commerce + POS orders
- `product.catalog_current` — SKUs with current price and availability
- `fulfilment.shipment_status` — shipment lifecycle states

**Lifecycle:** `draft → published → deprecated → retired`. See stage 4
(behaviour) for full lifecycle semantics.

## DataContract

A producer-consumer agreement capturing a data product's schema, semantics,
freshness, and quality guarantees; validated at deployment time via CI.

A breaking change (drop column, type change, SLO relaxation) requires a major
version bump and a deprecation window.

**Versioning:** semver — `<major>.<minor>.<patch>`. Major = breaking; minor =
additive column or looser constraint; patch = documentation or internal
refactor.

## DataProduct Lifecycle Example

1. Domain team opens a PR adding a new data product definition.
2. CI validates: contract is valid, SLOs are stated, schema matches the
   implementation.
3. On merge: data product is registered in the catalog.
4. Consumers subscribe via the marketplace UI; subscription is tracked.
5. Producer changes must be compatible with the contract; breaking changes
   require a deprecation window proportional to subscriber count.
6. Retirement requires sign-off from all subscribers.
