# Coinbase Commerce Rail — Detailed Reference

## Overview

Coinbase Commerce lets you accept cryptocurrency payments from customers. They pay in BTC, ETH, USDC, DAI, or other supported assets. Funds settle to your Coinbase Commerce account. The Coinbase brand provides trust — customers recognize it.

## Authentication

All requests use the `X-CC-Api-Key` header:

```bash
curl https://api.commerce.coinbase.com/... \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" \
  -H "Content-Type: application/json"
```

Get your API key at: https://commerce.coinbase.com → Settings → API Keys

## Core Operations

### Create a Charge (Accept Payment)

A charge represents a single payment request:

```bash
curl -X POST https://api.commerce.coinbase.com/charges \
  -H "Content-Type: application/json" \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" \
  -d '{
    "name": "Freelance Work — March 2026",
    "description": "10 hours of development at $150/hr",
    "pricing_type": "fixed_price",
    "local_price": {
      "amount": "1500.00",
      "currency": "USD"
    },
    "metadata": {
      "customer_id": "client_42",
      "invoice_number": "INV-2026-003"
    },
    "redirect_url": "https://yoursite.com/payment/success",
    "cancel_url": "https://yoursite.com/payment/cancel"
  }'
```

**Response includes:**
- `data.id` — Charge ID for status checks
- `data.hosted_url` — Coinbase-hosted checkout page (send customer here)
- `data.addresses` — Direct crypto addresses (BTC, ETH, USDC, etc.)
- `data.pricing` — Amounts in each supported cryptocurrency
- `data.expires_at` — Charge expires after ~60 minutes

**Pricing types:**
- `fixed_price` — Specific amount in fiat (most common)
- `no_price` — Customer chooses how much to pay (donations)

### Retrieve a Charge

```bash
curl https://api.commerce.coinbase.com/charges/{charge_id} \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

### List All Charges

```bash
curl "https://api.commerce.coinbase.com/charges?limit=25&order=desc" \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

### Cancel a Charge

```bash
curl -X POST https://api.commerce.coinbase.com/charges/{charge_id}/cancel \
  -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY"
```

Only works for charges with status `NEW` (no payment detected yet).

## Charge Lifecycle

Timeline statuses:
1. `NEW` — Charge created, awaiting payment
2. `PENDING` — Payment detected on blockchain, waiting for confirmations
3. `COMPLETED` — Payment confirmed and settled
4. `EXPIRED` — No payment received before expiration (~60 min)
5. `CANCELED` — Charge was manually canceled
6. `UNRESOLVED` — Payment received but needs manual review (underpaid/overpaid)

## Supported Cryptocurrencies

Bitcoin (BTC), Ethereum (ETH), USD Coin (USDC), DAI, Litecoin (LTC), Bitcoin Cash (BCH), Dogecoin (DOGE), Shiba Inu (SHIB), and others depending on account settings.

## Webhooks

Configure webhook endpoint in Commerce dashboard → Settings → Webhook subscriptions.

Key events:
- `charge:created` — New charge created
- `charge:confirmed` — Payment confirmed
- `charge:failed` — Payment failed
- `charge:pending` — Payment detected, awaiting confirmations

Verify webhooks using the shared secret (Settings → Webhook subscriptions → Show shared secret):

```bash
# Webhook payload includes X-CC-Webhook-Signature header
# Verify: HMAC-SHA256 of raw body with shared secret
```

## Use Cases

**Accept payment for a product/service:**
Create a fixed_price charge, redirect customer to hosted_url.

**Donation page:**
Create a no_price charge, let customers choose the amount.

**Invoice in crypto:**
Create a charge with metadata linking to your internal invoice, send hosted_url to client.

**Automated payment tracking:**
Set up webhook to listen for `charge:confirmed`, update your database automatically.

## Links

- Dashboard: https://commerce.coinbase.com
- API Docs: https://docs.cdp.coinbase.com/commerce
- Node.js SDK: https://github.com/coinbase/coinbase-commerce-node
