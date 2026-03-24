# Draft Glossary

*Auto-generated from glossary-seeds.csv.*

## account

A financial account within NovaPay that tracks a merchant's balance and transactions

**Source:** Billing Ledger

## acquirer

The bank or financial institution that processes card payments on behalf of the merchant

**Source:** Payments Architect

## acquiring bank

The bank that maintains the merchant's account and receives funds from card network settlement

**Source:** Payments Architect

## authorization

A request to the card network to verify and reserve funds on the cardholder's account

**Source:** Payment Gateway

## capture

The conversion of an authorization hold into an actual charge against the cardholder's account

**Source:** Payment Gateway

## card network

The payment network that routes transactions between issuers and acquirers (e.g. Visa or Mastercard)

**Source:** Payments Architect

## chargeback

A forced reversal of a transaction initiated by the cardholder's issuing bank

**Source:** Fraud Engine

## dispute

A formal challenge to a transaction raised by the cardholder through their issuing bank

**Source:** Fraud Engine

## fee schedule

A merchant-specific configuration defining processing fees and rates for each transaction type

**Source:** Merchant Portal

## gateway

The technical infrastructure that receives payment requests and routes them to card networks

**Source:** Payment Gateway

## idempotency key

A unique client-generated identifier ensuring a payment request is processed exactly once

**Source:** Payment Gateway

## interchange fee

The fee paid by the acquiring bank to the issuing bank for each card transaction

**Source:** Payments Architect

## issuer

The bank or financial institution that issued the payment card to the consumer

**Source:** Payments Architect

## issuing bank

The bank that issued the consumer's payment card and is liable for cardholder funds

**Source:** Payments Architect

## ledger entry

A single debit or credit record in the double-entry billing ledger

**Source:** Billing Ledger

## merchant

A business entity that accepts payments through the NovaPay platform

**Source:** Merchant Portal

## payment method

A specific instrument used by a consumer to make a payment (e.g. credit card or bank transfer)

**Source:** Payment Gateway

## payout

The disbursement of settled funds from NovaPay to the merchant's bank account

**Source:** Billing Ledger

## PCI compliance

Adherence to Payment Card Industry Data Security Standards for handling cardholder data

**Source:** Risk & Compliance

## refund

A merchant-initiated return of funds to the consumer for a previously captured transaction

**Source:** Payment Gateway

## settlement

The process of transferring captured funds from the acquiring bank to the merchant's account

**Source:** Billing Ledger

## settlement batch

A group of captured transactions settled together in a single processing cycle

**Source:** Billing Ledger

## tokenization

The process of replacing sensitive card data with a non-sensitive token for secure storage and transmission

**Source:** Payment Gateway

## transaction

A single payment attempt from a consumer to a merchant, whether it succeeds or fails

**Source:** Payment Gateway

## webhook

An HTTP callback notification sent to a merchant's endpoint when a payment event occurs

**Source:** Merchant Portal

