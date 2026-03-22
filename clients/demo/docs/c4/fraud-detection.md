# Fraud Detection System

Real-time fraud scoring with a dual approach: configurable rules and ML-based scoring running in parallel for every transaction.

**Scoring pipeline:**
1. Transaction arrives at Scoring API
2. Rule Engine evaluates velocity counters, geo anomalies, and amount thresholds (Redis-backed, < 5ms)
3. ML Scorer runs ONNX inference using features from the Feature Store (< 20ms)
4. Combined score = max(rule_score, ml_score)
5. Decision: ALLOW (< 0.5), ALLOW_WITH_REVIEW (0.5–0.8), or BLOCK (> 0.8)

**Model details:**
- Gradient boosted trees trained on 18 months of labeled transaction data
- Retrained weekly with automated evaluation against precision@95% recall threshold
- AUC-ROC target: > 0.96
