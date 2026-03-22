# Fraud Case Data Model

The fraud investigation data model tracks scores, rules, cases, and ML model metadata.

**Score → Case flow:** Not every scored transaction generates a case. Cases are only created when the combined score exceeds the REVIEW or BLOCK threshold. Each case links back to the original fraud score for full traceability.

**Model versioning:** The `fraud_models` table tracks model performance metrics (AUC-ROC, precision@95%) so the team can compare production models against candidates before promoting a new version.
