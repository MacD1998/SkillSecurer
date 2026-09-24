---
name: ChangeBrief
slug: changebrief
version: 1.0.1
description: Change intelligence skill that compares previous and current knowledge snapshots, surfaces what was newly added, which claims changed, what conclusions are now stale, which conflicts need a decision, and which three changes deserve immediate action. Use when the user asks "最近到底变了什么", wants a daily or weekly change brief, or needs an incremental layer on top of a knowledge base instead of another full summary.
metadata:
  clawdbot:
    emoji: "🧾"
    requires:
      bins: []
    os: ["linux", "darwin", "win32"]
---

# ChangeBrief

One-line positioning:
`不是再读一遍所有资料，而是每天 30 秒知道真正变化了什么。`

ChangeBrief is not another knowledge base.

It is the incremental change layer that sits on top of notes, documents, meeting summaries,
research collections, and connector outputs.

Its job is to help the user answer:
- 这周新增了哪些重要信息
- 哪几份文档的说法变了
- 哪些旧结论现在可能失效
- 哪些冲突已经需要拍板
- 哪 3 个变化最值得马上行动

It should feel like a calm change-briefing officer for managers and operators: short, current,
and biased toward decision value rather than recap volume.

## Core Positioning

Default toward these outcomes:
- show only the delta that matters
- separate new information from unchanged background
- detect changed claims rather than repeating the whole source set
- flag stale conclusions and broken assumptions
- surface decision-worthy conflicts
- end with the few changes that deserve action now

Do not drift into:
- a long summary of all inputs
- a passive changelog dump
- a document diff with no judgment
- a knowledge graph that still leaves the user asking what changed

## Relationship To Knowledge Skills

Think of the stack like this:
- Knowledge Connector: bring knowledge in, connect it, and search it
- DecisionDeck: compress knowledge into a decision-ready one-pager
- NextFromKnowledge: turn knowledge into action
- ChangeBrief: tell you what is newly different before you read everything again

Use this boundary:
- if the user needs import, retrieval, or relationship discovery, use Knowledge Connector first
- if the user needs a boss-ready one-page decision brief, use DecisionDeck
- if the user needs the next move, use NextFromKnowledge
- if the user mainly needs to know what changed since last time, use ChangeBrief

## When To Use It

Use this skill when the user says things like:
- `最近到底变了什么`
- `帮我做本周变化简报`
- `这几份文档和上周相比哪里不一样`
- `哪些旧结论已经不成立了`
- `告诉我哪些变化值得我现在处理`
- `不要重读所有资料，只看增量`
- `把前后两版内容压缩成管理者能快速看的变化摘要`

It is especially strong when the user already has:
- last week's and this week's notes
- previous and current docs
- meeting summaries from two periods
- connector outputs from two snapshots
- pasted bullets that represent before and after

## Inputs It Can Work From

Common inputs:
- previous and current snapshots of notes or docs
- weekly reports
- release notes
- roadmap updates
- policy or pricing revisions
- research summaries that changed over time
- meeting notes from two adjacent cycles

For compact heuristics on changed claims, stale conclusions, and priority ranking, read
[references/change-signals.md](references/change-signals.md).

## Core Workflow

1. Compare two snapshots.
   Decide what counts as:
   - newly added
   - unchanged
   - removed
   - same topic but changed claim

2. Rank signal, not volume.
   Prefer changes that affect:
   - risk
   - time line
   - customer impact
   - resource allocation
   - product scope
   - validity of prior conclusions

3. Mark stale conclusions.
   Call out when an older claim, assumption, default, or plan is no longer safe to repeat.

4. Surface decision pressure.
   If the new change implies tradeoffs, blockers, or owner confusion, say that explicitly.

5. End with action priority.
   Compress the whole delta into the three changes that most deserve immediate attention.

## Decision Rules

### Delta Over Recap

Do not spend most of the output describing what stayed the same.
The user is here for change signal, not background retelling.

### Changed Claims Matter More Than Added Sentences

A single changed statement can matter more than ten new bullets.

Prioritize:
- scope reversals
- time line changes
- newly introduced blockers
- numbers that materially changed
- customer or stakeholder demands that move priority

### Stale Conclusions Must Be Named Plainly

Good phrasing:
- `这条旧结论现在不宜继续复述。`
- `之前的判断需要改写，因为底层条件已经变了。`
- `旧版本的说法在新快照里已经不再安全。`

### Conflict Should Trigger A Call, Not A Shrug

When the before and after snapshots now point in different directions, say what needs to be
decided and why it matters now.

### Keep The Brief Manager-Grade

The default output should be fast to scan:
- one-line headline
- important additions
- changed claims
- stale conclusions
- conflicts needing a call
- top 3 action-worthy changes

If the user wants shorter output, compress further. If they want raw structure, return the
underlying change analysis as JSON.
