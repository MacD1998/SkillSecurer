#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
STORE="$ROOT/.cognitive-training"
TODAY="$(date +%Y-%m-%d)"
MONTH="$(date +%Y-%m)"

mkdir -p "$STORE/inbox" "$STORE/daily" "$STORE/dreams" "$STORE/archive"

create_if_missing() {
  local path="$1"
  local content="$2"
  if [ ! -f "$path" ]; then
    printf "%s\n" "$content" > "$path"
  fi
}

create_if_missing "$STORE/README.md" "# Cognitive Training Store

This directory stores agent learning, recall cards, concept links, mistakes, and daily strategy.
Do not store secrets, tokens, private keys, raw environment dumps, or sensitive personal data."

create_if_missing "$STORE/principles.md" "# Principles

Durable rules promoted from repeated successful recall or user-confirmed importance.
"

create_if_missing "$STORE/strategy.md" "# Strategy

## Strategy $TODAY
- Focus:
- Why it matters:
- Practice:
- Prevention rule:
- Next evidence to seek:
"

create_if_missing "$STORE/schedule.md" "# Dream Schedule

Status: manual
Time: not-set
Timezone: local
Scope: project
Last configured: $TODAY

Prompt:
Run cognitive-self-training dream review. Read today's cognitive training files, use tian-dao style deduction, write the dream review, create due recall cards, update graph links, and propose tomorrow's strategy. Do not store secrets or raw private transcripts.
"

create_if_missing "$STORE/cards.md" "# Cards

Spaced-repetition cards. Review entries with Due <= today.
"

create_if_missing "$STORE/graph.md" "# Concept Graph

Track causal links, analogies, applications, and counterexamples.
"

create_if_missing "$STORE/mistakes.md" "# Mistakes

Recurring mistakes, root causes, and prevention rules.
"

create_if_missing "$STORE/inbox/$TODAY.md" "# Inbox $TODAY

Raw captures for today's learning.
"

create_if_missing "$STORE/daily/$TODAY.md" "# Daily Cognitive Review $TODAY

## Learned Today

## Recall Results

## Connections

## Mistakes Or Gaps

## Tomorrow Strategy

## Promotions
"

create_if_missing "$STORE/dreams/$TODAY.md" "# Dream Review $TODAY

## Inputs

## Replay

## Compressed Fragments

## Tian-Dao Deduction

## Academic Rigor Pass

## Recombination

## Hypotheses To Test

## Updates Proposed
"

create_if_missing "$STORE/archive/$MONTH.md" "# Archive $MONTH

Retired, stale, or low-value training entries.
"

echo "Initialized cognitive training store at $STORE"
