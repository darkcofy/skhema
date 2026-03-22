# Real-Time Fraud Check

Detailed view of the parallel rule + ML scoring pipeline that runs for every transaction.

**Performance budget:** Total scoring latency must stay under 50ms p99. Rules and ML scoring run in parallel (`par` block) to stay within budget. The Feature Store is optimized for online serving with < 5ms read latency.

**Escalation thresholds:**

| Score Range | Decision | Action |
|-------------|----------|--------|
| < 0.5 | ALLOW | Transaction proceeds normally |
| 0.5 – 0.8 | ALLOW_WITH_REVIEW | Transaction proceeds, case created for manual review |
| > 0.8 | BLOCK | Transaction declined, urgent case created |
