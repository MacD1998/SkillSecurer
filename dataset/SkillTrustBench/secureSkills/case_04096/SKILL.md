---
name: agent-payments
description: >
  The universal payment skill for AI agents. Fiat payments via Stripe (invoices,
  subscriptions, one-time charges), crypto payments via Coinbase Commerce (accept BTC,
  ETH, USDC with a trusted brand), batch crypto payments via Spraay (pay multiple
  recipients in one transaction across 13+ chains), and x402 micropayments for
  agent-to-agent commerce. Use this skill whenever the user wants to: send money, accept
  payments, create invoices, charge customers, process payroll, pay contractors, tip
  someone, split a bill, distribute tokens, do batch payments, set up subscriptions,
  create payment links, accept crypto, send USDC, pay a team, airdrop tokens, process
  refunds, check payment status, or build any payment workflow. Also trigger for
  mentions of: Stripe, Coinbase Commerce, Coinbase Pay, batch payments, mass transfers,
  x402, micropayments, agent payments, crypto payroll, payment gateway, checkout,
  payment intent, or payment automation.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - curl
      optionalEnv:
        - STRIPE_SECRET_KEY
        - COINBASE_COMMERCE_API_KEY
        - SPRAAY_GATEWAY_URL
    emoji: "💳"
    homepage: https://github.com/plagtech/agent-payments
    tags:
      - payments
      - stripe
      - coinbase
      - crypto
      - fiat
      - batch
      - x402
      - invoices
      - payroll
      - subscriptions
      - agents
      - defi
      - usdc
---

# 💳 Agent Payments — Every Payment Rail for AI Agents

One skill. Every payment rail your agent needs.

- **Stripe** — Fiat payments, invoices, subscriptions, payment links
- **Coinbase Commerce** — Accept crypto (BTC, ETH, USDC) through a trusted brand
- **Spraay** — Batch payments to multiple recipients across 13+ chains, x402 micropayments for agent-to-agent commerce

## Quick Start

### Which rail do I need?

| Use Case | Rail | Command |
|---|---|---|
| Charge a customer in USD | Stripe | `pay stripe charge` |
| Create an invoice | Stripe | `pay stripe invoice` |
| Set up recurring billing | Stripe | `pay stripe subscribe` |
| Accept crypto from a customer | Coinbase | `pay coinbase charge` |
| Pay 1 person in USDC/ETH | Spraay | `pay spraay send` |
| Pay 10-1000 people at once | Spraay | `pay spraay batch` |
| Agent-to-agent micropayment | Spraay x402 | `pay spraay x402` |
| Payroll (team/contractors) | Spraay | `pay spraay payroll` |
| Check any payment status | Any | `pay status <id>` |

## Setup

Each payment rail requires its own API key. You only need to configure the rails you use:

```bash
# Fiat payments (Stripe)
export STRIPE_SECRET_KEY="sk_live_..."

# Crypto acceptance (Coinbase Commerce)
export COINBASE_COMMERCE_API_KEY="..."

# Batch + x402 payments (Spraay)
export SPRAAY_GATEWAY_URL="https://gateway.spraay.app"
```

The skill works with any combination — install once, enable rails as needed.

---

## Rail 1: Stripe (Fiat Payments)

Full Stripe integration for traditional payment processing. Your agent can charge customers, create invoices, manage subscriptions, and generate payment links.

### Create a Payment (One-Time Charge)

```bash
curl -X POST https://api.stripe.com/v1/payment_intents \
  -u "$STRIPE_SECRET_KEY:" \
  -d amount=2000 \
  -d currency=usd \
  -d "payment_method_types[]"=card \
  -d description="Service payment"
```

**Parameters:**
- `amount` — Amount in cents (2000 = $20.00)
- `currency` — Three-letter ISO code (usd, eur, gbp, etc.)
- `description` — What the payment is for
- `receipt_email` — Optional, sends receipt to customer
- `metadata[key]` — Custom key-value pairs for your records

### Create an Invoice

```bash
# Step 1: Create invoice item
curl -X POST https://api.stripe.com/v1/invoiceitems \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d amount=5000 \
  -d currency=usd \
  -d description="Consulting — March 2026"

# Step 2: Create and send invoice
curl -X POST https://api.stripe.com/v1/invoices \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d collection_method=send_invoice \
  -d days_until_due=30

# Step 3: Finalize and send
curl -X POST https://api.stripe.com/v1/invoices/{invoice_id}/finalize \
  -u "$STRIPE_SECRET_KEY:"

curl -X POST https://api.stripe.com/v1/invoices/{invoice_id}/send \
  -u "$STRIPE_SECRET_KEY:"
```

### Create a Subscription

```bash
curl -X POST https://api.stripe.com/v1/subscriptions \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d "items[0][price]"="price_..." \
  -d payment_behavior=default_incomplete
```

### Create a Payment Link

```bash
curl -X POST https://api.stripe.com/v1/payment_links \
  -u "$STRIPE_SECRET_KEY:" \
  -d "line_items[0][price]"="price_..." \
  -d "line_items[0][quantity]"=1
```

### Check Payment Status

```bash
curl https://api.stripe.com/v1/payment_intents/{pi_id} \
  -u "$STRIPE_SECRET_KEY:"
```

Status values: `requires_payment_method`, `requires_confirmation`, `requires_action`, `processing`, `succeeded`, `canceled`

### Refund a Payment

```bash
curl -X POST https://api.stripe.com/v1/refunds \
  -u "$STRIPE_SECRET_KEY:" \
  -d payment_intent="pi_..."
```

For detailed Stripe API reference, see `references/stripe-rail.md`.

---

## Rail 2: Coinbase Commerce (Crypto Acceptance)

