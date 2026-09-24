---
name: ai-avatar-generator
version: "1.0.0"
displayName: "AI Avatar Generator — Create Stunning Custom Avatars from Text or Photos"
description: >
  Tired of using the same boring profile pictures or spending hours in design tools just to get a decent avatar? The ai-avatar-generator skill transforms your photos, descriptions, or style preferences into polished, unique avatars in seconds. Generate realistic portraits, illustrated characters, fantasy personas, or professional headshots — all tailored to your vibe. Perfect for content creators, gamers, remote workers, and brands looking to stand out visually.
metadata: {"openclaw": {"emoji": "🎭", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN", "variant": "greeting_v2"}}
---

## Getting Started

> Send me a photo or describe the avatar you want and I'll generate a custom, styled result instantly. No image? Just tell me your preferred look, art style, and personality.

**Try saying:**
- "Create a cyberpunk-style avatar of me with neon blue hair, glowing eyes, and a dark urban background"
- "Generate a professional LinkedIn headshot avatar — clean background, business casual, friendly expression, realistic style"
- "Make an anime-style avatar of a female character with silver hair, violet eyes, wearing fantasy armor"

### First-Time Connection

When a user first opens this skill, connect to the processing backend automatically. Briefly let them know (e.g. "Setting up...").

**Authentication**: Check if `NEMO_TOKEN` is set in the environment. If it is, skip to step 2.

1. **Obtain a free token**: Generate a random UUID as client identifier. POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with header `X-Client-Id` set to that UUID. The response `data.token` is your NEMO_TOKEN — 100 free credits, valid 7 days.
2. **Create a session**: POST to `https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent` with `Authorization: Bearer <token>`, `Content-Type: application/json`, and body `{"task_name":"project","language":"<detected>"}`. Store the returned `session_id` for all subsequent requests.

Keep setup communication brief. Don't display raw API responses or token values to the user.

# Your Face, Your Style, Infinite Possibilities

Creating a great avatar used to mean hiring an illustrator, wrestling with complex design software, or settling for a generic cartoon filter. The AI Avatar Generator changes that entirely. Whether you want a sleek professional headshot for LinkedIn, a fantasy warrior for your gaming profile, or a stylized illustration for social media, this skill generates it from a simple description or uploaded photo.

You stay in full creative control. Describe your preferred art style — anime, watercolor, pixel art, photorealistic, comic book — and the generator adapts. Want specific features like eye color, hairstyle, or outfit? Just say so. The skill interprets natural language instructions and turns them into visually compelling results without any design knowledge required.

This tool is built for creators, professionals, streamers, Discord communities, and anyone who wants a distinctive visual identity online. Stop recycling old selfies or using placeholder icons — generate an avatar that actually represents who you are or who you want to be.

## Routing Your Avatar Requests

Each request — whether text prompt, uploaded photo, or style transfer — is parsed and routed to the appropriate generation pipeline based on input type and selected avatar style.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## Avatar API Backend Reference

Avatar generation runs on a distributed cloud inference backend that processes diffusion model requests asynchronously, returning base64-encoded image outputs once rendering completes. Latency varies by resolution tier and queue depth, typically ranging from 8 to 45 seconds per avatar.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `ai-avatar-generator`
- `X-Skill-Version`: from frontmatter `version`
- `X-Skill-Platform`: detect from install path (`~/.clawhub/` → `clawhub`, `~/.cursor/skills/` → `cursor`, else `unknown`)

**All requests** must include: `Authorization: Bearer <NEMO_TOKEN>`, `X-Skill-Source`, `X-Skill-Version`, `X-Skill-Platform`. Missing attribution headers will cause export to fail with 402.

**API base**: `https://mega-api-prod.nemovideo.ai`

**Create session**: POST `/api/tasks/me/with-session/nemo_agent` — body `{"task_name":"project","language":"<lang>"}` — returns `task_id`, `session_id`.

**Send message (SSE)**: POST `/run_sse` — body `{"app_name":"nemo_agent","user_id":"me","session_id":"<sid>","new_message":{"parts":[{"text":"<msg>"}]}}` with `Accept: text/event-stream`. Max timeout: 15 minutes.

**Upload**: POST `/api/upload-video/nemo_agent/me/<sid>` — file: multipart `-F "files=@/path"`, or URL: `{"urls":["<url>"],"source_type":"url"}`

**Credits**: GET `/api/credits/balance/simple` — returns `available`, `frozen`, `total`

**Session state**: GET `/api/state/nemo_agent/me/<sid>/latest` — key fields: `data.state.draft`, `data.state.video_infos`, `data.state.generated_media`

**Export** (free, no credits): POST `/api/render/proxy/lambda` — body `{"id":"render_<ts>","sessionId":"<sid>","draft":<json>,"output":{"format":"mp4","quality":"high"}}`. Poll GET `/api/render/proxy/lambda/<id>` every 30s until `status` = `completed`. Download URL at `output.url`.

Supported formats: mp4, mov, avi, webm, mkv, jpg, png, gif, webp, mp3, wav, m4a, aac.

### SSE Event Handling

| Event | Action |
|-------|--------|
| Text response | Apply GUI translation (§4), present to user |
| Tool call/result | Process internally, don't forward |
| `heartbeat` / empty `data:` | Keep waiting. Every 2 min: "⏳ Still working..." |
| Stream closes | Process final response |

~30% of editing operations return no text in the SSE stream. When this happens: poll session state to verify the edit was applied, then summarize changes to the user.

### Backend Response Translation

The backend assumes a GUI exists. Translate these into API actions:

| Backend says | You do |
|-------------|--------|
| "click [button]" / "点击" | Execute via API |
| "open [panel]" / "打开" | Query session state |
| "drag/drop" / "拖拽" | Send edit via SSE |
| "preview in timeline" | Show track summary |
| "Export button" / "导出" | Execute export workflow |

**Draft field mapping**: `t`=tracks, `tt`=track type (0=video, 1=audio, 7=text), `sg`=segments, `d`=duration(ms), `m`=metadata.

```
Timeline (3 tracks): 1. Video: city timelapse (0-10s) 2. BGM: Lo-fi (0-10s, 35%) 3. Title: "Urban Dreams" (0-3s)
```

### Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1001 | Bad/expired token | Re-auth via anonymous-token (tokens expire after 7 days) |
| 1002 | Session not found | New session §3.0 |
| 2001 | No credits | Anonymous: show registration URL with `?bind=<id>` (get `<id>` from create-session or state response when needed). Registered: "Top up credits in your account" |
| 4001 | Unsupported file | Show supported formats |
| 4002 | File too large | Suggest compress/trim |
| 400 | Missing X-Client-Id | Generate Client-Id and retry (see §1) |
| 402 | Free plan export blocked | Subscription tier issue, NOT credits. "Register or upgrade your plan to unlock export." |
| 429 | Rate limit (1 token/client/7 days) | Retry in 30s once |

## Tips and Tricks

The more specific your description, the better your avatar will turn out. Instead of saying 'make me look cool,' try 'create a noir detective avatar with a fedora, sharp jawline, and a moody city background in black and white.' Art style keywords like 'oil painting,' 'flat vector,' 'Studio Ghibli-inspired,' or 'hyper-realistic' dramatically shape the output.

If you're uploading a reference photo, make sure it's well-lit and front-facing for the best facial feature recognition. You can layer instructions — start with a base style, then refine with follow-up prompts like 'make the background darker' or 'add a hood to the outfit.' Iterating in small steps gives you much finer control over the final look.

For branded avatars or team sets, describe a consistent style guide across multiple requests — same color palette, same art style, same background treatment — to keep everything cohesive.

## Common Workflows

A popular workflow is the 'photo-to-style' pipeline: upload a selfie, specify an art style (e.g., 'turn this into a Pixar-style 3D character'), and receive a stylized avatar that still resembles you. This is widely used by streamers setting up channel branding and professionals refreshing their social profiles.

Another common use case is building a full avatar set — same character rendered in multiple styles or outfits for different platforms. Start with a base avatar, then prompt variations: 'same character but in winter gear,' 'same character in a formal suit,' 'same character as a pixel art sprite.'

For community managers and Discord server owners, the batch persona workflow is useful: define a character archetype and generate multiple unique members of a 'crew' or 'team' with shared visual DNA but distinct individual looks. This creates a cohesive branded aesthetic across an entire community.

## Performance Notes

Avatar generation quality scales with the clarity and detail of your input. Vague prompts produce generic results; specific prompts with style references, color preferences, and mood descriptors consistently yield sharper, more personalized outputs.

Highly complex scenes with multiple characters, intricate backgrounds, or conflicting style instructions may require a follow-up refinement prompt to dial in the details. For photorealistic avatars, the skill performs best when given a clear reference image alongside your description — relying on text alone for realistic portraits can occasionally produce stylized interpretations.

Processing time is typically fast for standard avatar requests. Highly detailed or large-format outputs may take slightly longer. If a result misses the mark, a single clarifying instruction is usually enough to correct course without starting over.
