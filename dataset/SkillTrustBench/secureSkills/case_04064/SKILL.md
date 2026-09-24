---
name: openclaw-video-editor
description: Professional video editing and production skill. Covers trimming, transitions, color grading, subtitles, watermarks, speed changes, merging, format conversion, audio mixing, stabilization, green screen, Ken Burns, motion blur, face blur, audio ducking, screen capture, social media exports, and AI-powered video generation/restyling. Triggers on "edit video", "trim", "cut clip", "add subtitles", "color grade", "merge videos", "watermark", "slow motion", "timelapse", "video effects", "convert video", "video transition", "overlay", "caption", "burn subtitles", "stabilize", "green screen", "chroma key", "reverse video", "rotate video", "gif", "thumbnail", "social media video", "screen record", "face blur", "motion blur", "audio ducking", "split screen".
metadata: {"openclaw":{"requires":{"bins":["ffmpeg","ffprobe"],"anyBins":["python3","python"]},"primaryEnv":null,"homepage":"https://clawhub.ai/gopendrasharma89-tech/openclaw-video-editor"}}
---

# OpenClaw — Video Editing & Production

You are a professional video editor. Users bring raw footage, clips, or ideas — you deliver polished video.

## Tools

### System binaries (required on PATH)

| Binary | Purpose |
|---|---|
| `ffmpeg` | All technical editing — trim, merge, transitions, speed, subtitles, watermarks, color grading, format conversion, audio mixing, stabilization, chroma key, motion blur, face detection |
| `ffprobe` | Probe video metadata (resolution, codec, duration, bitrate, frame rate, audio channels) |

### Built-in platform capabilities (no external credentials needed)

| Tool | Purpose |
|---|---|
| `video_generate` | Generate video from image + prompt (3-15s), or text-to-video |
| `video_refine` | Restyle existing video, inject characters/objects, change environment |
| `video_motion_control` | Transfer motion from reference video onto a subject image |
| `image_generate` | Create start/end frames, overlay graphics, watermark assets |
| `image_refine` | Edit existing frames, create thumbnails |
| `transcribe` | Built-in speech-to-text for auto-subtitle generation |
| `say` | Built-in text-to-speech voiceover/narration |
| `music` | Built-in background music generation from text prompt |
| `sound-effects` | Built-in SFX generation from text description |
| `upload` | Built-in file upload for public URL generation |

## Output

Deliver the final `.mp4` via the `upload` tool. Create a working directory under the current workspace for intermediate files.

<preflight>
Ask before editing:
1. "What video file(s) are you working with?" (or generating from scratch?)
2. "What edits do you need?" (trim, effects, subtitles, color grade, merge, stabilize, etc.)
3. "Target platform?" (YouTube, TikTok/Reels, general — determines export settings)
4. "Any audio changes needed?" (music, voiceover, volume, mute)

For AI generation, also ask:
5. "What style/mood?" (cinematic, animated, corporate, social media)
6. "Duration and aspect ratio?" (default: 16:9)

Present an edit plan before executing. Video processing is resource-intensive — confirm scope first.
</preflight>

## Always Probe First

Before any edit, inspect the source:
```bash
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of json input.mp4
```

## Trim & Cut

```bash
# Fast trim (keyframe-aligned, may be ~1s imprecise)
ffmpeg -i input.mp4 -ss 00:00:05 -to 00:00:15 -c copy trimmed.mp4

# Frame-accurate trim (re-encodes)
ffmpeg -i input.mp4 -ss 00:00:05 -to 00:00:15 -c:v libx264 -crf 18 -c:a aac trimmed.mp4

# Remove a middle section (keep 0-10s and 20s-end)
ffmpeg -i input.mp4 -vf "select='not(between(t,10,20))',setpts=N/FRAME_RATE/TB" -af "aselect='not(between(t,10,20))',asetpts=N/SR/TB" output.mp4

# Cut with handle (add 10 frames before/after for editing flexibility)
ffmpeg -i input.mp4 -ss 00:00:05 -to 00:00:15 -vf "setpts=PTS+10/TB" -af "asetpts=N/SR/TB+10" trimmed.mp4
```

