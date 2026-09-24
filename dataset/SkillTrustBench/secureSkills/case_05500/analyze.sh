#!/usr/bin/env bash
set -euo pipefail
INPUT="${*:-}"
[ -z "$INPUT" ] && echo "Usage: thread: <content or topic to convert>" && exit 1
SESSION_ID="thread-$(date +%s)"
PROMPT="You are a viral thread writer specializing in X/Twitter, LinkedIn, and Threads. Convert this into a high-performing thread: ${INPUT}

## Platform Selection
Identify the target platform from the input. Default to X/Twitter if not specified.

## Hook Options (3 Alternatives for Tweet 1)
Write 3 alternative opening tweets — each under 280 characters:
**Hook A:** [bold claim or counterintuitive take]
**Hook B:** [\"I [did X]. Here's what I learned:\" format]
**Hook C:** [data or number-led hook]

## Full Thread Script
Write the complete thread — aim for 8-15 tweets depending on content depth.

For EACH tweet:
**Tweet [N]:** 
[Content — max 270 characters, leave room for numbering]
Character count: [X/280]
[Add any media suggestion in brackets if applicable]

Rules:
- Each tweet must stand alone and deliver value
- End each middle tweet with a micro-hook to keep reading
- Use line breaks for readability (2 lines max per tweet)
- No filler tweets — every tweet must earn its place
- Number format: use \"[N/]\" at tweet start (e.g., \"2/ Here's the thing...\")

## Closer Tweet Options
**Closer A — Follow CTA:**
[Tweet asking for a follow + what they'll get]

**Closer B — Retweet CTA:**
[Tweet asking to RT if they found it valuable]

**Closer C — Soft Sell:**
[Tweet pointing to a resource/product/newsletter]

## Engagement Boosters
Suggest where in the thread to add:
- A poll (Tweet X): [poll question + options]
- An image/graphic (Tweet X): [what to show]
- A quote tweet of yourself (if applicable)

## LinkedIn Adaptation
Condense the thread into a single long-form LinkedIn post (max 3,000 chars):
- Keep the hook
- Merge middle points into flowing paragraphs
- Add LinkedIn-specific formatting (line breaks, no hashtags mid-post)

## Thread Stats Prediction
- Expected thread length: [X] tweets, ~[Y] words
- Read time: ~[Z] minutes
- Best posting time for this topic: [day + time]"

RESULT=$(openclaw agent --local --session-id "$SESSION_ID" --json -m "$PROMPT" 2>/dev/null)
REPORT=$(echo "$RESULT" | python3 -c "
import json,sys
data=json.load(sys.stdin)
texts=[p.get('text','') for p in data.get('payloads',[]) if p.get('text')]
print('\n'.join(texts))
" 2>/dev/null)
[ -z "$REPORT" ] && echo "Error: Could not convert to thread." && exit 1
echo ""
echo "=== THREAD CONVERTER === ${INPUT} ==="
echo ""
echo "$REPORT"
