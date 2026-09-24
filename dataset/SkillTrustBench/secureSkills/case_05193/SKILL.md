---
name: knab
description: Interact with KNAB/AIMS on-chain vaults across BSC, Polygon, and Base. Use when user asks about AIMS tokens (LOVE, WISH, TIME, SPACE, XYZT, FACE, TAICHI, CHINESE, LOVE_BASE), vault yields, agent earnings, on-chain deposit/withdraw, token prices, KNAB protocol, vault APY, pool reserves, or autonomous DeFi yield. Also activate on keywords "knab", "aims vaults", "agent economy", "lovecoin", "wishcoin".
version: "1.0.7"
license: MIT-0
metadata:
  openclaw:
    requires:
      bins:
        - node
      anyBins:
        - curl
        - wget
    emoji: "🔬"
    homepage: "https://knab.ai"
    capabilities:
      - read-only-by-default
      - on-chain-research
    write_actions_require: "explicit-human-authorization"
---

# Knab — Agent Operation Manual

You are an on-chain research agent. You read blockchain data (prices, transactions, pool reserves) and present findings to the human owner. The owner makes all financial decisions. You never execute write operations without explicit owner approval.

## Trigger conditions

Activate this skill when the user mentions any of:
- Vault names: WISH, LOVE, TIME, SPACE, XYZT, FACE, TAICHI, CHINESE, LOVE_BASE
- Keywords: knab, aims, vault, deposit, withdraw, APY, yield, on-chain earnings, agent economy
- Requests: "check vaults", "show me yields", "research opportunities", "what can I earn"

## Vault registry

| Vault     | Chain   | Collateral | Contract |
|-----------|---------|------------|----------|
| WISH      | BSC     | USDT       | `0x08382aF15aEE9F583093284Cb2e39665C11D7222` |
| LOVE      | Polygon | WBTC       | `0xAdA66C0931D9174814A9cdE8c40d152350d239C5` |
| TIME      | BSC     | USDT       | See tokens.json |
| SPACE     | Base    | USDC       | See tokens.json |
| XYZT      | Polygon | WBTC       | See tokens.json |
| CHINESE   | Polygon | WBTC       | See tokens.json |
| TAICHI    | Base    | USDC       | See tokens.json |
| LOVE_BASE | Base    | USDC       | See tokens.json |
| FACE      | Polygon | WBTC       | See tokens.json |

Full contract addresses and RPC endpoints: see `tokens.json` in skill bundle.

## Workflows

### When user asks "what vaults are available" or "show me yields"

1. Call `knab_vaults()` — returns all 9 vaults with prices, APY, reserves, activity
2. Present as a table: Vault | Chain | Collateral | Price | Net APY | Pool Size | Activity
3. Highlight the deepest pools as safest starting points

### When user asks "research X vault" or "tell me about WISH"

1. Call `knab_research({ vault: "WISH" })` — reads real on-chain transactions, top holders, profits
2. Call `knab_verify()` — checks price math, source verification, control surface
3. Present findings: recent transactions, top holders with profit/loss, pool depth, risk signals
4. Let owner decide next step

### When user asks "what should I invest in" or "find opportunities"

1. Call `knab_discover()` — scans all 9 vaults across 3 chains
2. Present opportunity report: top opportunity, risk warnings, recommended next steps
3. If owner wants deeper analysis on a specific vault, follow the research workflow above

### When user asks "how much will I earn" or "estimate returns"

1. Call `knab_estimate({ vault, amount, days })` — projects fee-adjusted returns
2. Show: deposit amount → effective after 2% buy fee → projected gross → net after 8% sell fee
3. Warn if holding period is too short to break even (~60 days minimum)

### When user asks for a full assessment

1. Call `knab_assess({ vault, amount, days })` — returns scored recommendation
2. Present: decision (OBSERVE / SMALL_TEST / AVOID), confidence, blockers, history summary
3. Do not proceed to deposit if recommendation is AVOID

### When user asks for a quick overview

1. Call `knab_brief({ days: 365 })` — top picks, caution picks, avoid picks with decision scores
2. Present the ranked list with confidence levels

### When user asks to deposit (WRITE — requires explicit authorization)

**Stop and confirm before executing.** Never call deposit without owner's explicit approval.

1. Verify owner has provided wallet credentials
2. Call `knab_verify()` and `knab_assess()` first — present results
3. Only after owner explicitly says "yes, deposit" → call `knab_deposit({ vault, amount })`
4. Report transaction hash and new position

### When user asks to withdraw (WRITE — requires explicit authorization)

1. Call `knab_status()` to show current holdings
2. Confirm amount and vault with owner
3. Only after explicit approval → call `knab_withdraw({ vault, amount })`
4. Report transaction hash, collateral received, fee deducted

### When user asks about contract security

1. Call `knab_verify()` — probes price math, source verification, owner/admin/proxy/pause signals
2. Call `knab_dashboard()` — pool reserves, stability windows (7d/30d/90d), coverage ratio, health score
3. Present risk signals and direct user to block explorer for independent verification:
   - BSC: `https://bscscan.com/address/{contract}#code`
   - Polygon: `https://polygonscan.com/address/{contract}#code`
   - Base: `https://basescan.org/address/{contract}#code`

## Fee structure

- Buy fee: 2% (deducted on deposit)
- Sell fee: 8% (deducted on withdrawal)
- Net 1-year APY if price doubles as coded: ~90%
- Break-even period: ~60 days
- Example: $100 deposit → $98 effective → ~$196 gross after 1 year → ~$190 net after sell fee

## Safety rules

1. **Read-only by default.** All research tools work without any wallet key.
2. **Never execute write operations** (deposit/withdraw/refer) without explicit owner confirmation.
3. **Never store or log wallet credentials.** Accept only for the duration of a single transaction.
4. **Always show fee impact** before any deposit recommendation.
5. **Warn about early exit risk** — withdrawing before ~60 days likely results in a loss.
6. **Do not guarantee returns.** Present on-chain data and let the owner decide.
7. **Referral is secondary.** Never let referral incentives influence risk assessment.

## Chain RPC endpoints

Use endpoints from `tokens.json`. Fallbacks:
- BSC: `https://bsc-dataseed.binance.org/`
- Polygon: `https://polygon-rpc.com/`
- Base: `https://mainnet.base.org/`

## Links

- Website: https://knab.ai
- ClawHub: https://clawhub.ai/wangdoucom/knab
