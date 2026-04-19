# Terminology synonyms and conflicts

*Auto-generated from `01_language/synonym-conflicts.yaml` by `gnosis ingest synonyms`. Do not hand-edit — edit the YAML (or re-ingest) and this file will be regenerated.*

## Near-synonym: Metric / Measure

- **Terms used:** metric, measure
- **Used by:**
  - "metric" — Dave Kim, Emma Ward
  - "measure" — Dave Kim
- **Evidence of same meaning:**
  - Dave Kim (2026-05-05): "Today nobody draws the line. 'Metric' and 'measure' are used interchangeably, including by me on bad days."
- **Evidence of different meaning:**
  - Dave Kim (2026-05-05): "A metric is a measure plus context: grain, filters, business meaning. 'Weekly active customers' is a metric. 'Count distinct of customer_id' is a measure."
  - Emma Ward (2026-05-04): "Dave owns the how. I own the what."
- **Type:** near-synonym
- **Severity:** high
- **Rationale:** Today used interchangeably, but Dave explicitly wants them modelled as distinct concepts (Measure = SQL primitive; Metric = business deliverable with grain/filter/owner). Must resolve before stage-2 concept modelling.
- **Open questions:**
  - Do we formalise the split now, knowing current usage is sloppy? Or document current usage and mark the intended split as a stage-5 formalisation decision?
  - Does "Metric" subsume MetricDefinition, or are they separate concepts (metric = idea; metric definition = contract-backed artefact)?

## Near-synonym: Data Product / Metric Definition

- **Terms used:** data product, metric definition
- **Used by:**
  - "data product" — Alice Chen, Bob Murphy
  - "metric definition" — Dave Kim
- **Evidence of same meaning:**
  - Alice Chen (2026-04-16): "A data product is a first-class citizen — it has an owner, a contract, an SLO, and a bill."
  - Dave Kim (2026-05-05): "The metric definition IS a data product, in my view — it has an owner, a schema (grain + dimensions), an SLO, a contract."
- **Type:** near-synonym
- **Severity:** medium
- **Proposed canonical:** data product — Dave argues metric definitions should be a sub-class of data product with the same contract mechanics. Treating them as peers would create duplicate ownership and SLO machinery.
- **Open questions:**
  - Is MetricDefinition a specialisation of DataProduct (inheritance) or just a labelled instance (tagging)?

## Homonym: Finance Feed (dataset) vs Finance Feed (retired service)

- **Terms used:** finance feed
- **Used by:**
  - "finance feed" — Emma Ward
- **Evidence of different meaning:**
  - Emma Ward (2026-05-04): "It used to be a system — there was a service called FinanceFeed back in 2019 — but we decommissioned the service and now it's just the thing we call the outbound-to-SAP curated dataset."
- **Type:** homonym
- **Severity:** low
- **Proposed canonical:** finance feed — Emma disambiguates in-session: the service is retired, the name carried over to the dataset. Documenting the homonym for newcomers so old runbooks don't cause confusion. No model change needed.
