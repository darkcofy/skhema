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