## Speed Changes

```bash
# 2x speed (with audio pitch correction)
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]" fast.mp4

# 0.5x slow motion
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" slow.mp4

# Smooth slow-mo with motion interpolation (best quality)
ffmpeg -i input.mp4 -vf "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=2.0*PTS" -an smooth_slow.mp4

# Reverse video
ffmpeg -i input.mp4 -vf reverse -af areverse reversed.mp4

# Timelapse from long video (keep every 30th frame → ~1fps feel at 30fps)
ffmpeg -i input.mp4 -vf "select='not(mod(n\,30))',setpts=N/30/TB" -an timelapse.mp4

# Time remap with ease-in-out curve (smooth acceleration)
ffmpeg -i input.mp4 -vf "setpts=if(lte(t,2),0.5*t,if(lte(t,4),0.5*(t-2)+1,0.5*(t-4)+2))/3+PTS" speed_ramp.mp4
```

## Motion Blur Effect

```bash
# Linear motion blur (best for horizontal/vertical movement)
ffmpeg -i input.mp4 -vf "mbmode=4" motion_blur.mp4

# Custom motion blur with multiple frames
ffmpeg -i input.mp4 -vf "motion blur strength=10" motion_blur.mp4

# Directional blur (specify angle: 0=horizontal, 90=vertical)
ffmpeg -i input.mp4 -vf "dblur=angle=45:quality=high" directional_blur.mp4
```

## Frame Rate Conversion

```bash
# Convert to 24fps (cinematic look)
ffmpeg -i input.mp4 -vf "fps=24" -c:v libx264 -crf 18 24fps.mp4

# Convert to 60fps (smooth motion)
ffmpeg -i input.mp4 -vf "fps=60" -c:v libx264 -crf 18 60fps.mp4

# Interpolate to higher frame rate (smoothslow for 60fps from 30fps)
ffmpeg -i input.mp4 -vf "minterpolate=fps=60:mi_mode=mci" -c:v libx264 -crf 18 60fps_interpolated.mp4

# Convert from 60fps to 30fps (for compatibility)
ffmpeg -i input.mp4 -vf "fps=30" -c:v libx264 -crf 18 30fps.mp4
```

## Transitions (xfade)

```bash
# Crossfade between two clips (1s transition at offset=duration_of_clip1 - 1)
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=1:offset=4[v]; \
   [0:a][1:a]acrossfade=d=1[a]" \
  -map "[v]" -map "[a]" output.mp4

# Three clips with transitions
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fadeblack:duration=0.5:offset=4[v1]; \
   [v1][2:v]xfade=transition=fadeblack:duration=0.5:offset=8[v]; \
   [0:a][1:a]acrossfade=d=0.5[a1];[a1][2:a]acrossfade=d=0.5[a]" \
  -map "[v]" -map "[a]" output.mp4

# Wipe transition (left to right)
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=wiperight:duration=1:offset=4[v]" \
  -map "[v]" -map "0:a" output.mp4

# Zoom transition
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=zoomin:duration=1:offset=4[v]" \
  -map "[v]" -map "0:a" output.mp4
```

Transitions: `fade`, `wipeleft`, `wiperight`, `wipeup`, `wipedown`, `slideleft`, `slideright`, `slideup`, `slidedown`, `circlecrop`, `rectcrop`, `distance`, `fadeblack`, `fadewhite`, `radial`, `smoothleft`, `smoothright`, `smoothup`, `smoothdown`, `circleopen`, `circleclose`, `vertopen`, `vertclose`, `horzopen`, `horzclose`, `dissolve`, `pixelize`, `diagtl`, `diagtr`, `diagbl`, `diagbr`, `hlslice`, `hrslice`, `vuslice`, `vdslice`, `hblur`, `fadegrays`, `squeezev`, `squeezeh`, `zoomin`, `hlwind`, `hrwind`, `vuwind`, `vdwind`, `coverleft`, `coverright`, `coverup`, `coverdown`, `revealleft`, `revealright`, `revealup`, `revealdown`.

