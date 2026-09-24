---
name: ai-video-highlight-maker
version: 1.0.1
displayName: "AI Video Highlight Maker — Auto-Extract Best Moments and Create Highlight Reels"
description: >
  Auto-extract best moments and create highlight reels from any long video with AI — find peak moments, emotional highlights, action sequences, key quotes, and audience reactions, then compile into polished highlight clips. NemoVideo watches your entire video and identifies the moments worth sharing: laughter peaks, applause, dramatic pauses, visual action spikes, quotable statements, and engagement-worthy reactions. From a 2-hour stream or 60-minute event, get a 60-second highlight reel ready for social sharing. Highlight reel maker AI, best moments extractor, auto clip generator, video summary maker, key moment finder, stream highlights AI, event recap video, top clips generator.
metadata: {"openclaw": {"emoji": "⭐", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

# AI Video Highlight Maker — Hours of Content. Seconds of Magic.

Long-form content contains concentrated moments of brilliance buried in hours of context. A 3-hour live stream has 5 minutes of viral clips. A 90-minute conference talk has 3 quotes worth sharing. A 2-hour wedding video has 10 minutes that make people cry. A 45-minute podcast has the one insight that changes someone's perspective. Finding these moments manually means watching the entire video, noting timestamps, cutting clips, adding transitions, and exporting — hours of work for minutes of output. For streamers who produce 4-6 hours of content daily, manual highlight creation is physically impossible to maintain. NemoVideo watches the entire video and identifies highlight-worthy moments through multiple signals: audio energy spikes (laughter, applause, raised voices, music crescendos), visual action (fast movement, new scenes, dramatic lighting changes), speech analysis (quotable statements, emotional delivery, punchlines), chat engagement (for streams: moments when chat explodes with messages or emotes), and content structure (introductions, conclusions, topic transitions, demonstrations). The AI extracts these moments, orders them for narrative coherence, adds transitions, and exports a polished highlight reel at any target duration.

## Use Cases

1. **Stream Highlights — Daily Content to Viral Clips (2-6 hours → 1-5 min)** — A Twitch streamer records 4 hours daily and needs highlights for YouTube and TikTok. NemoVideo: analyzes the full stream, detects laugh moments, rage moments, clutch plays, viewer interaction highlights, and unexpected events, ranks by engagement potential, compiles the top moments into a 3-minute highlight reel with smooth transitions, adds the stream's chat reactions as overlay graphics at peak moments, and exports in both 16:9 (YouTube) and 9:16 (TikTok clips). Four hours of content → 3 minutes of the best moments, published the same day.

2. **Conference/Event Recap — Key Insights Summary (1-4 hours → 2-5 min)** — A multi-speaker conference or keynote needs a recap video for social media and email follow-up. NemoVideo: identifies each speaker's strongest quote or insight (based on audience reaction, delivery energy, and semantic importance), captures the best visual moments (applause, standing ovations, demonstrations), compiles a narrative-coherent recap (maintaining chronological flow), adds speaker name lower-thirds, and exports a professional event recap. Attendees get a shareable summary. Non-attendees get a taste that drives future registrations.

3. **Sports/Gaming — Action Highlights (any length → 30-120s)** — A football game, basketball match, or esports tournament needs a highlight reel. NemoVideo: detects high-action moments (scoring, near-misses, dramatic plays), identifies crowd/commentator reaction peaks, compiles with momentum-building order (not just chronological — saves the best for last), adds slow-motion on the most impressive plays, and exports a highlight reel that captures the excitement. The full game experience compressed into the most shareable moments.

4. **Wedding/Event — Emotional Highlights (2-4 hours → 3-8 min)** — A wedding videographer delivers a full ceremony and reception recording but needs a short emotional highlight video for the couple's social media. NemoVideo: identifies emotional peaks (vows, first kiss, first dance, speeches that make guests cry or laugh, surprise moments), captures reaction shots (parents' faces during vows, friends laughing during speeches), compiles with emotional arc (building from preparation to ceremony to celebration), adds music that matches the emotional trajectory, and exports a highlight film. The video that gets shared with family and posted on social media.

5. **Podcast — Quotable Clips for Social (30-90 min → multiple 15-60s clips)** — A podcast episode needs short clips for social media promotion. NemoVideo: identifies the 5-8 most quotable, insightful, or entertaining moments (based on delivery energy, statement completeness, and topic resonance), extracts each as a standalone clip that makes sense without context, adds subtitles (essential for social where most viewing is muted), and exports each clip in 9:16 for TikTok/Reels. One podcast episode becomes a week of social content.

## How It Works

### Step 1 — Upload Long-Form Video
Any video of any length. NemoVideo's analysis scales linearly — a 4-hour video takes proportionally longer but works identically.

### Step 2 — Define Highlight Parameters
Target duration, number of clips, style (action, emotional, funny, educational), and platform format.

### Step 3 — Generate
```bash
curl -X POST https://mega-api-prod.nemovideo.ai/api/v1/generate \
  -H "Authorization: Bearer $NEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "ai-video-highlight-maker",
    "prompt": "Create a 3-minute highlight reel from a 4-hour Twitch stream. Focus on: funny moments (laughter, chat spam), clutch gaming plays (close calls, victories), and viewer interaction highlights (raids, donations, funny chat messages). Order for maximum entertainment — build energy, peak in the middle, satisfying ending. Add transitions between clips (quick cuts, not fades). Add chat overlay on the funniest chat moments. Subtitles on all spoken moments. Export: 16:9 YouTube highlight + five 30-second 9:16 TikTok clips (the five best individual moments).",
    "source_type": "twitch-stream",
    "target_duration": 180,
    "highlight_types": ["funny", "clutch", "viewer-interaction"],
    "ordering": "entertainment-arc",
    "transitions": "quick-cut",
    "chat_overlay": true,
    "subtitles": true,
    "outputs": [
      {"type": "highlight-reel", "format": "16:9", "duration": 180},
      {"type": "individual-clips", "format": "9:16", "count": 5, "duration": 30}
    ]
  }'
```

### Step 4 — Review and Adjust
Preview the highlight reel. Swap any moment the AI selected for a different one. Adjust clip order. Re-export with changes.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `prompt` | string | ✅ | Highlight requirements |
| `target_duration` | int | | Target highlight reel length in seconds |
| `highlight_types` | array | | ["funny", "emotional", "action", "quotable", "dramatic"] |
| `ordering` | string | | "chronological", "entertainment-arc", "energy-build", "best-first" |
| `transitions` | string | | "quick-cut", "fade", "swipe", "none" |
| `subtitles` | boolean | | Add subtitles to highlights |
| `chat_overlay` | boolean | | Show chat reactions (for streams) |
| `music` | string | | Background music style or "preserve-original" |
| `outputs` | array | | [{type, format, duration, count}] |
| `exclude_segments` | array | | [{start, end}] time ranges to skip |

## Output Example

```json
{
  "job_id": "avhl-20260328-001",
  "status": "completed",
  "source_duration": "4:02:15",
  "moments_detected": 47,
  "moments_selected": 12,
  "outputs": {
    "highlight_reel": {
      "file": "stream-highlights-16x9.mp4",
      "duration": "3:04",
      "moments": 12,
      "ordering": "entertainment-arc"
    },
    "tiktok_clips": [
      {"file": "clip-1-funny-9x16.mp4", "duration": "0:28", "type": "funny", "source_time": "1:23:45"},
      {"file": "clip-2-clutch-9x16.mp4", "duration": "0:31", "type": "clutch", "source_time": "2:45:12"},
      {"file": "clip-3-funny-9x16.mp4", "duration": "0:26", "type": "funny", "source_time": "0:34:08"},
      {"file": "clip-4-viewer-9x16.mp4", "duration": "0:30", "type": "viewer-interaction", "source_time": "3:12:55"},
      {"file": "clip-5-clutch-9x16.mp4", "duration": "0:29", "type": "clutch", "source_time": "3:51:22"}
    ]
  }
}
```

## Tips

1. **Entertainment arc ordering outperforms chronological for highlights** — Starting with a strong hook, building to the peak moment, and ending satisfyingly creates a mini-narrative that holds attention. Chronological order often starts slow (stream openings are rarely the most exciting part).
2. **Individual clips for TikTok are often more valuable than the highlight reel** — A single 30-second viral clip can drive more channel growth than a 3-minute highlight reel. Always extract standalone moments alongside the compiled reel.
3. **Subtitles are mandatory for social clips** — Highlight clips posted on social media are viewed muted by default. Without subtitles, the funniest quote or most insightful moment is invisible. Always add subtitles to social clips.
4. **The 10:1 compression ratio is the sweet spot** — A 60-minute source → 6-minute highlight or 30-minute source → 3-minute highlight preserves enough context while staying watchable. More compression loses too many good moments; less compression includes filler.
5. **Chat overlay proves moments are genuinely entertaining** — When the chat explodes with "LUL" or "LMAO" during a moment, overlaying that reaction validates the humor for viewers who were not in the live stream. Social proof of entertainment value.

## Output Formats

| Format | Resolution | Use Case |
|--------|-----------|----------|
| MP4 16:9 | 1080p / 4K | YouTube highlight reel |
| MP4 9:16 | 1080x1920 | TikTok / Reels / Shorts clips |
| MP4 1:1 | 1080x1080 | Instagram / LinkedIn |

## Related Skills

- [ai-video-intro-maker](/skills/ai-video-intro-maker) — Video intros
- [ai-video-outro-maker](/skills/ai-video-outro-maker) — Video outros
- [ai-video-thumbnail-maker](/skills/ai-video-thumbnail-maker) — Thumbnails
- [ai-video-chapter-maker](/skills/ai-video-chapter-maker) — Video chapters
