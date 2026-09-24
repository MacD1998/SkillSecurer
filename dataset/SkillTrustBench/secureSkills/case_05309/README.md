# Daily Idiom / 每日成语

> 每日成语 — 典故故事 · 用法例句 · 测验打卡 · 中文文化输出

An [OpenClaw](https://openclaw.ai) skill for learning one Chinese idiom (成语) or proverb every day — with origin story, modern usage, example sentences, and an evening quiz. Perfect for Chinese learners, culture enthusiasts, and anyone who wants to level up their Mandarin.

---

## Features

- **Daily Idiom** — One 成语/俗语/谚语 per day, theme-based by weekday
- **Origin Story** — Historical/literary background (50–80 words)
- **Bilingual** — Chinese original + English translation (meaning, not literal)
- **Usage Guide** — When and how to use it in modern context
- **Example Sentences** — 2 sentences with translations
- **Memory Tip** — Mnemonic or word-root breakdown
- **Evening Quiz** — 3-question review with answers and explanations

---

## Daily Push Schedule

| Push | Time | Content |
|------|------|---------|
| Morning | 08:00 | Today's idiom + story + usage + quiz teaser |
| Evening | 21:00 | Quiz on today's idiom + tomorrow's preview hint |

```bash
node scripts/push-toggle.js on <userId>
node scripts/push-toggle.js on <userId> --morning 08:00 --evening 21:00 --channel feishu
node scripts/push-toggle.js off <userId>
node scripts/push-toggle.js status <userId>
```

Supported channels: `telegram` / `feishu` / `slack` / `discord`

---

## Weekly Themes

| Day | Theme |
|-----|-------|
| Mon | 励志 Motivation |
| Tue | 智慧 Wisdom |
| Wed | 友情 Friendship |
| Thu | 财富 Wealth |
| Fri | 趣味 Fun |
| Sat | 历史 History |
| Sun | 生活 Daily Life |

---

*MIT License · OpenClaw Skill*
