---
name: ffmpeg-video-to-mp3
version: "1.0.0"
displayName: "FFmpeg Video to MP3 Converter — Extract High-Quality Audio from Any Video File"
description: >
  Turn raw video files into clean, ready-to-use MP3 audio tracks in seconds. This ffmpeg-video-to-mp3 skill strips the audio layer from your footage and delivers a properly encoded MP3 — no quality loss, no manual fiddling. Works with mp4, mov, avi, webm, and mkv formats. Perfect for podcasters pulling interview recordings, creators repurposing video content, and editors needing standalone audio assets.
metadata: {"openclaw": {"emoji": "🎵", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
apiDomain: https://mega-api-prod.nemovideo.ai
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

## Getting Started

> Hey there! Ready to pull the audio from your video? Drop in your mp4, mov, avi, webm, or mkv file and I'll convert it to a clean MP3 for you — just tell me your file and any bitrate preferences to get started.

**Try saying:**
- "Convert this mp4 interview recording to an MP3 at 192kbps for my podcast episode."
- "Extract the audio from my webinar.mkv file and save it as a high-quality MP3."
- "I have a mov file from my iPhone — can you pull the audio out as an MP3 with a small file size?"

### Getting Connected

Before handling any user request, establish a connection to the NemoVideo backend. Show a brief status like "Connecting...".

**If `NEMO_TOKEN` is in the environment**, use it directly and create a session. Otherwise, acquire a free starter token:
- Ensure a client identifier exists at `~/.config/nemovideo/client_id` (create one as a UUID if needed)
- POST to `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with the `X-Client-Id` header
- The response includes a `token` with 100 free credits valid for 7 days — use it as NEMO_TOKEN

**Then create a session** by POSTing to `/api/tasks/me/with-session/nemo_agent` with Bearer authorization and body `{"task_name":"project","language":"en"}`. The `session_id` in the response is needed for all following requests.

Tell the user you're ready. Keep the technical details out of the chat.

# Pull Studio-Quality Audio Straight From Your Video

You shot the perfect interview, recorded a live session, or captured a webinar — but now you need just the audio. This skill takes any video file and extracts the audio track as a fully encoded MP3, ready to upload, edit, or share. No re-encoding artifacts, no silent gaps, just the audio exactly as it existed in the original footage.

Whether you're a podcaster who records video calls and needs the audio-only version, a content creator repurposing YouTube videos for a podcast feed, or a video editor who needs to hand off a music or voiceover track separately, this skill fits naturally into your workflow. Drop in your file, specify your preferences, and get your MP3 back fast.

Support covers the most common video containers — mp4, mov, avi, webm, and mkv — so regardless of how your footage was captured or exported, the conversion just works. Bitrate control is also available, giving you the flexibility to optimize for file size or maximum audio fidelity depending on where the file is headed.

## Routing Your Conversion Requests

When you drop a video file or URL into the chat, the skill parses your intent and routes the extraction job to the appropriate FFmpeg pipeline based on format, bitrate preferences, and any codec flags you specify.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## NemoVideo API Reference

The NemoVideo backend spins up a containerized FFmpeg instance that demuxes your source container — whether MKV, MP4, MOV, or AVI — strips the video stream, and re-encodes or losslessly extracts the audio track to MP3 at your target bitrate (up to 320kbps CBR). All processing happens server-side, so no local FFmpeg installation is required.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `ffmpeg-video-to-mp3`
- `X-Skill-Version`: from frontmatter `version`
- `X-Skill-Platform`: detect from install path (`~/.clawhub/` → `clawhub`, `~/.cursor/skills/` → `cursor`, else `unknown`)

**All requests** must include: `Authorization: Bearer <NEMO_TOKEN>`, `X-Skill-Source`, `X-Skill-Version`, `X-Skill-Platform`. Missing attribution headers will cause export to fail with 402.

**API base**: `https://mega-api-prod.nemovideo.ai`

**Create session**: POST `/api/tasks/me/with-session/nemo_agent` — body `{"task_name":"project","language":"<lang>"}` — returns `task_id`, `session_id`. After creating a session, give the user a link: `https://nemovideo.com/workspace/claim?token=$TOKEN&task=<task_id>&session=<session_id>&skill_name=ffmpeg-video-to-mp3&skill_version=1.0.0&skill_source=<platform>`

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

## Use Cases

**Podcast Production:** Many podcasters record their guest interviews over video calls. Rather than keeping the full video file, this skill lets you extract just the audio track as an MP3, ready to drop into your editing timeline or upload directly to your hosting platform.

**Content Repurposing:** If you publish video content on YouTube or social media, converting those videos to MP3 lets you distribute the same content on podcast platforms or audio apps without re-recording anything. One shoot, multiple formats.

**Music and Live Performance Recordings:** Videographers who capture live concerts or rehearsals can use this skill to deliver an MP3 of the performance to artists or clients alongside the video — useful for demos, archives, or promotional material.

**E-Learning and Training:** Course creators who record video lessons can extract the audio tracks so learners have an MP3 version to listen to on the go, extending the reach of existing content without extra production work.

## FAQ

**What video formats are supported?** This skill handles mp4, mov, avi, webm, and mkv files — the most widely used video containers across cameras, phones, screen recorders, and editing software.

**Can I control the MP3 bitrate?** Yes. You can specify a target bitrate such as 128kbps for smaller files or 320kbps for maximum audio quality. If you don't specify, a sensible default is applied automatically.

**Will the audio quality degrade during conversion?** The audio is extracted directly from the video's existing audio stream. As long as the source file has a decent audio track, the resulting MP3 will reflect that quality accurately.

**What if my video has multiple audio tracks?** You can specify which audio track to extract — for example, if a video has both a main mix and a commentary track, just mention which one you want in your request and the correct stream will be targeted.
