#!/usr/bin/env bash
set -euo pipefail
INPUT="${*:-}"
[ -z "$INPUT" ] && echo "Usage: caption: <post topic and platform>" && exit 1
SESSION_ID="caption-$(date +%s)"
PROMPT="You are a social media copywriter specializing in A/B testing captions. Write 5 caption variants for: ${INPUT}

## 5 Caption Variants

**Variant A — Storytelling**
[Write full caption using narrative arc, personal angle]
Hashtags: [10 relevant hashtags]
CTA: [soft CTA]
Predicted engagement style: comments

**Variant B — Educational/Value-First**
[Write full caption leading with the takeaway/lesson]
Hashtags: [10 relevant hashtags]
CTA: [save/share CTA]
Predicted engagement style: saves

**Variant C — Punchy & Direct**
[Write full caption — short, bold, no fluff, direct offer]
Hashtags: [10 relevant hashtags]
CTA: [link in bio CTA]
Predicted engagement style: clicks

**Variant D — Question/Engagement Bait**
[Write full caption ending with a question that prompts replies]
Hashtags: [10 relevant hashtags]
CTA: [comment CTA]
Predicted engagement style: comments

**Variant E — Social Proof/Results**
[Write full caption leading with results, numbers, transformation]
Hashtags: [10 relevant hashtags]
CTA: [DM CTA]
Predicted engagement style: DMs + saves

## Winner Prediction
- Most likely to win: Variant [X]
- Why: [specific reason based on platform + topic]
- Dark horse: Variant [X] — could surprise if [condition]

## A/B Testing Framework
- Test duration: X days minimum
- Audience split: [how to split]
- Primary metric to track: [metric]
- Secondary metrics: [list]
- Decision threshold: [when to call a winner]

## Platform Adaptation Notes
Adjust the winning variant for:
- Instagram: [specific tweak]
- LinkedIn: [specific tweak]
- TikTok: [specific tweak]
- X/Twitter: [trim to 280 chars version]"

RESULT=$(openclaw agent --local --session-id "$SESSION_ID" --json -m "$PROMPT" 2>/dev/null)
REPORT=$(echo "$RESULT" | python3 -c "
import json,sys
data=json.load(sys.stdin)
texts=[p.get('text','') for p in data.get('payloads',[]) if p.get('text')]
print('\n'.join(texts))
" 2>/dev/null)
[ -z "$REPORT" ] && echo "Error: Could not generate captions." && exit 1
echo ""
echo "=== CAPTION A/B WRITER === ${INPUT} ==="
echo ""
echo "$REPORT"
