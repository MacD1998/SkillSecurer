#!/usr/bin/env bash
set -euo pipefail
INPUT="${*:-}"
[ -z "$INPUT" ] && echo "Usage: growth: <platform, niche, current followers, follower goal>" && exit 1
SESSION_ID="growth-$(date +%s)"
PROMPT="You are a social media growth hacker with proven results across platforms. Build a 90-day growth strategy for: ${INPUT}

## Growth Reality Check
Realistic growth projections for this platform + niche:
- Conservative (low effort): +X followers/month
- Realistic (consistent effort): +X followers/month
- Aggressive (high effort + luck): +X followers/month
- What separates top 10% growers in this niche: [key differentiator]

## Top 5 Growth Levers
Ranked by follower growth impact:

**Lever #1: [Name]** — Impact: HIGH / Effort: MEDIUM
- What it is: [explanation]
- Exactly how to do it: [step by step]
- Time investment: X hours/week
- Expected result: +X followers/month

**Lever #2: [Name]**
[Same format]

**Lever #3: [Name]**
[Same format]

**Lever #4: [Name]**
[Same format]

**Lever #5: [Name]**
[Same format]

## 90-Day Growth Plan

### Month 1 — Foundation (Weeks 1-4)
Goal: [specific follower target + engagement rate target]

Week 1: [5 specific daily actions]
Week 2: [5 specific daily actions]
Week 3: [5 specific daily actions]
Week 4: [Review + what to double down on]

### Month 2 — Acceleration (Weeks 5-8)
Goal: [specific target]
Focus: [main tactic to push hard]
[Weekly breakdown]

### Month 3 — Compound (Weeks 9-12)
Goal: [specific target]
Focus: [what's working — scale it]
[Weekly breakdown]

## Viral Content Formula
The post structure that attracts NEW followers (not just engagement from existing):
- Format: [specific format — reel / thread / carousel / etc.]
- Hook pattern: [exact hook formula]
- Content structure: [outline]
- Distribution hack: [how to get it seen beyond your followers]
- Frequency: [how often to post this type]

## Collaboration & Cross-Pollination
How to borrow audiences from bigger accounts:
- Collab post strategy (for this platform)
- Comment farming: how to leave comments that drive profile visits
- Duet / Stitch / Quote Tweet strategy
- Shoutout exchange framework (how to pitch accounts)
- Who to target: [follower size range that makes sense]

## Algorithm Hacks (Platform-Specific)
What's working RIGHT NOW on this platform:
1. [Specific tactic]
2. [Specific tactic]
3. [Specific tactic]
4. [Specific tactic]
5. [Specific tactic]

## Weekly Tracking Dashboard
Metrics to check every Monday:
| Metric | Week 1 Target | Week 4 Target | Week 12 Target |
|--------|-------------|--------------|----------------|
| Followers | | | |
| Avg reach per post | | | |
| Engagement rate | | | |
| Profile visits | | | |
| Follower conversion rate | | | |

## Common Growth Mistakes to Avoid
Top 5 things that stall growth in this niche — with fixes."

RESULT=$(openclaw agent --local --session-id "$SESSION_ID" --json -m "$PROMPT" 2>/dev/null)
REPORT=$(echo "$RESULT" | python3 -c "
import json,sys
data=json.load(sys.stdin)
texts=[p.get('text','') for p in data.get('payloads',[]) if p.get('text')]
print('\n'.join(texts))
" 2>/dev/null)
[ -z "$REPORT" ] && echo "Error: Could not generate growth strategy." && exit 1
echo ""
echo "=== SOCIAL GROWTH STRATEGY === ${INPUT} ==="
echo ""
echo "$REPORT"