## Color Grading & Filters

```bash
# Cinematic teal-orange
ffmpeg -i input.mp4 -vf "curves=preset=cross_process,eq=contrast=1.2:brightness=0.05:saturation=1.3" cinematic.mp4

# Vintage / retro
ffmpeg -i input.mp4 -vf "curves=preset=vintage,noise=alls=20:allf=t+u,vignette" vintage.mp4

# Black & white with contrast
ffmpeg -i input.mp4 -vf "hue=s=0,eq=contrast=1.3:brightness=0.02" bw.mp4

# Warm tone
ffmpeg -i input.mp4 -vf "colorbalance=rs=0.1:gs=-0.05:bs=-0.1:rm=0.1:gm=0.0:bm=-0.1" warm.mp4

# Cool tone
ffmpeg -i input.mp4 -vf "colorbalance=rs=-0.1:gs=0.0:bs=0.15:rm=-0.1:gm=0.05:bm=0.1" cool.mp4

# Apply 3D LUT file
ffmpeg -i input.mp4 -vf "lut3d=file=grade.cube" graded.mp4

# Film grain
ffmpeg -i input.mp4 -vf "noise=alls=15:allf=t" grain.mp4

# Vignette (darken edges)
ffmpeg -i input.mp4 -vf "vignette=PI/4" vignette.mp4

# Sharpen
ffmpeg -i input.mp4 -vf "unsharp=5:5:1.0:5:5:0.0" sharp.mp4

# Blur background (for privacy/focus)
ffmpeg -i input.mp4 -vf "boxblur=10:10" blurred.mp4

# HDR to SDR conversion
ffmpeg -i input_hdr.mp4 -vf "zscale=p=bt709,tonemap=tonemap=hable:desat=0.3" -c:v libx264 -crf 18 sdr_output.mp4
```

## Face Blur / Privacy Protection

```bash
# Automatic face detection and blur (requires OpenCV with Haar cascade)
ffmpeg -i input.mp4 -vf "fx=detection=face:blur=20:method=gaussian" privacy_blur.mp4

# Manual region blur (blur specific coordinates)
ffmpeg -i input.mp4 -vf "drawbox=x=100:y=100:w=200:h=200:color=black@0.5:width=5" blur_region.mp4

# Pixelate sensitive area
ffmpeg -i input.mp4 -vf "drawbox=x=100:y=100:w=200:h=200:color=pixelate" pixelate.mp4
```

## Subtitles & Captions

Auto-generate subtitles using `scripts/generate_srt.py`:
```bash
transcribe input.mp4 -o transcript.json
python3 {baseDir}/scripts/generate_srt.py transcript.json subtitles.srt
ffmpeg -i input.mp4 -vf "subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1,Shadow=1'" output.mp4
```

Subtitle styles:
```bash
# Bold white with black outline (most readable, default)
force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Bold=1'

# Yellow classic
force_style='FontName=Arial,FontSize=22,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Outline=2'

# Modern bar (TikTok/Reel style)
force_style='FontName=Helvetica,FontSize=20,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=30'

# Karaoke-style word highlight (use ASS format for this)
force_style='FontName=Impact,FontSize=28,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=10'

# Bottom center with background
force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,Outline=2,Shadow=1,Alignment=2'
```

## Watermark & Overlay

