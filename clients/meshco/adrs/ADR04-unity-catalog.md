# ADR04: Unity Catalog for discovery, lineage, and governance

<!-- skhema:elements catalog, contracts -->
<!-- gnosis:concepts DataProduct, LineageEdge, DataContract -->

**Status:** Accepted
**Date:** 2026-04-18
**Deciders:** Alice Chen, Bob Murphy

## Context

The mesh requires a unified surface for data-product discovery, column-level
lineage, contract violation reporting, and policy-based access. Four
options were considered: Unity Catalog, DataHub, Atlan, and Collibra.

## Decision

Adopt **Unity Catalog** as the primary catalog + lineage surface. Emit
lineage via OpenLineage from dbt and the ingestion layer.

## Alternatives considered

### DataHub

- Pros: Open source, large community, strong lineage visualisation.
- Cons: Self-managed operational burden; commercial support (Acryl) is
  still young; policy enforcement story weaker than Unity.

### Atlan

- Pros: Strong UX, good governance-driven workflows.
- Cons: Commercial SaaS; cost scales with asset count; less developer-
  friendly for the analytics engineering team.

### Collibra

- Pros: Enterprise-grade; strong compliance story.
- Cons: Heavy, enterprise-centric; overkill for MeshCo's current scale;
  UX doesn't match the developer-first culture.

## Consequences

- **Catalog-as-governance:** Unity's policy primitives become the enforcement
  layer for PII-tagged columns. This is a meaningful upside over DataHub.
- **Vendor lock:** Unity is Databricks-managed. We mitigate by keeping the
  metadata portable (we own the dbt-emitted OpenLineage JSON) — if we need
  to switch, we're not trapped.
- **OpenLineage emission:** required from dbt (already supported) and the
  ingestion jobs (custom work, ~1 engineer-week).
- **Contract-break surfacing:** Contract Registry writes violation records
  that Unity displays in the asset detail view. Unity doesn't block access
  on violations — that remains the Contract Registry's CI-gate job.
- **Access control policy:** Unity's row-level and column-level masking
  becomes the PII-enforcement layer; see future ADR on the policy model.

## Links

- [Unity Catalog](https://www.unitycatalog.io/)
- [OpenLineage](https://openlineage.io/)
- Related: ADR01 (Iceberg lakehouse), ADR03 (Contracts-first publishing)
