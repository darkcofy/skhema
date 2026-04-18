# ADR01: Apache Iceberg for the lakehouse table format

<!-- skhema:elements lakehouse, catalog -->
<!-- gnosis:concepts DataProduct, LineageEdge -->

**Status:** Accepted
**Date:** 2026-04-16
**Deciders:** Alice Chen (Head of Platform), Bob Murphy (Principal Data Engineer), MeshCo Data Council

## Context

MeshCo is adopting a data-mesh model requiring open, durable, cross-engine
table formats for its lakehouse layer. Three options were seriously
considered: Apache Iceberg, Delta Lake, and Apache Hudi. We need ACID
guarantees, time travel for audit, hidden partitioning to reduce consumer-
side toil, and interoperability with Snowflake (for BI), Databricks (for
some ML workloads), and ad-hoc Trino queries.

## Decision

Use **Apache Iceberg** as the canonical table format for all lakehouse data.
Use AWS Glue as the metastore for now, with a documented migration path to
Apache Polaris once it reaches GA.

## Alternatives considered

### Delta Lake

- Pros: Excellent Databricks integration; mature; Snowflake can read Delta
  natively via iceberg-compatible bridge.
- Cons: Commercial gravitational pull toward Databricks is at odds with a
  mesh architecture; community-owned Delta spec lags the Databricks-managed
  version; Polaris-equivalent story is weaker.

### Apache Hudi

- Pros: Best-in-class upsert performance; streaming-native; incremental
  query model.
- Cons: Smaller community and fewer third-party integrations; MeshCo's
  workload is append-dominant with rare upserts (identity resolution);
  operational burden higher than Iceberg.

## Consequences

- Iceberg's hidden partitioning removes partition-management toil from
  consumer code — a meaningful ergonomics win for domain teams.
- Snowflake's native Iceberg support becomes the primary cross-engine
  consumption path. Must validate at scale in PoC phase before committing
  BI workloads.
- Catalog choice (Glue → Polaris) is a separately-recorded decision — see
  ADR04.
- Time-travel queries enable regulatory-audit scenarios not previously
  supported.
- Migration cost from existing Parquet tables estimated at ~4 engineer-weeks,
  ring-fenced to the platform team.
- We lose some Databricks-specific tooling ergonomics. Acceptable; the mesh
  model de-emphasises tight coupling to any single compute engine.

## Links

- [Iceberg specification](https://iceberg.apache.org/spec/)
- Related: ADR04 (Catalog choice)
- Supersedes: informal "raw Parquet" baseline with no ACID guarantees
