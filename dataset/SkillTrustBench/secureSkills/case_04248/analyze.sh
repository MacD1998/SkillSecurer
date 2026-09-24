#!/usr/bin/env bash
# shopify-dropshipping-finder — Product research and supplier evaluation
set -euo pipefail

INPUT="${*:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: dropshipping: <product or niche>"
  echo "Example: dropshipping: evaluate phone accessories niche"
  exit 1
fi

SESSION_ID="dropship-$(date +%s)"

PROMPT="You are a Shopify dropshipping expert with deep knowledge of product research, supplier evaluation, and profitability analysis. Analyze this dropshipping opportunity: ${INPUT}

## 1. Product Viability Score (out of 100)
Score this opportunity:
- Market demand score (Google Trends, search volume): /20
- Competition level (inverse): /20
- Profit margin potential: /20
- Shipping feasibility: /20
- Brand-building potential: /20
- **Total Viability Score: /100**
→ Verdict: Strong / Moderate / Weak opportunity

## 2. Product Selection Criteria
For this niche, the ideal dropshipping product must:
- Price range: $X - $Y retail
- COGS range: $X - $Y
- Weight/dimensions: [specs to hit under $5 ePacket]
- Impulse buy score: /10
- Problem-solving score: /10
- Top 10 specific winning product ideas in this niche

## 3. Supplier Platform Comparison
| Platform | Best For | Avg Shipping (US) | Quality Control | Min Order | Price Range |
|----------|----------|-------------------|-----------------|-----------|-------------|
| AliExpress | | | | | |
| Spocket | | | | | |
| CJDropshipping | | | | | |
| Zendrop | | | | | |
| Oberlo (via DSers) | | | | | |
| Alibaba (MOQ) | | | | | |
| SaleHoo | | | | | |

**Recommended for this niche:** [Platform + reason]

## 4. Supplier Evaluation Checklist
When vetting a supplier, check:
- Response time (<24h target)
- Sample order evaluation criteria
- Return/refund policy terms
- Shipping time guarantees
- Product quality indicators
- Red flags to watch for

## 5. Margin Calculator
For a typical product in this niche (example: $39.99 retail):
- Retail price: $39.99
- COGS (product): -$X.XX
- Shipping to customer: -$X.XX
- Shopify fees (2%): -$X.XX
- Payment processing (2.9%+$0.30): -$X.XX
- Facebook/Meta CPA estimate: -$X.XX
- **Net profit per order: $X.XX (X%)**
- Break-even ROAS: X.Xx

## 6. Differentiation Strategy
How to win in this niche without competing on price:
- Bundling strategy (what to bundle)
- Custom packaging opportunity
- Brand story angle
- Upsell/cross-sell stack
- Unique value proposition that suppliers can't copy

## 7. Shipping & Fulfillment Plan
- Best shipping options for US/EU/AU customers
- Handling time expectations to set
- Customer communication templates for delays
- Returns handling workflow

## 8. Risk Management
Top risks in this niche and mitigation:
- Supplier reliability risk → mitigation
- Shipping delay risk → mitigation
- Product quality risk → mitigation
- Ad account ban risk → mitigation
- Saturation risk → mitigation

## 9. Scale-Up Roadmap
Phase 1 (Month 1-3): Pure dropshipping, test and validate
Phase 2 (Month 4-6): Negotiate with top 2 suppliers, custom packaging
Phase 3 (Month 7-12): Move to private label / inventory for winning SKUs
Phase 4 (12M+): Brand building, own supply chain

## 10. First 30 Days Action Plan
Week-by-week steps to launch this dropshipping store."

RESULT=$(openclaw agent --local --session-id "$SESSION_ID" --json -m "$PROMPT" 2>/dev/null)
REPORT=$(echo "$RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
payloads = data.get('payloads', [])
texts = [p.get('text','') for p in payloads if p.get('text')]
print('\n'.join(texts))
" 2>/dev/null)

if [ -z "$REPORT" ]; then
  echo "Error: Could not generate report."
  exit 1
fi

echo ""
echo "================================================"
echo "  DROPSHIPPING PRODUCT RESEARCH REPORT"
echo "  Target: ${INPUT}"
echo "================================================"
echo ""
echo "$REPORT"
echo ""
echo "================================================"
echo "  Powered by Shopify Dropshipping Finder"
echo "  clawhub.ai/mguozhen/shopify-dropshipping-finder"
echo "================================================"
