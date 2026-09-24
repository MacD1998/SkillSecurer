---
name: knowledge-base
description: >
  Personal knowledge wiki compiler. Ingests raw data (URLs, papers, articles, files),
  compiles into structured .md wiki with concept pages, summaries, and backlinks.
  Auto-maintained by LLM agent, user only reads.
  Activate when: user sends a link/file and says "add to wiki" / "加到知识库",
  asks to query knowledge base, or mentions "knowledge base" / "知识库".
metadata:
  permissions:
    - file:read
    - file:write
  behavior:
    network: none
    telemetry: none
    credentials: none
---

# Knowledge Base

Personal knowledge wiki at `~/.openclaw/workspace/knowledge/`.
Inspired by Karpathy's [LLM Knowledge Bases](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## Directory Structure

```
knowledge/
├── raw/<category>/        # Immutable source documents (LLM reads, never modifies)
├── wiki/
│   ├── index.md           # Content catalog (auto-updated on every ingest)
│   ├── log.md             # Chronological operation log (append-only)
│   ├── concepts/          # Concept pages (PascalCase: Self-Distillation.md)
│   ├── summaries/         # Document summaries (date-slug.md)
│   ├── analyses/          # Query writeback results (date-query-slug.md)
│   └── notes/             # User notes (optional manual)
└── output/                # Generated outputs (slides, charts)
```

Categories: `ai-llm`, `engineering`, `products`, `startups`

## Schema Conventions

