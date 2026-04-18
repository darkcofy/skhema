# Terminology Conflict Report

*Auto-generated from synonym-conflicts.md.*

# Terminology synonyms and conflicts — MeshCo

## Capture

## Synonym: Customer / Account Holder / Buyer

- **Terms used:** customer, account holder, buyer
- **Used by:**
  - "customer" — Carol Singh (Customer Domain Lead), platform team
  - "account holder" — Sales Ops team (from Salesforce language), Finance
  - "buyer" — Product team (commerce-platform language)
- **Evidence of same meaning:**
  - Carol: "Every order has one customer" (2026-04-16)
  - Sales Ops: "Account holder is the person the Salesforce record is against" (2026-04-16)
  - Product: "Buyers are who place orders on the web" (2026-04-17)
- **Evidence of possible distinction:**
  - Corporate B2B orders: the buyer (person clicking) may differ from the account holder (entity billed). This case currently has no canonical model.
- **Type:** near-synonym
- **Severity:** high — load-bearing for cross-domain data products
- **Proposed canonical:** Customer (most-used across domains, and already canonical in the customer domain)
- **Open questions:**
  - B2B: should we model Buyer and AccountHolder as distinct concepts, or collapse into Customer with a sub-type?

## Homonym: Order

- **Terms used:** order
- **Used by:**
  - Commerce team uses "order" for a shopping-cart checkout (one basket)
  - POS team uses "order" for a single-receipt purchase (one in-store visit)
  - ERP uses "order" for a purchase order (supplier-side) which is completely unrelated
- **Evidence of different meaning:**
  - Commerce: "Orders go through auth, capture, and fulfilment"
  - POS: "Every order at the till is a new order"
  - ERP: "Purchase orders are raised against suppliers for stock"
- **Type:** homonym — same word, three different concepts
- **Severity:** high — must be namespaced or renamed to avoid corrupting the cross-domain model
- **Proposed resolution:** `CustomerOrder` (commerce + POS unified), `PurchaseOrder` (ERP, supplier-side). Rename `CustomerOrder` to just `Order` within the retail-customer domain if namespacing is clear.

## Synonym: Data Product / Data Set / Feed

- **Terms used:** data product, data set, feed
- **Used by:**
  - Platform team: "data product"
  - Legacy central-data team: "data set" (table in the warehouse)
  - Domain engineering: "feed" (for real-time streams)
- **Evidence of same meaning:**
  - Alice: "A data set is just what we used to call a data product before we had contracts" (2026-04-16)
  - Bob: "Feeds are data products too — real-time ones" (2026-04-17)
- **Type:** synonym (retirement candidate)
- **Severity:** medium — will resolve naturally as mesh terminology takes hold; must not appear in new artefacts
- **Proposed canonical:** Data Product. Deprecate "data set" and "feed" in any new documentation.
- **Open questions:**
  - Do we retain "feed" for the streaming sub-type, or collapse everything under Data Product with a delivery-mode attribute?

## Near-synonym: Lineage / Provenance

- **Terms used:** lineage, provenance
- **Used by:**
  - Platform team: "lineage"
  - Compliance team: "provenance" (regulatory language)
- **Evidence:**
  - Bob: "We track lineage column-by-column" (2026-04-17)
  - Compliance: "We need provenance for the audit trail" (2026-04-18)
- **Type:** near-synonym — overlapping but not identical. Provenance typically includes *who did what* (auditability), lineage is primarily *where data came from* (tracing).
- **Severity:** low — both will coexist; worth noting that they're not interchangeable
- **Proposed resolution:** Keep both. Lineage for technical flow, provenance for audit trail. Document the distinction in the glossary.

