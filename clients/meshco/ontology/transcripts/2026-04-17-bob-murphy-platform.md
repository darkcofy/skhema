# Bob Murphy — Principal Data Engineer, Platform team — 2026-04-17

**Me:** Walk me through the platform stack as you see it.

**Bob:** Ingestion is CDC — Debezium on the MySQL replicas for POS, direct
Kafka for commerce events, Fivetran for CRM because Salesforce is a pain to
source directly. Everything lands in the lakehouse.

**Me:** Which format?

**Bob:** Iceberg. We had Delta for a hot second when someone was Databricks-
curious, but we ripped it out. Iceberg plus Glue for the metastore. Polaris
when it's ready.

**Me:** Medallion architecture?

**Bob:** Bronze, silver, gold. Bronze is raw-but-type-safe CDC output. Silver
is joined, deduplicated, with identity resolution applied. Gold is business-
facing — that's where data products live.

**Me:** Transformations?

**Bob:** dbt Core, orchestrated by Airflow. Silver and gold both in dbt. We
piloted SQLMesh but the team skills are dbt so we stuck. Maybe revisit in 18
months.

**Me:** Lineage?

**Bob:** OpenLineage emits from dbt and the ingestion jobs. Column-level —
table-level is useless for impact analysis. If a column changes upstream I
want to see every downstream column that depends on it.

**Me:** What about quality?

**Bob:** dbt tests at the data-product boundary. Plus a data-contract
validator that runs at PR time — if you change the schema or tighten an SLO
in a way that breaks consumers, the PR can't merge. That's enforced in CI.

**Me:** Catalog?

**Bob:** Unity Catalog for discovery and lineage display. It's not perfect
but it's the least-bad commercial option.

**Me:** What's the hardest part of the migration?

**Bob:** Two things. First, contracts — getting domain teams to actually
write them and keep them versioned. We're forcing it via CI but culturally
it's a lift. Second, SLO enforcement — what happens when a data product
misses its freshness SLO? Who gets paged? That policy doesn't exist yet.

**Me:** Contract break — define it.

**Bob:** A change to a producer's data product that violates its published
contract. Drop column, change type, loosen SLO. Anything a consumer was
legitimately relying on.

**Me:** Detected where?

**Bob:** PR time. We diff the new contract against the previous version, and
against real usage from the catalog. If a consumer subscribes to a column
you're about to drop, CI goes red.

**Me:** Medallion, EOD, CDC — you're throwing acronyms. Let's glossary
them.

**Bob:** EOD is end of day, daily batch cut-off. Typically midnight UTC.
Medallion is just the bronze/silver/gold convention. CDC is change data
capture — streaming source DB mutations.
