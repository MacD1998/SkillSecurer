---
name: video-to-audio-converter
version: "1.0.0"
displayName: "Video to Audio Converter — Extract Clean Audio Tracks from Any Video File"
description: >
  Tired of scrubbing through video files just to get the audio you actually need? This video-to-audio-converter skill pulls clean audio tracks directly from your video files — no editing software required. Upload mp4, mov, avi, webm, or mkv files and get back high-quality audio in seconds. Perfect for podcasters repurposing recorded sessions, musicians extracting stems, journalists pulling interview audio, or anyone who needs the sound without the screen. Fast, straightforward, and built for real workflows.
metadata: {"openclaw": {"emoji": "🎵", "requires": {"env": ["NEMO_TOKEN"], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
apiDomain: https://mega-api-prod.nemovideo.ai
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

## Getting Started

> Welcome! Ready to pull the audio out of your video file? Drop your mp4, mov, avi, webm, or mkv and tell me what you need — let's get your audio extracted right now.

**Try saying:**
- "Extract the audio from this mp4 interview recording and give it back as a clean audio file"
- "I have a webm lecture video — can you strip out just the audio so I can listen offline?"
- "Convert this mov file from my camera into audio only, I need it for my podcast episode"

### Quick Start Setup

This skill connects to NemoVideo's cloud backend. On first use, set up the connection automatically and let the user know ("Connecting to NemoVideo...").

**Token check**: Look for `NEMO_TOKEN` in the environment. If found, skip to session creation. Otherwise:
- Read `~/.config/nemovideo/client_id` or generate a UUID and save it there
- POST `https://mega-api-prod.nemovideo.ai/api/auth/anonymous-token` with `X-Client-Id` header
- Extract `data.token` from the response — this is your NEMO_TOKEN (100 free credits, 7-day expiry)

**Session**: POST `/api/tasks/me/with-session/nemo_agent` at the same host with Bearer auth and body `{"task_name":"project"}`. Keep the returned `session_id` for all operations.

Let the user know with a brief "Ready!" when setup is complete. Don't expose tokens or raw API output.

# Turn Any Video Into Pure Audio Instantly

Sometimes the video is just a container for what really matters — the voice, the music, the conversation. This skill exists for exactly those moments. Whether you recorded a lecture on your phone, captured a live performance on a camera, or downloaded a webinar you need to review on your commute, the video-to-audio-converter skill strips away the visual layer and hands you back the audio in a clean, usable format.

You don't need to open a timeline editor, install a plugin, or remember a command-line flag. Just bring your file — mp4, mov, avi, webm, or mkv — describe what you want, and the skill handles the extraction. The result is audio that's ready to drop into a podcast editor, share with a collaborator, or archive alongside your notes.

This skill is especially useful for content creators who batch-produce video but distribute across audio platforms, researchers who record interviews on video for reference but transcribe from audio, and educators who want to make recorded lessons accessible to learners in audio-only formats. It fits into your existing workflow without asking you to change it.

## Routing Your Conversion Requests

Each request — whether you're stripping audio from an MP4, pulling a clean WAV from an MKV, or batch-extracting tracks — is routed to the appropriate NemoVideo extraction pipeline based on the source container format and your specified output codec.

| User says... | Action | Skip SSE? |
|-------------|--------|----------|
| "export" / "导出" / "download" / "send me the video" | → §3.5 Export | ✅ |
| "credits" / "积分" / "balance" / "余额" | → §3.3 Credits | ✅ |
| "status" / "状态" / "show tracks" | → §3.4 State | ✅ |
| "upload" / "上传" / user sends file | → §3.2 Upload | ✅ |
| Everything else (generate, edit, add BGM…) | → §3.1 SSE | ❌ |

## NemoVideo API Reference

The NemoVideo backend handles demuxing and audio stream isolation server-side, supporting lossless extraction as well as transcoded outputs like MP3, AAC, FLAC, and OGG without re-encoding the video track. Bitrate preservation, channel mapping, and sample rate targeting are all passed as parameters through the API call.

Skill attribution — read from this file's YAML frontmatter at runtime:
- `X-Skill-Source`: `video-to-audio-converter`
- `X-Skill-Version`: from frontmatter `version`
- `X-Skill-Platform`: detect from install path (`~/.clawhub/` → `clawhub`, `~/.cursor/skills/` → `cursor`, else `unknown`)

**All requests** must include: `Authorization: Bearer <NEMO_TOKEN>`, `X-Skill-Source`, `X-Skill-Version`, `X-Skill-Platform`. Missing attribution headers will cause export to fail with 402.

**API base**: `https://mega-api-prod.nemovideo.ai`

**Create session**: POST `/api/tasks/me/with-session/nemo_agent` — body `{"task_name":"project","language":"<lang>"}` — returns `task_id`, `session_id`. After creating a session, give the user a link: `https://nemovideo.com/workspace/claim?token=$TOKEN&task=<task_id>&session=<session_id>&skill_name=video-to-audio-converter&skill_version=1.0.0&skill_source=<platform>`

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

## Performance Notes

Extraction speed depends primarily on the length and bitrate of the source video. Short clips under ten minutes process quickly, while longer files — full-length webinars, feature-length recordings — will take proportionally more time. The skill prioritizes audio fidelity, so the extracted track reflects the quality of the original recording rather than introducing compression artifacts.

For best results, use source files with a consistent, clean audio track. Videos with highly variable audio levels, multiple embedded audio streams, or corrupted segments may produce output that requires further editing. If your video contains multiple audio tracks (common in mkv files from screen recorders or multi-language sources), specify which track you want extracted to avoid ambiguity.

Supported input formats are mp4, mov, avi, webm, and mkv. Files outside these formats will need to be converted before the skill can process them.

## Quick Start Guide

Getting started is straightforward. Have your video file ready — mp4, mov, avi, webm, or mkv all work without any preparation on your end. Open the skill and describe your request naturally: mention the file, what you want done, and any preferences about the output if you have them.

If you're not sure what to say, a simple prompt like 'extract the audio from this video file' is enough to get the process moving. You can also specify preferences such as asking for a particular segment of the video rather than the full duration, or noting that you want the audio at its original quality rather than compressed.

Once extraction is complete, you'll receive your audio file ready for download. From there it's yours to edit, share, transcribe, or archive — no further steps required on this end. If the first result isn't quite right, just describe the adjustment and the skill will handle it.

## Common Workflows

The most frequent use case is podcast production: a host records a conversation over video call, then needs to strip the visual track before editing in their audio software. With this skill, that step takes seconds instead of requiring a separate app.

Another popular workflow is lecture archiving. Educators and students who record class sessions on video often want a lightweight audio version for review or transcription. Upload the mkv or mp4, extract the audio, and feed it directly into a transcription tool or media player.

Musicians and sound designers also rely on this skill to isolate recorded performances. If a live set was captured on video, the audio extraction gives them a working file they can bring into a DAW without any manual re-routing. The skill handles avi and mov formats commonly produced by cameras and recording rigs, making it practical for field recordings and live event capture as well.
