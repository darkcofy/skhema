# ADR02: PostgreSQL as Primary Operational Store

## Status
Accepted

## Context
NovaPay requires a primary transactional database to store the authoritative state of payments,
merchants, accounts, and settlement records. This store must satisfy ACID guarantees: partial
writes during a transaction authorization cannot leave the system in an inconsistent state.

Early prototypes used a document store, which reduced schema rigidity during exploration but
introduced anomalies when concurrent updates to Account balances were not serialized correctly.
Chargeback disputes require complex multi-table queries joining Transaction, SettlementBatch,
Merchant, and Account records with precise consistency guarantees that document databases
handle poorly.

Regulatory requirements (PCI-DSS, SOC 2) mandate auditability and point-in-time recovery.
We need a database with mature tooling for logical replication, PITR backups, and row-level
security for PCI scope isolation.

## Decision
PostgreSQL will serve as the primary operational database for all core payment entities.
Each domain (core payments, merchant management, fraud) will use a dedicated schema within
a shared cluster during initial scale, with logical replication feeding the data warehouse
and analytics tier. Row-level security policies will enforce PCI scope boundaries so that
card data columns are only accessible to the tokenization service.

The operational_db element in the architecture represents this PostgreSQL cluster. The
data_warehouse is fed via logical replication and ETL from this source of truth.

<!-- skhema:elements operational_db, data_warehouse, elt_pipeline, lineage_tracker -->
<!-- gnosis:concepts Transaction, Account, Merchant, SettlementBatch, Chargeback, Payout -->

## Consequences
**Easier:**
- ACID transactions across Transaction, Account, and SettlementBatch records prevent double-spend anomalies
- Mature ecosystem for PITR backups, streaming replication, and logical decoding (change data capture)
- Row-level security and column encryption simplify PCI scope containment
- Rich SQL joins across merchant, transaction, and chargeback records for fraud investigation queries

**Harder:**
- Vertical scaling limits require careful partitioning strategy as transaction volume grows beyond hundreds of millions of rows
- Schema migrations on live tables require careful online-migration tooling to avoid table locks
- Multi-region active-active write patterns are not natively supported; read replicas serve reporting only
- Operational expertise in PostgreSQL tuning, vacuuming, and index maintenance must be maintained
