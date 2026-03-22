# Production Infrastructure

The production environment runs on AWS eu-west-1 with EKS (Kubernetes) for container orchestration. Services are deployed across multiple availability zones for resilience.

**Key infrastructure:**
- **ALB + CloudFront** — TLS termination and edge caching for static assets
- **EKS Cluster** — runs all application services with per-service pod scaling
- **Aurora PostgreSQL** — Multi-AZ for automatic failover, handles all transactional data
- **ElastiCache Redis** — cluster mode enabled for fraud feature serving and caching
- **MSK Kafka** — 3-broker cluster for event streaming

**DR:** Asynchronous replication to eu-central-1 with Aurora read replicas and Kafka MirrorMaker 2.
