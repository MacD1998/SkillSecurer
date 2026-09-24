# Spraay Rail — Detailed Reference

## Overview

Spraay is the batch payment and micropayment protocol for AI agents. It does what Stripe and Coinbase Commerce can't:

- **Batch payments** — Pay multiple recipients in a single transaction (2 to 1000+ addresses)
- **Multi-chain** — 13+ blockchains from one API
- **x402 micropayments** — Pay-per-API-call for agent-to-agent commerce
- **Bitcoin PSBT** — Non-custodial batch payments on Bitcoin via PSBTs

## Gateway

Base URL: `https://gateway.spraay.app`

No API key required for x402 endpoints (payment happens via HTTP headers). Batch payment endpoints use the gateway directly.

## Batch Payments (EVM Chains)

### Execute Batch Payment

```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "base",
    "token": "USDC",
    "recipients": [
      {"address": "0xAlice...", "amount": "100.00"},
      {"address": "0xBob...", "amount": "75.50"},
      {"address": "0xCharlie...", "amount": "200.00"},
      {"address": "0xDave...", "amount": "50.00"}
    ]
  }'
```

### Supported EVM Chains

| Chain | Chain ID | Native Token | USDC |
|---|---|---|---|
| Base | 8453 | ETH | ✅ |
| Ethereum | 1 | ETH | ✅ |
| Arbitrum | 42161 | ETH | ✅ |
| Polygon | 137 | MATIC | ✅ |
| BNB Chain | 56 | BNB | ✅ |
| Avalanche | 43114 | AVAX | ✅ |
| Unichain | 130 | ETH | ✅ |
| Plasma | — | — | ✅ |
| BOB | — | ETH | ✅ |

### Non-EVM Chains

| Chain | Token Support | Notes |
|---|---|---|
| Solana | SOL, USDC, SPL tokens | TypeScript SDK |
| Bitcoin | BTC (sats) | PSBT-based, non-custodial |
| Stacks | STX | Clarity smart contract |
| Bittensor | TAO | Subnet payments |

### Single Send

```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/send" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "base",
    "token": "USDC",
    "to": "0xRecipient...",
    "amount": "250.00"
  }'
```

## Bitcoin Batch Payments (PSBT)

Non-custodial Bitcoin batch payments using Partially Signed Bitcoin Transactions:

### Prepare Batch

```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/bitcoin/batch-prepare" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAddress": "bc1qSender...",
    "recipients": [
      {"address": "bc1qAlice...", "amountSats": 50000},
      {"address": "bc1qBob...", "amountSats": 100000}
    ],
    "feeRate": 10
  }'
```

Returns unsigned PSBT hex. Sign with your wallet, then broadcast:

### Broadcast Signed Transaction

```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/bitcoin/batch-broadcast" \
  -H "Content-Type: application/json" \
  -d '{"signedTxHex": "0200000001..."}'
```

### Utility Endpoints

```bash
# Estimate fees
curl "$SPRAAY_GATEWAY_URL/api/bitcoin/fee-estimate"

# Check balance
curl "$SPRAAY_GATEWAY_URL/api/bitcoin/balance?address=bc1q..."

# List UTXOs
curl "$SPRAAY_GATEWAY_URL/api/bitcoin/utxos?address=bc1q..."

# Validate address
curl "$SPRAAY_GATEWAY_URL/api/bitcoin/validate?address=bc1q..."
```

## x402 Micropayments (Agent-to-Agent)

x402 is an HTTP-native payment protocol. Endpoints return `402 Payment Required` with pricing info. Your agent's x402 client handles payment automatically via HTTP headers.

### Gateway Categories (76+ endpoints)

**Category 1: AI Inference** ($0.01/call)
```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/ai/inference" \
  -d '{"model": "claude-sonnet-4-20250514", "prompt": "..."}'
```

**Category 2: Search & RAG** ($0.005/call)
```bash
curl "$SPRAAY_GATEWAY_URL/api/search?q=latest+defi+news"
```

**Category 3: Communication** ($0.005/call)
- Email (via AgentMail)
- XMTP messaging
- SMS (simulated)

**Category 4: IPFS/Storage** ($0.005/call)
```bash
curl -X POST "$SPRAAY_GATEWAY_URL/api/ipfs/pin" \
  -d '{"content": "..."}'
```

**Category 5: Compliance** ($0.01/call)
- KYC verification
- AML screening
- Sanctions check

**Category 6: Oracle** ($0.001/call)
- Price feeds
- Gas estimates

**Category 7: GPU/Compute** ($0.02/call)
- Image generation (Replicate)
- Model inference

**Category 8: RPC** ($0.001/call)
- 7 chains: Base, Ethereum, Arbitrum, Polygon, BNB, Avalanche, Optimism

**Category 9-14:** Data Reads, Bridge, Escrow, Payroll, Wallet Provisioning, DeFi Reads

**Category 15: Robot Task Protocol (RTP)** ($0.001–$0.02/call)
- Discover robots, commission tasks, track status
- AI agents can hire physical robots via x402 micropayments

**Category 16: Bitcoin** ($0.001–$0.02/call)
- PSBT batch prepare/broadcast, fee estimates, balance, UTXOs

## Payroll Use Case

Spraay batch payments are ideal for crypto payroll:

```bash
# Pay entire team in one transaction
curl -X POST "$SPRAAY_GATEWAY_URL/api/batch" \
  -d '{
    "chain": "base",
    "token": "USDC",
    "recipients": [
      {"address": "0xEmployee1...", "amount": "3500.00"},
      {"address": "0xEmployee2...", "amount": "4200.00"},
      {"address": "0xContractor1...", "amount": "2000.00"},
      {"address": "0xContractor2...", "amount": "1500.00"},
      {"address": "0xContractor3...", "amount": "800.00"}
    ]
  }'
```

One transaction, one gas fee, five people paid. Compare to five separate transfers.

## Protocol Fee

Batch payments: 0.3% protocol fee
x402 endpoints: per-request pricing (varies by category)

## MCP Server

For MCP-compatible AI agents (Claude, Cursor, etc.):
- **Smithery:** `@plagtech/spraay-x402-mcp`
- **MCP Registry:** `io.github.plagtech/spraay-x402-mcp`
- 66 tools covering all gateway endpoints

## Links

- Gateway: https://gateway.spraay.app
- Docs: https://docs.spraay.app
- GitHub: https://github.com/plagtech
- Twitter: https://x.com/Spraay_app
