---
name: ai-video-transcription
version: 1.0.1
displayName: "AI Video Transcription — Transcribe Video Speech to Text with 98% Accuracy"
description: >
  Transcribe video speech to text with 98%+ accuracy using AI — convert spoken audio from any video into perfectly timed text transcripts, searchable documents, subtitle files, and chapter-marked outlines. NemoVideo transcribes with context-aware speech recognition that handles technical vocabulary, proper nouns, multiple speakers, accents, and background noise. Generate word-level timed transcripts, speaker-identified dialogue, searchable full-text documents, subtitle files in any format, and structured content outlines from any video in 50+ languages. AI video transcription, transcribe video to text, speech to text video, video transcript generator, audio transcription AI, convert speech to text, video to document, meeting transcription, lecture transcription tool.
metadata: {"openclaw": {"emoji": "📜", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
---

# AI Video Transcription — Every Spoken Word. Perfectly Captured. Instantly Searchable.

Video content is rich but unsearchable. A 60-minute podcast contains 8,000-10,000 words of valuable content — invisible to search engines, impossible to skim, and inaccessible to anyone who cannot dedicate an hour to watching. Transcription unlocks this value: converting spoken content into text that can be searched, skimmed, quoted, repurposed, translated, and archived. Transcription transforms a video from a time-locked experience into an accessible, reusable asset. The applications span every domain: content creators need transcripts for blog post repurposing and SEO. Educators need transcripts for student study materials and accessibility compliance. Journalists need transcripts for quote verification and article research. Legal professionals need transcripts for deposition records. Businesses need transcripts for meeting documentation and knowledge management. Researchers need transcripts for qualitative data analysis. Platform auto-transcription provides 80-85% accuracy — one error every 15-20 words. For a 60-minute video, that is 400-600 errors: names misspelled, technical terms garbled, numbers wrong, and sentences that make no sense. Professional human transcription achieves 99%+ accuracy at $1.50-3.00 per audio minute with 24-48 hour turnaround. NemoVideo delivers 98%+ accuracy with word-level timing, speaker identification, context-aware vocabulary handling, and instant results — the quality threshold where transcripts are usable without extensive manual correction.

## Use Cases

1. **Podcast Transcription — Full Episode to Searchable Text (30-120 min)** — A weekly podcast needs transcripts for: blog post repurposing (the transcript becomes the basis for a written article), SEO (Google indexes transcript text, making the podcast discoverable through search), accessibility (deaf and hard-of-hearing audiences access the content), and show notes (key points, timestamps, and quotes extracted from the transcript). NemoVideo: transcribes the entire episode at 98%+ accuracy, identifies speakers with labels ("Host:" / "Guest:"), adds timestamps at paragraph breaks (linking text to the audio moment), handles conversational speech patterns (crosstalk, interruptions, filler removal optional), preserves proper nouns and brand names correctly, and outputs both a raw transcript and a structured show-notes document with key topics extracted.

2. **Meeting Documentation — Automated Minutes (15-90 min)** — Every meeting generates discussions and decisions that need documentation. Manual note-taking is incomplete and distracting. Post-meeting memory is unreliable. NemoVideo: transcribes the entire meeting with speaker identification (each participant labeled by name or role), identifies action items through speech pattern analysis ("We need to..." / "Can you..." / "By Friday..."), extracts key decisions ("We decided to..."), creates a structured meeting summary (attendees, topics discussed, decisions made, action items with owners), and provides the full transcript as a searchable reference. Meeting documentation that captures everything without anyone needing to take notes.

3. **Lecture Transcription — Study Materials from Class (45-90 min)** — University lectures and educational content need transcripts for student study, accessibility compliance (ADA/WCAG), and content archival. NemoVideo: transcribes lecture audio with technical vocabulary handling (discipline-specific terms transcribed correctly — "eigenvalue" not "I can value", "mitochondria" not "my toe Condria"), preserves mathematical and scientific notation when spoken ("x squared plus 2x" transcribed with correct formatting), creates chapter-marked sections aligned to topic transitions, generates a topic outline (extracting the lecture's structure from the speech content), and outputs in formats compatible with LMS platforms. Study materials generated automatically from every lecture.

4. **Content Repurposing — Video to Blog Post Foundation (any length)** — A creator's video content contains valuable information that could reach a wider audience as written content: blog posts, articles, newsletters, social media threads. NemoVideo: transcribes the video, structures the transcript into readable paragraphs (not a wall of continuous text — logical paragraph breaks at topic transitions), identifies key quotes and insights (highlighting the most publishable statements), creates a topic outline that serves as a blog post structure, and outputs a clean, formatted document ready for editorial refinement. A 15-minute video becomes a 2,000-word blog post foundation in seconds.

5. **Legal and Compliance — Verbatim Record (any length)** — Depositions, interviews, compliance recordings, and legal proceedings need accurate verbatim transcripts with speaker identification and timestamps. NemoVideo: provides strict verbatim transcription (preserving every word including false starts, filler words, and repetitions — the legal standard for evidentiary transcripts), identifies each speaker consistently throughout, adds precise timestamps (minute:second accuracy for every paragraph), handles overlapping speech (noting when multiple speakers talk simultaneously), and outputs in standard legal transcript format. Documentation that meets the accuracy and formatting standards of legal proceedings.

## How It Works

### Step 1 — Upload Video
Any video with speech. Any language. Any number of speakers. Any audio quality (NemoVideo's noise-robust recognition handles background noise, room echo, and poor microphone quality).

### Step 2 — Configure Transcription Output
Speaker identification, timestamp granularity, verbatim vs. clean transcript, output format, and any vocabulary guidance (proper nouns, technical terms).

### Step 3 — Generate
```bash
curl -X POST https://mega-api-prod.nemovideo.ai/api/v1/generate \
  -H "Authorization: Bearer $NEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "ai-video-transcription",
    "prompt": "Transcribe a 45-minute podcast interview with 2 speakers. Speaker identification: label as Host and Guest. Clean transcript (remove filler words and false starts). Paragraph breaks at natural topic transitions. Timestamps at each paragraph. Also generate: (1) Structured show notes with key topics and timestamps, (2) A list of the 5 most quotable statements, (3) An SRT subtitle file with word-level timing, (4) A blog-post-ready formatted version with topic headings. Custom vocabulary: NemoVideo, ClawHub, OpenClaw — ensure correct capitalization.",
    "speakers": {"identify": true, "labels": ["Host", "Guest"]},
    "transcript_style": "clean",
    "timestamps": "per-paragraph",
    "custom_vocabulary": ["NemoVideo", "ClawHub", "OpenClaw"],
    "outputs": {
      "transcript": {"format": "markdown", "paragraphs": true},
      "show_notes": true,
      "key_quotes": 5,
      "subtitles": {"format": "srt", "timing": "word-level"},
      "blog_ready": true
    }
  }'
```

### Step 4 — Review Accuracy
Scan the transcript for: proper noun spelling, technical term accuracy, speaker label correctness, and any passages where audio quality may have reduced accuracy (NemoVideo flags low-confidence sections). Correct and finalize.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `prompt` | string | ✅ | Transcription requirements |
| `speakers` | object | | {identify, labels, count} |
| `transcript_style` | string | | "verbatim", "clean", "editorial" |
| `timestamps` | string | | "per-paragraph", "per-sentence", "per-word" |
| `custom_vocabulary` | array | | Proper nouns and technical terms |
| `language` | string | | Source language (auto-detect if omitted) |
| `outputs` | object | | {transcript, show_notes, key_quotes, subtitles, blog_ready, action_items} |
| `noise_handling` | string | | "standard", "aggressive" for poor audio |

## Output Example

```json
{
  "job_id": "avtr-20260329-001",
  "status": "completed",
  "source_duration": "45:12",
  "language": "en",
  "confidence": 0.984,
  "speakers": 2,
  "word_count": 7840,
  "outputs": {
    "transcript": {"file": "podcast-transcript.md", "paragraphs": 62},
    "show_notes": {"file": "podcast-show-notes.md", "topics": 8},
    "key_quotes": {"file": "podcast-quotes.md", "quotes": 5},
    "subtitles": {"file": "podcast.srt", "format": "SRT"},
    "blog_ready": {"file": "podcast-blog-draft.md", "word_count": 7840}
  }
}
```

## Tips

1. **98% accuracy means usable transcripts; 85% means unusable ones** — At 98%, a 45-minute transcript has ~35 errors — minor corrections that take 5 minutes. At 85% (platform auto), the same transcript has ~525 errors — corrections that take longer than just transcribing manually. Accuracy is not a spectrum; there is a usability cliff.
2. **Custom vocabulary eliminates proper noun errors** — Providing a list of expected proper nouns (company names, product names, people's names, technical terms) before transcription allows the AI to match these terms correctly rather than guessing phonetically. Always provide custom vocabulary for domain-specific content.
3. **Clean transcripts are better for repurposing; verbatim for legal** — Clean transcripts (filler words removed, false starts cleaned, grammar lightly smoothed) produce readable text suitable for blog posts and documentation. Verbatim transcripts (every word exactly as spoken) are required for legal, compliance, and research contexts. Choose based on the output's purpose.
4. **Speaker identification transforms monologue into dialogue** — A transcript without speaker labels is a wall of text. Speaker-identified transcripts show conversation structure, making the content skimmable (jump to the guest's answers) and quotable (attribute statements to the correct person).
5. **Transcripts are the foundation for 5 content types** — One transcript produces: a blog post (reformatted), social media quotes (extracted), an email newsletter (summarized), subtitle files (timed), and show notes (structured). Transcription is the first step in a content multiplication pipeline.

## Output Formats

| Output | Format | Use Case |
|--------|--------|----------|
| Transcript | Markdown / TXT / DOCX | Blog, documentation, archive |
| Subtitles | SRT / VTT / TTML | Platform caption upload |
| Show Notes | Markdown | Podcast publishing |
| Blog Draft | Markdown | Content repurposing |
| Action Items | JSON / Markdown | Meeting documentation |

## Related Skills

- [ai-video-caption-generator](/skills/ai-video-caption-generator) — Render captions into video
- [ai-video-voiceover](/skills/ai-video-voiceover) — Add narration from text
- [ai-video-translation](/skills/ai-video-translation) — Translate transcribed content
- [ai-video-chapter-maker](/skills/ai-video-chapter-maker) — Chapter markers from transcript
