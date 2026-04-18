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
