# Podcast Production Pipeline

An OpenClaw skill that handles the most tedious parts of podcast production -- before the mic turns on and after the recording stops.

## What It Does

Drop in your guest's name, paste a transcript, or describe a solo episode topic. The skill detects what you need and produces ready-to-use content without a lengthy back-and-forth.

It operates in three modes:

**Mode 1: Interview Prep (Pre-Recording)**
Give it a guest name and topic. It returns a guest research brief, a 15-20 question interview set organized by section, and a guest prep email you can send directly.

**Mode 2: Post-Recording (Transcript to Show Notes)**
Paste your raw transcript. It produces structured show notes (400-600 words), three social media posts (teaser, launch, quote), and a YouTube description with placeholder timestamps.

**Mode 3: Solo Episode Planning**
Give it a topic and any key points you want to hit. It returns five title options, a full recording outline, pre-recording show notes, and social posts.

## How to Trigger It

The skill detects mode from context automatically. No need to specify a mode. Examples:

- "I have a guest coming on Thursday -- her name is Sarah Chen, she wrote a book about..."
- "Just finished recording. Here's the transcript: ..."
- "I want to record a solo episode about why most small businesses ignore email lists."

It also responds to casual phrasing: "I need show notes," "Can you prep me for my interview," "I have a guest this week."

## Installation

1. In your OpenClaw workspace, navigate to `.openclaw/workspace/skills/`
2. Create a folder named `podcast-pipeline`
3. Copy `SKILL.md` into that folder
4. Restart OpenClaw or reload skills

## Evals

The `evals/evals.json` file contains three test prompts -- one per mode -- with expected output descriptions. Use these to verify the skill is working correctly after installation.

## Notes

- The skill works best when given a guest name and some context. It will make reasonable assumptions if details are missing and flag them at the end of the output.
- If your OpenClaw instance has web access enabled, Interview Prep mode will search for current information on the guest. If not, it works from what you provide.
- All outputs are clearly labeled and formatted so you can copy each section directly.

## Skill Metadata

| Field | Value |
|---|---|
| Name | podcast-pipeline |
| Version | 1.0.0 |
| Author | Chris (zocase) |
| Compatible with | OpenClaw |
| Category | Content Production |
| Modes | Interview Prep, Post-Recording, Solo Episode |
