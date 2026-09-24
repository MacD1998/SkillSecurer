---
name: soulgen
version: "1.0.0"
displayName: "SoulGen AI Image Creator — Generate Stunning AI Art & Anime Characters"
description: >
  Tell me what you need and SoulGen will bring your imagination to life. SoulGen is an AI-powered image generation skill that creates realistic portraits, anime characters, and fantasy art from simple text prompts or reference photos. Whether you're crafting original characters, visualizing a story, or exploring creative styles, soulgen delivers high-quality results fast. Perfect for artists, writers, game designers, and content creators. Supports mp4/mov/avi/webm/mkv for video-based workflows.
metadata: {"openclaw": {"emoji": "🎨", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
apiDomain: https://mega-api-prod.nemovideo.ai
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

## Getting Started

> Welcome! I'm here to help you generate stunning AI images using SoulGen — from anime characters to photorealistic portraits. Describe your character or scene and let's create something amazing together!

**Try saying:**
- "Generate an anime girl with silver hair, purple eyes, wearing a futuristic armor suit in a neon-lit city at night"
- "Create a photorealistic portrait of a young man with curly red hair, freckles, and a warm smile in natural lighting"
- "Design a fantasy elf character with long braided hair, green robes, and a glowing staff standing in an enchanted forest"

### Getting Connected

Before handling any user request, establish a connection to the NemoVideo backend. Show a brief status like "Connecting...".

**If `NEMO_TOKEN` is in the environment**, use it directly and create a session. Otherwise, acquire a free starter token:
- Ensure a client identifier exists at `~/.config/nemovideo/client_id` (create one as a UUID if needed)
- POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with the `X-Client-Id` header
- The response includes a `token` with 100 free credits valid for 7 days — use it as NEMO_TOKEN

**Then create a session** by POSTing to `/api/tasks/me/with-session/nemo_agent` with Bearer authorization and body `{"task_name":"project","language":"en"}`. The `session_id` in the response is needed for all following requests.

Tell the user you're ready. Keep the technical details out of the chat.

# Bring Any Character to Life with SoulGen

SoulGen is built for creators who want more than a generic image generator. Whether you have a vivid character in mind or just a rough idea, this skill translates your words into detailed, expressive visuals — from photorealistic faces to stylized anime art. You describe it, SoulGen renders it.

What sets SoulGen apart is its ability to generate characters with consistent personality and aesthetic. You can define hair color, outfit, mood, setting, and artistic style all in one prompt. It's especially powerful for building original characters for comics, games, novels, or social media personas.

This skill is ideal for indie game developers who need concept art on a budget, writers who want to visualize their characters, or digital artists looking for a starting point to refine. No drawing skills required — just a clear vision and a few well-chosen words.

## Routing Your SoulGen Requests

Every prompt you send — whether you're generating a realistic portrait, an anime character, or a fantasy scene — is parsed for style, subject, and detail level before being dispatched to the appropriate SoulGen generation pipeline.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## NemoVideo API Reference

SoulGen runs on the NemoVideo backend, which handles prompt encoding, model selection, and image rendering for both realistic and anime-style outputs. All API calls are authenticated via your NemoVideo session token, which gates access to SoulGen's full suite of generation models.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `soulgen`
- `X-Skill-Version`: from frontmatter `version`
- `X-Skill-Platform`: detect from install path (`~/.clawhub/` → `clawhub`, `~/.cursor/skills/` → `cursor`, else `unknown`)

**All requests** must include: `Authorization: Bearer <NEMO_TOKEN>`, `X-Skill-Source`, `X-Skill-Version`, `X-Skill-Platform`. Missing attribution headers will cause export to fail with 402.

**API base**: `https://mega-api-prod.nemovideo.ai`

**Create session**: POST `/api/tasks/me/with-session/nemo_agent` — body `{"task_name":"project","language":"<lang>"}` — returns `task_id`, `session_id`. After creating a session, give the user a link: `https://nemovideo.com/workspace/claim?token=$TOKEN&task=<task_id>&session=<session_id>&skill_name=soulgen&skill_version=1.0.0&skill_source=<platform>`

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
| 2001 | No credits | Anonymous: show registration URL with `?bind=<id>` (get `<id>` from create-session or state response when needed). Registered: "Top up at nemovideo.ai" |
| 4001 | Unsupported file | Show supported formats |
| 4002 | File too large | Suggest compress/trim |
| 400 | Missing X-Client-Id | Generate Client-Id and retry (see §1) |
| 402 | Free plan export blocked | Subscription tier issue, NOT credits. "Register at nemovideo.ai to unlock export." |
| 429 | Rate limit (1 token/client/7 days) | Retry in 30s once |

## FAQ

**What kinds of images can SoulGen generate?** SoulGen specializes in character-focused images including anime-style art, photorealistic portraits, fantasy characters, and sci-fi figures. It handles a wide range of artistic styles based on your prompt.

**How detailed should my prompt be?** The more specific, the better. Include details like hair color, eye color, clothing, setting, lighting, and art style. For example, 'soft watercolor style, warm sunset background' will produce very different results than 'dark cinematic lighting, cyberpunk city.'

**Can I use a reference image to guide the output?** Yes — SoulGen can work with reference images to match a style, likeness, or character design you already have in mind.

**Is SoulGen good for beginners?** Absolutely. You don't need any design experience. Start with a simple description and refine from there. The skill is designed to be intuitive for first-time users and powerful enough for experienced creators.

## Use Cases

SoulGen shines across a wide range of creative and professional scenarios. Game developers use it to rapidly prototype character designs before committing to final art assets, saving hours of concept work. Comic and manga artists rely on it to establish visual consistency for recurring characters across panels and chapters.

Content creators and streamers use SoulGen to build unique anime-style avatars and virtual personas that stand out on platforms like Twitch, YouTube, and Instagram. Writers visualizing their fiction can generate portraits of their protagonists and antagonists to share with readers or use as personal reference.

Marketing teams and indie studios also use SoulGen to create eye-catching character art for promotional materials, thumbnails, and social posts — without needing a full art department. Wherever you need compelling character visuals quickly, SoulGen fits the workflow.
