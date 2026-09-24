---
name: ai-clip-maker
version: 1.0.1
displayName: "AI Clip Maker — Extract Viral Clips from Long Videos Automatically with AI"
description: >
  Extract viral clips from long videos automatically with AI — NemoVideo analyzes podcasts, streams, lectures, interviews, and any long-form content to find the most shareable moments, then produces polished short clips ready for TikTok, Instagram Reels, and YouTube Shorts. AI identifies: emotional peaks, quotable statements, funny moments, controversial takes, insightful explanations, and dramatic reveals. Each clip is extracted with context, reframed to vertical, captioned, and exported platform-ready. AI clip maker, clip extractor, highlight clipper, auto clip generator, podcast clip maker, stream clipper, viral clip finder.
metadata: {"openclaw": {"emoji": "✂️", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

# AI Clip Maker — Every Long Video Contains 10 Viral Clips Waiting to Be Found

Long-form video is a goldmine of short-form content. A 60-minute podcast contains 8-15 moments that would perform as standalone clips: a surprising statistic, a personal revelation, a controversial opinion, a perfectly articulated insight, a funny exchange, a motivational statement. Each of these moments — extracted, trimmed, captioned, and reframed — is a complete piece of content for TikTok, Reels, or Shorts. The average podcast episode produces enough clips for 2 weeks of daily short-form posting. The problem is finding those moments. A human clipping a 60-minute video scrubs through the entire recording, identifies promising moments by memory and instinct, sets in-and-out points, evaluates whether each clip stands alone without context, and repeats for every potential clip. For a single episode: 2-4 hours of clipping work to produce 8-12 clips. For a weekly podcast with back catalog: the clipping debt is insurmountable. NemoVideo watches the entire video once and identifies every clippable moment using multiple signals: transcript analysis (quotable phrases, strong statements, complete thoughts), audio analysis (energy spikes, laughter, emphasis), engagement prediction (which moments would make viewers stop scrolling), and narrative completeness (does the clip make sense without the surrounding context). Each identified moment is extracted, trimmed to optimal length, reframed to vertical, captioned in trending style, and exported platform-ready.

## Use Cases

1. **Podcast Clipping — Weekly Episode to Daily Clips (45-90 min → 10-15 clips)** — A weekly interview podcast runs 75 minutes. NemoVideo: transcribes the full episode, identifies 12 standout moments (ranked by virality potential: surprising facts > personal stories > actionable advice > funny exchanges), extracts each with 2-3 seconds of context before and after (the clip starts mid-thought → confusing; starts with setup → compelling), reframes to 9:16 vertical with speaker face tracking, applies word-by-word animated captions (white bold, accent color highlight, dark pill background), adds the podcast branding (name + episode number as subtle lower-third), and exports all 12 clips. One episode → 12 clips → nearly 2 weeks of daily content across TikTok, Reels, and Shorts.

2. **Stream Clipping — Live Stream to Highlights (2-8 hours → 20-50 clips)** — A 4-hour Twitch stream contains dozens of clippable moments. NemoVideo: analyzes audio peaks (streamer reactions, audience interaction sounds), visual events (gameplay kills, wins, funny glitches), and chat activity spikes (emote floods, PogChamp clusters), extracts 30 clips ranked by entertainment value, applies gaming-native editing (zoom on key moments, slow-mo on highlights, meme captions on funny parts), and exports in both horizontal (Twitch/YouTube) and vertical (TikTok/Shorts) formats. A 4-hour stream becomes a month of clip content.

3. **Lecture Clipping — Educational Highlights (30-120 min → 5-10 clips)** — A 90-minute conference keynote contains insights that deserve wider distribution. NemoVideo: identifies the key takeaways (the "tweetable" moments — complete ideas expressed in 30-60 seconds), extracts each with the visual context (slides, demonstrations), adds clean professional captions (sentence-level for LinkedIn, word-by-word for TikTok), and formats for the platforms where professional content performs (LinkedIn 16:9 + TikTok 9:16). The keynote that 500 people attended reaches 500,000 through strategic clipping.

4. **Interview Clipping — Best Answers as Standalone Content (20-60 min → 8-12 clips)** — A 45-minute interview with a CEO covers 15 questions. NemoVideo: identifies the 10 most compelling answers (judged by: specificity of insight, emotional delivery, universality of relevance), extracts each as a Q&A clip (includes the question for context), reframes with the speaker centered in vertical format, adds the interviewee's name/title as a lower-third, and captions. Each clip is a self-contained piece of thought leadership content attributed to the speaker.

5. **Back Catalog Mining — Clip 100 Old Episodes (batch)** — A podcast with 200 episodes has never been clipped for short-form. NemoVideo: batch-processes the entire catalog, extracts 8-12 clips per episode (producing 1,600-2,400 total clips), ranks all clips by predicted virality, identifies the top 100 across the entire catalog, and delivers a content calendar showing which clips to post each day. Years of untapped content unlocked in one batch operation.

## How It Works

### Step 1 — Upload Long Video
Any long-form content: podcast, stream, lecture, interview, webinar, meeting, event recording. Any length — NemoVideo handles multi-hour files.

### Step 2 — Set Clip Preferences
Clip style (trending captions, clean professional, gaming-native), target length (15-60 seconds), number of clips desired, and platform targets.

### Step 3 — Generate
```bash
curl -X POST https://mega-api-prod.nemovideo.ai/api/v1/generate \
  -H "Authorization: Bearer $NEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "ai-clip-maker",
    "prompt": "Extract the 10 best clips from a 65-minute podcast interview. Find: surprising facts, strong opinions, personal stories, actionable advice, and funny moments. Each clip 30-55 seconds. Include 2-3 seconds of setup context before the main moment. Reframe to 9:16 vertical with face tracking. Captions: word-by-word highlight (white #FFFFFF, coral highlight #FF6B6B, dark pill bg, large font). Add podcast branding: show name + episode number as lower-third. Rank clips by virality potential. Export for TikTok + Reels + Shorts.",
    "clip_count": 10,
    "clip_duration": "30-55 sec",
    "clip_types": ["surprising-facts", "strong-opinions", "personal-stories", "actionable-advice", "funny-moments"],
    "context_buffer": 3,
    "reframe": "9:16-face-tracking",
    "captions": {"style": "word-highlight", "text": "#FFFFFF", "highlight": "#FF6B6B", "bg": "pill-dark", "size": "large"},
    "branding": {"show": "The Growth Show", "episode": "EP 142"},
    "rank_by": "virality",
    "platforms": ["tiktok", "reels", "shorts"]
  }'
```

### Step 4 — Review and Schedule
Preview all clips ranked by virality. Adjust: trim points, caption timing, clip selection. Schedule for daily posting across platforms.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `prompt` | string | ✅ | Source description and clipping preferences |
| `clip_count` | integer | | Number of clips to extract (1-50) |
| `clip_duration` | string | | "15-30 sec", "30-55 sec", "45-60 sec" |
| `clip_types` | array | | ["surprising", "funny", "emotional", "actionable", "controversial"] |
| `context_buffer` | integer | | Seconds of setup context before clip |
| `reframe` | string | | "9:16-face-tracking", "9:16-center-crop", "keep-original" |
| `captions` | object | | {style, text, highlight, bg, size} |
| `branding` | object | | {show, episode, logo} |
| `rank_by` | string | | "virality", "chronological", "topic" |
| `platforms` | array | | ["tiktok", "reels", "shorts", "linkedin", "twitter"] |
| `batch` | array | | Multiple long videos |

## Output Example

```json
{
  "job_id": "acm-20260328-001",
  "status": "completed",
  "source_duration": "65:22",
  "clips_found": 18,
  "clips_exported": 10,
  "clips": [
    {"rank": 1, "file": "clip-01-surprising-stat.mp4", "duration": "0:42", "timestamp": "12:15-12:57", "type": "surprising-fact", "virality_score": 94},
    {"rank": 2, "file": "clip-02-personal-story.mp4", "duration": "0:51", "timestamp": "28:30-29:21", "type": "personal-story", "virality_score": 91},
    {"rank": 3, "file": "clip-03-hot-take.mp4", "duration": "0:38", "timestamp": "35:08-35:46", "type": "strong-opinion", "virality_score": 88},
    {"rank": 4, "file": "clip-04-advice.mp4", "duration": "0:45", "timestamp": "41:22-42:07", "type": "actionable-advice", "virality_score": 85},
    {"rank": 5, "file": "clip-05-funny-exchange.mp4", "duration": "0:33", "timestamp": "48:55-49:28", "type": "funny-moment", "virality_score": 83}
  ]
}
```

## Tips

1. **Clips need a self-contained arc: setup → insight → reaction** — A clip that starts mid-sentence confuses viewers. A clip that ends without resolution frustrates them. Every clip should be a micro-story with beginning, middle, and end.
2. **The first 2 seconds of the clip determine if it gets watched** — Even within a clip, the opening matters. If the first words are "um, so, yeah" the viewer scrolls. Trim the clip to start at the moment energy is highest.
3. **Surprising content outperforms agreeable content 3:1** — Clips that make viewers think "wait, really?" generate shares and comments. Clips that make viewers think "yeah, that's true" get a nod and a scroll. Prioritize surprising over validating.
4. **Batch-clipping back catalogs is the highest-ROI content strategy** — 100 podcast episodes × 10 clips = 1,000 pieces of content from recordings that already exist. Zero new production cost. The content is already recorded — clipping just unlocks it.
5. **Platform-specific caption style matters** — TikTok: large bold word-by-word with accent color highlight. LinkedIn: clean sentence-level, professional font. The caption style signals which audience the content is for.

## Output Formats

| Format | Resolution | Platform |
|--------|-----------|----------|
| MP4 9:16 | 1080x1920 | TikTok / Reels / Shorts |
| MP4 16:9 | 1920x1080 | YouTube / LinkedIn / Twitter |
| MP4 1:1 | 1080x1080 | Instagram / Facebook feed |
| SRT | — | Per-clip subtitles |

## Related Skills

- [ai-reel-creator](/skills/ai-reel-creator) — Reel creation
- [ai-video-creator](/skills/ai-video-creator) — Video creation
- [video-creation-ai](/skills/video-creation-ai) — AI video production
