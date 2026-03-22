# Analytics Platform

The analytics platform follows a medallion architecture pattern with real-time and batch ingestion paths converging in a shared data lake.

**Data flow:**
- **Real-time path:** Kafka → Stream Processor → Data Lake (raw zone, Parquet)
- **Batch path:** Batch ETL → Data Lake (daily extracts from operational systems)
- **Transform:** Data Lake → dbt → Data Warehouse (Snowflake, dimensional models)
- **Serve:** Data Warehouse → BI Platform (dashboards and reports)

**Data quality:** Great Expectations runs validation checks after every dbt transformation. Failures block promotion to the serving layer. OpenLineage tracks end-to-end data lineage for audit and debugging.
