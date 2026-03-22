# Disaster Recovery Architecture

Active-passive DR across two AWS regions with Route 53 health-check failover.

**Recovery targets:**
- **RTO: 15 minutes** — scale standby pods, promote Aurora replica, update Route 53 routing
- **RPO: < 1 minute** — Aurora async replication lag is typically under 30 seconds

**Replication:**

| Component | Method | Target |
|-----------|--------|--------|
| Aurora PostgreSQL | Async replication | eu-central-1 read replica |
| MSK Kafka | MirrorMaker 2 | eu-central-1 topic sync |
| S3 | Cross-region replication | eu-central-1 bucket |

**Failover procedure is documented in the team runbook and tested quarterly.**
