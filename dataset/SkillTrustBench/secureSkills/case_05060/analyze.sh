#!/usr/bin/env bash
# shopify-backlink-builder — Link acquisition strategy for Shopify stores
set -euo pipefail

INPUT="${*:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: backlinks: <store niche and current DA>"
  echo "Example: backlinks: build strategy for pet accessories store DA 15"
  exit 1
fi

SESSION_ID="backlink-$(date +%s)"

PROMPT="You are an SEO link building expert specializing in Shopify e-commerce stores. Build a complete backlink acquisition strategy for: ${INPUT}

## 1. Link Opportunity Matrix
Categorize and prioritize link types:
| Link Type | Difficulty | Impact | Volume/Month | Priority |
|-----------|-----------|--------|--------------|----------|
| Guest Posts | | | | |
| HARO Responses | | | | |
| Broken Link Building | | | | |
| Resource Page Links | | | | |
| Competitor Steal | | | | |
| Digital PR / Data | | | | |
| Podcast Appearances | | | | |
| Forum/Community | | | | |
| Directory Listings | | | | |
| Supplier/Partner Links | | | | |

## 2. Competitor Backlink Gap Analysis
For the top 3 competitors in this niche, identify:
- Types of sites linking to them
- Content assets attracting the most links
- Link patterns unique to each competitor
- Top 10 link opportunities you can replicate immediately

## 3. Guest Post Target List
20 specific websites to target in this niche:
| Site | Domain Authority | Niche Relevance | Contact Method | Topic Ideas |
|------|-----------------|----------------|----------------|-------------|
[List 20 real, relevant publication types with specific topic angles]

## 4. Digital PR Playbook
Data-driven content that earns links automatically:
- 5 research report ideas for this niche (journalists will cite these)
- How to create and distribute the data
- Target publications to pitch to
- Press release template for link-worthy content
- HARO category to monitor (specific subreddits/topics)

## 5. HARO Response Strategy
- Best HARO categories for this niche
- Response template that gets accepted (150 words)
- Positioning as an expert in this niche
- Response timing (within 1 hour rule)
- Track record: expect X% acceptance rate

## 6. Outreach Email Templates
**Guest Post Pitch:**
Subject: [Subject line]
[200-word email template]

**Resource Page Link Request:**
Subject: [Subject line]
[150-word email template]

**Broken Link Replacement:**
Subject: [Subject line]
[150-word email template]

**Podcast Guest Pitch:**
Subject: [Subject line]
[150-word email template]

## 7. Link Velocity Plan (12 Months)
Natural link building pace to avoid penalties:
- Month 1-3: X links/month (foundation)
- Month 4-6: X links/month (acceleration)
- Month 7-12: X links/month (scale)
- Link type mix per month
- DA targets by month

## 8. Internal Link Optimization
Maximize existing link equity:
- Hub pages to create (link magnets)
- Internal link structure for Shopify (collections → products)
- Anchor text distribution guidelines
- PageRank sculpting strategy

## 9. 90-Day Quick Win Plan
First 90 days to build 30 quality links:
- Week 1-2: [specific actions]
- Week 3-4: [specific actions]
- Month 2: [specific actions]
- Month 3: [specific actions]

## 10. Link Quality Checklist
Before accepting any link, verify:
- DA/DR threshold
- Traffic verification
- Spam score limits
- Niche relevance score
- Follow vs nofollow strategy"

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
echo "  BACKLINK BUILDING STRATEGY"
echo "  Target: ${INPUT}"
echo "================================================"
echo ""
echo "$REPORT"
echo ""
echo "================================================"
echo "  Powered by Shopify Backlink Builder"
echo "  clawhub.ai/mguozhen/shopify-backlink-builder"
echo "================================================"
