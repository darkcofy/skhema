# ADR06: Monte Carlo for data observability

<!-- skhema:elements observability, catalog -->
<!-- gnosis:concepts DataProduct, SLO, LineageEdge -->

**Status:** Accepted
**Date:** 2026-04-19
**Deciders:** Alice Chen (Head of Platform), Bob Murphy, Monte Carlo sales

## Context

Data contracts + SLOs are only as real as the system watching them.
Without runtime observability we'd have contract validation at deploy
time but no way to know a data product is silently late, incomplete, or
drifting in production. Three options considered: Monte Carlo, Anomalo,
rolling our own.

## Decision

Adopt **Monte Carlo** as the primary data observability platform,
retaining **Great Expectations** for in-flight dbt-level assertions.

## Alternatives considered

### Anomalo

- Pros: Strong anomaly-detection ML; clean UI.
- Cons: Smaller integration footprint; less mature Unity Catalog +
  OpenLineage integration.

### Build our own (Airflow alerts + dbt test metadata)

- Pros: Zero licensing cost, full control.
- Cons: 2–3 engineer-quarters of platform-team time to reach feature
  parity; ongoing maintenance drag; nobody's core competence.

## Consequences

- **Contract SLO breaches surface automatically.** If `orders.transactional_orders`
  misses its D+1 09:00 UTC completeness SLO, the Observability container
  posts an incident to the Catalog and Monte Carlo pages the on-call
  domain team.
- **Model drift monitoring** runs on top of the ML Platform's predictions;
  Monte Carlo subscribes to feature-store updates and flags skew.
- **Catalog integration:** incidents surface as badges in the discovery
  UI, so consumers browsing a data product see open issues without
  leaving the catalog.
- **Cost:** ~$40k/year at the committed scale (10 domains, ~80 data
  products). Tracks with platform engagement ROI on close-automation alone.
- **Vendor risk:** Monte Carlo is a SaaS; the data it sees is metadata +
  sampled statistics, not content. Existing EY vendor review confirms it
  meets data-residency requirements.

## Links

- [Monte Carlo](https://www.montecarlodata.com/)
- [Great Expectations](https://greatexpectations.io/)
- Related: ADR03 (Contracts-first), ADR04 (Unity Catalog)
