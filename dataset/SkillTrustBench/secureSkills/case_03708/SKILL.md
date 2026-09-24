---
name: ai-video-splitter
version: 1.0.1
displayName: "AI Video Splitter — Split Videos into Clips Chapters and Scenes Automatically"
description: >
  Split videos into clips, chapters, and scenes automatically with AI — detect topic changes, scene transitions, silence gaps, and speaker turns to divide any long video into individual segments. NemoVideo analyzes content structure and splits intelligently: podcasts into topic discussions, lectures into lesson modules, meetings into agenda items, streams into game sessions, interviews into Q&A pairs, and tutorials into step-by-step segments. Upload one long video and receive organized individual files. AI video splitter, split video into clips, auto scene detection, video chapter splitter, divide video into parts, clip extractor AI, smart video cutter.
metadata: {"openclaw": {"emoji": "🔪", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

# AI Video Splitter — Unlock the Content Trapped Inside Long Videos

Long videos are content warehouses. A 60-minute podcast contains a dozen standalone discussions. A 2-hour workshop contains fifteen teaching modules. A 4-hour stream contains fifty highlight moments. Every piece of content inside those long videos has independent value — value that is locked away because nobody will scrub through 60 minutes to find the 3 minutes they care about. Video splitting is the key that unlocks that value. The challenge is finding where to split. Not at arbitrary timestamps — at meaningful boundaries where one topic ends and another begins, where one scene transitions to another, where one speaker finishes and another starts. Finding these boundaries in a 60-minute video takes a human 60 minutes of watching. Finding them in a library of 100 videos takes weeks. NemoVideo finds every meaningful split point in seconds. The AI analyzes multiple signals simultaneously: transcript analysis (topic transitions detected from language patterns), audio analysis (silence gaps, speaker changes, energy shifts), visual analysis (scene changes, slide transitions, location changes), and structural analysis (meeting agenda patterns, lecture formats, interview rhythms). Each split point is identified, the video is divided into clean individual segments, and each segment is exported with an auto-generated title, proper transitions at cut points, and platform-ready formatting.

## Use Cases

1. **Podcast to Clips — One Episode Becomes a Content Library (45-90 min)** — A business podcast interviews a CEO for 70 minutes covering: their origin story, biggest failure, hiring philosophy, management style, industry predictions, book recommendations, and rapid-fire questions. NemoVideo: identifies all 7 topic boundaries from transcript analysis, splits into 7 individual clips (8-12 minutes each), titles each from the topic discussed ("Hiring Philosophy — Why We Stopped Doing Culture Fit Interviews"), applies 0.3s crossfade at each split point, and extracts the single most quotable 40-second moment from each clip as a vertical Short. Seven YouTube clips + seven TikTok Shorts from one interview. The episode that took 70 minutes to record generates 14 pieces of content.

2. **Course Module Splitting — Lecture to Learning Units (30-120 min)** — An online course platform requires videos under 15 minutes. A professor recorded a 90-minute lecture as one continuous file. NemoVideo: detects 6 natural module boundaries (introduction, concept 1, example 1, concept 2, example 2, summary), splits at each boundary, adds module title cards ("Module 3: Market Equilibrium — 12:30"), numbers sequentially, generates a table of contents with timestamps, and exports all 6 modules. A single lecture recording becomes a structured course with navigable modules — without the professor re-recording anything.

3. **Meeting to Agenda Items — Find What Matters (30-90 min)** — A 55-minute all-hands meeting covers: CEO update, product roadmap, sales results, engineering milestones, Q&A, and next steps. Only the product roadmap and Q&A sections are relevant to most team members. NemoVideo: identifies all 6 agenda segments using speaker changes and topic transitions, splits into individual segments, titles each with the agenda topic and speaker, and provides a summary document listing each segment with timestamps and key points. Team members watch only their relevant 10-minute segment instead of the full 55 minutes.

4. **Stream to Games — Divide by Session (2-8 hours)** — A 5-hour variety stream cycles through 4 different games plus chat-only segments between them. NemoVideo: detects game transitions (loading screens, menu changes, game audio shifts), splits into per-game segments ("Segment 2: Elden Ring — 1:22:00"), identifies the top 5 highlight moments within each game segment, and exports: 4 full game sessions (for YouTube), 20 highlight clips (for Shorts/TikTok), and a 5-minute best-of compilation. Five hours of streaming becomes a structured content catalog.

5. **Back Catalog Processing — Split 100 Videos at Once (batch)** — A media company has 500 hours of unsplit interview footage archived across 200 files. NemoVideo: batch-processes the entire catalog, splits each interview into individual Q&A segments, titles each with the question asked, tags by topic and speaker, and organizes into a searchable database. Two hundred monolithic files become 2,000+ individually-accessible clips. A content library that was practically unsearchable becomes a structured catalog.

## How It Works

### Step 1 — Upload Long Video
Any length, any format. NemoVideo handles multi-hour files without issue.

### Step 2 — Choose Split Method
Topic-based (AI detects subject changes), scene-based (visual transitions), silence-based (pauses), speaker-based (who is talking), duration-based (equal chunks), or custom timestamps.

### Step 3 — Generate
```bash
curl -X POST https://mega-api-prod.nemovideo.ai/api/v1/generate \
  -H "Authorization: Bearer $NEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "ai-video-splitter",
    "prompt": "Split a 70-minute podcast interview into individual topic segments. Detect topic transitions from conversation flow. Title each segment with the topic discussed. Add 0.3s crossfade at each split point. Extract the best 40-second moment from each segment as a vertical Short (9:16, word-by-word captions: white #FFFFFF, #F472B6 pink highlight, pill-dark bg). Export all segments as MP4.",
    "split_method": "topic",
    "crossfade": 0.3,
    "auto_title": true,
    "shorts": {"per_segment": 1, "duration": "40s", "format": "9:16", "captions": {"style": "word-highlight", "text": "#FFFFFF", "highlight": "#F472B6", "bg": "pill-dark"}},
    "output_format": "mp4"
  }'
```

### Step 4 — Review and Distribute
Preview each segment's boundaries. Verify: no mid-sentence cuts, each segment stands alone, titles are accurate. Download and distribute across platforms.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `prompt` | string | ✅ | Video description and split requirements |
| `split_method` | string | | "topic", "scene", "silence", "speaker", "duration", "timestamps" |
| `split_duration` | string | | For duration method: "5 min", "10 min", "15 min" |
| `timestamps` | array | | Manual split points: ["5:30", "12:15"] |
| `crossfade` | float | | Seconds at each cut (default: 0) |
| `auto_title` | boolean | | AI titles per segment |
| `shorts` | object | | {per_segment, duration, format, captions} |
| `output_format` | string | | "mp4", "mov" |
| `naming` | string | | "sequential", "sequential-with-title", "title-only" |
| `chapters_only` | boolean | | Output timestamps without splitting |
| `batch` | array | | Multiple videos |

## Output Example

```json
{
  "job_id": "avs-20260328-001",
  "status": "completed",
  "source_duration": "70:15",
  "split_method": "topic",
  "segments": [
    {"file": "01-origin-story.mp4", "duration": "9:22", "start": "0:00"},
    {"file": "02-biggest-failure.mp4", "duration": "11:05", "start": "9:22"},
    {"file": "03-hiring-philosophy.mp4", "duration": "10:18", "start": "20:27"},
    {"file": "04-management-style.mp4", "duration": "8:45", "start": "30:45"},
    {"file": "05-industry-predictions.mp4", "duration": "12:30", "start": "39:30"},
    {"file": "06-book-recommendations.mp4", "duration": "7:15", "start": "52:00"},
    {"file": "07-rapid-fire.mp4", "duration": "11:00", "start": "59:15"}
  ],
  "shorts_extracted": 7,
  "total_segments": 7
}
```

## Tips

1. **Topic splitting produces the most valuable individual segments** — Each segment is a complete discussion that stands alone. Scene splitting creates too many fragments. Duration splitting cuts mid-topic. Topic splitting creates content with independent value.
2. **Crossfade at split points prevents audio artifacts** — Even at perfect split points, a hard cut can create an audible pop from the room tone discontinuity. A 0.2-0.3 second crossfade eliminates this completely.
3. **Extract Shorts from each segment to double content output** — Splitting creates long-form segments. Extracting a Short from each creates short-form content. Both from one source video with one operation.
4. **Auto-titling eliminates the tedious metadata step** — Manually titling 7-10 segments requires re-listening to each. AI titles based on transcript analysis are accurate and instant. Ready for YouTube titles and file naming.
5. **Batch splitting unlocks content at scale** — 100 podcast episodes × 8 segments × 8 Shorts = 1,600 content pieces from existing recordings. The content was always there — splitting makes it accessible.

## Output Formats

| Format | Content | Use Case |
|--------|---------|----------|
| MP4 16:9 | Individual segments | YouTube / website |
| MP4 9:16 | Short clips per segment | TikTok / Reels / Shorts |
| JSON | Segment metadata | CMS / YouTube chapters |
| SRT | Per-segment subtitles | Accessibility |

## Related Skills

- [ai-video-color-grading](/skills/ai-video-color-grading) — Color grading
- [ai-video-trimmer](/skills/ai-video-trimmer) — Video trimming
- [ai-clip-maker](/skills/ai-clip-maker) — Clip extraction
