#!/usr/bin/env bash
set -euo pipefail
INPUT="${*:-}"
[ -z "$INPUT" ] && echo "Usage: carousel: <topic and slide count>" && exit 1
SESSION_ID="carousel-$(date +%s)"
PROMPT="You are a carousel content specialist for LinkedIn and Instagram. Write a complete carousel post for: ${INPUT}

## Cover Slide (3 Options to A/B Test)
**Option A:** [Headline — bold, curiosity-driven]
**Option B:** [Headline — number-led, promise-based]
**Option C:** [Headline — question format]
Visual direction: [background style, font weight, visual element suggestion]

## Slide-by-Slide Script
For each slide (aim for 8-12 slides total based on the topic):

**Slide [N]: [Slide Title]**
- Headline: [bold, short — max 8 words]
- Body text: [2-4 lines of supporting copy — clear and punchy]
- Visual direction: [what to show — icon / illustration / data visualization / photo / minimal text]
- Transition hook: [optional — last line that makes reader swipe]

[Write all slides]

## CTA Slide (3 Options)
**Option A — Save:**
[Write save-focused CTA slide]

**Option B — Follow:**
[Write follow-focused CTA slide]

**Option C — Comment:**
[Write comment-focused CTA slide]

## Post Caption
Write the full caption to accompany the carousel (150-300 words):
- Hook line
- Brief context
- Tease the content
- CTA to swipe / save
- Sign off

## Hashtag Set
30 hashtags split into 3 tiers:
- Niche (under 100K): [10 hashtags]
- Mid (100K-1M): [10 hashtags]
- Large (1M+): [10 hashtags]

## Design Tips
Quick Canva/Figma tips to make this carousel look great:
- Recommended dimensions: [for LinkedIn / Instagram]
- Font pairing suggestion
- Color palette idea
- One design trick that increases saves"

RESULT=$(openclaw agent --local --session-id "$SESSION_ID" --json -m "$PROMPT" 2>/dev/null)
REPORT=$(echo "$RESULT" | python3 -c "
import json,sys
data=json.load(sys.stdin)
texts=[p.get('text','') for p in data.get('payloads',[]) if p.get('text')]
print('\n'.join(texts))
" 2>/dev/null)
[ -z "$REPORT" ] && echo "Error: Could not generate carousel script." && exit 1
echo ""
echo "=== CAROUSEL SCRIPT === ${INPUT} ==="
echo ""
echo "$REPORT"
