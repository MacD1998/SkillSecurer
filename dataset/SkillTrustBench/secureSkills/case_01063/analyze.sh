#!/usr/bin/env bash
# shopify-social-content-planner — 30-day social content calendar generator
set -euo pipefail

INPUT="${*:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: social content: <store niche and platforms>"
  echo "Example: social content: 30-day plan for pet accessories Instagram TikTok"
  exit 1
fi

SESSION_ID="social-$(date +%s)"

PROMPT="You are a social media strategist specializing in Shopify e-commerce brands. Create a complete 30-day social content plan for: ${INPUT}

## 1. Platform Strategy
For this niche, rank and configure each platform:
| Platform | Priority | Post Frequency | Content Type | Primary Goal |
|----------|----------|---------------|--------------|--------------|
| Instagram Feed | | | | |
| Instagram Reels | | | | |
| Instagram Stories | | | | |
| TikTok | | | | |
| Pinterest | | | | |
| Facebook | | | | |

## 2. Content Mix Formula
Define the 80/20 content strategy:
- Educational/Value: X%
- Entertaining/Relatable: X%
- User Generated Content: X%
- Product Showcase: X%
- Promotional/Sale: X%
- Behind the Scenes: X%
- Community/Engagement: X%

## 3. 30-Day Content Calendar
For each day, provide:
| Day | Platform | Content Type | Hook/Angle | Caption (50 words) | Hashtags | CTA |
[Create all 30 days — keep it specific to the niche, not generic]

Day 1: [fill]
Day 2: [fill]
Day 3: [fill]
... [continue for all 30 days]

## 4. Caption Templates (10 per platform)
**Instagram Templates:**
1. [Template with blanks to fill in]
...10 templates

**TikTok Hook Templates:**
1. [Hook that stops the scroll]
...10 hooks

**Pinterest Description Templates:**
1. [SEO-optimized description template]
...5 templates

## 5. Hashtag Strategy
**Instagram:**
- Niche hashtags (under 100K posts): [10 specific hashtags]
- Mid-size (100K-1M posts): [10 specific hashtags]
- Large (1M+ posts): [5 hashtags]
- Branded hashtag: [recommendation]

**TikTok:**
- Trending hashtags for this niche: [10 specific]
- Evergreen hashtags: [5 specific]

**Pinterest:**
- Board names: [5 board name suggestions]
- Pin keywords: [15 keywords to include]

## 6. Content Batching Guide
3-hour content shoot plan:
- Equipment setup (30 min)
- Shots to capture (list all scenes/angles)
- B-roll list
- UGC collection method
- Editing batch workflow
- Scheduling tools recommendation

## 7. Best Posting Times
For this niche's target audience:
- Instagram: [specific times and days]
- TikTok: [specific times and days]
- Pinterest: [specific times and days]
- Facebook: [specific times and days]

## 8. Engagement Automation
10 engagement tactics that take <5 min/day:
- Comment response templates
- Story interaction ideas
- Collab/duet strategy (TikTok)
- Community building tactics"

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
echo "  30-DAY SOCIAL CONTENT CALENDAR"
echo "  Brand: ${INPUT}"
echo "================================================"
echo ""
echo "$REPORT"
echo ""
echo "================================================"
echo "  Powered by Shopify Social Content Planner"
echo "  clawhub.ai/mguozhen/shopify-social-content-planner"
echo "================================================"
