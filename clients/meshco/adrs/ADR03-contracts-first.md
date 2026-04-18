# ADR03: Contracts-first publishing for all data products

<!-- skhema:elements contracts, catalog, transforms -->
<!-- gnosis:concepts DataContract, DataProduct, ContractBreak, SLO -->

**Status:** Accepted
**Date:** 2026-04-18
**Deciders:** Alice Chen (Head of Platform), MeshCo Data Council

## Context

A mesh model is only as strong as its cross-domain interfaces. Without
explicit contracts, consuming teams build against implicit schemas, and
producer-side changes silently break downstream workloads. This is the
failure mode the central-data-team era already suffered from — repeating
it in a federated model would make things worse, not better.

## Decision

Every data product published on the platform must have:

1. A versioned contract checked in alongside the dbt/Spark code that
   produces it.
2. At least three SLOs: freshness, completeness, accuracy.
3. A published schema that matches the implementation.
4. Column-level lineage emitted via OpenLineage.

Contracts are validated at PR time via CI. Breaking changes (drop column,
type change, SLO relaxation) require a semver major bump and a deprecation
window proportional to subscriber count. Merging a breaking change without
the window is blocked in CI.

## Alternatives considered

### Contracts as optional / aspirational

- Pros: Lower adoption friction; domain teams move fast.
- Cons: Contracts that are optional are ignored. Six months in, the mesh
  becomes the central-team era with extra ceremony. This is the failure
  mode we're trying to avoid.

### Contracts at runtime (validation on every read)

- Pros: Detects drift the instant it happens.
- Cons: Adds per-query latency; producer errors surface at consume time,
  not at publish time (harder to attribute); doesn't catch schema drift
  until something downstream breaks.

## Consequences

- **Producer-side friction:** domain teams must learn contract authoring.
  The platform team ships a template and will pair on first contracts for
  each domain in the first four weeks.
- **PR-time failures:** CI will sometimes red on contract breaks. That's
  the point. No override path; exceptions require an explicit ADR.
- **Subscriber tracking:** the platform tracks data-product consumers via
  catalog queries and explicit subscriptions. Without this, breaking-change
  deprecation windows can't be sized.
- **Cost:** initial rollout of the contract-validation CI is ~2 engineer-
  weeks platform-side, plus ~0.5 weeks per domain team for onboarding.
- **Cultural payoff:** domain teams get a clear "done" signal (contract
  passes CI) and a clear accountability line (contract breaks = your bug).

## Links

- [Data contracts on the modern data stack](https://datacontract.com/)
- Related: ADR02 (dbt for transformations)
