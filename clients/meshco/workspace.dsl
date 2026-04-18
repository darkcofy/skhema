workspace "MeshCo Retail Data Platform" "Federated data platform supporting MeshCo's transition to a domain-owned data mesh model." {

    !identifiers hierarchical

    model {
        // ─── People ───────────────────────────────────────────────
        dataAnalyst   = person "Data Analyst"        "Queries curated data products via BI and SQL."
        mlEngineer    = person "ML Engineer"         "Builds and operates ML models against feature stores and lakehouse data."
        domainTeam    = person "Domain Team"         "Owns one or more data products (customer, product, orders, inventory, fulfilment)."
        platformTeam  = person "Platform Team"       "Runs shared platform infrastructure, catalog, and contract governance."
        financeUser   = person "Finance Business User" "Consumes dashboards and reports for monthly close and management reporting."

        // ─── External systems ─────────────────────────────────────
        pos      = softwareSystem "POS"             "Point-of-sale transactions from 820 stores." "External"
        ecom     = softwareSystem "Commerce"        "D2C commerce platform — customer orders and browsing telemetry." "External"
        erp      = softwareSystem "ERP"             "SAP ECC — financial and inventory source of truth." "External"
        crm      = softwareSystem "CRM"             "Salesforce — customer master data." "External"
        fulfilment = softwareSystem "Fulfilment"    "Third-party warehouse and last-mile fulfilment." "External"

        // ─── The data platform in focus ───────────────────────────
        platform = softwareSystem "MeshCo Data Platform" "Federated, mesh-oriented data platform." {

            ingestion  = container "Ingestion"            "CDC and event-stream ingestion from source systems"           "Debezium, Kafka, Fivetran"                     "Ingestion"
            lakehouse  = container "Lakehouse"            "Iceberg tables on S3 with Glue metastore; bronze/silver/gold zones" "Apache Iceberg, S3, AWS Glue"          "Lakehouse"
            transforms = container "Transformations"      "dbt projects producing silver + gold models"                  "dbt Core, Airflow"                              "Processing"
            semantic   = container "Semantic Layer"       "Business metrics and dimensions, exposed via SQL/GraphQL"     "Cube, dbt Semantic Layer"                       "Semantic"
            contracts  = container "Contract Registry"    "Data contract definitions, PR-time validation, and versioning" "GitHub + custom CI tooling"                   "Contracts"
            catalog    = container "Data Catalog"         "Discovery, column-level lineage, quality SLOs"                "Unity Catalog, OpenLineage"                     "Catalog"
            mlPlatform = container "ML Platform"          "Feature store, model registry, training, serving"             "Feast, MLflow, SageMaker"                       "MLPlatform"
            serving    = container "Serving Layer"        "BI connectors, ML endpoints, operational APIs"                "Cube API, FastAPI, SageMaker endpoints"         "Serving"
        }

        // ─── Source relationships ─────────────────────────────────
        pos        -> platform.ingestion "Streams transactions via CDC"
        ecom       -> platform.ingestion "Publishes order + clickstream events"
        erp        -> platform.ingestion "Daily batch extract + CDC for finance data"
        crm        -> platform.ingestion "Customer master nightly extract"
        fulfilment -> platform.ingestion "Posts shipment status webhooks"

        // ─── Internal data flow ───────────────────────────────────
        platform.ingestion  -> platform.lakehouse  "Writes raw + bronze Iceberg tables"
        platform.lakehouse  -> platform.transforms "Reads bronze; writes silver + gold"
        platform.transforms -> platform.semantic   "Populates metric and dimension models"
        platform.transforms -> platform.catalog    "Emits column-level lineage"
        platform.contracts  -> platform.transforms "Validates contracts at deployment time"
        platform.catalog    -> platform.contracts  "Surfaces contract violations in discovery UI"
        platform.lakehouse  -> platform.mlPlatform "Feature pipelines read silver/gold"
        platform.semantic   -> platform.serving    "BI dashboards query metrics"
        platform.mlPlatform -> platform.serving    "Exposes model endpoints"

        // ─── Consumer relationships ───────────────────────────────
        dataAnalyst  -> platform.serving    "Queries metrics and dashboards"
        financeUser  -> platform.serving    "Consumes management reports"
        mlEngineer   -> platform.mlPlatform "Trains and deploys models"
        domainTeam   -> platform.contracts  "Publishes data products with contracts"
        domainTeam   -> platform.lakehouse  "Materialises product tables"
        platformTeam -> platform.catalog    "Operates catalog + contract governance"
    }

    views {
        systemContext platform "context" "L1: MeshCo platform in its system context" {
            include *
            autolayout lr
        }

        container platform "containers" "L2: Containers inside the MeshCo data platform" {
            include *
            autolayout tb
        }

        styles {
            element "Person" {
                shape person
                background #1168bd
                color #ffffff
                fontSize 22
            }
            element "External" {
                background #8B8B8B
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                color #ffffff
            }
            element "Ingestion"  { background #D97706 }
            element "Lakehouse"  { background #0369A1 }
            element "Processing" { background #059669 }
            element "Semantic"   { background #7C3AED }
            element "Contracts"  { background #BE185D }
            element "Catalog"    { background #DC2626 }
            element "MLPlatform" { background #DB2777 }
            element "Serving"    { background #4338CA }
        }
    }
}
