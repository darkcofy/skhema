# Arch-Diagrams Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers-extended-cc:subagent-driven-development (if subagents available) or superpowers-extended-cc:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a version-controlled, AI-agent-friendly PlantUML/C4 architecture diagram system with reusable model primitives, Kroki rendering, and validation.

**Architecture:** Three-layer system (foundation → model → view) where `lib/` provides theme and macros, `models/` defines reusable C4 elements as procedures, and `diagrams/` composes thin view files. Python scripts handle rendering via Kroki API and linting.

**Tech Stack:** PlantUML, C4-PlantUML, Python 3 (stdlib only — no pip dependencies), Kroki public API, YAML

---

### Task 0: Repo Scaffolding

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: empty directories via `.gitkeep` files

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Rendered output (reproducible from source)
rendered/

# Python
__pycache__/
*.pyc

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
```

- [ ] **Step 2: Create directory structure with `.gitkeep` files**

Create empty dirs that git would otherwise ignore:
```
diagrams/c4/.gitkeep
diagrams/sequence/.gitkeep
diagrams/erd/.gitkeep
diagrams/deployment/.gitkeep
rendered/.gitkeep  (NOTE: this won't be tracked due to .gitignore — skip it)
prompts/examples/.gitkeep
```

- [ ] **Step 3: Create `README.md`**

```markdown
# arch-diagrams

Version-controlled enterprise architecture diagrams using PlantUML + C4-PlantUML, rendered via Kroki API.

## Quick Start

```bash
# Render a single diagram
python scripts/render.py diagrams/c4/data-platform-context.puml

# Render all diagrams
python scripts/render.py --all

# Validate all files
python scripts/validate.py

# Dry-run (see resolved source without rendering)
python scripts/render.py diagrams/c4/data-platform-context.puml --dry-run
```

## Architecture

Three-layer system:

- **`lib/`** — Foundation layer: theme colours, macros, shared styling
- **`models/`** — Model layer: reusable C4 element definitions (one file per domain)
- **`diagrams/`** — View layer: thin files that compose models into specific views

See `docs/superpowers/specs/2026-03-22-arch-diagrams-design.md` for full design spec.

## Conventions

- Element IDs: `snake_case`
- File names: `kebab-case`
- Theme variables set BEFORE C4 include
- Elements defined ONCE in model layer, never in view files
- AI agents: read `manifest.yaml` first, then load relevant model files
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md diagrams/ prompts/
git commit -m "scaffold: repo structure with gitignore and README"
```

---

### Task 1: Foundation Layer — Theme

**Files:**
- Create: `lib/theme.puml`

- [ ] **Step 1: Create `lib/theme.puml`**

This is the validated theme from our prototyping (v6). Variables MUST be set before any C4 include.

```plantuml
' ============================================================
' arch-diagrams theme — Yellow & White palette
' USAGE: !include this file BEFORE the C4 library include
' ============================================================

' --- Persons ---
!$PERSON_BG_COLOR = "#FDE68A"
!$PERSON_FONT_COLOR = "#333333"
!$PERSON_BORDER_COLOR = "#D97706"

' --- Systems ---
!$SYSTEM_BG_COLOR = "#FEF3C7"
!$SYSTEM_FONT_COLOR = "#333333"
!$SYSTEM_BORDER_COLOR = "#D97706"

' --- Containers ---
!$CONTAINER_BG_COLOR = "#FEF3C7"
!$CONTAINER_FONT_COLOR = "#333333"
!$CONTAINER_BORDER_COLOR = "#D97706"

' --- Container DBs ---
!$CONTAINER_DB_BG_COLOR = "#FCD34D"
!$CONTAINER_DB_FONT_COLOR = "#333333"
!$CONTAINER_DB_BORDER_COLOR = "#B45309"

' --- Components ---
!$COMPONENT_BG_COLOR = "#FEF9C3"
!$COMPONENT_FONT_COLOR = "#333333"
!$COMPONENT_BORDER_COLOR = "#CA8A04"

' --- External Persons ---
!$EXTERNAL_PERSON_BG_COLOR = "#F5F5F4"
!$EXTERNAL_PERSON_FONT_COLOR = "#666666"
!$EXTERNAL_PERSON_BORDER_COLOR = "#A8A29E"

' --- External Systems ---
!$EXTERNAL_SYSTEM_BG_COLOR = "#F5F5F4"
!$EXTERNAL_SYSTEM_FONT_COLOR = "#666666"
!$EXTERNAL_SYSTEM_BORDER_COLOR = "#A8A29E"

' --- External Containers ---
!$EXTERNAL_CONTAINER_BG_COLOR = "#F5F5F4"
!$EXTERNAL_CONTAINER_FONT_COLOR = "#666666"
!$EXTERNAL_CONTAINER_BORDER_COLOR = "#A8A29E"

' --- External Components ---
!$EXTERNAL_COMPONENT_BG_COLOR = "#F5F5F4"
!$EXTERNAL_COMPONENT_FONT_COLOR = "#666666"
!$EXTERNAL_COMPONENT_BORDER_COLOR = "#A8A29E"

' --- Relationships ---
!$REL_TEXT_COLOR = "#78716C"
!$REL_LINE_COLOR = "#92400E"

' --- Boundaries ---
!$BOUNDARY_COLOR = "#D97706"
!$BOUNDARY_BG_COLOR = "#FFFBEB"

' --- Skinparams (applied after C4 include) ---
' These are defined as a procedure so views can call them after the C4 include
!procedure $ApplySkinparams()
  skinparam backgroundColor #FFFFFF
  skinparam defaultFontName "Segoe UI", Arial, sans-serif
  skinparam defaultFontSize 12
  skinparam legend {
    BackgroundColor #FFFBEB
    BorderColor #D97706
    FontColor #333333
    FontSize 11
  }
!endprocedure
```

- [ ] **Step 2: Commit**

```bash
git add lib/theme.puml
git commit -m "feat: add foundation theme with yellow/white C4 palette"
```

---

### Task 2: Foundation Layer — Macros

**Files:**
- Create: `lib/macros.puml`

- [ ] **Step 1: Create `lib/macros.puml`**

```plantuml
' ============================================================
' arch-diagrams shared macros
' USAGE: !include after lib/theme.puml and C4 library
' ============================================================

' Force left-to-right layout
!procedure $LayoutLR()
  left to right direction
!endprocedure

' Domain boundary with consistent styling
!procedure $DomainBoundary($alias, $label)
  Boundary($alias, $label, "Domain")
!endprocedure

' Styled note attached to an element
!procedure $Note($alias, $text)
  note right of $alias
    $text
  end note
!endprocedure
```

- [ ] **Step 2: Commit**

```bash
git add lib/macros.puml
git commit -m "feat: add shared macros for layout and boundaries"
```

---

### Task 3: Model Layer — Consumers & Ingestion

**Files:**
- Create: `models/consumers.puml`
- Create: `models/ingestion.puml`

- [ ] **Step 1: Create `models/consumers.puml`**

```plantuml
' ============================================================
' Domain: Consumers — people and external actors
' ============================================================

!procedure $DataAnalyst()
  Person(data_analyst, "Data Analyst", "Queries data via BI/SQL tools")
!endprocedure

!procedure $DataEngineer()
  Person(data_engineer, "Data Engineer", "Builds and maintains pipelines")
!endprocedure

!procedure $DataScientist()
  Person(data_scientist, "Data Scientist", "Builds models, explores data")
!endprocedure

!procedure $BusinessUser()
  Person(business_user, "Business User", "Consumes reports and dashboards")
!endprocedure

!procedure $ExternalSystem()
  System_Ext(external_system, "External System", "System outside the boundary")
!endprocedure
```

- [ ] **Step 2: Create `models/ingestion.puml`**

```plantuml
' ============================================================
' Domain: Ingestion — how data gets in
' ============================================================

!procedure $ApiGateway()
  Container(api_gateway, "API Gateway", "Technology TBD", "Entry point for API-based ingestion")
!endprocedure

!procedure $EventStream()
  Container(event_stream, "Event Stream", "Technology TBD", "Real-time event ingestion")
!endprocedure

!procedure $BatchEtl()
  Container(batch_etl, "Batch ETL", "Technology TBD", "Scheduled batch data extraction")
!endprocedure

!procedure $CdcPipeline()
  Container(cdc_pipeline, "CDC Pipeline", "Technology TBD", "Change data capture from source DBs")
!endprocedure

!procedure $FileDrop()
  Container(file_drop, "File Drop", "Technology TBD", "SFTP/S3/blob file-based ingestion")
!endprocedure
```

- [ ] **Step 3: Commit**

```bash
git add models/consumers.puml models/ingestion.puml
git commit -m "feat: add consumer and ingestion model primitives"
```

---

### Task 4: Model Layer — Storage & Processing

**Files:**
- Create: `models/storage.puml`
- Create: `models/processing.puml`

- [ ] **Step 1: Create `models/storage.puml`**

```plantuml
' ============================================================
' Domain: Storage — where data lives
' ============================================================

!procedure $DataLake()
  ContainerDb(data_lake, "Data Lake", "Technology TBD", "Raw + curated zones")
!endprocedure

!procedure $DataWarehouse()
  ContainerDb(data_warehouse, "Data Warehouse", "Technology TBD", "Dimensional models, governed data")
!endprocedure

!procedure $OperationalDb()
  ContainerDb(operational_db, "Operational DB", "Technology TBD", "Transactional/operational database")
!endprocedure

!procedure $ObjectStore()
  ContainerDb(object_store, "Object Store", "Technology TBD", "Unstructured blob/file storage")
!endprocedure

!procedure $CacheLayer()
  Container(cache_layer, "Cache Layer", "Technology TBD", "Low-latency cache")
!endprocedure
```

- [ ] **Step 2: Create `models/processing.puml`**

```plantuml
' ============================================================
' Domain: Processing — how data moves and transforms
' ============================================================

!procedure $EltPipeline()
  Container(elt_pipeline, "ELT Pipeline", "Technology TBD", "Extract-load-transform pipeline")
!endprocedure

!procedure $StreamProcessor()
  Container(stream_processor, "Stream Processor", "Technology TBD", "Real-time stream processing")
!endprocedure

!procedure $Orchestrator()
  Container(orchestrator, "Orchestrator", "Technology TBD", "Workflow orchestration")
!endprocedure

!procedure $DbtTransform()
  Container(dbt_transform, "dbt Transform", "dbt Core", "SQL transformations")
!endprocedure

!procedure $SparkJob()
  Container(spark_job, "Spark Job", "Technology TBD", "Distributed compute processing")
!endprocedure
```

- [ ] **Step 3: Commit**

```bash
git add models/storage.puml models/processing.puml
git commit -m "feat: add storage and processing model primitives"
```

---

### Task 5: Model Layer — Serving & Governance

**Files:**
- Create: `models/serving.puml`
- Create: `models/governance.puml`

- [ ] **Step 1: Create `models/serving.puml`**

```plantuml
' ============================================================
' Domain: Serving — how data gets consumed
' ============================================================

!procedure $BiPlatform()
  Container(bi_platform, "BI Platform", "Technology TBD", "Dashboards and reports")
!endprocedure

!procedure $ApiService()
  Container(api_service, "API Service", "Technology TBD", "Data API for downstream consumers")
!endprocedure

!procedure $MlEndpoint()
  Container(ml_endpoint, "ML Endpoint", "Technology TBD", "Deployed ML model serving predictions")
!endprocedure

!procedure $DataCatalog()
  Container(data_catalog, "Data Catalog", "Technology TBD", "Searchable metadata catalog")
!endprocedure

!procedure $ReportDashboard()
  Container(report_dashboard, "Report Dashboard", "Technology TBD", "Scheduled/static reports")
!endprocedure
```

- [ ] **Step 2: Create `models/governance.puml`**

```plantuml
' ============================================================
' Domain: Governance — data quality, lineage, policy
' ============================================================

!procedure $QualityEngine()
  Container(quality_engine, "Quality Engine", "Technology TBD", "Data quality checks and monitoring")
!endprocedure

!procedure $AccessControl()
  Container(access_control, "Access Control", "Technology TBD", "RBAC/ABAC policy enforcement")
!endprocedure

!procedure $LineageTracker()
  Container(lineage_tracker, "Lineage Tracker", "Technology TBD", "End-to-end data lineage")
!endprocedure

!procedure $MasterDataSvc()
  Container(master_data_svc, "Master Data Service", "Technology TBD", "Master data management")
!endprocedure

!procedure $PolicyEngine()
  Container(policy_engine, "Policy Engine", "Technology TBD", "Data classification and policy rules")
!endprocedure
```

- [ ] **Step 3: Commit**

```bash
git add models/serving.puml models/governance.puml
git commit -m "feat: add serving and governance model primitives"
```

---

### Task 6: Model Layer — Integration & Security

**Files:**
- Create: `models/integration.puml`
- Create: `models/security.puml`

- [ ] **Step 1: Create `models/integration.puml`**

```plantuml
' ============================================================
' Domain: Integration — system-to-system glue
' ============================================================

!procedure $Esb()
  Container(esb, "ESB / Integration Platform", "Technology TBD", "Enterprise service bus")
!endprocedure

!procedure $MessageBroker()
  Container(message_broker, "Message Broker", "Technology TBD", "Async message routing")
!endprocedure

!procedure $WebhookHandler()
  Container(webhook_handler, "Webhook Handler", "Technology TBD", "Inbound webhook receiver")
!endprocedure

!procedure $RestApi()
  Container(rest_api, "REST API", "Technology TBD", "RESTful integration endpoint")
!endprocedure

!procedure $GraphqlEndpoint()
  Container(graphql_endpoint, "GraphQL Endpoint", "Technology TBD", "GraphQL integration endpoint")
!endprocedure
```

- [ ] **Step 2: Create `models/security.puml`**

```plantuml
' ============================================================
' Domain: Security — auth, secrets, audit
' ============================================================

!procedure $IdentityProvider()
  Container_Ext(identity_provider, "Identity Provider", "Technology TBD", "OAuth/SAML/OIDC provider")
!endprocedure

!procedure $AuthGateway()
  Container(auth_gateway, "Auth Gateway", "Technology TBD", "API auth enforcement (token validation, mTLS)")
!endprocedure

!procedure $SecretsVault()
  Container(secrets_vault, "Secrets Vault", "Technology TBD", "Secrets/key management")
!endprocedure

!procedure $Firewall()
  Container_Ext(firewall, "Firewall", "Technology TBD", "Network perimeter / WAF")
!endprocedure

!procedure $CertificateMgr()
  Container(certificate_mgr, "Certificate Manager", "Technology TBD", "TLS cert provisioning and rotation")
!endprocedure

!procedure $AuditLog()
  ContainerDb(audit_log, "Audit Log", "Technology TBD", "Security audit trail")
!endprocedure
```

- [ ] **Step 3: Commit**

```bash
git add models/integration.puml models/security.puml
git commit -m "feat: add integration and security model primitives"
```

---

### Task 7: Model Layer — IoT, ML Platform, GenAI

**Files:**
- Create: `models/iot.puml`
- Create: `models/ml-platform.puml`
- Create: `models/genai.puml`

- [ ] **Step 1: Create `models/iot.puml`**

```plantuml
' ============================================================
' Domain: IoT — edge devices and telemetry
' ============================================================

!procedure $EdgeDevice()
  Container_Ext(edge_device, "Edge Device", "Technology TBD", "Sensor / edge compute device")
!endprocedure

!procedure $EdgeGateway()
  Container(edge_gateway, "Edge Gateway", "Technology TBD", "Local aggregation and protocol translation")
!endprocedure

!procedure $TelemetryCollector()
  Container(telemetry_collector, "Telemetry Collector", "Technology TBD", "Ingests device telemetry at scale")
!endprocedure

!procedure $DeviceRegistry()
  ContainerDb(device_registry, "Device Registry", "Technology TBD", "Device identity and configuration store")
!endprocedure

!procedure $CommandDispatcher()
  Container(command_dispatcher, "Command Dispatcher", "Technology TBD", "Cloud-to-device command routing")
!endprocedure
```

- [ ] **Step 2: Create `models/ml-platform.puml`**

```plantuml
' ============================================================
' Domain: ML Platform — training, serving, experiment tracking
' ============================================================

!procedure $FeatureStore()
  ContainerDb(feature_store, "Feature Store", "Technology TBD", "Managed feature storage (online + offline)")
!endprocedure

!procedure $ModelRegistry()
  ContainerDb(model_registry, "Model Registry", "Technology TBD", "Versioned model artifacts and metadata")
!endprocedure

!procedure $TrainingInfra()
  Container(training_infra, "Training Infra", "Technology TBD", "Model training compute")
!endprocedure

!procedure $ExperimentTracker()
  Container(experiment_tracker, "Experiment Tracker", "Technology TBD", "Experiment logging and comparison")
!endprocedure

!procedure $MlPipeline()
  Container(ml_pipeline, "ML Pipeline", "Technology TBD", "End-to-end ML pipeline orchestration")
!endprocedure
```

- [ ] **Step 3: Create `models/genai.puml`**

```plantuml
' ============================================================
' Domain: GenAI — LLM ops, RAG, evals, safety
' ============================================================

!procedure $LlmGateway()
  Container(llm_gateway, "LLM Gateway", "Technology TBD", "Unified LLM API proxy")
!endprocedure

!procedure $PromptRegistry()
  ContainerDb(prompt_registry, "Prompt Registry", "Technology TBD", "Versioned prompt templates and system prompts")
!endprocedure

!procedure $RagPipeline()
  Container(rag_pipeline, "RAG Pipeline", "Technology TBD", "Retrieval-augmented generation orchestration")
!endprocedure

!procedure $VectorStore()
  ContainerDb(vector_store, "Vector Store", "Technology TBD", "Embedding storage and similarity search")
!endprocedure

!procedure $EvalFramework()
  Container(eval_framework, "Eval Framework", "Technology TBD", "Automated evaluation and benchmarking")
!endprocedure

!procedure $RedteamHarness()
  Container(redteam_harness, "Redteam Harness", "Technology TBD", "Adversarial testing and safety probing")
!endprocedure

!procedure $GuardrailsEngine()
  Container(guardrails_engine, "Guardrails Engine", "Technology TBD", "Input/output filtering, PII detection, policy enforcement")
!endprocedure

!procedure $AgentRuntime()
  Container(agent_runtime, "Agent Runtime", "Technology TBD", "Agent orchestration and tool execution")
!endprocedure

!procedure $FeedbackCollector()
  Container(feedback_collector, "Feedback Collector", "Technology TBD", "Human feedback capture")
!endprocedure
```

- [ ] **Step 4: Commit**

```bash
git add models/iot.puml models/ml-platform.puml models/genai.puml
git commit -m "feat: add IoT, ML platform, and GenAI model primitives"
```

---

### Task 8: Manifest

**Files:**
- Create: `manifest.yaml`

- [ ] **Step 1: Create `manifest.yaml`**

```yaml
version: "1.0"

domains:
  consumers:
    file: models/consumers.puml
    elements:
      data_analyst:
        type: Person
        description: "Queries data via BI/SQL tools"
      data_engineer:
        type: Person
        description: "Builds and maintains pipelines"
      data_scientist:
        type: Person
        description: "Builds models, explores data"
      business_user:
        type: Person
        description: "Consumes reports and dashboards"
      external_system:
        type: System_Ext
        description: "System outside the boundary"

  ingestion:
    file: models/ingestion.puml
    elements:
      api_gateway:
        type: Container
        description: "Entry point for API-based ingestion"
      event_stream:
        type: Container
        description: "Real-time event ingestion"
      batch_etl:
        type: Container
        description: "Scheduled batch data extraction"
      cdc_pipeline:
        type: Container
        description: "Change data capture from source DBs"
      file_drop:
        type: Container
        description: "SFTP/S3/blob file-based ingestion"

  storage:
    file: models/storage.puml
    elements:
      data_lake:
        type: ContainerDb
        description: "Raw + curated zones"
      data_warehouse:
        type: ContainerDb
        description: "Dimensional models, governed data"
      operational_db:
        type: ContainerDb
        description: "Transactional/operational database"
      object_store:
        type: ContainerDb
        description: "Unstructured blob/file storage"
      cache_layer:
        type: Container
        description: "Low-latency cache"

  processing:
    file: models/processing.puml
    elements:
      elt_pipeline:
        type: Container
        description: "Extract-load-transform pipeline"
      stream_processor:
        type: Container
        description: "Real-time stream processing"
      orchestrator:
        type: Container
        description: "Workflow orchestration"
      dbt_transform:
        type: Container
        description: "SQL transformations"
      spark_job:
        type: Container
        description: "Distributed compute processing"

  serving:
    file: models/serving.puml
    elements:
      bi_platform:
        type: Container
        description: "Dashboards and reports"
      api_service:
        type: Container
        description: "Data API for downstream consumers"
      ml_endpoint:
        type: Container
        description: "Deployed ML model serving predictions"
      data_catalog:
        type: Container
        description: "Searchable metadata catalog"
      report_dashboard:
        type: Container
        description: "Scheduled/static reports"

  governance:
    file: models/governance.puml
    elements:
      quality_engine:
        type: Container
        description: "Data quality checks and monitoring"
      access_control:
        type: Container
        description: "RBAC/ABAC policy enforcement"
      lineage_tracker:
        type: Container
        description: "End-to-end data lineage"
      master_data_svc:
        type: Container
        description: "Master data management"
      policy_engine:
        type: Container
        description: "Data classification and policy rules"

  integration:
    file: models/integration.puml
    elements:
      esb:
        type: Container
        description: "Enterprise service bus"
      message_broker:
        type: Container
        description: "Async message routing"
      webhook_handler:
        type: Container
        description: "Inbound webhook receiver"
      rest_api:
        type: Container
        description: "RESTful integration endpoint"
      graphql_endpoint:
        type: Container
        description: "GraphQL integration endpoint"

  security:
    file: models/security.puml
    elements:
      identity_provider:
        type: Container_Ext
        description: "OAuth/SAML/OIDC provider"
      auth_gateway:
        type: Container
        description: "API auth enforcement"
      secrets_vault:
        type: Container
        description: "Secrets/key management"
      firewall:
        type: Container_Ext
        description: "Network perimeter / WAF"
      certificate_mgr:
        type: Container
        description: "TLS cert provisioning and rotation"
      audit_log:
        type: ContainerDb
        description: "Security audit trail"

  iot:
    file: models/iot.puml
    elements:
      edge_device:
        type: Container_Ext
        description: "Sensor / edge compute device"
      edge_gateway:
        type: Container
        description: "Local aggregation and protocol translation"
      telemetry_collector:
        type: Container
        description: "Ingests device telemetry at scale"
      device_registry:
        type: ContainerDb
        description: "Device identity and configuration store"
      command_dispatcher:
        type: Container
        description: "Cloud-to-device command routing"

  ml_platform:
    file: models/ml-platform.puml
    elements:
      feature_store:
        type: ContainerDb
        description: "Managed feature storage (online + offline)"
      model_registry:
        type: ContainerDb
        description: "Versioned model artifacts and metadata"
      training_infra:
        type: Container
        description: "Model training compute"
      experiment_tracker:
        type: Container
        description: "Experiment logging and comparison"
      ml_pipeline:
        type: Container
        description: "End-to-end ML pipeline orchestration"

  genai:
    file: models/genai.puml
    elements:
      llm_gateway:
        type: Container
        description: "Unified LLM API proxy"
      prompt_registry:
        type: ContainerDb
        description: "Versioned prompt templates and system prompts"
      rag_pipeline:
        type: Container
        description: "Retrieval-augmented generation orchestration"
      vector_store:
        type: ContainerDb
        description: "Embedding storage and similarity search"
      eval_framework:
        type: Container
        description: "Automated evaluation and benchmarking"
      redteam_harness:
        type: Container
        description: "Adversarial testing and safety probing"
      guardrails_engine:
        type: Container
        description: "Input/output filtering, PII detection"
      agent_runtime:
        type: Container
        description: "Agent orchestration and tool execution"
      feedback_collector:
        type: Container
        description: "Human feedback capture"

diagrams: []
```

- [ ] **Step 2: Commit**

```bash
git add manifest.yaml
git commit -m "feat: add element manifest for AI agent context"
```

---

### Task 9: Templates

**Files:**
- Create: `templates/c4-context.puml`
- Create: `templates/c4-container.puml`
- Create: `templates/sequence.puml`
- Create: `templates/erd.puml`

- [ ] **Step 1: Create `templates/c4-context.puml`**

```plantuml
@startuml
' === TEMPLATE: C4 Context Diagram ===
' 1. Copy this file to diagrams/c4/<your-diagram-name>.puml
' 2. Include the model files you need
' 3. Call element procedures and define relationships
' 4. Remove these comments

' Theme MUST come before C4 include
!include ../../lib/theme.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
$ApplySkinparams()

' Include model files (uncomment what you need)
' !include ../../models/consumers.puml
' !include ../../models/storage.puml

' Call element procedures
' $DataAnalyst()
' $DataWarehouse()

' Define relationships
' Rel(data_analyst, data_warehouse, "Queries", "SQL")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 2: Create `templates/c4-container.puml`**

```plantuml
@startuml
' === TEMPLATE: C4 Container Diagram ===
' 1. Copy this file to diagrams/c4/<your-diagram-name>.puml
' 2. Include the model files you need
' 3. Call element procedures and define relationships
' 4. Remove these comments

' Theme MUST come before C4 include
!include ../../lib/theme.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
$ApplySkinparams()

' Include model files (uncomment what you need)
' !include ../../models/consumers.puml
' !include ../../models/ingestion.puml
' !include ../../models/storage.puml
' !include ../../models/processing.puml
' !include ../../models/serving.puml

' System boundary
' System_Boundary(my_system, "My System") {
'   $DataLake()
'   $DataWarehouse()
'   $DbtTransform()
' }

' External actors
' $DataAnalyst()

' Relationships
' Rel(data_analyst, data_warehouse, "Queries", "SQL")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 3: Create `templates/sequence.puml`**

```plantuml
@startuml
' === TEMPLATE: Sequence Diagram ===
' 1. Copy this file to diagrams/sequence/<your-diagram-name>.puml
' 2. Define participants and interactions
' 3. Remove these comments

' No C4 include needed — standard PlantUML sequence syntax
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Segoe UI", Arial, sans-serif
skinparam defaultFontSize 12

skinparam sequence {
  ArrowColor #92400E
  LifeLineBorderColor #D97706
  LifeLineBackgroundColor #FFFBEB
  ParticipantBackgroundColor #FEF3C7
  ParticipantBorderColor #D97706
  ParticipantFontColor #333333
}

title Sequence Diagram Title

' participant "Service A" as svc_a
' participant "Service B" as svc_b
' database "Data Store" as db

' svc_a -> svc_b: Request
' svc_b -> db: Query
' db --> svc_b: Results
' svc_b --> svc_a: Response

@enduml
```

- [ ] **Step 4: Create `templates/erd.puml`**

```plantuml
@startuml
' === TEMPLATE: Entity Relationship Diagram ===
' 1. Copy this file to diagrams/erd/<your-diagram-name>.puml
' 2. Define entities and relationships
' 3. Remove these comments

' No C4 include needed — standard PlantUML entity syntax
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Segoe UI", Arial, sans-serif
skinparam defaultFontSize 12

skinparam entity {
  BackgroundColor #FEF3C7
  BorderColor #D97706
  FontColor #333333
}

' entity "Customer" as customer {
'   *customer_id : uuid <<PK>>
'   --
'   name : varchar
'   email : varchar
'   created_at : timestamp
' }

' entity "Order" as order {
'   *order_id : uuid <<PK>>
'   --
'   *customer_id : uuid <<FK>>
'   total : decimal
'   status : varchar
' }

' customer ||--o{ order : "places"

@enduml
```

- [ ] **Step 5: Commit**

```bash
git add templates/
git commit -m "feat: add starter templates for C4, sequence, and ERD diagrams"
```

---

### Task 10: Render Script

**Files:**
- Create: `scripts/render.py`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write tests for include resolver**

Create `tests/test_render.py`:

```python
"""Tests for the render script's include resolution logic."""
import os
import tempfile
import pytest

# We'll import after creating the module
from scripts.render import resolve_includes


class TestResolveIncludes:
    """Test local !include inlining."""

    def test_no_includes(self):
        source = "@startuml\nPerson(a, 'A', 'desc')\n@enduml"
        result = resolve_includes(source, base_dir="/tmp")
        assert result == source

    def test_remote_include_left_untouched(self):
        source = "!include https://example.com/C4_Context.puml\nPerson(a, 'A', 'desc')"
        result = resolve_includes(source, base_dir="/tmp")
        assert "https://example.com/C4_Context.puml" in result

    def test_local_include_inlined(self, tmp_path):
        # Create a file to include
        inc_file = tmp_path / "inc.puml"
        inc_file.write_text("' included content\n!define FOO bar")
        # Source references it
        source = f"!include inc.puml\nPerson(a, 'A', 'desc')"
        result = resolve_includes(source, base_dir=str(tmp_path))
        assert "' included content" in result
        assert "!define FOO bar" in result
        assert "!include inc.puml" not in result

    def test_nested_local_includes(self, tmp_path):
        # Create nested include chain: a.puml -> b.puml
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.puml").write_text("' leaf content")
        (tmp_path / "a.puml").write_text("!include sub/b.puml")
        source = "!include a.puml\nDone"
        result = resolve_includes(source, base_dir=str(tmp_path))
        assert "' leaf content" in result
        assert "!include" not in result.replace("!include https", "")

    def test_circular_include_raises(self, tmp_path):
        (tmp_path / "a.puml").write_text("!include b.puml")
        (tmp_path / "b.puml").write_text("!include a.puml")
        source = "!include a.puml"
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_includes(source, base_dir=str(tmp_path))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/alfred/code/arch-diagrams
python -m pytest tests/test_render.py -v
```

Expected: ImportError — `scripts.render` doesn't exist yet.

- [ ] **Step 3: Create `scripts/__init__.py` and `tests/__init__.py`**

Empty `__init__.py` files so Python can import:
```bash
touch scripts/__init__.py tests/__init__.py
```

- [ ] **Step 4: Implement `scripts/render.py`**

```python
#!/usr/bin/env python3
"""Render PlantUML diagrams via the Kroki public API.

Usage:
    python scripts/render.py <file.puml>              # Render single file to SVG
    python scripts/render.py <file.puml> --png         # Render single file to PNG
    python scripts/render.py <file.puml> --dry-run     # Print resolved source
    python scripts/render.py --all                     # Render all diagrams/
    python scripts/render.py --all --png               # Render all as PNG
"""
import argparse
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

KROKI_BASE = "https://kroki.io/plantuml"
DIAGRAMS_DIR = "diagrams"
RENDERED_DIR = "rendered"
INCLUDE_RE = re.compile(r"^\s*!include\s+(.+)\s*$", re.MULTILINE)


def resolve_includes(source: str, base_dir: str, seen: set | None = None) -> str:
    """Recursively inline local !include directives. Remote URLs are left untouched."""
    if seen is None:
        seen = set()

    def replacer(match):
        path_str = match.group(1).strip()
        # Skip remote includes
        if path_str.startswith("http://") or path_str.startswith("https://"):
            return match.group(0)
        # Skip stdlib includes like <C4/C4_Context>
        if path_str.startswith("<") and path_str.endswith(">"):
            return match.group(0)
        # Resolve local path
        full_path = os.path.normpath(os.path.join(base_dir, path_str))
        if full_path in seen:
            raise ValueError(f"Circular include detected: {full_path}")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Include file not found: {full_path}")
        seen.add(full_path)
        content = open(full_path).read()
        # Recursively resolve includes in the included file
        inc_dir = os.path.dirname(full_path)
        resolved = resolve_includes(content, base_dir=inc_dir, seen=seen)
        seen.discard(full_path)
        return resolved

    return INCLUDE_RE.sub(replacer, source)


def post_to_kroki(source: str, fmt: str = "svg") -> bytes:
    """POST resolved PlantUML source to Kroki and return the response bytes."""
    url = f"{KROKI_BASE}/{fmt}"
    data = source.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "text/plain"})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Retrying in {wait}s (HTTP {e.code})...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    return b""  # unreachable


