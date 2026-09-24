# FFmpeg Reference for Video Analysis

## Basic Video Information

```bash
# Get video metadata
ffmpeg -i video.mp4 2>&1 | grep -E "(Duration|Video|Audio)"

# Get detailed stream info
ffprobe -v quiet -print_format json -show_streams video.mp4
```

## Frame Extraction Methods

### 1. Keyframe (I-frame) Extraction - Recommended
Extracts only keyframes (I-frames), which represent scene changes:
```bash
ffmpeg -i video.mp4 -vf "select='eq(pict_type,I)',scale=640:-1" -vsync vfr -q:v 2 frame_%02d.jpg
```

### 2. Uniform Sampling
Extract frames at fixed intervals (e.g., every 1 second):
```bash
ffmpeg -i video.mp4 -vf "fps=1,scale=640:-1" -q:v 2 frame_%02d.jpg
```

### 3. Scene Change Detection
Extract frames when scene changes significantly:
```bash
ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',scale=640:-1" -vsync vfr -q:v 2 frame_%02d.jpg
```

### 4. Specific Time Points
Extract frames at specific timestamps:
```bash
# At 5 seconds
ffmpeg -ss 00:00:05 -i video.mp4 -frames:v 1 -q:v 2 frame.jpg

# Multiple timestamps
for t in 5 10 15; do
    ffmpeg -ss 00:00:$t -i video.mp4 -frames:v 1 -q:v 2 frame_${t}s.jpg
done
```

## Video Processing

### Resize Video
```bash
# Scale to 640px width, maintain aspect ratio
ffmpeg -i video.mp4 -vf "scale=640:-1" output.mp4

# Scale to specific resolution
ffmpeg -i video.mp4 -vf "scale=1280:720" output.mp4
```

### Trim Video
```bash
# Extract segment from 10s to 20s
ffmpeg -ss 00:00:10 -to 00:00:20 -i video.mp4 -c copy output.mp4
```

### Extract Audio
```bash
# Extract audio as MP3
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3
```

## Quality Settings

### JPEG Quality
- `-q:v 2` - High quality (recommended for analysis)
- `-q:v 5` - Medium quality
- `-q:v 10` - Lower quality (smaller files)

### Image Size
- `scale=640:-1` - 640px width, auto height
- `scale=320:-1` - 320px width (lower tokens)
- `scale=1280:-1` - 1280px width (higher detail)

## Performance Tips

1. **Use I-frame extraction** for token efficiency
2. **Scale images to 640px** for balanced quality/tokens
3. **Use `-q:v 2`** for good quality without huge files
4. **Clear output directory** before extraction to avoid confusion

## Common Video Formats

| Format | Extension | Codec |
|--------|-----------|-------|
| MP4 | .mp4 | h264, h265 |
| MOV | .mov | h264, ProRes |
| AVI | .avi | Various |
| WebM | .webm | VP8, VP9 |
| MKV | .mkv | Various |

## Troubleshooting

### No frames extracted
- Video may have few keyframes - try uniform sampling
- Check video codec: `ffprobe -v error -select_streams v:0 -show_entries stream=codec_name video.mp4`

### Poor image quality
- Lower `-q:v` value (2 is best, 31 is worst)

### Too many frames
- Increase scene threshold: `select='gt(scene,0.5)'`
- Use uniform sampling with lower fps: `fps=1/2` (every 2 seconds)
