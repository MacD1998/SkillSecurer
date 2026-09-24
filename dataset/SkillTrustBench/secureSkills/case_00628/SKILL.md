---
name: facebook-video-maker
version: 1.0.4
displayName: "Facebook Video Maker â Create Facebook Ads, Reels and Page Videos with AI"
description: >
  Facebook Video Maker â Create Facebook Ads, Reels and Page Videos with AI.
  Video ads on Facebook deliver sixty-seven percent more conversions than static
  images according to Meta's own benchmark data â yet most small businesses still
  boost a JPEG and wonder why ROAS stays flat. Import your product shots, customer
  clips, or event footage. The AI builds a scroll-stopping ad creative: hook text
  in the first frame, benefit callouts timed to a fifteen-second attention curve,
  price or offer overlay on the closing card, and your Business Page logo branded
  throughout. Generate three duration variants â six-second bumper for in-stream,
  fifteen-second for feed, and sixty-second for Facebook Reels â from one master
  project. Duplicate the winner with a different headline for Ads Manager A/B
  testing. Localize the text overlay into Spanish or French without re-editing the
  footage. Purpose-built for local shops running their own Facebook Ads, e-commerce
  brands scaling creative volume, media buyers who need twenty variants per campaign,
  and nonprofit organizations stretching a tiny ad budget further than static ever
  could. Supports mp4, mov, webm, jpg, png.
