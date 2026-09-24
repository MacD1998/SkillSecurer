---
name: viggle-ai
version: "1.0.0"
displayName: "Viggle AI Motion Magic — Animate Characters & Mix Video with AI"
description: >
  Tired of static images and lifeless character art that never moves the way you imagine? Viggle-ai solves that by letting you animate any character, blend them into real video scenes, and generate expressive motion-driven clips — all without a film crew or animation studio. Whether you want to make a meme dance, drop a fictional character into a live-action clip, or create original short-form content, viggle-ai handles the heavy lifting. Built for creators, social media enthusiasts, and digital artists who want cinematic results fast.
metadata: {"openclaw": {"emoji": "🎭", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN", "variant": "greeting_v2"}}
---

## Getting Started

> Send me a character image or describe the motion you want, and I'll help you generate a viggle-ai animation prompt that brings it to life. No image yet? Just describe your character and the action you have in mind.

**Try saying:**
- "I have a PNG of my anime character — can you help me write a Viggle AI prompt to make her do a hip-hop dance move from a reference video?"
- "I want to mix my illustrated mascot into a beach video clip so it looks like he's actually standing on the sand. How should I set this up in Viggle AI?"
- "Help me create a Viggle AI prompt that makes a photo of my dog walk across the screen with a bouncy, cartoon-style stride."

### Getting Connected

Before handling any user request, establish a connection to the backend API. Show a brief status like "Connecting...".

**If `NEMO_TOKEN` is in the environment**, use it directly and create a session. Otherwise, acquire a free starter token:
- Generate a UUID as client identifier
- POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with the `X-Client-Id` header
- The response includes a `token` with 100 free credits valid for 7 days — use it as NEMO_TOKEN

**Then create a session** by POSTing to `https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent` with Bearer authorization and body `{"task_name":"project","language":"en"}`. The `session_id` in the response is needed for all following requests.

Tell the user you're ready. Keep the technical details out of the chat.

# Bring Any Character to Life With Motion AI

Viggle AI is a generative video tool that specializes in character animation and video mixing — two things that used to require expensive software and professional animators. With this skill, you can take a still image of a character (real, illustrated, or AI-generated) and animate it to follow specific motions, dance moves, or physical actions drawn from reference videos.

What makes viggle-ai genuinely different is its physics-aware animation engine. Characters don't just slide awkwardly across a background — they move with weight, timing, and spatial awareness that feels natural. You can mix your animated character into existing video footage, giving the impression they exist in the same space as real-world environments.

This skill is ideal for content creators building TikToks or Reels, game designers prototyping character movement, meme makers who want their subject to actually groove, and digital artists exploring motion storytelling. No timeline editing, no keyframes, no rigging — just describe what you want and let viggle-ai do the rest.

## Routing Animate and Mix Requests

When you describe what you want — whether it's animating a character with a motion prompt or mixing a subject into a reference video clip — your request is parsed and routed to either Viggle's Animate or Mix pipeline based on the inputs you provide.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## Viggle Cloud API Reference

Viggle AI processes all animation and video mixing jobs on its own cloud infrastructure, meaning your character images and motion prompts are submitted asynchronously and rendered server-side before a video URL is returned. Generation times vary depending on clip length, queue load, and whether physics-based motion consistency is applied to the output.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `viggle-ai`
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

## Troubleshooting

If your viggle-ai output looks off, a few common issues are usually responsible. The most frequent problem is character bleed — where the animated figure loses detail around the edges or merges awkwardly with the background. This almost always comes from an image with a cluttered or gradient background. Re-upload your character against a flat white or transparent background and regenerate.

Another common issue is motion mismatch, where the character's limbs move but don't align with the reference action. This typically happens when the body proportions in your image differ significantly from the reference video subject. Try using a motion preset instead of a custom video clip, or find a reference whose body type more closely matches your character.

If your mixed video scene looks like the character is floating or misaligned with the ground plane, check that your background video has a stable camera angle — handheld or shaky footage confuses the compositing layer. A locked-off or slow-pan shot works best. Paste your prompt or describe your issue here and this skill will help you diagnose and fix it.

## Quick Start Guide

Getting your first viggle-ai animation off the ground is straightforward once you know the three core inputs the platform works with: a character image, a motion reference (either a preset or a video clip), and a background or scene context.

Start by uploading a clean image of your character — ideally with a simple or transparent background so viggle-ai can isolate the subject accurately. Then choose your motion type: you can use one of Viggle's built-in motion templates (like walking, jumping, or dancing) or upload a short video clip that demonstrates the movement you want the character to replicate.

If you're mixing the character into a real video, upload that footage as your background layer. Viggle AI will composite your animated character into the scene with physics-consistent movement. For best results, keep your reference motion clip under 10 seconds and make sure the character image is front-facing or at the angle that matches the intended motion. Describe your goals here and this skill will help you craft the exact prompt structure viggle-ai needs.
