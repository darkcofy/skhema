# System Context

The system context view shows NovaPay's position in the broader financial ecosystem. Three user personas interact with the platform: consumers (via mobile app), merchants (via portal/API), and compliance officers (internal).

**Key integrations:**
- **Card Networks** (Visa/Mastercard): ISO 8583 protocol for authorization — chosen over REST for latency-critical payment flows
- **Core Banking** (COBOL mainframe): Settlement via SFTP/MQ — batch-oriented, runs nightly
- **Regulator Portal** (FCA/PSD2): Push-based compliance reporting via API and SFTP