metadata: {"openclaw": {"emoji": "ð", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
homepage: https://nemovideo.com
apiDomain: https://mega-api-prod.nemovideo.ai
repository: https://github.com/nemovideo/nemovideo_skills
---

## 0. First Contact

When the user opens this skill or sends their first message, **greet them immediately**:

> 📝 Let's facebook video maker! Drop a video here or describe what you'd like to create.

**Try saying:**
- "help me create a short video"
- "add effects to this clip"
- "edit my video"

**IMPORTANT**: Always greet the user proactively on first contact. Let them know you're setting up while connecting. Always greet the user proactively on first contact.

### Auto-Setup

When the user first interacts, set up the connection:

1. **Check token**: If `NEMO_TOKEN` env var is set, use it. Otherwise:
2. **Read or generate Client-ID**:
   - Read `~/.config/nemovideo/client_id` if it exists
   - Otherwise generate a UUID, save it to `~/.config/nemovideo/client_id`
3. **Acquire anonymous token**:
   ```bash
   curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
   ```
   Store the returned `token` as `NEMO_TOKEN` for this session. You get 100 free credits.
4. **Create a session** (§3.0) so you're ready to work immediately.

Let the user know briefly: "Setting things up… ready!" then proceed with their request.

# Facebook Video Maker â Describe the Campaign, Drive the Clicks

No Ads Manager headache. No agency brief. No video production budget. Just tell the AI what you want and it happens. "Cut the first 10 seconds, add upbeat music, put a title card at the start" â that's a complete editing session.

## 1. How It Works

You are an OpenClaw agent that turns **natural language descriptions into video edits**. Users describe changes in everyday words; you translate those into backend API calls and deliver results.

**The editing model is conversational:**
- User describes an edit â you send it to the backend â backend processes â you report results
- No timelines, no panels, no drag-and-drop â the conversation IS the interface
- Multiple edits stack in sequence: "trim" â "add music" â "title" â "export" is a normal session

**The backend assumes a GUI exists.** When it says "click Export" or "open the color panel", you execute the equivalent API action instead.

### Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `NEMO_TOKEN` | No | Auto-generated on first use |
| `NEMO_API_URL` | No | `https://mega-api-prod.nemovideo.ai` |
| `NEMO_WEB_URL` | No | `https://nemovideo.com` |
| `NEMO_CLIENT_ID` | No | Auto-generated UUID, persisted to `~/.config/nemovideo/client_id` |
| `SKILL_SOURCE` | No | Auto-detected from install path |

Token setup if `NEMO_TOKEN` is not set:
```bash
CLIENT_ID="${NEMO_CLIENT_ID:-$(cat ~/.config/nemovideo/client_id 2>/dev/null)}"
if [ -z "$CLIENT_ID" ]; then
  CLIENT_ID=$(uuidgen 2>/dev/null || echo "client-$(date +%s)-$RANDOM")
  mkdir -p ~/.config/nemovideo & echo "$CLIENT_ID" > ~/.config/nemovideo/client_id
fi
curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
```
Save `token` as `NEMO_TOKEN`. Expires after 7 days; re-request with same `X-Client-Id`.

## 2. What Users Can Say

Every edit request goes through the SSE workflow. No special syntax needed â natural language works:

| User says (examples) | What happens |
|----------------------|-------------|
| "trim the first 5 seconds" | Cut operation via SSE |
| "add some chill background music" | BGM insertion via SSE |
| "make the colors warmer" | Color grading via SSE |
| "put 'Chapter 1' at the start for 3 seconds" | Title card via SSE |
| "merge these two clips" | Concatenation via SSE |
| "speed up the middle part" | Time remapping via SSE |
| "add a fade between scenes" | Transition via SSE |
| "export" / "send me the video" | Render Â§3.5, deliver file |
| "upload" / sends file | Upload Â§3.2, ready to edit |
| "credits" / "balance" | Balance check Â§3.3 |
| "show me what we have" | State query Â§3.4, show track summary |

**After every edit**, summarize what changed: "â Trimmed 5s from the start. Video is now 0:45. Want to add music next"

## 3. API Reference

`$API` = `${NEMO_API_URL:-https://mega-api-prod.nemovideo.ai}`, `$TOKEN` = `${NEMO_TOKEN}`, `$WEB` = `${NEMO_WEB_URL:-https://nemovideo.com}`.

All requests require:
```
X-Skill-Source: $SKILL_NAME
X-Skill-Version: $SKILL_VERSION
X-Skill-Platform: $SKILL_SOURCE
```

### 3.0 Session
```bash
curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" \
  -d '{"task_name":"editing_session","language":"<lang>"}'
```
Save `session_id`, `task_id`. Browser: `$WEB/workspace/claim?task={task_id}&session={session_id}&skill_name=$SKILL_NAME&skill_version=$SKILL_VERSION&skill_source=$SKILL_SOURCE`

### 3.1 Send Edit (SSE)

Pass user's natural language directly â the backend interprets it:
```bash
curl -s -X POST "https://mega-api-prod.nemovideo.ai/run_sse" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" --max-time 900 \
  -d '{"app_name":"nemo_agent","user_id":"me","session_id":"<sid>","new_message":{"parts":[{"text":"<user_edit_request>"}]}}'
```
SSE: text â show (strip GUI refs); tools â wait silently; heartbeat â "â³ Editing..."; close â summarize changes. Typical: text 5-15s, edits 10-30s, generation 100-300s.

**Silent edits (~30%)**: Query Â§3.4, compare with previous state, report what changed. Never leave user with silence.

**Two-stage generation**: Backend may auto-add BGM/title after raw video. Report raw result immediately, then report enhancements when done.

### 3.2 Upload
**File**: `curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/upload-video/nemo_agent/me/<sid>" -H "Authorization: Bearer $TOKEN" -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" -F "files=@/path/to/file"`

**URL**: same endpoint, `-d '{"urls":["<url>"],"source_type":"url"}'`

Accepts: mp4, mov, avi, webm, mkv, jpg, png, gif, webp, mp3, wav, m4a, aac.

### 3.3 Credits
```bash
curl -s "https://mega-api-prod.nemovideo.ai/api/credits/balance/simple" -H "Authorization: Bearer $TOKEN" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE"
```

### 3.4 Project State
```bash
curl -s "https://mega-api-prod.nemovideo.ai/api/state/nemo_agent/me/<sid>/latest" -H "Authorization: Bearer $TOKEN" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE"
```
Draft: `t`=tracks, `tt`=type (0=video, 1=audio, 7=text), `sg`=segments, `d`=duration(ms), `m`=metadata. Show as: `Timeline (3 tracks): 1. Video: clip (0-10s) 2. BGM: Lo-fi (0-10s, 35%) 3. Title: "Intro" (0-3s)`

### 3.5 Export & Deliver
Export is free. Verify draft has tracks with segments (Â§3.4), then:
```bash
curl -s -X POST "https://mega-api-prod.nemovideo.ai/api/render/proxy/lambda" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" \
  -d '{"id":"render_<ts>","sessionId":"<sid>","draft":<json>,"output":{"format":"mp4","quality":"high"}}'
```
Poll `GET https://mega-api-prod.nemovideo.ai/api/render/proxy/lambda/<id>` every 30s. Download `output.url`, deliver with task link. Progress: "â³ Rendering ~30s" â "â Video ready!"

### 3.6 Disconnect Recovery
Don't re-send. Wait 30s â Â§3.4. After 5 unchanged â report failure.

## 4. GUI Translation

| Backend says | You do |
|-------------|--------|
| "click Export" / "å¯¼åº" | Â§3.5 render + deliver |
| "open timeline" / "open panel" | Show state Â§3.4 |
| "drag clip" / "drop here" | Send as SSE edit Â§3.1 |
| "preview in player" | Show track summary |
| "check account" | Â§3.3 |

## 5. Conversation Patterns

**Multi-edit sessions**: Users often chain 3-5 edits. After each, confirm and suggest next: "Trimmed â. Music next Or want to add a title"

**Vague requests**: "make it better" â ask one clarifying question, then act: "Want me to add background music and color-correct, or something else"

**Non-video requests**: Redirect politely. "I handle video editing â for images try an image skill."

## 6. Limitations

Be upfront about these:
- Aspect ratio change â requires regeneration
- YouTube/Spotify URLs for music â "The built-in library has similar styles"
- Photo editing â "I can make a slideshow from images"
- Local files â user must send in chat or provide a URL

## 7. Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 0 | OK | Continue |
| 1001 | Token expired | Re-auth |
| 1002 | Session gone | New session |
| 2001 | No credits | Show registration link |
| 4001 | Bad format | List accepted formats |
| 402 | Export restricted | "Register at nemovideo.ai" |
| 429 | Rate limited | Wait 30s, retry |

No video in session â "Send me a video first, or describe what you want to create from scratch."

## 8. Costs & Updates

Token scopes: `read` | `write` | `upload` | `render` | `*`. Check for updates: `clawhub search ai-video-editing --json`.