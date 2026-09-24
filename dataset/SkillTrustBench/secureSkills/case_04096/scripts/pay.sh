#!/bin/bash
# pay.sh — Universal payment router for Agent Payments skill
# Routes commands across Stripe, Coinbase Commerce, and Spraay
#
# Usage: pay.sh <rail> <command> [args...]
#   pay.sh stripe charge --amount 2000 --currency usd
#   pay.sh coinbase charge --amount 100.00 --name "Service"
#   pay.sh spraay batch --chain base --token USDC --file recipients.json
#   pay.sh status stripe pi_1234...
#   pay.sh status coinbase charge_5678...

set -euo pipefail

STRIPE_URL="https://api.stripe.com/v1"
COINBASE_URL="https://api.commerce.coinbase.com"
SPRAAY_URL="${SPRAAY_GATEWAY_URL:-https://gateway.spraay.app}"

# ─── Stripe Rail ───────────────────────────────────────────────

stripe_charge() {
  local amount="" currency="usd" description="" email="" customer=""
  while [[ $# -gt 0 ]]; do
    case $1 in
      --amount) amount="$2"; shift 2 ;;
      --currency) currency="$2"; shift 2 ;;
      --description) description="$2"; shift 2 ;;
      --email) email="$2"; shift 2 ;;
      --customer) customer="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  local args=(-X POST "$STRIPE_URL/payment_intents" -u "$STRIPE_SECRET_KEY:")
  args+=(-d "amount=$amount" -d "currency=$currency" -d "payment_method_types[]=card")
  [[ -n "$description" ]] && args+=(-d "description=$description")
  [[ -n "$email" ]] && args+=(-d "receipt_email=$email")
  [[ -n "$customer" ]] && args+=(-d "customer=$customer")

  curl -s "${args[@]}" | jq .
}

stripe_invoice() {
  local customer="" amount="" currency="usd" description="" days_due=30
  while [[ $# -gt 0 ]]; do
    case $1 in
      --customer) customer="$2"; shift 2 ;;
      --amount) amount="$2"; shift 2 ;;
      --currency) currency="$2"; shift 2 ;;
      --description) description="$2"; shift 2 ;;
      --days) days_due="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  # Create invoice item
  curl -s -X POST "$STRIPE_URL/invoiceitems" -u "$STRIPE_SECRET_KEY:" \
    -d "customer=$customer" -d "amount=$amount" -d "currency=$currency" \
    -d "description=$description" | jq .

  # Create, finalize, and send invoice
  local inv_id
  inv_id=$(curl -s -X POST "$STRIPE_URL/invoices" -u "$STRIPE_SECRET_KEY:" \
    -d "customer=$customer" -d "collection_method=send_invoice" \
    -d "days_until_due=$days_due" | jq -r '.id')

  curl -s -X POST "$STRIPE_URL/invoices/$inv_id/finalize" -u "$STRIPE_SECRET_KEY:" | jq .
  curl -s -X POST "$STRIPE_URL/invoices/$inv_id/send" -u "$STRIPE_SECRET_KEY:" | jq .
}

stripe_link() {
  local price="" quantity=1
  while [[ $# -gt 0 ]]; do
    case $1 in
      --price) price="$2"; shift 2 ;;
      --quantity) quantity="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  curl -s -X POST "$STRIPE_URL/payment_links" -u "$STRIPE_SECRET_KEY:" \
    -d "line_items[0][price]=$price" -d "line_items[0][quantity]=$quantity" | jq .
}

stripe_refund() {
  local pi_id="$1" amount=""
  [[ $# -gt 1 ]] && amount="$2"

  local args=(-X POST "$STRIPE_URL/refunds" -u "$STRIPE_SECRET_KEY:" -d "payment_intent=$pi_id")
  [[ -n "$amount" ]] && args+=(-d "amount=$amount")

  curl -s "${args[@]}" | jq .
}

# ─── Coinbase Commerce Rail ────────────────────────────────────

coinbase_charge() {
  local name="" description="" amount="" currency="USD"
  while [[ $# -gt 0 ]]; do
    case $1 in
      --name) name="$2"; shift 2 ;;
      --description) description="$2"; shift 2 ;;
      --amount) amount="$2"; shift 2 ;;
      --currency) currency="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  curl -s -X POST "$COINBASE_URL/charges" \
    -H "Content-Type: application/json" \
    -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" \
    -d "{
      \"name\": \"$name\",
      \"description\": \"$description\",
      \"pricing_type\": \"fixed_price\",
      \"local_price\": {
        \"amount\": \"$amount\",
        \"currency\": \"$currency\"
      }
    }" | jq .
}

coinbase_list() {
  curl -s "$COINBASE_URL/charges?limit=25" \
    -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" | jq .
}

coinbase_cancel() {
  local charge_id="$1"
  curl -s -X POST "$COINBASE_URL/charges/$charge_id/cancel" \
    -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" | jq .
}

