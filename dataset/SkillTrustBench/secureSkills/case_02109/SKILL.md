---
name: video-editor-online
version: "1.0.3"
displayName: "Video Editor Online — Edit, Trim, and Export Videos Directly in Your Browser"
description: >
  From raw footage to polished video in seconds — this skill powers your video-editor-online workflow by helping you cut clips, add captions, apply transitions, and export in the right format without installing anything. It handles the logic behind common editing decisions: aspect ratio conversion, timeline structuring, subtitle syncing, and export settings for different platforms. Built for creators who need fast turnaround on social content, short-form videos, tutorials, or repurposed footage. Think of it as an editing co-pilot that speaks your language instead of forcing you through a complex interface.
metadata: {"openclaw": {"emoji": "🎬", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN", "variant": "control"}}
---

## Getting Started

> Welcome to your video-editor-online workspace — whether you're trimming a raw recording or building a fully captioned reel from scratch, you're in the right place. Drop your video details or describe what you need edited and let's get it done.

**Try saying:**
- "I have a 12-minute screen recording of a tutorial — help me cut it down to the key moments and add chapter markers for YouTube"
- "Convert my horizontal 16:9 wedding highlight clip to a 9:16 vertical format for Instagram Reels without cropping out the subjects"
- "My podcast video has inconsistent audio levels and I need to add auto-synced captions before uploading to LinkedIn — what's the best approach?"

### Getting Connected

Before handling any user request, establish a connection to the backend API. Show a brief status like "Connecting...".

**If `NEMO_TOKEN` is in the environment**, use it directly and create a session. Otherwise, acquire a free starter token:
- Generate a UUID as client identifier
- POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with the `X-Client-Id` header
- The response includes a `token` with 100 free credits valid for 7 days — use it as NEMO_TOKEN

**Then create a session** by POSTing to `https://mega-api-prod.nemovideo.ai/api/tasks/me/with-session/nemo_agent` with Bearer authorization and body `{"task_name":"project","language":"en"}`. The `session_id` in the response is needed for all following requests.

Tell the user you're ready. Keep the technical details out of the chat.

# Edit Any Video Without Leaving Your Browser

Most people don't need a full desktop suite — they need to trim a clip, slap on some captions, and get it uploaded before the moment passes. This skill is built around that reality. Whether you're cutting down a long recording into a punchy 60-second reel or converting horizontal footage into a vertical format for Instagram Stories, the video-editor-online workflow keeps things fast and friction-free.

You describe what you want — in plain language — and this skill maps your intent to the right editing actions. Want to remove the first 10 seconds, add auto-generated subtitles, and export at 1080p? Just say so. No menus to dig through, no timeline drag-and-drop required unless you want it.

It also handles the less obvious stuff: suggesting cuts based on pacing, recommending export settings for YouTube vs. TikTok, and flagging common mistakes like mismatched audio levels or incorrect frame rates. It's the kind of guidance you'd get from a video editor friend who actually knows what they're doing.

## Routing Edits to the Right Pipeline

When you submit a trim, cut, merge, or export request, ClawHub parses your intent and routes it to the matching video processing endpoint based on the operation type, codec requirements, and output format you've selected.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## Cloud Rendering API Reference

All timeline renders, frame extractions, and transcode jobs run through a distributed cloud backend that handles H.264, H.265, and WebM encoding without touching your local CPU. Processed assets are temporarily staged in a secure buffer and streamed directly to your browser for download once the render pipeline completes.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `video-editor-online`
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

## Troubleshooting Common Video Editor Online Issues

**Export fails or stalls at a certain percentage** — This usually happens when the source file has a codec your browser-based editor doesn't support natively (common with .MKV or older .AVI files). Convert your source to H.264 MP4 before importing and you'll avoid 90% of export failures.

**Subtitles are out of sync after export** — If your video was recorded at a variable frame rate (common with screen recorders and phone cameras), subtitle timing calculated at a fixed frame rate will drift. Re-encode the source at a constant frame rate (24fps or 30fps) before adding captions.

**Video looks pixelated after export** — Check your export bitrate. Many online editors default to low bitrate settings to reduce file size. For 1080p content, aim for at least 8 Mbps for standard motion and 16+ Mbps for fast-moving footage.

**Audio and video fall out of sync mid-clip** — This is almost always a source file issue, not an editor bug. Run your file through a remux tool to realign the audio track before editing.

## Integration Guide — Connecting Video Editor Online to Your Workflow

**Connecting to cloud storage** — Most browser-based video editors support direct import from Google Drive, Dropbox, and OneDrive. Instead of uploading large files each time, link your cloud folder once and pull footage directly. This is especially useful for teams sharing raw footage across locations.

**Automating repetitive edits with templates** — If you produce recurring content formats — weekly recaps, product demos, interview cuts — build a reusable template with your intro, outro, font styles, and color grades locked in. Export the template and import it at the start of each new project to skip the setup phase entirely.

**Publishing directly to platforms** — Several video-editor-online tools support one-click publishing to YouTube, TikTok, and Instagram. Set up your channel credentials inside the editor's publish settings once, then export and post without downloading the file to your device first. This cuts the final step of your workflow significantly.

**Webhook and Zapier triggers** — If your editor supports it, set up a Zap that notifies your team in Slack or sends a review link via email the moment an export completes. Keeps feedback loops tight without manual status updates.
