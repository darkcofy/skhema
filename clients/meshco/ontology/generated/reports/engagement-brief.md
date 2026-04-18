# Engagement Brief

*Auto-generated from ontology workspace scope files.*

## Scope

# MeshCo Engagement Brief

## domain

Retail Data Mesh — MeshCo is migrating from a monolithic, central-data-team
model to a federated data mesh where five business domains (customer, product,
orders, inventory, fulfilment) own their data products and publish them against
shared platform infrastructure.

## outcomes

By end of engagement (8 weeks):

1. A target-state architecture captured in Structurizr DSL, signed off by the
   Data Council and the five domain leads.
2. A canonical domain ontology covering the ~15 concepts that span two or more
   domains (e.g. Customer, Order, Product, Shipment).
3. Four "lighthouse" data products published end-to-end through the platform
   with contracts, SLOs, and lineage.
4. Documented migration playbook for onboarding remaining domains in Q3/Q4.

## out_of_scope

- Operational migration timeline and staffing plans (covered separately by the
  delivery team).
- Vendor selection for net-new tooling (ML Platform and Observability vendors
  are both TBD and will be addressed in a follow-on engagement).
- GDPR/privacy review of customer data flows (handled by MeshCo's internal
  compliance team in parallel).
- Any retail-specific regulatory work (PCI compliance for POS ingestion stays
  with MeshCo Platform Security).

## Stakeholders

| Name | Role |
|------|------|
| Alice Chen | Head of Data Platform |
| Bob Murphy | Principal Data Engineer |
| Carol Singh | Customer Domain Lead |
| Dave Kim | Analytics Engineering Lead |
| Emma Ward | Head of Finance Systems |
| TBD | ML Platform Lead |

## Success Criteria

# Success Criteria — MeshCo Data Mesh Engagement

The engagement is successful if, by the end of week 8:

1. **Architecture sign-off** — Target-state architecture captured in
   `workspace.dsl`, reviewed and approved by the Data Council and all five
   domain leads.
2. **Canonical ontology** — Domain ontology covering the ~15 cross-domain
   concepts (Customer, Order, Product, Shipment, etc.) is published and all
   stakeholders have acknowledged it as the reference vocabulary.
3. **Four lighthouse data products** — Live on the platform with contracts,
   SLOs, and column-level lineage visible in the catalog:
   - `customer.master_customer`
   - `orders.transactional_orders`
   - `product.catalog_current`
   - `fulfilment.shipment_status`
4. **Contract-break detection** — PR-time contract diff and breaking-change
   detection demonstrated to produce red/green CI status on the lighthouse
   data products.
5. **Migration playbook** — One-page playbook signed off by the platform team
   for onboarding the remaining domains (marketing, supply, pricing) in Q3/Q4.

The engagement is *not* successful if:

- Any of the above remain open or vetoed after sign-off sessions.
- Major stakeholders (particularly Emma Ward and the Data Council) feel the
  mesh model is a retrofit of the existing central estate rather than a genuine
  federation.
- The "lighthouse" data products are demo-only and cannot be consumed by live
  production workloads.

