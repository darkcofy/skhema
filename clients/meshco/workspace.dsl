workspace "MeshCo Retail Data Platform" "Federated data platform supporting MeshCo's transition to a domain-owned data mesh model." {

    !identifiers hierarchical

    model {
        // ─── People ───────────────────────────────────────────────
        dataAnalyst   = person "Data Analyst" "Queries curated data products via BI and SQL for MeshCo merchandising and marketing teams."
        mlEngineer    = person "ML Engineer"  "Builds and operates ML models against feature stores and lakehouse data (pricing, recommendations)."
        domainTeam    = person "Domain Team"  "Owns one or more data products across the five MeshCo domains (customer, product, orders, inventory, fulfilment)."
        platformTeam  = person "Platform Team" "Runs shared platform infrastructure, catalog governance, and contract tooling."
        financeUser   = person "Finance User" "Consumes dashboards and reports for monthly close and management reporting."
        aiAssistant   = person "AI Agent / Assistant" "Automated agent querying metrics and structured data via the MCP server (retail assistant, ops copilot)."

        // ─── External systems ─────────────────────────────────────
        pos        = softwareSystem "POS"        "Point-of-sale transactions from 820 stores (in-house, MySQL)." {
            tags "External"
        }
        ecom       = softwareSystem "Commerce"   "D2C commerce platform — customer orders, checkout, clickstream (Shopify Plus + Snowplow)." {
            tags "External"
        }
        erp        = softwareSystem "ERP"        "SAP ECC — financial and inventory source of truth." {
            tags "External"
        }
        crm        = softwareSystem "CRM"        "Salesforce — customer master data." {
            tags "External"
        }
        fulfilment = softwareSystem "Fulfilment" "Manhattan WMS plus third-party last-mile carriers." {
            tags "External"
        }
        bi         = softwareSystem "BI Platform" "Tableau + Looker — executive and operational dashboards." {
            tags "External"
        }
        bedrock    = softwareSystem "AWS Bedrock" "Managed foundation-model service — hosts Claude, Titan, and Llama models." {
            tags "External"
        }
        monteCarlo = softwareSystem "Monte Carlo" "Data observability SaaS — freshness, quality, and anomaly monitoring." {
            tags "External"
        }

        // ─── The data platform in focus ───────────────────────────
        platform = softwareSystem "MeshCo Data Platform" "Federated, mesh-oriented data platform with contracts, catalog, semantic layer, ML, and GenAI surfaces." {

            ingestion  = container "Ingestion"         "CDC, event-stream, and batch ingestion from source systems."              "Debezium, Kafka, Fivetran"                "Ingestion"
            lakehouse  = container "Lakehouse"         "Iceberg tables on S3 with Glue metastore — bronze, silver, gold zones."  "Apache Iceberg, S3, AWS Glue, Trino"      "Lakehouse"
            transforms = container "Transformations"   "dbt projects producing silver + gold data products from bronze tables." "dbt Core, Airflow"                         "Processing"
            semantic   = container "Semantic Layer"    "Business metrics and dimensions exposed via SQL / GraphQL / REST APIs." "Cube, dbt Semantic Layer"                  "Semantic"
            contracts  = container "Contract Registry" "Data contract definitions, PR-time validation, and versioning."         "GitHub + custom CI tooling"                "Contracts" {
                contracts_repo      = component "Contract Repository"       "Stores versioned contract YAML per data product."              "Git"
                contracts_validator = component "Contract Validator"         "Validates producer schema changes against published contracts." "Python, JSON Schema"
                contracts_ci_gate   = component "PR-Time CI Gate"           "GitHub Action that blocks merge on detected contract breaks."  "GitHub Actions"
                contracts_diff      = component "Breaking-Change Detector"  "Computes semantic diff against previous contract version."     "Python"
                contracts_subs      = component "Subscription Tracker"      "Tracks which consumers have subscribed to which contracts."   "Postgres"

                contracts_ci_gate -> contracts_validator "Runs on every PR"
                contracts_validator -> contracts_repo    "Reads current + proposed contracts"
                contracts_validator -> contracts_diff    "Delegates breaking-change analysis"
                contracts_validator -> contracts_subs    "Looks up active subscribers"
            }
            catalog    = container "Data Catalog" "Discovery, column-level lineage, quality SLOs, and contract-violation surfacing." "Unity Catalog, OpenLineage" "Catalog" {
                cat_discovery   = component "Discovery UI"          "Searchable web UI over all data products."                 "Unity Catalog"
                cat_lineage     = component "Lineage Service"        "Column-level lineage indexed from OpenLineage events."     "OpenLineage, Neo4j"
                cat_marketplace = component "Data Product Marketplace" "Subscription UI — browse, subscribe, and track SLOs."    "Unity Catalog UI"
                cat_policy      = component "Policy Engine"          "Row/column-level masking based on PII + consent tags."     "OPA, Lake Formation"
                cat_classifier  = component "PII Classification"     "Automated PII/PHI scanner tagging columns at ingest time." "Python + ML"

                cat_discovery -> cat_lineage
                cat_discovery -> cat_marketplace
                cat_policy -> cat_classifier
                cat_marketplace -> cat_lineage
            }
            observability = container "Data Observability" "Freshness, quality, and anomaly monitoring across the lakehouse + serving." "Monte Carlo, Great Expectations" "Observability"
            mlPlatform = container "ML Platform" "Feature store, model registry, training, serving, and drift monitoring." "Feast, MLflow, SageMaker" "MLPlatform"
            genai      = container "GenAI Gateway" "LLM inference proxy, RAG pipelines, vector search, and the MCP server for AI agents." "LiteLLM, Bedrock, pgvector, MCP" "GenAI" {
                genai_gateway    = component "LLM Gateway"            "Unified proxy over Bedrock Claude, Titan, and local Llama models." "LiteLLM"
                genai_prompts    = component "Prompt Registry"        "Versioned prompt templates and system prompts per use case."      "Git + Postgres"
                genai_rag        = component "RAG Pipeline"           "Retrieval-augmented generation orchestration."                     "LangChain, custom Python"
                genai_vector     = component "Vector Store"           "Embedding storage + similarity search for retail product copy, docs, and concepts." "pgvector on RDS"
                genai_guardrails = component "Guardrails Engine"       "Input/output filtering, PII detection, prompt-injection defence." "Python + policy rules"
                genai_eval       = component "Evaluation Framework"    "Offline + online eval suite for prompts and model responses."    "Braintrust, custom harness"
                genai_mcp        = component "MCP Server"             "Model Context Protocol server exposing MeshCo data products as tools to AI agents." "TypeScript + @modelcontextprotocol/sdk"
                genai_feedback   = component "Feedback Collector"      "Captures thumbs + corrections + edits from agents and humans."    "FastAPI + Postgres"

                genai_mcp -> genai_gateway        "Delegates LLM calls"
                genai_mcp -> genai_guardrails     "Passes every request through guardrails"
                genai_rag -> genai_vector         "Retrieves top-k passages"
                genai_rag -> genai_gateway        "Augmented prompt to the chosen LLM"
                genai_gateway -> genai_prompts    "Loads system prompt by template key"
                genai_guardrails -> genai_gateway "Denies / redacts via gateway"
                genai_feedback -> genai_eval      "Feeds online eval signals"
            }
            serving    = container "Serving Layer"     "BI connectors, ML endpoints, operational APIs."                          "Cube API, FastAPI, SageMaker endpoints"    "Serving"
        }

        // ─── Source relationships ─────────────────────────────────
        pos        -> platform.ingestion "Streams transactions via CDC"    "Debezium → Kafka"
        ecom       -> platform.ingestion "Publishes order + clickstream events" "Kafka + Snowplow SDK"
        erp        -> platform.ingestion "Daily batch extract + CDC for finance data" "SAP BW + Debezium"
        crm        -> platform.ingestion "Nightly customer extract"         "Fivetran"
        fulfilment -> platform.ingestion "Shipment status webhooks"         "HTTPS webhook"
        platform.serving -> erp "Reverse-ETL cohort and LTV back to SAP" "Hightouch"
        platform.serving -> bi  "Surfaces metrics to dashboards"         "SQL over Cube API"

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

        // ─── Observability ────────────────────────────────────────
        platform.lakehouse     -> platform.observability "Emits table-level freshness + quality signals"
        platform.transforms    -> platform.observability "Emits dbt test + run metadata"
        platform.mlPlatform    -> platform.observability "Emits model drift + skew signals"
        platform.observability -> monteCarlo             "Ships signals to Monte Carlo"
        platform.observability -> platform.catalog       "Posts incidents to the discovery UI"

        // ─── GenAI flows ──────────────────────────────────────────
        platform.genai -> bedrock            "Invokes Claude / Titan via boto3"
        platform.genai -> platform.semantic  "Reads metrics for natural-language questions"
        platform.genai -> platform.catalog   "Surfaces data-product context via the catalog"
        platform.genai -> platform.lakehouse "RAG over product copy, docs, and concept definitions"
        aiAssistant    -> platform.genai     "Invokes MCP tools on behalf of users"
        platform.genai -> platform.serving   "Agent responses return via the serving layer"

        // ─── Consumer relationships ───────────────────────────────
        dataAnalyst  -> platform.serving      "Queries metrics and dashboards"     "SQL via Cube"
        financeUser  -> bi                     "Consumes management reports"
        mlEngineer   -> platform.mlPlatform   "Trains and deploys models"          "SageMaker Studio"
        mlEngineer   -> platform.genai        "Builds agents + prompt templates"
        domainTeam   -> platform.contracts    "Publishes data products with contracts" "Git PR"
        domainTeam   -> platform.lakehouse    "Materialises product tables"        "dbt"
        domainTeam   -> platform.catalog      "Registers data products in the marketplace" "Marketplace UI"
        platformTeam -> platform.catalog      "Operates catalog + contract governance" "Web UI + Git"
        platformTeam -> platform.observability "Triages incidents and SLO breaches" "Monte Carlo UI"
        platformTeam -> platform.genai        "Operates LLM gateway + prompt governance" "Git + Admin UI"
    }

    views {

        systemLandscape "landscape" "L0: Everyone and everything in scope for the MeshCo mesh migration." {
            include *
            autolayout lr
        }

        systemContext platform "context" "L1: MeshCo Data Platform in its system context." {
            include *
            autolayout lr
        }

        container platform "containers" "L2: All ten containers inside the MeshCo Data Platform." {
            include *
            autolayout tb
        }

        component platform.contracts "contract-registry-components" "L3: Contract Registry internals — how contract breaks are detected at PR time." {
            include *
            autolayout tb
        }

        component platform.catalog "catalog-components" "L3: Data Catalog internals — discovery, lineage, marketplace, and policy enforcement." {
            include *
            autolayout tb
        }

        component platform.genai "genai-components" "L3: GenAI Gateway internals — LLM proxy, RAG, vector store, MCP server, and guardrails." {
            include *
            autolayout tb
        }

        dynamic platform "order-ingestion" "End-to-end flow: a POS order becomes a row in the orders.transactional_orders data product." {
            pos -> platform.ingestion "Order event emitted via CDC"
            platform.ingestion -> platform.lakehouse "Appends to bronze.pos_orders"
            platform.lakehouse -> platform.transforms "dbt runs silver + gold models"
            platform.transforms -> platform.contracts "Validates contract before publishing"
            platform.transforms -> platform.catalog "Emits column-level lineage for the new orders batch"
            platform.transforms -> platform.semantic "Populates orders metrics"
            dataAnalyst -> platform.serving "Queries orders dashboard"
            autolayout lr
        }

        dynamic platform "ai-assistant-query" "Dynamic: a natural-language question from the retail AI assistant resolves into a semantic-layer answer." {
            aiAssistant -> platform.genai "Asks: 'What were UK orders above £50 last week?'"
            platform.genai -> platform.catalog "Looks up data products tagged orders"
            platform.genai -> platform.semantic "Issues metric query against orders.gross_amount"
            platform.semantic -> platform.genai "Returns metric rows"
            platform.genai -> bedrock "Composes natural-language answer via Claude"
            bedrock -> platform.genai "Answer text"
            platform.genai -> aiAssistant "Returns answer + source links"
            autolayout lr
        }

        styles {
            element "Person" {
                shape person
                background #1168bd
                color #ffffff
                fontSize 22
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #8B8B8B
                color #ffffff
            }
            element "Container" {
                color #ffffff
            }
            element "Component" {
                background #facc15
                color #111111
            }
            element "Ingestion" {
                background #D97706
                color #ffffff
            }
            element "Lakehouse" {
                background #0369A1
                color #ffffff
            }
            element "Processing" {
                background #059669
                color #ffffff
            }
            element "Semantic" {
                background #7C3AED
                color #ffffff
            }
            element "Contracts" {
                background #BE185D
                color #ffffff
            }
            element "Catalog" {
                background #DC2626
                color #ffffff
            }
            element "Observability" {
                background #0891B2
                color #ffffff
            }
            element "MLPlatform" {
                background #DB2777
                color #ffffff
            }
            element "GenAI" {
                background #16A34A
                color #ffffff
            }
            element "Serving" {
                background #4338CA
                color #ffffff
            }
        }

        terminology {
            person "Role"
            softwareSystem "System"
            container "Container"
            component "Component"
            relationship "Uses"
        }
    }
}
