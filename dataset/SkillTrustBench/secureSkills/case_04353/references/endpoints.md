# AgentCanary — Full Endpoint Reference

Base URL: `https://api.agentcanary.ai/api`
Auth: `?apikey={key}` (query param on all requests)

## Table of Contents

1. [Key Management & Billing](#key-management--billing)
2. [Indicators](#indicators)
3. [Scenarios](#scenarios)
4. [Briefs](#briefs)
5. [Macro](#macro)
6. [Regime](#regime)
7. [Signals](#signals)
8. [Narratives](#narratives)
9. [Expectations](#expectations)
10. [DeFi](#defi)
11. [BTC Options](#btc-options)
12. [Central Banks](#central-banks)
13. [Premiums](#premiums)
14. [Predictions](#predictions)
15. [Sentiment](#sentiment)
16. [Mean Reversion](#mean-reversion)
17. [Hindenburg Omen](#hindenburg-omen)
18. [CAPE Ratio](#cape-ratio)
19. [Kill Conditions](#kill-conditions)
20. [Crypto Re-entry](#crypto-re-entry)
21. [Institutional](#institutional)
22. [News Intelligence](#news-intelligence)
23. [Data Endpoints](#data-endpoints)

---

## Key Management & Billing

These endpoints handle authentication and payments. Not gated by tier.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/keys/create` | Create API key. Body: `{ walletAddress }` |
| POST | `/keys/rotate` | Rotate API key |
| GET | `/keys/balance` | Check credit balance and tier |
| GET | `/keys/info` | Full key info |
| GET | `/billing/pricing` | Public pricing and tier info |
| POST | `/billing/verify` | Verify payment by tx hash. Body: `{ apiKey, txHash }` |
| POST | `/billing/check` | Auto-detect payment. Body: `{ apiKey }` |

### Key Creation Response
```json
{
  "success": true,
  "apiKey": "ac_...",
  "tier": "explorer",
  "credits": 0,
  "rateLimit": { "rpm": 10, "rpd": 50 }
}
```

### Balance Response
```json
{
  "credits": 250,
  "tier": "builder",
  "cumulativeDepositsUsd": 55,
  "rateLimit": { "rpm": 60, "rpd": 5000 }
}
```

---

## Indicators

AC proprietary indicators with history and summary views. 36 indicators across macro, technical, crypto, and liquidity categories.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/indicators` | Explorer | List all 36 available indicators |
| GET | `/indicators/summary` | Builder | Dashboard summary of all indicators |
| GET | `/indicators/:name` | Varies | Single indicator current value |
| GET | `/indicators/:name/history` | Varies | Historical values for indicator |

### Featured Indicator: Bull Market Support Band

The Bull Market Support Band (BMSB) is a widely-used BTC cycle indicator combining the 20-week SMA and 21-week EMA. When BTC trades above both, bull structure is intact. Below = broken.

**Request:** `GET /indicators/bull-market-support-band`

**Response:**
```json
{
  "indicator": "bull-market-support-band",
  "category": "technical",
  "tier": "builder",
  "date": "2026-03-18",
  "signal": "bearish",
  "level": "BELOW_BAND",
  "btcPrice": 74495.15,
  "bmsb": 79644,
  "sma20w": 79754,
  "ema21w": 79534,
  "pctFromBand": -6.46,
  "interpretation": "BTC 6.5% below BMSB. Bull market structure broken.",
  "timestamp": "2026-03-18T04:04:53.830Z"
}
```

**Signal values:** `bullish` (above band) | `bearish` (below band) | `cautious` (testing band)
**Level values:** `ABOVE_BAND` | `BELOW_BAND` | `TESTING_BAND`

### Available Indicators (36 total)

| Indicator | Category | Tier |
|-----------|----------|------|
| `composite-risk-score` | macro | explorer |
| `sector-rotation` | macro | signal |
| `dispersion-regime` | macro | signal |
| `cape-ratio` | macro | signal |
| `hindenburg-omen` | macro | signal |
| `narrative-momentum` | narrative | signal |
| `geopolitical-risk` | macro | signal |
| `insider-signals` | institutional | signal |
| `oil-futures-curve` | macro | builder |
| `war-commodity-disruption` | macro | signal |
| `21ema-trend` | technical | builder |
| `alt-funding-spike` | crypto | signal |
| `alt-volatility-spike` | crypto | signal |
| `btc-dominance` | crypto | builder |
| `btc-leverage-risk` | crypto | signal |
| `btc-liquidation-heatmap` | crypto | signal |
| `btc-momentum-reversal` | technical | signal |
| `btc-exchange-flows` | crypto | signal |
| `btc-oi-funding` | crypto | signal |
| `btc-orderbook-imbalance` | crypto | signal |
| `btc-pi-cycle` | technical | builder |
| `btc-quintile-model` | technical | signal |
| `btc-whale-activity` | crypto | signal |
| `bull-market-support-band` | technical | builder |
| `cross-asset-volatility` | macro | signal |
| `derivatives-structure-shift` | crypto | signal |
| `ethbtc-ratio` | crypto | builder |
| `global-safety-override` | macro | signal |
| `gold-btc-correlation` | macro | signal |
| `large-trades-whale-orders` | crypto | signal |
| `liquidation-ranges` | crypto | signal |
| `ma-trend-reversal` | technical | signal |
| `midtier-alt-crash` | crypto | signal |
| `social-sentiment` | sentiment | signal |
| `stablecoin-composite` | liquidity | builder |
| `stablecoin-vs-tcmc` | liquidity | signal |
| `wyckoff-structure` | technical | signal |

---

## Scenarios

Macro scenario modeling with probability assignments.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/scenarios/current` | Signal | Current scenario probabilities (6 scenarios) |
| GET | `/scenarios/history` | Signal | Historical scenario probability changes |
| GET | `/scenarios/signals` | Signal | Signals driving scenario shifts |

### Response (`/scenarios/current`)
```json
{
  "scenarios": [
    { "name": "Soft Landing", "probability": 0.35, "description": "..." },
    { "name": "Stagflation", "probability": 0.15, "description": "..." }
  ],
  "timestamp": "2026-03-13T00:00:00Z"
}
```

---

## Briefs

4× daily AI-generated market intelligence reports.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/briefs/latest` | Explorer | Latest brief (free teaser) |
| GET | `/briefs/feed` | Builder | Recent briefs feed |
| GET | `/briefs/archive` | Signal | Full brief archive |
| GET | `/briefs/:type` | Varies | Specific brief type: `radar`, `signal`, `pulse`, `wrap` |

Brief schedule (UTC): Radar 04:15, Signal 10:15, Pulse 16:15, Wrap 22:15.

---

## Macro

Macro regime detection, liquidity, and economic indicators.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/macro/regime` | Explorer | Current regime label, flags, composite scores |
| GET | `/macro/snapshot` | Builder | Full snapshot: 30+ FRED series, z-scores, business cycle |
| GET | `/macro/signals` | Builder | Macro signals summary |
| GET | `/macro/global-liquidity` | Builder | Global liquidity conditions (central bank aggregate) |
| GET | `/macro/us-m2` | Builder | US M2 money supply |
| GET | `/macro/central-banks` | Builder | Central bank policy summary |
| GET | `/macro/supply-chain` | Builder | Supply chain stress indicators |
| GET | `/macro/calendar-high-impact` | Builder | High-impact economic events |

### Response (`/macro/regime`)
```json
{
  "regime": {
    "label": "Risk-On · Neutral",
    "flags": ["RISK_ON", "LOW_STRESS"],
    "scores": {
      "riskOn": 5.69,
      "tightening": 0,
      "inflation": -1.35,
      "liquidity": 1.10,
      "stress": 0.50
    },
    "explanation": "Clear risk-on conditions..."
  },
  "asOf": "2026-03-13T06:00:00Z"
}
```

---

## Regime

Detailed regime classification with matrix view and history.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/regime` | Signal | Current regime state |
| GET | `/regime/matrix` | Signal | Multi-factor regime matrix |
| GET | `/regime/history` | Signal | Regime transitions over time |

---

## Signals

32 signal endpoints covering cross-asset correlations, positioning, and market structure.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/signals/correlations` | Signal | Cross-asset correlation matrix |
| GET | `/signals/attention` | Signal | Asset attention scores |
| GET | `/signals/attention/:ticker` | Signal | Single asset attention detail |
| GET | `/signals/insider-trades` | Signal | Insider trading activity |
| GET | `/signals/signal-stats` | Signal | Signal state statistics |
| GET | `/signals/treasury-rankings` | Signal | Treasury holding rankings |
| GET | `/signals/treasury-concentration` | Signal | Treasury concentration metrics |
| GET | `/signals/btc-orderbook` | Signal | BTC orderbook analytics |
| GET | `/signals/market-structure` | Signal | Market structure composite |
| GET | `/signals/vix` | Signal | VIX analysis |
| GET | `/signals/dxy` | Signal | Dollar index analysis |
| GET | `/signals/yield-curve` | Signal | Yield curve analysis |
| GET | `/signals/oil` | Signal | Oil market analysis |
| GET | `/signals/icsa` | Signal | Initial claims (labor) |
| GET | `/signals/credit-stress` | Signal | Credit stress indicators |
| GET | `/signals/cape-ratio` | Signal | Shiller CAPE ratio |
| GET | `/signals/hindenburg-omen` | Signal | Hindenburg omen status |
| GET | `/signals/geopolitical-risk` | Signal | Geopolitical risk index |
| GET | `/signals/dispersion` | Signal | Market dispersion metrics |
| GET | `/signals/sector-rotation` | Signal | Sector rotation signals |
| GET | `/signals/insider-activity` | Signal | Aggregate insider activity |
| GET | `/signals/btc-etf-flows` | Signal | Bitcoin ETF flow analysis |
| GET | `/signals/fear-greed` | Signal | Fear & Greed composite |
| GET | `/signals/funding-rates` | Signal | Funding rate analysis |
| GET | `/signals/whale-positions` | Signal | Whale position analysis |
| GET | `/signals/stablecoin-dominance` | Signal | Stablecoin dominance signals |
| GET | `/signals/bofa-fms` | Signal | BofA Fund Manager Survey |
| GET | `/signals/bofa-crowded` | Signal | BofA most crowded trades |
| GET | `/signals/cftc-cot` | Signal | CFTC Commitment of Traders |
| GET | `/signals/sector/:ticker` | Signal | Single sector analysis |
| GET | `/signals/whale-alerts` | Signal | Whale alert analysis |
| GET | `/signals/decision-engine` | Signal | Multi-factor decision engine |

---

## Narratives

Narrative theme tracking with crowding scores (21 themes).

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/narratives` | Signal | All narrative scores (crowding 1–5) |
| GET | `/narratives/history` | Signal | Historical narrative scores |
| GET | `/narratives/:name` | Signal | Single narrative detail |

### Response (`/narratives`)
```json
{
  "narratives": [
    { "name": "AI", "score": 4.2, "momentum": "rising", "assets": ["NVDA", "MSFT", "GOOGL"] },
    { "name": "Energy", "score": 2.8, "momentum": "flat", "assets": ["XLE", "CVX", "XOM"] }
  ]
}
```

---

## Expectations

Market expectations, rotation signals, and crowded trades.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/expectations` | Signal | Current market expectations summary |
| GET | `/expectations/rotation` | Signal | Sector/asset rotation signals |
| GET | `/expectations/crowded` | Signal | Most crowded trades |
| GET | `/expectations/early` | Signal | Early-stage narrative detection |
| GET | `/expectations/:narrative` | Signal | Single narrative expectations |

---

## DeFi

DeFi protocol intelligence: yields, PE ratios, token unlocks, perpetuals.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/defi/intelligence` | Signal | DeFi market overview |
| GET | `/defi/pe-ratios` | Signal | Protocol PE ratios |
| GET | `/defi/pe-ratios/apps-vs-l1s` | Signal | Apps vs L1 valuation comparison |
| GET | `/defi/pe-ratios/:tier` | Signal | PE ratios by tier (blue-chip, mid, small) |
| GET | `/defi/yields` | Signal | DeFi yield opportunities |
| GET | `/defi/yields/stable` | Signal | Stablecoin yield strategies |
| GET | `/defi/perps` | Signal | Perpetual DEX analytics |
| GET | `/defi/stablecoins` | Signal | Stablecoin market analytics |
| GET | `/defi/chains` | Signal | L1/L2 chain metrics (TVL, fees, users) |
| GET | `/defi/unlocks` | Signal | Upcoming token unlocks |
| GET | `/defi/signals` | Signal | DeFi-specific trading signals |

---

## BTC Options

Bitcoin options market data: max pain, skew, open interest.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/btc-options` | Signal | BTC options overview |
| GET | `/btc-options/maxpain` | Signal | Max pain by expiry |
| GET | `/btc-options/skew` | Signal | Put/call skew analysis |

---

## Central Banks

Central bank balance sheets, reserves, and policy analysis.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/central-banks` | Signal | Central bank policy overview |
| GET | `/central-banks/balance-sheets` | Signal | Balance sheet data (Fed, ECB, BOJ, etc.) |
| GET | `/central-banks/btc` | Signal | Central bank BTC exposure/policy |
| GET | `/central-banks/stablecoins` | Signal | Central bank stablecoin policy |
| GET | `/central-banks/gold` | Signal | Gold reserves by country |
| GET | `/central-banks/reserves` | Signal | Foreign reserves data |
| GET | `/central-banks/tic` | Signal | Treasury International Capital flows |

---

## Premiums

Exchange premiums and arbitrage indicators.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/premiums` | Signal | Premium overview |
| GET | `/premiums/coinbase` | Signal | Coinbase premium index |
| GET | `/premiums/kimchi` | Signal | Korea (Kimchi) premium |

---

## Predictions

Prediction market tracking (Polymarket).

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/predictions` | Signal | All tracked prediction markets |
| GET | `/predictions/movers` | Signal | Biggest probability movers |
| GET | `/predictions/:slug` | Signal | Single market detail |

---

## Sentiment

Social sentiment analysis.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/sentiment/reddit` | Signal | Reddit cross-subreddit sentiment (14 subs) |

---

## Mean Reversion

Mean reversion trading signals.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/mr/signals` | Signal | Current mean reversion signals |
| GET | `/mr/trades` | Signal | Active/recent MR trades |
| GET | `/mr/stats` | Signal | MR strategy statistics |

---

## Hindenburg Omen

Market breadth warning indicator.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/hindenburg` | Signal | Current Hindenburg omen status |
| GET | `/hindenburg/history` | Signal | Historical occurrences |

---

## CAPE Ratio

Shiller Cyclically Adjusted PE Ratio.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/cape` | Signal | Current CAPE ratio and percentile |

---

## Kill Conditions

Hard stop conditions that should halt all trading.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/kill-conditions` | Signal | Active kill conditions (if any) |

---

## Crypto Re-entry

Multi-factor crypto re-entry framework scoring.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/crypto-reentry` | Signal | Current re-entry score and factors |
| GET | `/crypto-reentry/history` | Signal | Historical re-entry scores |

---

## Institutional

Institutional positioning data.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/institutional/13f` | Signal | 13F filing analysis |

---

## News Intelligence

Processed news with trending analysis and AI summaries.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| GET | `/news/trending` | Signal | Trending tickers from news flow |
| GET | `/news/stats` | Signal | News volume statistics |
| GET | `/news/market-analysis` | Signal | AI market analysis from news |
| GET | `/news/xtg-analysis` | Signal | X/Telegram message analysis |

---

## Data Endpoints

Cached dataset access via `/api/data/:name`. Refreshed on schedule (varies by dataset).

### Prices & Markets

| Dataset | Tier | Description |
|---------|------|-------------|
| `realtime-prices` | Explorer | 100+ crypto tokens with 24h change |
| `yahoo-quotes` | Builder | SPY, QQQ, VIX, TLT, DXY, Oil, Brent, 16 sector ETFs, stocks |
| `exchange-volumes` | Builder | Exchange trading volumes |

### Macro & Regime

| Dataset | Tier | Description |
|---------|------|-------------|
| `macro-snapshot` | Builder | 30+ FRED series, regime, risk gauge, z-scores |
| `vix-term-structure` | Builder | VIX term structure (contango/backwardation) |
| `cftc-cot` | Signal | CFTC Commitment of Traders positioning |
| `treasury-stats` | Signal | US Treasury statistics |

### Crypto

| Dataset | Tier | Description |
|---------|------|-------------|
| `whale-alerts` | Explorer | Large crypto transactions and wallet movements |
| `funding-rates` | Builder | Perpetual funding rates across exchanges |
| `btc-etf-flows` | Signal | Bitcoin ETF daily flows (IBIT, FBTC, etc.) |
| `fear-greed` | Explorer | Crypto Fear & Greed Index |
| `coingecko-global` | Builder | Global crypto market cap and dominance |

### News & Social

| Dataset | Tier | Description |
|---------|------|-------------|
| `breaking-news` | Explorer | Financial news with FinBERT sentiment |
| `newsletters` | Builder | Curated newsletter intelligence |
| `reddit-sentiment` | Signal | 14 subreddit sentiment analysis |
| `x-sentiment` | Signal | X/Twitter sentiment per narrative |
| `narrative-scores` | Signal | 21 narrative crowding scores (1–5) |

### Institutional

| Dataset | Tier | Description |
|---------|------|-------------|
| `wikipedia-pageviews` | Builder | Wikipedia pageview trends for key assets |
| `short-interest` | Signal | Short interest data (39 stocks) |
| `etf-fund-flows` | Signal | ETF fund flow estimates (44 ETFs) |
| `etf-options-pcr` | Signal | Options put/call ratios (42 ETFs) |

### Calendar & Predictions

| Dataset | Tier | Description |
|---------|------|-------------|
| `financial-calendar` | Builder | High-impact economic events |
| `polymarket` | Signal | Polymarket prediction market events |

### Proprietary

| Dataset | Tier | Description |
|---------|------|-------------|
| `decision-engine` | Signal | Multi-factor crypto re-entry scoring |
| `risk-summary` | Signal | Daily risk assessment |
| `scenario-probs` | Signal | 6 macro scenario probabilities |

---

## Tier Access Summary

| Tier | Deposit | Access |
|------|---------|--------|
| **Explorer** (free) | $0 | Prices, breaking news, whale alerts, Fear & Greed, regime, latest brief |
| **Builder** ($50+) | $50 | + macro snapshot, signals, calendar, volumes, newsletters, yahoo quotes |
| **Signal** ($150+) | $150 | All 130+ endpoints. AI reports. Orderbook. DeFi. Options. Institutional. |
| **Institutional** ($500+) | $500 | Unlimited. White-label. SLA. |

---

*AgentCanary provides market data and intelligence for informational purposes only. Nothing constitutes financial advice.*