def find_all_diagrams(root: str) -> list[str]:
    """Find all .puml files under the diagrams/ directory."""
    diagrams_path = os.path.join(root, DIAGRAMS_DIR)
    results = []
    for dirpath, _, filenames in os.walk(diagrams_path):
        for f in sorted(filenames):
            if f.endswith(".puml"):
                results.append(os.path.join(dirpath, f))
    return results


def output_path(source_path: str, root: str, fmt: str) -> str:
    """Compute output path mirroring diagrams/ structure into rendered/."""
    rel = os.path.relpath(source_path, os.path.join(root, DIAGRAMS_DIR))
    name = os.path.splitext(rel)[0] + f".{fmt}"
    return os.path.join(root, RENDERED_DIR, name)


def render_file(source_path: str, root: str, fmt: str, dry_run: bool) -> bool:
    """Render a single .puml file. Returns True on success."""
    print(f"Rendering: {os.path.relpath(source_path, root)}")
    source = open(source_path).read()
    base_dir = os.path.dirname(source_path)

    try:
        resolved = resolve_includes(source, base_dir=base_dir)
    except (ValueError, FileNotFoundError) as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False

    if dry_run:
        print(resolved)
        return True

    try:
        image_data = post_to_kroki(resolved, fmt)
    except Exception as e:
        print(f"  ERROR: Kroki request failed: {e}", file=sys.stderr)
        return False

    out = output_path(source_path, root, fmt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(image_data)
    print(f"  -> {os.path.relpath(out, root)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Render PlantUML diagrams via Kroki API")
    parser.add_argument("file", nargs="?", help="Path to .puml file")
    parser.add_argument("--all", action="store_true", help="Render all diagrams/")
    parser.add_argument("--png", action="store_true", help="Output PNG instead of SVG")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved source only")
    args = parser.parse_args()

    if not args.file and not args.all:
        parser.error("Provide a file path or use --all")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fmt = "png" if args.png else "svg"

    if args.all:
        files = find_all_diagrams(root)
        if not files:
            print("No .puml files found in diagrams/")
            return
        failures = []
        for f in files:
            if not render_file(f, root, fmt, args.dry_run):
                failures.append(f)
        if failures:
            print(f"\n{len(failures)} file(s) failed:", file=sys.stderr)
            for f in failures:
                print(f"  - {os.path.relpath(f, root)}", file=sys.stderr)
            sys.exit(1)
    else:
        source_path = os.path.abspath(args.file)
        if not os.path.isfile(source_path):
            print(f"File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        if not render_file(source_path, root, fmt, args.dry_run):
            sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests**

```bash
cd /home/alfred/code/arch-diagrams
python -m pytest tests/test_render.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/ tests/
git commit -m "feat: add render script with include resolution and Kroki API"
```

---

### Task 11: Validation Script

**Files:**
- Create: `scripts/validate.py`
- Create: `tests/test_validate.py`

- [ ] **Step 1: Write tests for validation rules**

Create `tests/test_validate.py`:

```python
"""Tests for the validation script."""
import pytest
from scripts.validate import (
    check_inline_definitions,
    check_hardcoded_colours,
    check_duplicate_ids,
)


class TestInlineDefinitions:
    def test_clean_view_passes(self):
        source = "!include ../../models/consumers.puml\n$DataAnalyst()\nRel(a, b, 'uses')"
        errors = check_inline_definitions(source, "diagrams/c4/test.puml")
        assert errors == []

    def test_inline_container_fails(self):
        source = 'Container(my_svc, "My Service", "Java", "Does things")'
        errors = check_inline_definitions(source, "diagrams/c4/test.puml")
        assert len(errors) == 1
        assert "Container(" in errors[0]

    def test_procedure_definition_ok(self):
        """!procedure blocks containing Container() are fine in models/"""
        source = '!procedure $Foo()\n  Container(foo, "Foo", "Tech", "Desc")\n!endprocedure'
        errors = check_inline_definitions(source, "models/test.puml")
        assert errors == []


class TestHardcodedColours:
    def test_no_colours_passes(self):
        source = "$DataAnalyst()\nRel(a, b, 'uses')"
        errors = check_hardcoded_colours(source, "diagrams/c4/test.puml")
        assert errors == []

    def test_hex_colour_fails(self):
        source = 'skinparam backgroundColor #FF0000'
        errors = check_hardcoded_colours(source, "diagrams/c4/test.puml")
        assert len(errors) == 1

    def test_theme_file_exempt(self):
        source = '!$PERSON_BG_COLOR = "#FDE68A"'
        errors = check_hardcoded_colours(source, "lib/theme.puml")
        assert errors == []


class TestDuplicateIds:
    def test_no_duplicates_passes(self):
        models = {
            "models/a.puml": "Container(foo, 'Foo', 'T', 'D')",
            "models/b.puml": "Container(bar, 'Bar', 'T', 'D')",
        }
        errors = check_duplicate_ids(models)
        assert errors == []

    def test_duplicates_caught(self):
        models = {
            "models/a.puml": "Container(foo, 'Foo', 'T', 'D')",
            "models/b.puml": "Container(foo, 'Foo2', 'T', 'D')",
        }
        errors = check_duplicate_ids(models)
        assert len(errors) == 1
        assert "foo" in errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_validate.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `scripts/validate.py`**

```python
#!/usr/bin/env python3
"""Validate PlantUML files against arch-diagrams conventions.

Usage:
    python scripts/validate.py            # Check everything
    python scripts/validate.py diagrams/  # Check only views
"""
import argparse
import os
import re
import sys
from pathlib import Path

# C4 element definition patterns (not inside !procedure)
ELEMENT_PATTERNS = [
    r"^\s*(?:Person|Person_Ext|System|System_Ext|Container|Container_Ext|ContainerDb|ContainerDb_Ext|Component|Component_Ext)\s*\(",
]
ELEMENT_RE = re.compile("|".join(ELEMENT_PATTERNS), re.MULTILINE)

# Hex colour pattern
HEX_COLOUR_RE = re.compile(r"#[0-9A-Fa-f]{3,8}(?![0-9A-Fa-f])")

# Element ID extractor: first argument to C4 macros
ID_RE = re.compile(
    r"(?:Person|Person_Ext|System|System_Ext|Container|Container_Ext|ContainerDb|ContainerDb_Ext|Component|Component_Ext)\s*\(\s*(\w+)"
)


def check_inline_definitions(source: str, filepath: str) -> list[str]:
    """Check that view-layer files don't define elements inline."""
    errors = []
    if not filepath.startswith("diagrams"):
        return errors
    for i, line in enumerate(source.splitlines(), 1):
        if ELEMENT_RE.match(line):
            errors.append(f"{filepath}:{i}: Inline element definition: {line.strip()}")
    return errors


def check_hardcoded_colours(source: str, filepath: str) -> list[str]:
    """Check that hex colours only appear in theme.puml."""
    errors = []
    if filepath.endswith("theme.puml"):
        return errors
    for i, line in enumerate(source.splitlines(), 1):
        if HEX_COLOUR_RE.search(line):
            errors.append(f"{filepath}:{i}: Hardcoded colour: {line.strip()}")
    return errors


def check_duplicate_ids(models: dict[str, str]) -> list[str]:
    """Check for duplicate element IDs across model files."""
    seen: dict[str, str] = {}
    errors = []
    for filepath, source in models.items():
        for match in ID_RE.finditer(source):
            eid = match.group(1)
            if eid in seen:
                errors.append(
                    f"Duplicate element ID '{eid}' in {filepath} (first seen in {seen[eid]})"
                )
            else:
                seen[eid] = filepath
    return errors


def check_manifest_sync(manifest_path: str, models_dir: str) -> list[str]:
    """Check manifest.yaml matches model file contents."""
    errors = []
    try:
        # Use simple YAML parsing (no dependency) — read key structure
        import yaml
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
    except ImportError:
        # Fallback: skip this check if PyYAML not available
        return [f"SKIP: PyYAML not installed, cannot check manifest sync"]
    except FileNotFoundError:
        return [f"manifest.yaml not found at {manifest_path}"]

    manifest_ids = set()
    for domain in manifest.get("domains", {}).values():
        for eid in domain.get("elements", {}).keys():
            manifest_ids.add(eid)

    # Collect IDs from model files
    file_ids = set()
    for fname in os.listdir(models_dir):
        if fname.endswith(".puml"):
            source = open(os.path.join(models_dir, fname)).read()
            for match in ID_RE.finditer(source):
                file_ids.add(match.group(1))

    missing_from_manifest = file_ids - manifest_ids
    missing_from_files = manifest_ids - file_ids

    for eid in sorted(missing_from_manifest):
        errors.append(f"Element '{eid}' in model files but missing from manifest.yaml")
    for eid in sorted(missing_from_files):
        errors.append(f"Element '{eid}' in manifest.yaml but missing from model files")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate arch-diagrams conventions")
    parser.add_argument("path", nargs="?", default=".", help="Path to check")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check_path = os.path.abspath(args.path)

    all_errors = []

    # Collect files to check
    puml_files = []
    for dirpath, _, filenames in os.walk(check_path):
        for f in filenames:
            if f.endswith(".puml"):
                puml_files.append(os.path.join(dirpath, f))

    # Run per-file checks
    for fpath in sorted(puml_files):
        relpath = os.path.relpath(fpath, root)
        source = open(fpath).read()
        all_errors.extend(check_inline_definitions(source, relpath))
        all_errors.extend(check_hardcoded_colours(source, relpath))

    # Run cross-file checks
    models_dir = os.path.join(root, "models")
    if os.path.isdir(models_dir):
        models = {}
        for f in os.listdir(models_dir):
            if f.endswith(".puml"):
                fpath = os.path.join(models_dir, f)
                models[f"models/{f}"] = open(fpath).read()
        all_errors.extend(check_duplicate_ids(models))

    # Manifest sync
    manifest_path = os.path.join(root, "manifest.yaml")
    if os.path.isfile(manifest_path) and os.path.isdir(models_dir):
        all_errors.extend(check_manifest_sync(manifest_path, models_dir))

    # Report
    if all_errors:
        print(f"Found {len(all_errors)} issue(s):\n")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_validate.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: add validation script with inline, colour, and duplicate checks"
```

---

### Task 12: Agent Prompt & Examples

**Files:**
- Create: `prompts/diagram-agent.md`
- Create: `prompts/examples/good-c4-context.puml`
- Create: `prompts/examples/bad-inline-defs.puml`

- [ ] **Step 1: Create `prompts/diagram-agent.md`**

```markdown
# Diagram Agent — System Prompt

You are an architecture diagram agent working in the `arch-diagrams` repo. You generate PlantUML + C4 diagrams following a strict three-layer architecture.

## Before Generating Anything

1. Read `manifest.yaml` to see all available elements
2. Identify which domains are relevant to the user's request
3. Load only the model files you need

## Rules

### Three-Layer Discipline
- **View files** (`diagrams/`): ONLY contain `!include` directives, element procedure calls, `Rel()` relationships, and layout. NO element definitions.
- **Model files** (`models/`): Define elements as `!procedure` blocks. Each element defined ONCE.
- **Foundation** (`lib/`): Theme and macros. Never hardcode colours.

### Reuse Over Create
- If an element exists in `manifest.yaml`, include its model file and call its procedure.
- NEVER redefine an existing element. NEVER copy-paste element definitions into view files.

### New Elements
- If a genuinely new element is needed:
  1. Add the `!procedure` to the appropriate model file
  2. Add the entry to `manifest.yaml`
  3. Use `snake_case` for the element ID
  4. Use `PascalCase` for the procedure name (e.g., `$MyNewElement()`)

### Include Order (MUST follow)
```
!include ../../lib/theme.puml           ← Theme variables FIRST
!include https://...C4_Container.puml   ← C4 library SECOND
$ApplySkinparams()                      ← Skinparams THIRD
!include ../../models/consumers.puml    ← Model files AFTER
```

### C4 Library Selection
| Diagram type | Include |
|---|---|
| Context | `C4_Context.puml` |
| Container | `C4_Container.puml` |
| Component | `C4_Component.puml` |
| Deployment | `C4_Deployment.puml` |
| Sequence | No C4 (standard PlantUML) |
| ERD | No C4 (standard PlantUML) |

### Naming
- Element IDs: `snake_case` (e.g., `data_lake`, `auth_gateway`)
- File names: `kebab-case` (e.g., `data-platform-context.puml`)
- Procedure names: `$PascalCase` (e.g., `$DataLake()`)

### Output Format
Every diagram must end with `LAYOUT_WITH_LEGEND()` (for C4 diagrams).

## Example: Good Output

See `prompts/examples/good-c4-context.puml`

## Example: Bad Output (Anti-Pattern)

See `prompts/examples/bad-inline-defs.puml`
```

- [ ] **Step 2: Create `prompts/examples/good-c4-context.puml`**

```plantuml
@startuml
' GOOD: Thin view file — includes models, defines only relationships

!include ../../lib/theme.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
$ApplySkinparams()

!include ../../models/consumers.puml
!include ../../models/storage.puml
!include ../../models/serving.puml

title Data Platform — System Context

$DataAnalyst()
$BusinessUser()
$DataWarehouse()
$BiPlatform()

Rel(data_analyst, data_warehouse, "Queries", "SQL")
Rel(business_user, bi_platform, "Views reports")
Rel(bi_platform, data_warehouse, "Reads from", "DirectQuery")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 3: Create `prompts/examples/bad-inline-defs.puml`**

```plantuml
@startuml
' BAD: Elements defined inline — violates three-layer architecture
' DO NOT do this. Elements belong in models/ files.

!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title Data Platform — System Context

' BAD: Inline person definition (should be in models/consumers.puml)
Person(data_analyst, "Data Analyst", "Queries data via BI/SQL tools")

' BAD: Inline container definition (should be in models/storage.puml)
ContainerDb(data_warehouse, "Data Warehouse", "Snowflake", "Dimensional models")

' BAD: Hardcoded colour (should use theme)
skinparam backgroundColor #F0F0F0

' BAD: Missing theme include — legend will have default blue colours

Rel(data_analyst, data_warehouse, "Queries", "SQL")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 4: Commit**

```bash
git add prompts/
git commit -m "feat: add agent system prompt and good/bad examples"
```

---

### Task 13: Smoke Test — End-to-End Render

**Files:**
- Create: `diagrams/c4/data-platform-context.puml` (first real diagram)

- [ ] **Step 1: Create `diagrams/c4/data-platform-context.puml`**

```plantuml
@startuml
!include ../../lib/theme.puml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
$ApplySkinparams()

!include ../../models/consumers.puml
!include ../../models/ingestion.puml
!include ../../models/storage.puml
!include ../../models/processing.puml
!include ../../models/serving.puml

title Data Platform — Container View

$DataAnalyst()
$DataEngineer()

$EventStream()
$BatchEtl()

$DataLake()
$DataWarehouse()

$DbtTransform()
$Orchestrator()

$BiPlatform()

Rel(data_analyst, bi_platform, "Views reports")
Rel(data_analyst, data_warehouse, "Queries", "SQL")
Rel(data_engineer, orchestrator, "Manages")
Rel(event_stream, data_lake, "Streams to", "Avro/JSON")
Rel(batch_etl, data_lake, "Loads to", "Parquet")
Rel(data_lake, dbt_transform, "Source for")
Rel(dbt_transform, data_warehouse, "Writes to")
Rel(orchestrator, dbt_transform, "Triggers")
Rel(orchestrator, batch_etl, "Triggers")
Rel(data_warehouse, bi_platform, "Serves", "DirectQuery")

LAYOUT_WITH_LEGEND()
@enduml
```

- [ ] **Step 2: Run validation**

```bash
python scripts/validate.py
```

Expected: All checks passed (or known SKIP for PyYAML).

- [ ] **Step 3: Render via script**

```bash
python scripts/render.py diagrams/c4/data-platform-context.puml
```

Expected: `rendered/c4/data-platform-context.svg` created, HTTP 200.

- [ ] **Step 4: Render with --dry-run to verify include resolution**

```bash
python scripts/render.py diagrams/c4/data-platform-context.puml --dry-run
```

Expected: Printed source with local `!include` directives replaced by inlined content. Remote C4 URL still present.

- [ ] **Step 5: Open and visually verify**

```bash
xdg-open rendered/c4/data-platform-context.svg
```

Expected: Yellow/white themed C4 container diagram with legend matching.

- [ ] **Step 6: Update manifest with first diagram**

Add to the `diagrams:` section of `manifest.yaml`:

```yaml
diagrams:
  - path: diagrams/c4/data-platform-context.puml
    title: "Data Platform — Container View"
    type: c4_container
    includes_domains: [consumers, ingestion, storage, processing, serving]
```

- [ ] **Step 7: Commit**

```bash
git add diagrams/c4/data-platform-context.puml manifest.yaml
git commit -m "feat: add data platform context diagram and smoke test"
```