Accept cryptocurrency payments through Coinbase Commerce. Customers pay in BTC, ETH, USDC, or other supported coins. Funds settle to your Coinbase account.

### Create a Charge

```bash
curl -X POST https://api.commerce.coinbase.com/charges \
  -H "Content-Type: application/json" \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" \
  -d '{
    "name": "Service Payment",
    "description": "Payment for consulting services",
    "pricing_type": "fixed_price",
    "local_price": {
      "amount": "100.00",
      "currency": "USD"
    },
    "metadata": {
      "customer_id": "cust_123",
      "order_id": "ord_456"
    }
  }'
```

**Response includes:**
- `hosted_url` — Coinbase-hosted checkout page (redirect customer here)
- `addresses` — Direct crypto addresses for each supported coin
- `expires_at` — Charge expires after 60 minutes

### Check Charge Status

```bash
curl https://api.commerce.coinbase.com/charges/{charge_id} \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

Status timeline: `NEW` → `PENDING` → `CONFIRMED` / `FAILED` / `EXPIRED`

### List All Charges

```bash
curl https://api.commerce.coinbase.com/charges \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

### Cancel a Charge

```bash
curl -X POST https://api.commerce.coinbase.com/charges/{charge_id}/cancel \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

For detailed Coinbase Commerce reference, see `references/coinbase-rail.md`.

---

## Rail 3: Spraay (Batch Payments + x402 Micropayments)

Spraay is the batch payment and micropayment layer. Pay multiple recipients in a single transaction across 13+ blockchains, or use x402 micropayments for agent-to-agent commerce.

**What makes Spraay unique:** Neither Stripe nor Coinbase can send payments to multiple recipients at once. Spraay does this natively — pay your whole team, distribute tokens to a community, or airdrop to thousands of addresses in one transaction.

### Batch Payment (Multiple Recipients)

```bash
# Pay 3 people on Base in one transaction
curl -X POST "$SPRAAY_GATEWAY_URL/api/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "base",
    "token": "USDC",
    "recipients": [
      {"address": "0xAlice...", "amount": "100.00"},
      {"address": "0xBob...", "amount": "75.50"},
      {"address": "0xCharlie...", "amount": "200.00"}
    ]
  }'
```

### Single Send

```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "base",
    "token": "USDC",
    "to": "0xRecipient...",
    "amount": "50.00"
  }'
```

### Supported Chains (13+)

Base, Ethereum, Arbitrum, Polygon, BNB Chain, Avalanche, Unichain, Plasma, BOB, Solana, Bittensor, Stacks, Bitcoin

### x402 Micropayments (Agent-to-Agent)

x402 enables pay-per-request API calls. Your agent pays fractions of a cent per call — no subscriptions, no API keys, just HTTP payments.

```bash
# Any x402-enabled endpoint — payment happens via HTTP headers
curl "$SPRAAY_GATEWAY_URL/api/ai/inference" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "prompt": "Summarize this document"
  }'
```

The Spraay gateway has 76+ x402 endpoints across 16 categories:
- AI Inference, Search/RAG, Communication (Email, XMTP)
- IPFS/Storage, Compliance (KYC/AML), Oracle, GPU/Compute
- RPC (7 chains), Data Reads, Bridge, Escrow, Payroll
- Wallet Provisioning, DeFi Reads, Robot Task Protocol

### Bitcoin Batch Payments (PSBT)

```bash
# Prepare a Bitcoin batch transaction
curl -X POST "$SPRAAY_GATEWAY_URL/api/bitcoin/batch-prepare" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAddress": "bc1q...",
    "recipients": [
      {"address": "bc1qAlice...", "amountSats": 50000},
      {"address": "bc1qBob...", "amountSats": 75000}
    ],
    "feeRate": 10
  }'
```

For detailed Spraay reference, see `references/spraay-rail.md`.

---

## Cross-Rail Workflows

### Workflow: Accept fiat, pay team in crypto

1. Customer pays via Stripe → `pay stripe charge`
2. Confirm payment received → `pay status <stripe_pi_id>`
3. Batch pay your team in USDC via Spraay → `pay spraay batch`

### Workflow: Crypto invoice with fiat fallback

1. Create Coinbase Commerce charge → `pay coinbase charge`
2. If customer prefers fiat, create Stripe payment link → `pay stripe link`
3. Track both → `pay status <id>`

### Workflow: Agent-to-agent service payment

1. Agent A calls Agent B's API via x402 → `pay spraay x402`
2. Payment settles automatically via HTTP headers
3. No invoicing, no accounts, no API keys needed

### Workflow: Payroll (contractors worldwide)

1. US contractors → Stripe (ACH/direct deposit)
2. International contractors → Spraay batch (USDC on Base/Polygon)
3. One skill handles both rails

---

## Payment Status (Universal)

Check payment status across any rail:

```bash
# Stripe payment
./scripts/pay.sh status stripe pi_1234...

# Coinbase charge
./scripts/pay.sh status coinbase charge_5678...

# Spraay transaction
./scripts/pay.sh status spraay tx_9abc...
```

---

## Reference Docs

See `references/` for detailed documentation on each payment rail:
- `stripe-rail.md` — Full Stripe API reference (PaymentIntents, Invoices, Subscriptions, Customers)
- `coinbase-rail.md` — Coinbase Commerce API reference (Charges, Webhooks, Checkout)
- `spraay-rail.md` — Spraay Protocol reference (Batch payments, x402 gateway, Bitcoin PSBT, supported chains, RTP)

## Links

- **Stripe Docs:** https://docs.stripe.com
- **Coinbase Commerce Docs:** https://docs.cdp.coinbase.com/commerce
- **Spraay Gateway:** https://gateway.spraay.app
- **Spraay Docs:** https://docs.spraay.app
- **GitHub:** https://github.com/plagtech/agent-payments
