# ADR02: dbt Core for the silver and gold transformation layers

<!-- skhema:elements transforms, catalog, semantic -->
<!-- gnosis:concepts DataProduct, DimensionalModel -->

**Status:** Accepted
**Date:** 2026-04-16
**Deciders:** Alice Chen (Head of Platform), Dave Kim (Analytics Engineering Lead), Bob Murphy

## Context

We need a SQL-centric transformation framework supporting tests,
documentation, lineage emission, and cross-team contribution. Analytics
Engineering has 2 years of dbt experience; Data Engineering has been
piloting SQLMesh for 6 months.

## Decision

Adopt **dbt Core** for the silver and gold layers of the lakehouse.
Orchestrate via Airflow. Expose metrics to downstream via the dbt Semantic
Layer, feeding Cube at the serving edge.

## Alternatives considered

### SQLMesh

- Pros: Stronger Python integration; virtual environments for dev/staging;
  model-level versioning; plan/apply semantics familiar to IaC-trained
  engineers.
- Cons: Smaller community and ecosystem; steeper learning curve for the
  existing dbt-trained analytics engineering team; revisit in 18 months is
  cheap, adopting now is expensive.

### Pure Spark / Scala transforms

- Pros: Performance for heavy feature generation.
- Cons: Overkill for the silver/gold layer; Python-dominant team; not
  SQL-testable in the same way.

## Consequences

- Existing dbt skills carry over; analytics engineer onboarding is faster.
- We lose SQLMesh's virtual environment ergonomics. Acceptable for now;
  we'll revisit in 18 months with more experience.
- dbt's OpenLineage emission becomes the lineage backbone. No separate
  lineage tool needed for the Transformations → Catalog path.
- Domain teams must learn dbt model conventions. The platform team will
  publish a starter template and review first PRs for each domain.
- dbt's weakness on streaming transforms is acceptable — streaming lives
  in the Ingestion container, not Transformations.

## Links

- [dbt Core](https://docs.getdbt.com/)
- [dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl)
- Related: ADR03 (Contracts-first data product publishing)
