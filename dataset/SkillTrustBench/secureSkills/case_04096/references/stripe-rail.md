# Stripe Rail — Detailed Reference

## Overview

Stripe handles fiat payments: credit/debit cards, ACH bank transfers, Apple Pay, Google Pay, and 40+ local payment methods. Your agent can create charges, send invoices, manage subscriptions, and generate shareable payment links.

## Authentication

All requests use HTTP Basic Auth with your secret key:

```bash
curl https://api.stripe.com/v1/... -u "$STRIPE_SECRET_KEY:"
```

Note the trailing colon — Stripe uses the key as the username with no password.

## Core Operations

### Customers

Create a customer record to associate payments:

```bash
# Create
curl -X POST https://api.stripe.com/v1/customers \
  -u "$STRIPE_SECRET_KEY:" \
  -d email="alice@example.com" \
  -d name="Alice Johnson" \
  -d "metadata[internal_id]"="user_123"

# Retrieve
curl https://api.stripe.com/v1/customers/cus_... -u "$STRIPE_SECRET_KEY:"

# List
curl https://api.stripe.com/v1/customers?limit=10 -u "$STRIPE_SECRET_KEY:"
```

### Payment Intents (One-Time Charges)

The primary way to collect payments:

```bash
curl -X POST https://api.stripe.com/v1/payment_intents \
  -u "$STRIPE_SECRET_KEY:" \
  -d amount=5000 \
  -d currency=usd \
  -d customer="cus_..." \
  -d "payment_method_types[]"=card \
  -d description="Consulting — 1 hour" \
  -d receipt_email="customer@example.com" \
  -d "metadata[project]"="website-redesign"
```

**Amount is in cents:** 5000 = $50.00, 999 = $9.99

**Statuses:**
- `requires_payment_method` — Waiting for customer to provide payment details
- `requires_confirmation` — Ready to confirm
- `requires_action` — Customer needs to complete authentication (3D Secure)
- `processing` — Payment is being processed
- `succeeded` — Payment complete
- `canceled` — Payment was canceled

### Invoices

Send professional invoices that customers can pay online:

```bash
# 1. Create invoice items (line items)
curl -X POST https://api.stripe.com/v1/invoiceitems \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d amount=15000 \
  -d currency=usd \
  -d description="Website development — Phase 1"

curl -X POST https://api.stripe.com/v1/invoiceitems \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d amount=5000 \
  -d currency=usd \
  -d description="Domain registration and hosting setup"

# 2. Create the invoice
curl -X POST https://api.stripe.com/v1/invoices \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d collection_method=send_invoice \
  -d days_until_due=30

# 3. Finalize (locks the invoice)
curl -X POST https://api.stripe.com/v1/invoices/{inv_id}/finalize \
  -u "$STRIPE_SECRET_KEY:"

# 4. Send to customer
curl -X POST https://api.stripe.com/v1/invoices/{inv_id}/send \
  -u "$STRIPE_SECRET_KEY:"
```

### Subscriptions

Recurring billing:

```bash
# Create a product and price first
curl -X POST https://api.stripe.com/v1/products \
  -u "$STRIPE_SECRET_KEY:" \
  -d name="Pro Plan"

curl -X POST https://api.stripe.com/v1/prices \
  -u "$STRIPE_SECRET_KEY:" \
  -d product="prod_..." \
  -d unit_amount=2999 \
  -d currency=usd \
  -d "recurring[interval]"=month

# Create subscription
curl -X POST https://api.stripe.com/v1/subscriptions \
  -u "$STRIPE_SECRET_KEY:" \
  -d customer="cus_..." \
  -d "items[0][price]"="price_..."
```

### Payment Links (No-Code Checkout)

Generate a shareable URL that anyone can use to pay:

```bash
curl -X POST https://api.stripe.com/v1/payment_links \
  -u "$STRIPE_SECRET_KEY:" \
  -d "line_items[0][price]"="price_..." \
  -d "line_items[0][quantity]"=1 \
  -d after_completion[type]=redirect \
  -d "after_completion[redirect][url]"="https://yoursite.com/thanks"
```

### Refunds

```bash
# Full refund
curl -X POST https://api.stripe.com/v1/refunds \
  -u "$STRIPE_SECRET_KEY:" \
  -d payment_intent="pi_..."

# Partial refund
curl -X POST https://api.stripe.com/v1/refunds \
  -u "$STRIPE_SECRET_KEY:" \
  -d payment_intent="pi_..." \
  -d amount=1000
```

## Supported Currencies

USD, EUR, GBP, CAD, AUD, JPY, CNY, and 130+ more. Full list at stripe.com/docs/currencies.

## Webhooks

Stripe sends events for payment status changes. Key events:
- `payment_intent.succeeded` — Payment completed
- `payment_intent.payment_failed` — Payment failed
- `invoice.paid` — Invoice was paid
- `customer.subscription.created` — New subscription started
- `customer.subscription.deleted` — Subscription canceled

## Error Handling

Stripe returns structured errors:
- `card_declined` — Customer's card was declined
- `insufficient_funds` — Not enough balance
- `expired_card` — Card has expired
- `rate_limit` — Too many requests (back off and retry)

## Links

- API Reference: https://docs.stripe.com/api
- Dashboard: https://dashboard.stripe.com
- Test Mode: Use `sk_test_...` keys for testing (no real charges)
