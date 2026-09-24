---
name: bilibili-transcript
version: "2.2.0"
description: "Transcribe Bilibili videos to text with high accuracy using Whisper medium model. Use when the user provides a Bilibili video URL (BVxxxxx) and wants to: (1) Extract the complete audio content as text with high accuracy, (2) Get a detailed summary of the video content, (3) Save the transcript as a formatted TXT file instead of posting long text to Discord. Automatically detects CC subtitles if available, otherwise uses Whisper medium model with GPU acceleration. Output saves to 'Bilibili transcript' folder by default, includes video metadata, summary section, and full transcript in Simplified Chinese."
---

# Bilibili Transcript v2.2

High-accuracy Bilibili video transcription with multi-language AI subtitle support.

## Overview

This skill provides a **complete transcription workflow** for Bilibili videos:

1. **Extract Video Metadata** - Title, author, publish date, duration
2. **Smart Subtitle Detection** - Priority: CC subtitles → AI subtitles (multi-language) → Whisper transcription
3. **Multi-language AI Subtitle Support** - Auto-detects: `ai-zh`, `ai-en`, `ai-ja`, `ai-es`, `ai-ar`, `ai-pt`, `ai-ko`, `ai-de`, `ai-fr`
4. **Browser Cookie Support** - WSL Chromium or Windows Edge for member-only videos
5. **Formatted Output** - Saves as structured TXT file with metadata + summary placeholder + full transcript
6. **Simplified Chinese** - Automatically converts Traditional to Simplified Chinese

## What's New in v2.2

- ✅ **Fixed cookie detection** - Now uses browser config directory instead of SQLite file (avoids encoding errors)
- ✅ **One-stop solution** - CC subtitles → AI subtitles → Whisper transcription, all in one script
- ✅ **Better WSL support** - Automatically detects WSL Chromium and Windows Edge cookies
- ✅ **Smart fallback** - Seamlessly switches between subtitle sources without user intervention

## What's New in v2.1

- ✅ **Improved cookie handling** - Fixed UTF-8 encoding issues with snap Chromium
- ✅ **Three-tier fallback** - CC subtitles → AI subtitles → Whisper transcription
- ✅ **Better error handling** - Gracefully degrades when cookie sources fail

## What's New in v2.0

- ✅ **Multi-language AI subtitles** - Supports 9 languages: Chinese, English, Japanese, Spanish, Arabic, Portuguese, Korean, German, French
- ✅ **WSL Chromium support** - Better cookie extraction than Windows Edge
- ✅ **Correct subtitle download** - Uses `--write-subs --write-auto-subs` combo
- ✅ **Language auto-detection** - Automatically finds available AI subtitle language

## AI Subtitle Language Codes

Bilibili uses `ai-` prefix for AI-generated subtitles:

| Code | Language | 语言 |
|------|----------|------|
| `ai-zh` | Chinese | 中文 |
| `ai-en` | English | 英文 |
| `ai-ja` | Japanese | 日文 |
| `ai-es` | Spanish | 西班牙文 |
| `ai-ar` | Arabic | 阿拉伯文 |
| `ai-pt` | Portuguese | 葡萄牙文 |
| `ai-ko` | Korean | 韩文 |
| `ai-de` | German | 德文 |
| `ai-fr` | French | 法文 |

## Requirements

### Hardware (Your Setup)
- **GPU**: NVIDIA RTX 4070 Super (12GB VRAM) - ✅ Perfect for medium model
- **WSL Memory**: 16GB (configured)
- **WSL CPU**: 6 cores (configured)

### Software
- `yt-dlp` - Video/audio download
- `ffmpeg` - Audio processing
- `whisper` - Speech-to-text (local, no API key)
- `opencc` - Traditional to Simplified Chinese conversion (optional)

### Browser (for AI subtitles)
- **WSL Chromium** (recommended) - Log in to Bilibili in WSL
- **Windows Edge** - Alternative option

## Workflow

### Step 1: Run Transcription Script

```bash
./scripts/bilibili_transcript.sh "https://www.bilibili.com/video/BVxxxxx"
```

**Priority order:**
1. **CC Subtitles** (manual) - Fastest, highest accuracy
2. **AI Subtitles** (auto-generated) - Fast, good accuracy, multi-language
3. **Whisper Transcription** - Slowest, ~95% accuracy, works for all videos

### Step 2: Generate Detailed Summary

After the script completes, read the generated TXT file and:
1. Read the full transcript (第二部分)
2. Generate a comprehensive summary (第一部分)
3. Save the updated file

### Step 3: Present to User

In Discord, post:
- **Brief summary** in message
- **Attach the TXT file** for full content

## Setup WSL Chromium Login

For best results with AI subtitles:

1. Start WSL Chromium:
   ```bash
   chromium-browser &
   ```

2. Navigate to bilibili.com

3. Log in with your Bilibili account

4. Run the transcription script

The script will automatically use Chromium's cookies to access member-only AI subtitles.

## Usage Examples

### Example 1: Basic Transcription (Default Output)
```bash
./scripts/bilibili_transcript.sh "https://www.bilibili.com/video/BV1Z1wJzgEAj/"
# Output: workspace/Bilibili transcript/[VideoTitle]_BVxxxxx_transcript.txt
```

### Example 2: Custom Output Directory
```bash
./scripts/bilibili_transcript.sh "https://www.bilibili.com/video/BV1Z1wJzgEAj/" ~/Documents
```

## Notes

### Model Selection
- **Your config**: RTX 4070 Super 12GB + 16GB RAM + 6 cores
- **Default**: `medium` model (~95% accuracy, balanced speed) ✅
- **Fallback**: If GPU unavailable, automatically uses CPU (slower)

### Accuracy Comparison
| Source | Accuracy | Speed | Best For |
|--------|----------|-------|----------|
| CC Subtitles | 100% | ⚡ Instant | All videos with manual subtitles |
| AI Subtitles (ai-zh) | ~90% | ⚡ Instant | Chinese videos |
| AI Subtitles (ai-en) | ~85% | ⚡ Instant | English videos |
| Whisper medium | ~95% | 🐢 Slow | No subtitle videos |

### Default Output Directory
- **Location**: `workspace/Bilibili transcript/`
- **Created automatically** on first run
- All transcript files organized in one place

### File Naming
Output files are named: `[VideoTitle]_[BVID]_transcript.txt`
- Special characters (including Chinese punctuation) are replaced with underscores
- Title truncated to 50 characters
- Example: `股票分红_是从左口袋掏右口袋吗_BV1ddzUYTE27_transcript.txt`

### Subtitle Priority
The script tries subtitles in this order:
1. Manual CC subtitles (zh-CN, zh-TW, en, ja, etc.)
2. AI subtitles (any available language: ai-zh, ai-en, ai-ja, etc.)
3. Whisper voice transcription (fallback)

This ensures fastest processing while maintaining high accuracy.
