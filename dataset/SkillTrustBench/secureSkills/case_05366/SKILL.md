---
name: free-ai-image-generator
version: 1.0.6
displayName: "Free AI Image Generator — Create Stunning Visuals From Text Instantly"
description: >
  Tell me what you need and I'll turn your words into vivid, high-quality images — no design skills required. This free-ai-image-generator skill lets you create original artwork, product mockups, social media visuals, and creative illustrations just by describing what you imagine. Supports a wide range of styles from photorealistic to anime, watercolor, and beyond. Perfect for bloggers, marketers, entrepreneurs, and creatives who want professional visuals without a budget.
metadata: {"openclaw": {"emoji": "🎨", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN", "variant": "control"}}
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
apiDomain: https://mega-api-prod.nemovideo.ai
---

## Getting Started

> Welcome to your free AI image generator — describe any scene, character, or concept and I'll create a custom image for you right now. Ready to bring your vision to life? Just tell me what you want to see!

**Try saying:**
- "Generate a photorealistic image of a mountain cabin at sunset with snow on the roof and warm light glowing through the windows"
- "Create an anime-style portrait of a female warrior with silver hair, glowing blue eyes, and futuristic armor"
- "Make a flat-design illustration of a small business owner working at a desk surrounded by plants and coffee cups for a blog header"

### Getting Connected

Before handling any user request, establish a connection to the backend API. Show a brief status like "Connecting...".

**If `NEMO_TOKEN` is in the environment**, use it directly and create a session. Otherwise, acquire a free starter token:
- Generate a UUID as client identifier
- POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with the `X-Client-Id` header
- The response includes a `token` with 100 free credits valid for 7 days — use it as NEMO_TOKEN

**Then create a session** by POSTing to `https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent` with Bearer authorization and body `{"task_name":"project","language":"en"}`. The `session_id` in the response is needed for all following requests.

Tell the user you're ready. Keep the technical details out of the chat.

# From Words to Visuals in Seconds

Imagine being able to sketch out an idea in plain English and watch it come to life as a polished, ready-to-use image. That's exactly what this skill does. Whether you're building a brand, illustrating a blog post, or just exploring your creativity, you can generate original images without touching a single design tool.

This skill is built for people who have ideas but not necessarily the technical skills or budget to hire a designer. Describe a sunset over a neon-lit city, a cozy coffee shop interior, or a futuristic robot — and get a visually compelling result within moments. You control the style, mood, color palette, and composition simply through your description.

From solopreneurs crafting social content to writers visualizing characters and scenes, this free AI image generator opens up creative possibilities that used to require expensive software or professional help. The barrier to beautiful visuals is now just a sentence.

## Prompt Routing and Model Selection

When you submit a text prompt, ClawHub parses your input and routes the generation request to the optimal diffusion model endpoint based on style keywords, resolution parameters, and current server load.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## Backend API Reference Guide

Image synthesis runs through a cloud-hosted inference pipeline that processes your prompt via latent diffusion, applying negative prompt filtering and seed-based sampling before returning a fully rendered output. All generation jobs are queued, executed, and delivered asynchronously to keep response times stable even under high concurrency.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `free-ai-image-generator`
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

## Best Practices for Better AI-Generated Images

The quality of your output is directly tied to the clarity of your input. Start with the subject, then layer in environment, lighting, mood, and style. For example: 'A golden retriever sitting in a sunlit meadow, soft bokeh background, warm afternoon light, photorealistic style' will outperform 'a dog outside' every time.

Use reference style keywords strategically. Terms like 'cinematic lighting,' 'hyper-detailed,' '8K resolution,' 'studio photography,' or 'concept art' signal the model toward higher-quality rendering. Mixing styles intentionally — such as 'watercolor with neon accents' — can produce uniquely striking results.

Iterate quickly. Generate a first version, identify what's missing or off, then refine your prompt with targeted adjustments. Treat it like a conversation with a visual artist: the more feedback you give, the closer you get to your ideal image.

## Troubleshooting Common Image Generation Issues

If your generated image doesn't match what you had in mind, the most common fix is adding more specific detail to your prompt. Vague prompts like 'a nice landscape' produce generic results — try specifying time of day, weather, color mood, and artistic style instead.

If faces or hands look distorted, this is a known limitation of AI image models. Adding phrases like 'highly detailed face' or 'realistic hands' to your prompt often improves accuracy. For complex compositions with multiple subjects, try breaking your request into focused scenes rather than describing everything at once.

If the style isn't matching your vision, explicitly name an art style — such as 'oil painting,' 'digital art,' 'watercolor sketch,' or 'cinematic photography.' The more precise your style reference, the closer the output will match your expectation.

## Use Cases for Free AI Image Generation

This skill fits naturally into a surprising range of workflows. Content creators use it to produce custom thumbnails, blog headers, and social media graphics without paying for stock photos or designers. Small business owners generate product concept visuals, promotional banners, and brand mood boards on the fly.

Writers and game designers use it to visualize characters, settings, and scenes during the creative process — giving life to ideas that would otherwise stay in their heads. Teachers and educators create custom diagrams, illustrated examples, and engaging visual aids for presentations.

Even personal projects benefit: generate custom birthday card art, fantasy maps, dream home concepts, or unique phone wallpapers. The free-ai-image-generator skill adapts to your context, whether professional or purely creative.
