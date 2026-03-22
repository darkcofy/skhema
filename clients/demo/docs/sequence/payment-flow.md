# Payment Processing Flow

The happy-path payment flow from consumer tap to merchant webhook. The entire authorization path completes in < 500ms.

**Key observations:**
- Fraud check happens *before* card network authorization — blocking a fraudulent transaction is cheaper than reversing one
- The Kafka event bus decouples the notification and webhook delivery from the payment path — payment confirmation returns to the consumer immediately
- Settlement runs as a separate T+1 batch process