# ─── Spraay Rail ───────────────────────────────────────────────

spraay_batch() {
  local chain="base" token="USDC" file=""
  while [[ $# -gt 0 ]]; do
    case $1 in
      --chain) chain="$2"; shift 2 ;;
      --token) token="$2"; shift 2 ;;
      --file) file="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -n "$file" ]]; then
    local recipients
    recipients=$(cat "$file")
    curl -s -X POST "$SPRAAY_URL/api/batch" \
      -H "Content-Type: application/json" \
      -d "{\"chain\": \"$chain\", \"token\": \"$token\", \"recipients\": $recipients}" | jq .
  else
    echo "Error: --file required with JSON array of {address, amount} objects"
    exit 1
  fi
}

spraay_send() {
  local chain="base" token="USDC" to="" amount=""
  while [[ $# -gt 0 ]]; do
    case $1 in
      --chain) chain="$2"; shift 2 ;;
      --token) token="$2"; shift 2 ;;
      --to) to="$2"; shift 2 ;;
      --amount) amount="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  curl -s -X POST "$SPRAAY_URL/api/send" \
    -H "Content-Type: application/json" \
    -d "{\"chain\": \"$chain\", \"token\": \"$token\", \"to\": \"$to\", \"amount\": \"$amount\"}" | jq .
}

spraay_bitcoin_batch() {
  local from="" file="" fee_rate=10
  while [[ $# -gt 0 ]]; do
    case $1 in
      --from) from="$2"; shift 2 ;;
      --file) file="$2"; shift 2 ;;
      --fee-rate) fee_rate="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  local recipients
  recipients=$(cat "$file")
  curl -s -X POST "$SPRAAY_URL/api/bitcoin/batch-prepare" \
    -H "Content-Type: application/json" \
    -d "{\"fromAddress\": \"$from\", \"recipients\": $recipients, \"feeRate\": $fee_rate}" | jq .
}

# ─── Universal Status ─────────────────────────────────────────

check_status() {
  local rail="$1" id="$2"
  case $rail in
    stripe)
      curl -s "$STRIPE_URL/payment_intents/$id" -u "$STRIPE_SECRET_KEY:" | jq '{id: .id, status: .status, amount: .amount, currency: .currency}'
      ;;
    coinbase)
      curl -s "$COINBASE_URL/charges/$id" -H "X-CC-Api-Key: $COINBASE_COMMERCE_API_KEY" | jq '{id: .data.id, status: .data.timeline[-1].status, amount: .data.pricing.local.amount}'
      ;;
    spraay)
      curl -s "$SPRAAY_URL/api/status/$id" | jq .
      ;;
    *)
      echo "Unknown rail: $rail (use stripe, coinbase, or spraay)"
      exit 1
      ;;
  esac
}

# ─── Router ────────────────────────────────────────────────────

case "${1:-help}" in
  stripe)
    case "${2:-help}" in
      charge) shift 2; stripe_charge "$@" ;;
      invoice) shift 2; stripe_invoice "$@" ;;
      link) shift 2; stripe_link "$@" ;;
      refund) shift 2; stripe_refund "$@" ;;
      *) echo "Stripe commands: charge, invoice, link, refund" ;;
    esac
    ;;
  coinbase)
    case "${2:-help}" in
      charge) shift 2; coinbase_charge "$@" ;;
      list) coinbase_list ;;
      cancel) shift 2; coinbase_cancel "$@" ;;
      *) echo "Coinbase commands: charge, list, cancel" ;;
    esac
    ;;
  spraay)
    case "${2:-help}" in
      batch) shift 2; spraay_batch "$@" ;;
      send) shift 2; spraay_send "$@" ;;
      bitcoin) shift 2; spraay_bitcoin_batch "$@" ;;
      *) echo "Spraay commands: batch, send, bitcoin" ;;
    esac
    ;;
  status)
    check_status "${2:-}" "${3:-}"
    ;;
  *)
    echo "💳 Agent Payments — Universal Payment Router"
    echo ""
    echo "Usage: pay.sh <rail> <command> [options]"
    echo ""
    echo "Rails:"
    echo "  stripe    — Fiat payments (charges, invoices, subscriptions)"
    echo "  coinbase  — Crypto acceptance (BTC, ETH, USDC via Coinbase)"
    echo "  spraay    — Batch payments + x402 micropayments (13+ chains)"
    echo ""
    echo "Universal:"
    echo "  status <rail> <id>  — Check payment status on any rail"
    echo ""
    echo "Examples:"
    echo "  pay.sh stripe charge --amount 5000 --currency usd"
    echo "  pay.sh coinbase charge --name 'Invoice' --amount 100.00"
    echo "  pay.sh spraay batch --chain base --token USDC --file recipients.json"
    echo "  pay.sh spraay send --to 0x... --amount 50.00"
    echo "  pay.sh status stripe pi_1234..."
    ;;
esac
