# Merchant Onboarding

The onboarding flow handles identity verification and KYC/AML compliance checks. The Compliance Service performs automated screening against sanctions lists and PEP databases, plus document verification.

**Two outcomes:**
- **Approved:** Merchant account is activated, API keys are provisioned, and a welcome email is sent with getting-started documentation
- **Rejected:** Merchant is notified of the specific issue (e.g., document mismatch) and given clear next steps for resubmission
