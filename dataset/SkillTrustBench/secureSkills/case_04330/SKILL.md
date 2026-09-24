---
name: subtitle-maker
version: "1.0.0"
displayName: "Subtitle Maker — Auto-Generate Timed Captions in 50+ Languages from Any Video"
description: >
  You recorded a podcast episode. Your audience is global. The first viewer in Tokyo needs Japanese subtitles, the second in São Paulo needs Portuguese, the third in Berlin needs German. Subtitle Maker handles all of them from a single upload — AI transcribes speech, translates into 50+ languages, times every word to the audio waveform, and delivers styled subtitle files or burned-in captions ready for any platform.
metadata: {"openclaw": {"emoji": "🗣️", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
---

# Subtitle Maker — Your Audience Speaks Forty Languages. Your Video Speaks One. This Tool Bridges the Gap in Three Minutes.

You finished recording. The content is strong — forty minutes of conversation, insight, and expertise captured in crisp audio. Now the real work begins: making it accessible. The viewer in Osaka skips any video without Japanese subtitles. The commuter in Madrid watches on mute during the train ride and needs Spanish captions to follow along. The hearing-impaired viewer in London depends on accurate English subtitles synchronized to every syllable. Each of these viewers represents a segment of your audience that disappears the moment subtitles are absent or poorly timed.

Traditional subtitle creation is a manual grind. A professional subtitler charges $1-3 per minute of video per language. A forty-minute podcast episode in five languages costs $200-600 and takes three to five business days. The freelancer on Fiverr delivers faster but the timing drifts, the translations miss cultural nuance, and the revision cycle adds another two days. By the time the subtitles arrive, the content has lost its timeliness. Subtitle Maker collapses this entire workflow into a single API call: upload the video, specify the languages, receive frame-accurate subtitles styled and timed for immediate use.

## Use Cases

1. **Podcast Global Distribution — One Recording, Fifty Languages (per episode)** — Podcast video is the fastest-growing content format, and non-English audiences are the fastest-growing listener base. Subtitle Maker: transcribes the spoken conversation with speaker identification (differentiating host from guest), segments the transcript into subtitle blocks that respect sentence boundaries and natural pauses, translates each block into the target languages while preserving the conversational tone, synchronizes every subtitle to the audio waveform at word-level precision, and exports SRT files per language or burns the subtitles directly into separate video renders. The podcaster publishes one recording to YouTube with selectable subtitle tracks in twelve languages, tripling the addressable audience without recording a single additional word.

2. **Corporate Training Across Offices — Compliance in Every Local Language (per module)** — Multinational companies produce training videos at headquarters and distribute to offices worldwide. Subtitle Maker: ingests the training module (typically 15-30 minutes of a presenter with slides), transcribes the narration including technical terminology specific to the industry, translates into the required office languages (often 8-15 languages for global companies), formats the subtitles to avoid overlapping with on-screen text and slide content, and delivers the files in the format required by the LMS (Learning Management System). The compliance team that previously spent $2,000 and two weeks per module across ten languages now completes the same work in one afternoon.

3. **YouTube Creator Expansion — Breaking the Language Ceiling (per channel)** — YouTube channels plateau when they exhaust their native-language audience. Subtitle Maker: analyzes the channel's viewer geography to identify the highest-opportunity languages, transcribes the existing video library, translates and times subtitles for the priority languages, and generates the SRT files that YouTube accepts for its built-in subtitle selector. The creator uploads subtitle files alongside each new video, and the YouTube algorithm begins recommending the content to viewers who have set those languages as preferences. Channels that add subtitles in their top five viewer languages consistently report 20-40% audience growth within three months.

4. **Documentary and Film Post-Production — Festival-Ready Multilingual Delivery (per project)** — Film festivals require specific subtitle formats, timing standards, and translation quality. Subtitle Maker: handles the technical specifications (maximum characters per line, minimum display duration, reading speed calculation based on character count), applies professional subtitle formatting (two lines maximum, centered or left-aligned per convention, proper handling of italics for off-screen speech), and delivers the final files in the festival-required format (SRT, VTT, STL, or embedded burn-in). The independent filmmaker who cannot afford a $3,000 professional subtitle house gets festival-grade subtitle delivery at a fraction of the cost and timeline.

5. **Social Media Repurposing — Silent-Scroll Captions for Every Platform (per format)** — Eighty-five percent of social media video is watched without sound. Subtitle Maker: reformats long-form subtitles into the large, bold, center-screen caption style that social platforms demand, adjusts the timing for short attention spans (shorter display durations, faster transitions), applies platform-specific safe zones (avoiding the TikTok username area, the Instagram action buttons, the YouTube end-screen zone), and exports in the vertical 9:16 ratio with captions burned into the video. The content team that repurposes a single long-form video into ten platform-specific clips gets correctly captioned versions for every destination without manual adjustment.

## How It Works

### Step 1 — Upload Your Video
Any format, any length. The audio track is extracted and processed regardless of video codec.

### Step 2 — Select Target Languages
Choose from 50+ supported languages. The AI adapts translation style to the content type — conversational for vlogs, formal for corporate, precise for technical.

### Step 3 — Generate
```bash
curl -X POST https://mega-api-prod.nemovideo.ai/api/v1/generate \
  -H "Authorization: Bearer $NEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "subtitle-maker",
    "prompt": "Generate subtitles for a 25-minute podcast interview about startup fundraising. The host speaks English with an American accent, the guest speaks English with a French accent. Target languages: English (corrected transcript), Japanese, Portuguese (Brazilian), German, Spanish (Latin American). Style: conversational, preserve humor and informal language. Format: SRT files per language plus one English burned-in MP4 with white text, black outline, positioned at bottom-center safe zone.",
    "languages": ["en", "ja", "pt-BR", "de", "es-LATAM"],
    "output_formats": ["srt", "burned-mp4"],
    "caption_style": "conversational"
  }'
```

### Step 4 — Review and Publish
Download the SRT files, spot-check the translations in languages you know, and upload to your video platform. The burned-in version is ready for direct publishing.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `prompt` | string | ✅ | Subtitle requirements and context |
| `languages` | array | | Target language codes |
| `output_formats` | array | | srt, vtt, stl, burned-mp4 |
| `caption_style` | string | | conversational, formal, technical |

## Output Example

```json
{
  "job_id": "sm-20260330-001",
  "status": "completed",
  "source_language": "en",
  "target_languages": ["en", "ja", "pt-BR", "de", "es-LATAM"],
  "subtitle_files": {
    "en": "podcast-ep42-en.srt",
    "ja": "podcast-ep42-ja.srt",
    "pt-BR": "podcast-ep42-pt-BR.srt",
    "de": "podcast-ep42-de.srt",
    "es-LATAM": "podcast-ep42-es-LATAM.srt"
  },
  "burned_video": "podcast-ep42-captioned-en.mp4",
  "duration": "25:14",
  "word_count": 4832
}
```

## Tips

1. **Provide context in the prompt** — Mentioning the topic, speaker accents, and jargon domain improves transcription accuracy by 15-20%. "A podcast about machine learning" produces better results than "a podcast."
2. **Choose Brazilian vs European Portuguese** — The translation differs significantly. Specify pt-BR or pt-PT to match your audience geography.
3. **Use SRT for YouTube, VTT for web** — YouTube prefers SRT format for subtitle uploads. Web video players (HTML5) prefer WebVTT. Both are generated from the same transcription.
4. **Spot-check timestamps at scene transitions** — Subtitle timing is most likely to drift at hard cuts where audio context changes. A quick review at each scene boundary catches the rare timing issues.
5. **Request burned-in captions for social media** — Platform subtitle selectors are unreliable on mobile. Burned-in captions guarantee every viewer sees the text regardless of their device settings.

## Output Formats

| Format | Use Case | Platform |
|--------|----------|----------|
| SRT | Selectable subtitles | YouTube, Vimeo |
| VTT | Web video players | HTML5, HLS |
| STL | Broadcast standard | TV, streaming |
| Burned MP4 | Embedded captions | TikTok, Reels, Stories |

## Related Skills

- [ai-video-subtitle-editor](/skills/ai-video-subtitle-editor) — Edit existing subtitles
- [caption-creator-ai](/skills/caption-creator-ai) — Caption creation
- [subtitle-sync-tool](/skills/subtitle-sync-tool) — Timing correction
- [ai-video-travel-vlog-tips](/skills/ai-video-travel-vlog-tips) — Vlog captioning