### Frontmatter (all wiki pages)

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [[Concept-A]], [[Concept-B]]
sources: N
tags: [tag1, tag2]
status: active        # active | superseded | disputed
---
```

### Naming Rules
- **Concepts**: PascalCase, no spaces → `Self-Distillation.md`, `RAG.md`
- **Summaries**: `YYYY-MM-DD-<slug>.md` → `2026-04-05-gpt5-technical-report.md`
- **Analyses**: `YYYY-MM-DD-query-<slug>.md` → `2026-04-05-query-rag-vs-finetuning.md`
- **Slug**: lowercase, hyphens, max 60 chars, no special chars

### Cross-reference Format
- Wiki-links: `[[ConceptName]]` (Obsidian compatible)
- Source citation: `[[YYYY-MM-DD-summary-slug]]`
- Contradiction mark: `⚠️ [[ConceptName#disputed]]` when new data challenges old claims

### Status Lifecycle
- `active` → current knowledge
- `superseded` → newer source proved this wrong (keep with link to replacement)
- `disputed` → conflicting evidence, needs resolution

## ⚡ Auto-Detect (Smart Ingest)

**核心机制：用户发链接时，自动判断是否应该入库，无需每次手动说"加到知识库"。**

### 判断规则

| 匹配条件 | 示例 |
|----------|------|
| 域名：arxiv.org, paperswithcode.com, huggingface.co/papers | 🟢 论文 |
| 域名：github.com（非用户主页） | 🟢 技术项目 |
| 域名：medium.com, towardsdatascience.com, substack.com | 🟢 技术博客 |
| 域名：openai.com/blog, anthropic.com/news, deepmind.google | 🟢 AI 公司技术文章 |
| 域名：producthunt.com, techcrunch.com（产品/技术类） | 🟢 产品分析 |
| 消息含关键词：论文、paper、技术方案、架构设计 | 🟢 上下文判断 |
| 定时任务产出的重要内容 | 🟢 自动入库 |
| 技术相关但不在以上列表 | 🟡 询问用户 |
| 社交媒体、娱乐、新闻八卦 | 🔴 不入库 |

### 处理方式
- 🟢 静默 ingest → compile → 回复末尾加 `📝 已自动入库到知识库`
- 🟡 正常回答 + 追问"要加到知识库吗？"
- 🔴 只聊天

## Workflow

### Ingest (trigger: auto-detect or user command)

1. Fetch content with `web_fetch` → save to `raw/<category>/YYYY-MM-DD-<slug>.md`
2. Raw file frontmatter: `source`, `category`, `ingested`, `status: raw`
3. **Append to log.md**: `## [YYYY-MM-DD] ingest | <Title> | <category>`

Or run script: `scripts/ingest.sh <url> <category> [slug]`

### Compile (trigger: after ingest) — the core intelligence

1. Read raw document → extract key points
2. Write summary to `wiki/summaries/YYYY-MM-DD-<slug>.md`
3. **Contradiction Detection** (NEW):
   - Read existing concept pages related to this document
   - Compare new claims against existing `status: active` claims
   - If contradiction found:
     - Mark old claim with `⚠️ disputed` and link to new source
     - Update old page `status: superseded` or `status: disputed`
     - Add note to new page explaining the conflict
   - If reinforcement found:
     - Update existing page with new evidence, increment `sources` count
4. Extract concepts → update or create `wiki/concepts/<Concept>.md`
   - If exists: append new info, update `updated:` date, increment `sources`
   - If new: create with definition, key points, related concepts, source links
5. Add `[[backlinks]]` between related concept pages
6. Update raw file status: `status: compiled`
7. Run `scripts/update-index.sh` to refresh index
8. **Append to log.md**: `## [YYYY-MM-DD] compile | <Title> | touched N pages | conflicts: 0/N`

### Query (trigger: user asks about a topic)

1. Search `wiki/concepts/` for related concept pages
2. Search `wiki/summaries/` and `wiki/analyses/` for related content
3. Supplement from `raw/` if needed
4. Answer with source citations
5. **Writeback** (NEW): If the answer is substantial (comparison, synthesis, new insight):
   - Create `wiki/analyses/YYYY-MM-DD-query-<slug>.md`
   - Include the question, answer, key concepts linked
   - Update related concept pages with `[[backlinks]]`
   - Update index.md
   - **Append to log.md**: `## [YYYY-MM-DD] query → analysis | <Question summary>`
6. **Append to log.md**: `## [YYYY-MM-DD] query | <Question summary> | sources: N`

### Lint (trigger: cron weekly or user request)

Run `scripts/lint.sh` for basic checks, then LLM deep-lint:

**Shell checks (scripts/lint.sh):**
- Uncompiled raw docs
- Orphan pages (>30d no inbound links)
- Pages missing frontmatter
- Stats summary

**LLM deep-lint** (agent reads pages and analyzes):

1. **Contradiction scan**: Read pages with same `related` tags, check for conflicting claims
2. **Stale claims**: Find `status: active` pages where newer summaries mention contradictory data
3. **Missing concept pages**: Scan summaries for important terms that have no concept page
4. **Missing cross-references**: Find concept pages that should link but don't
5. **Data gaps**: Suggest new sources to search for based on incomplete coverage
6. **Suggested questions**: Propose new queries worth exploring

Output: structured report with action items. **Append to log.md**: `## [YYYY-MM-DD] lint | issues: N | actions: N`

## Quick Commands

| User says | Action |
|-----------|--------|
| 发链接（命中自动入库规则） | 静默 ingest → compile + 末尾提示 📝 |
| 发链接 + "加到知识库" | ingest → compile（强制） |
| "不要入库" / "就看看" | 只聊天 |
| "查查 X" | query concepts + summaries + analyses |
| "知识库状态" | run lint.sh (basic) |
| "深度检查" | full LLM lint |
| "编译知识库" | batch compile uncompiled raw |

## Templates

### Concept Page

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [[Concept-A]], [[Concept-B]]
sources: N
tags: [category]
status: active
---
# Concept Name

## Definition
One sentence.

## Key Points
- ...

## Contradictions & Updates
<!-- ⚠️ List any conflicting claims here -->
- ⚠️ [[YYYY-MM-DD-summary-slug]] challenges: <brief description>

## Related
- [[Concept-A]]
- [[Concept-B]]

## Sources
- [[YYYY-MM-DD-summary-slug]]
```

### Summary Page

```markdown
---
source: <URL>
category: <category>
concepts: [[Concept-A]], [[Concept-B]]
ingested: YYYY-MM-DD
tags: []
---
# Title

## Core Points
- ...

## Key Data
- ...

## Depth Questions
- ?
```

### Analysis Page (NEW)

```markdown
---
created: YYYY-MM-DD
query: <Original question>
concepts: [[Concept-A]], [[Concept-B]]
sources: N
---
# <Question Summary>

## Answer
...

## Key Insights
- ...

## Follow-up Questions
- ?
```

### Log Entry Format

```markdown
## [YYYY-MM-DD] <action> | <subject> | <metadata>

**Details**: Brief description of what happened.
**Pages touched**: list of modified files
**Conflicts**: 0 or description
```

Prefix convention for grep-ability:
- `## [date] ingest | ...`
- `## [date] compile | ...`
- `## [date] query | ...`
- `## [date] query → analysis | ...`
- `## [date] lint | ...`

## Cron Integration

- **Content auto-ingest**: AI news, papers, X posts with important topics
- **Weekly lint**: Monday 8:00 via `scripts/lint.sh` + LLM deep-lint
- **Health check**: weekly via `scripts/lint.sh`
