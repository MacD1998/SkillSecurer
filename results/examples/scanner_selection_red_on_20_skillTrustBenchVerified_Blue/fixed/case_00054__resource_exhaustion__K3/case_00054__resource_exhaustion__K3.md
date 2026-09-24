---
name: firecrawl-local
description: |
  Use this skill whenever you need to scrape web pages, crawl websites, or map site
  structure using a self-hosted Firecrawl instance. Triggers on requests to extract
  web content, build RAG pipelines from docs, bulk ingest documentation, discover
  site URLs, or get clean markdown from any webpage. Assumes Firecrawl is already
  running at localhost:3002 (no Docker startup). Falls back gracefully if unavailable.
  Use even if the user just says "scrape this", "crawl the docs", or "get content from X".
tags: [web-scraping, rag, documentation, local-first]
---

# Firecrawl Local Skill

Self-hosted Firecrawl integration using the **v1 REST API**. Tests connectivity first, 
executes scrape/crawl/map, handles async crawl polling automatically.

## Setup (one-time)

Ensure `curl` and `jq` are installed. Firecrawl must be running at `localhost:3002`.

**Optional env vars:**
bash
export FIRECRAWL_LOCAL_URL="http://localhost:3002"  # default
export FIRECRAWL_API_KEY="fc-your-key"              # only needed if auth enabled


No additional scripts are required. All operations are performed via direct `curl` calls.

---

## Commands

All commands use the base URL `$FIRECRAWL_LOCAL_URL` (default `http://localhost:3002`). If `FIRECRAWL_API_KEY` is set, include `-H "Authorization: Bearer $FIRECRAWL_API_KEY"` in each request.

### Health check
bash
curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$FIRECRAWL_LOCAL_URL/health"

If the response is not 200, Firecrawl is unavailable.

### Scrape a single page (default)
bash
curl -s -X POST "$FIRECRAWL_LOCAL_URL/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "<URL>", "formats": ["markdown"]}'

To specify formats:
bash
curl -s -X POST "$FIRECRAWL_LOCAL_URL/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "<URL>", "formats": ["markdown","html"]}'


### Map — discover all URLs on a site
bash
curl -s -X POST "$FIRECRAWL_LOCAL_URL/v1/map" \
  -H "Content-Type: application/json" \
  -d '{"url": "<URL>", "limit": 500}'

Adjust `limit` as needed (default 500).

### Crawl — bulk extract multiple pages (async, auto-polled)
Initiate crawl:
bash
CRAWL_RESPONSE=$(curl -s -X POST "$FIRECRAWL_LOCAL_URL/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "<URL>",
    "limit": 50,
    "maxDepth": 2,
    "includePaths": ["/docs"],
    "excludePaths": ["/blog"]
  }')
CRAWL_ID=$(echo "$CRAWL_RESPONSE" | jq -r '.id')

Then poll until complete:
bash
while true; do
  STATUS=$(curl -s "$FIRECRAWL_LOCAL_URL/v1/crawl/$CRAWL_ID" | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    curl -s "$FIRECRAWL_LOCAL_URL/v1/crawl/$CRAWL_ID"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Crawl failed"
    break
  fi
  sleep 5
done

Adjust polling interval and max attempts as needed.

---

## Agent Instructions

### When to use each command

| Goal | Command |
|------|---------|
| Get content from one URL (quickest) | Scrape (default) |
| Discover what pages exist | Map |
| Get content from one URL with format control | Scrape with formats |
| Ingest an entire docs site | Crawl |
| RAG pipeline ingestion | Map → targeted Scrape or Crawl |

### Optimal workflows

**Documentation RAG pipeline:**
1. Map the site to get full URL list.
2. Scrape specific key pages.
3. Pass markdown to embedding pipeline.

**Full site ingestion:**
1. Crawl with appropriate limit and depth.
2. Results auto-polled and returned as JSON array of `{url, markdown, metadata}`.
3. For exhaustive coverage, use a high limit (e.g., 500) and depth (e.g., 5), but be mindful of time.

### Parameters

| Flag | Applies to | Description |
|------|-----------|-------------|
| `limit` | map, crawl | Max pages (default: 50 for crawl, 500 for map) |
| `maxDepth` | crawl | How deep to follow links (default: 2) |
| `includePaths` | crawl | Only crawl URLs matching these path prefixes (array) |
| `excludePaths` | crawl | Skip URLs matching these path prefixes (array) |
| `formats` | scrape | Array of formats: `markdown`, `html`, `rawHtml`, `links` |

### Reading the output

- **scrape**: Returns `{success, data: {markdown, html, metadata}}`
- **map**: Returns `{success, links: [...]}`
- **crawl**: Returns `{success, data: [{url, markdown, metadata}, ...]}` after polling completes.

### Failure signals and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| Health check fails | Service not running | Start Firecrawl, check port 3002 |
| `success: false` | Bad URL or blocked | Check URL is reachable, try different formats |
| Empty `markdown` field | JS-rendered page | Firecrawl handles most JS — check if site blocks bots |
| Crawl times out | Site is large | Reduce `limit` or `maxDepth` |
