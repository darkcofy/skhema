# Open questions — language and vocabulary

## Capture

1. **B2B customer modelling:** Should Buyer and AccountHolder be distinct
   concepts in the customer domain, or collapsed into Customer with a sub-type
   attribute? [Carol, Sales Ops]

2. **Order namespace:** Can we rename the ERP "order" to PurchaseOrder
   universally, or is that vocabulary too entrenched with ERP users to change?
   [Emma Ward, ERP team]

3. **Feed vs data product:** Do we retain "feed" for streaming data products,
   or collapse under one Data Product concept with delivery-mode attribute?
   [Bob Murphy]

4. **Shipment vs delivery:** Fulfilment uses both interchangeably — is there
   a meaningful distinction (shipment = physical movement, delivery = customer
   receipt)? [Supply Chain]

5. **Product vs SKU:** When Carol says "product", she sometimes means the
   marketing-level product and sometimes the SKU. Need to disambiguate before
   the product-domain data product is modelled. [Carol, Product team]

6. **Lineage vs provenance:** Documented distinction (lineage = technical
   flow, provenance = audit/who-did-what). Confirm compliance team is
   comfortable with this split or whether provenance needs a distinct artifact.
   [Compliance]

7. **"Master" prefix on data products:** Customer domain wants to publish
   `master_customer`; the platform team's convention is noun-first. Does the
   "master" prefix survive, or do we rename to `customer_canonical`? [Carol,
   Platform team]
