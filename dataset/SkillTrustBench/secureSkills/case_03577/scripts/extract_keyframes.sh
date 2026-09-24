#!/bin/bash
# extract_keyframes.sh - Extract keyframes from video using I-frame detection
# Usage: bash extract_keyframes.sh <video_path> [output_dir]

set -e

# Parameters
VIDEO_PATH="$1"
OUTPUT_DIR="${2:-$HOME/.openclaw/media/keyframes}"

# Validate input
if [ -z "$VIDEO_PATH" ]; then
    echo "Error: Video path required"
    echo "Usage: bash extract_keyframes.sh <video_path> [output_dir]"
    exit 1
fi

if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: Video file not found: $VIDEO_PATH"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Clear existing keyframes
rm -f "$OUTPUT_DIR"/keyframe_*.jpg 2>/dev/null || true

# Extract keyframes using I-frame detection
echo "Extracting keyframes from: $VIDEO_PATH"
echo "Output directory: $OUTPUT_DIR"

ffmpeg -i "$VIDEO_PATH" \
    -vf "select='eq(pict_type,I)',scale=640:-1" \
    -vsync vfr \
    -q:v 2 \
    "$OUTPUT_DIR/keyframe_%02d.jpg" \
    -y \
    2>&1 | tail -5

# Count extracted frames
FRAME_COUNT=$(ls -1 "$OUTPUT_DIR"/keyframe_*.jpg 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "✅ Extracted $FRAME_COUNT keyframes to: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/keyframe_*.jpg 2>/dev/null | awk '{print $NF, $5}'