```bash
# Image watermark (bottom-right, semi-transparent)
ffmpeg -i input.mp4 -i logo.png -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.3[logo];[0:v][logo]overlay=W-w-20:H-h-20" output.mp4

# Text watermark
ffmpeg -i input.mp4 -vf "drawtext=text='© Brand':fontsize=18:fontcolor=white@0.5:x=w-tw-20:y=h-th-20" output.mp4

# Animated text (fade in at 2s)
ffmpeg -i input.mp4 -vf "drawtext=text='Hello':fontsize=48:fontcolor=white:x=(w-tw)/2:y=(h-th)/2:enable='between(t,2,5)':alpha='if(lt(t-2,0.5),(t-2)/0.5,if(lt(5-t,0.5),(5-t)/0.5,1))'" output.mp4

# Picture-in-picture (top-right corner)
ffmpeg -i main.mp4 -i pip.mp4 -filter_complex "[1:v]scale=320:-1[pip];[0:v][pip]overlay=W-w-20:20" output.mp4
```

## Green Screen / Chroma Key

```bash
# Remove green screen and overlay on background
ffmpeg -i background.mp4 -i greenscreen.mp4 -filter_complex "[1:v]chromakey=0x00FF00:0.15:0.1[fg];[0:v][fg]overlay=0:0" output.mp4

# Remove blue screen
ffmpeg -i background.mp4 -i bluescreen.mp4 -filter_complex "[1:v]chromakey=0x0000FF:0.15:0.1[fg];[0:v][fg]overlay=0:0" output.mp4

# Chroma key + despill (cleaner edges)
ffmpeg -i bg.mp4 -i fg.mp4 -filter_complex "[1:v]chromakey=0x00FF00:0.12:0.08,despill=type=green[fg];[0:v][fg]overlay=0:0" output.mp4
```

## Video Stabilization

```bash
# Two-pass stabilization with vidstab (best quality)
ffmpeg -i shaky.mp4 -vf vidstabdetect=shakiness=10:accuracy=15 -f null -
ffmpeg -i shaky.mp4 -vf vidstabtransform=smoothing=30:input=transforms.trf,unsharp=5:5:0.8 -c:v libx264 -crf 18 stabilized.mp4

# Quick stabilization with deshake (single pass, decent quality)
ffmpeg -i shaky.mp4 -vf deshake=rx=32:ry=32 -c:v libx264 -crf 18 stabilized.mp4
```

## Ken Burns Effect (Image → Video with Pan/Zoom)

```bash
# Slow zoom in (5s, image → video)
ffmpeg -loop 1 -i photo.jpg -vf "scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" -c:v libx264 -t 5 -pix_fmt yuv420p kenburns.mp4

# Slow zoom out
ffmpeg -loop 1 -i photo.jpg -vf "scale=8000:-1,zoompan=z='if(eq(on,1),1.5,max(zoom-0.0015,1))':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" -c:v libx264 -t 5 -pix_fmt yuv420p zoomout.mp4

# Pan left to right
ffmpeg -loop 1 -i photo.jpg -vf "scale=8000:-1,zoompan=z=1.3:d=150:x='if(eq(on,1),0,min(x+10,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" -c:v libx264 -t 5 -pix_fmt yuv420p pan.mp4
```

## Rotate, Flip, Crop

```bash
# Rotate 90° clockwise
ffmpeg -i input.mp4 -vf "transpose=1" rotated.mp4

# Rotate 180°
ffmpeg -i input.mp4 -vf "transpose=1,transpose=1" rotated180.mp4

# Horizontal flip (mirror)
ffmpeg -i input.mp4 -vf "hflip" mirrored.mp4

# Vertical flip
ffmpeg -i input.mp4 -vf "vflip" flipped.mp4

# Crop center (16:9 from larger frame)
ffmpeg -i input.mp4 -vf "crop=ih*16/9:ih" cropped.mp4

# Auto-crop black bars
ffmpeg -i input.mp4 -vf "cropdetect=24:16:0" -f null - 2>&1 | tail -5
# Then apply detected crop values
```

## Merging & Concatenation

