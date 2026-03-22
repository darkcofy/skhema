# CI/CD Pipeline

Fully automated pipeline from developer push to production deployment.

**Stages:**
1. **Build & Test** — unit tests, integration tests, SAST (Snyk), DAST (ZAP)
2. **Package** — Docker images pushed to ECR, Helm charts to S3
3. **Staging** — automatic deployment to staging EKS cluster
4. **Production** — manual promotion gate, then rolling deployment to production EKS

**Security:** Every build runs Snyk for dependency vulnerabilities and ZAP for dynamic security scanning against the staging environment. Failed security checks block promotion to production.
