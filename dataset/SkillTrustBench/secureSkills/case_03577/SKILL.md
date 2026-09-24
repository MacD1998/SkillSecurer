---
name: video-analyzer
description: Analyze video content to extract keyframes, identify themes, and generate representative screenshots with analysis reports. Use when: (1) User sends a video file and asks for analysis, (2) User wants to understand video content without watching, (3) User needs representative screenshots from a video, (4) User asks "what's in this video" or "analyze this video". Supports MP4, MOV, AVI and other common video formats.
---

# Video Analyzer

## Overview

Extract keyframes from videos, analyze content with vision models, and generate comprehensive reports with 3 representative screenshots. Optimized for token efficiency using I-frame detection.

## Workflow

```
Video Input → Extract Keyframes → Vision Analysis → Select Top 3 → Generate Report → Send Output
```

## Step-by-Step Process

### 1. Download Video (if from Feishu)

When user sends video via Feishu, the file is auto-saved to:
```
~/.openclaw/media/inbound/<filename>.mp4
```

### 2. Extract Video Metadata

```bash
ffmpeg -i <video_path> 2>&1 | grep -E "(Duration|Video)"
```

Returns: duration, resolution, bitrate, codec info.

### 3. Extract Keyframes

Use the provided script for optimal keyframe extraction:

```bash
bash ~/.openclaw/workspace/skills/video-analyzer/scripts/extract_keyframes.sh <video_path> [output_dir]
```

**Parameters:**
- `video_path`: Path to video file (required)
- `output_dir`: Output directory (optional, defaults to `~/.openclaw/media/keyframes/`)

**Output:** JPEG images at 640px width, named `keyframe_XX.jpg`

**Token efficiency:** Uses I-frame detection to extract only meaningful frames, reducing token consumption by ~7% vs uniform sampling.

### 4. Analyze with Vision Model

Use the `image` tool with all extracted keyframes:

```
prompt: "Analyze these keyframes from a video. Please:
1. Describe the video's theme and content
2. Select 3 most representative frames (explain why)"
```

### 5. Generate Report

Structure the analysis report:

```markdown
## 📌 Video Theme
[Description]

## 🖼️ Representative Screenshots
| Frame | Reason |
|-------|--------|
| frame_XX | [Why representative] |
```

### 6. Send Output

Send via Feishu:
1. Analysis report (text message)
2. 3 representative screenshots (image messages)

## Token Consumption Reference

| Video Length | Keyframes | Estimated Tokens |
|--------------|-----------|------------------|
| 5 seconds | 5-8 | ~8,000-14,000 |
| 15 seconds | 12-16 | ~20,000-28,000 |
| 30 seconds | 20-30 | ~35,000-50,000 |

**Optimization tips:**
- Images account for 95%+ of tokens
- Shorter videos = fewer tokens
- Low-motion videos produce fewer keyframes

## Resources

### scripts/
- `extract_keyframes.sh` - Extract keyframes using ffmpeg I-frame detection

### references/
- `ffmpeg_reference.md` - Advanced ffmpeg commands for video processing