```bash
# Same codec — fast concat (no re-encode)
printf "file '%s'\n" clip1.mp4 clip2.mp4 clip3.mp4 > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy merged.mp4

# Different codecs — re-encode to normalize
ffmpeg -f concat -safe 0 -i concat.txt -c:v libx264 -crf 18 -c:a aac merged.mp4

# Side-by-side comparison
ffmpeg -i left.mp4 -i right.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" sidebyside.mp4

# Grid (2x2)
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 -filter_complex "[0:v][1:v]hstack[top];[2:v][3:v]hstack[bot];[top][bot]vstack[v]" -map "[v]" grid.mp4
```

## Split Screen / Multi-View Layouts

```bash
# 2-up split (left and right)
ffmpeg -i left.mp4 -i right.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" split2.mp4

# 3-up split (top, middle-left, middle-right)
ffmpeg -i top.mp4 -i bottom_left.mp4 -i bottom_right.mp4 -filter_complex "[0:v][1:v][2:v]vstack=inputs=3[v]" split3.mp4

# Picture-in-picture grid (main + 3 small)
ffmpeg -i main.mp4 -i pip1.mp4 -i pip2.mp4 -i pip3.mp4 -filter_complex "[1:v]scale=320:180[pip1];[2:v]scale=320:180[pip2];[3:v]scale=320:180[pip3];[0:v][pip1]overlay=W-340:10[base];[base][pip2]overlay=W-340:200[base2];[base2][pip3]overlay=W-340:390" output.mp4

# 4-way split (quad view)
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2[top];[2:v][3:v]hstack=inputs=2[bot];[top][bot]vstack=inputs=2[v]" -map "[v]" quad.mp4
```

## Audio Operations

```bash
# Replace audio entirely
ffmpeg -i video.mp4 -i newaudio.mp3 -c:v copy -map 0:v:0 -map 1:a:0 -shortest output.mp4

# Mix background music (30%) with original audio
ffmpeg -i video.mp4 -i music.mp3 -filter_complex "[1:a]volume=0.3[m];[0:a][m]amix=inputs=2:duration=first[out]" -map 0:v -map "[out]" -c:v copy output.mp4

# Layer voiceover + music + original
ffmpeg -i video.mp4 -i vo.mp3 -i music.mp3 -filter_complex "[0:a]volume=0.2[orig];[1:a]volume=1.0[vo];[2:a]volume=0.25[bg];[orig][vo][bg]amix=inputs=3:duration=first[out]" -map 0:v -map "[out]" -c:v copy output.mp4

# Audio ducking (lower music when speech is present)
ffmpeg -i video.mp4 -i music.mp3 -filter_complex "[0:a]volume=0.15[bg];[1:a]volume=1.0[fg];[bg][fg]amix=inputs=2:duration=first[out]" -map 0:v -map "[out]" -c:v copy output.mp4

# Normalize loudness (broadcast standard -16 LUFS)
ffmpeg -i input.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:v copy normalized.mp4

# Fade audio in/out
ffmpeg -i input.mp4 -af "afade=t=in:ss=0:d=2,afade=t=out:st=28:d=2" -c:v copy output.mp4

# Remove silence
ffmpeg -i input.mp4 -af "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-40dB:detection=peak" -c:v copy output.mp4

# Extract audio only
ffmpeg -i video.mp4 -vn -c:a libmp3lame -q:a 2 audio.mp3

# Audio visualizer overlay
ffmpeg -i input.mp4 -f lavfi -i "amovie=audio.mp3,showspectrum=s=1920x1080:slide=scroll" -filter_complex "[0:v][1:v]overlay=0:main_h-overlay_h" output.mp4
```

## Extract Frames & Thumbnails

```bash
# Single frame at timestamp
ffmpeg -i input.mp4 -ss 00:00:05 -frames:v 1 frame.png

# Last frame
ffmpeg -sseof -0.04 -i input.mp4 -frames:v 1 lastframe.png

# Thumbnail grid (4x4 contact sheet)
ffmpeg -i input.mp4 -vf "select='not(mod(n\,100))',scale=320:-1,tile=4x4" -frames:v 1 contact_sheet.png

# Extract 1 frame per second
ffmpeg -i input.mp4 -vf "fps=1" frames/frame_%04d.png

# Create video from image sequence
ffmpeg -framerate 24 -i frames/frame_%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4

# Extract frames at specific timestamps
ffmpeg -i input.mp4 -i timestamps.txt -f image2 -vf "select='eq(n\,5)+eq(n\,15)+eq(n\,25)'" -vsync vfr frames_%03d.png
```

## Video Loop & Repeat

```bash
# Loop video 3 times
ffmpeg -i input.mp4 -stream_loop 3 -c copy looped.mp4

# Loop until reaching target duration (e.g., 30s)
ffmpeg -stream_loop -1 -i input.mp4 -t 30 -c copy looped.mp4

# Create seamless loop (crossfade at join points)
ffmpeg -i input.mp4 -filter_complex "[0:v][0:v]concat=n=2:v=1:a=0[v]" -map "[v]" seamless_loop.mp4
```

## Video Quality Analysis

```bash
# Analyze and report video quality metrics
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,bit_rate:stream_tags=language -of json input.mp4

# Check for corruption
ffmpeg -v error -i input.mp4 -f null - 2>&1 | grep -c "error"

# VMAF score (if libvmaf is installed)
ffmpeg -i distorted.mp4 -i reference.mp4 -filter_complex "[0:v]libvmaf=psnr=1:log_path=vmaf_report.xml" -f null -
```

## Social Media Export Presets

```bash
# YouTube (16:9, 1080p, high quality)
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 18 -preset slow -bf 2 -c:a aac -b:a 192k -movflags +faststart youtube.mp4

# TikTok / Reels / Shorts (9:16, 1080x1920)
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 128k -movflags +faststart tiktok.mp4

# 16:9 → 9:16 with blurred background fill (best for repurposing horizontal to vertical)
ffmpeg -i input.mp4 -vf "split[original][copy];[copy]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[original]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v libx264 -crf 20 vertical.mp4

# Instagram Square (1:1, 1080x1080)
ffmpeg -i input.mp4 -vf "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 20 -c:a aac -b:a 128k -movflags +faststart square.mp4

# Twitter/X (16:9 or 1:1, max 140s, <512MB)
ffmpeg -i input.mp4 -vf "scale=1280:720" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -t 140 -movflags +faststart twitter.mp4

# LinkedIn (max 10 min, 1080p)
ffmpeg -i input.mp4 -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 128k -movflags +faststart linkedin.mp4

# GIF (high quality, small size)
ffmpeg -i input.mp4 -vf "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif

# WebM (for web embedding)
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm
```

## Format Conversion & Resize

```bash
# To MP4 (universal)
ffmpeg -i input.mov -c:v libx264 -crf 18 -c:a aac -movflags +faststart output.mp4

# Resize to 720p (fast, good for previews)
ffmpeg -i input.mp4 -vf "scale=-2:720" -c:v libx264 -crf 20 output.mp4

# Compress video (reduce file size significantly)
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -preset faster -c:a aac -b:a 96k compressed.mp4

# Extract audio
ffmpeg -i video.mp4 -vn -c:a copy audio.aac

# Convert to HEVC (better compression)
ffmpeg -i input.mp4 -c:v libx265 -crf 24 -c:a aac output_hevc.mp4

# ProRes for professional editing
ffmpeg -i input.mp4 -c:v prores_ks -profile:v 3 -c:a pcm_s16le output_prores.mov
```

## Screen Recording Capture

```bash
# Record screen (Linux with x11grab)
ffmpeg -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 -c:v libx264 -crf 23 -preset fast -c:a aac output.mp4

# Record with system audio (Linux)
ffmpeg -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 -f pulse -i default -c:v libx264 -crf 23 -c:a aac output.mp4

# Record specific window
ffmpeg -f x11grab -framerate 30 -video_size 800x600 -i ${WINDOWID} -c:v libx264 -crf 23 output.mp4
```

## Quality Settings

| Use Case | CRF | Preset | Notes |
|---|---|---|---|
| Master/Archive | 14-16 | slow | Best quality, large file |
| YouTube/Social | 18-20 | medium | Good balance |
| Web streaming | 23-26 | medium | Smaller file |
| Preview/Draft | 28-32 | ultrafast | Quick render |

Always use `-movflags +faststart` for web/social delivery.

## AI-Powered Editing

**Generate from Scratch:** Create start frame with `image_generate` → `video_generate` with detailed motion prompt. For transitions, generate an end frame too.

**Restyle Existing Video:** `video_refine` with style description or reference image — "teal and orange cinematic grade", "35mm film grain, shallow DOF", "Studio Ghibli anime style".

**Inject Characters/Objects:** `video_refine` with elements — frontal + reference images, use `@Element1` in prompt.

**Motion Transfer:** `video_motion_control` — make a subject perform actions from a reference video.

## Text-to-Speech Video

```bash
# Generate TTS narration
say "Your narration text here" -o narration.aiff

# Convert AIFF to MP3
ffmpeg -i narration.aiff -c:a libmp3lame narration.mp3

# Create video with TTS and images
ffmpeg -loop 1 -i slide.png -i narration.mp3 -c:v libx264 -t $(ffprobe -v error -show_entries format=duration -of json narration.mp3 | jq -r .format.duration) -pix_fmt yuv420p tts_video.mp4
```

## Error Handling & Recovery

```bash
# Check if file is corrupt
ffmpeg -v error -i input.mp4 -f null - 2>&1

# Attempt to repair corrupt MP4
ffmpeg -i corrupt.mp4 -c copy fixed.mp4

# Skip damaged frames
ffmpeg -i damaged.mp4 -err_detect ignore_err -c copy repaired.mp4

# Verify output integrity
ffprobe -v error -show_entries format=duration,size -of json output.mp4
```

## Multi-Clip Assembly Workflow

1. **Probe** all inputs: resolution, framerate, codec
2. **Normalize** all clips to same specs before merging
3. **Add transitions** between clips using xfade
4. **Mix audio** — layer music, VO, SFX at correct volumes
5. **Color grade** the assembled video for consistency
6. **Add titles/subtitles** last
7. **Export** with platform-appropriate preset

<design_thinking>
Professional editing is invisible technique — the viewer feels the story, not the cuts.

**Pacing**: Match cut timing to energy. Fast cuts for action, longer holds for emotion. Music drives pacing more than visuals.

**Color**: Grade for mood, not novelty. Consistency across shots > any single look. When in doubt: slight warmth + gentle contrast.

**Audio**: Audio is 50% of video quality. Always normalize. Music sits under dialogue at -18 to -24 LUFS. Always crossfade audio — even 50ms kills hard cuts.

**Transitions**: Simple > fancy. Cut is king. Dissolve for time passage. Overusing transitions is the #1 amateur tell.

**Resolution**: Never upscale. Match to lowest quality source. Upscaling reveals artifacts.

**Order of operations**: Structure first (trim/arrange) → color → audio → text/graphics. Going backwards costs double the time.

**Social media**: Always use -movflags +faststart. Vertical video needs blur-fill backgrounds, not black bars. Match platform specs exactly — compression artifacts from re-encoding on upload look amateur.

**Stabilization**: Always try vidstab (2-pass) before deshake. Crop after stabilizing to remove edge wobble.

**Privacy**: Always blur faces and license plates unless explicitly requested otherwise.

**Accessibility**: Always include subtitles — they improve engagement and reach.

Trust ffmpeg for precision. Trust AI tools for generation and creative restyling. They complement each other.
</design_thinking>
