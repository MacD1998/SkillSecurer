#!/bin/bash
# 虾游 (WanderClaw) — 注册定时探索
# 需要 OpenClaw Gateway 运行中

set -e

TZ="${WANDERCLAW_TZ:-Asia/Shanghai}"
STATE_FILE="$HOME/.openclaw/workspace/wanderclaw/state.json"

echo "🦐 注册虾游定时探索任务（时区: $TZ）..."

# ========== 日常 Cron ==========

openclaw cron add \
  --name "虾游晨间探索" \
  --cron "0 9 * * *" --tz "$TZ" \
  --session isolated \
  --timeout 300 \
  --announce --best-effort-deliver \
  --message "按 wanderclaw/EXPLORER.md 六步流程执行一次深度探索。探索完把明信片完整正文回复出来。如果搜索失败，记录日志并正常退出。" \
  2>/dev/null && echo "  ✓ 晨间探索 09:00" || echo "  ✗ 晨间探索注册失败"

openclaw cron add \
  --name "虾游轻度扫描(午)" \
  --cron "0 12 * * *" --tz "$TZ" \
  --session isolated \
  --model minimax-cn/MiniMax-M2.5 \
  --timeout 300 \
  --announce --best-effort-deliver \
  --message "轻度扫描：检查 wanderclaw/sources.yaml 核心水域有无新内容，发现好的写明信片。如果搜索失败，记录日志并正常退出。把明信片完整正文回复出来。" \
  2>/dev/null && echo "  ✓ 午间扫描 12:00" || echo "  ✗ 午间扫描注册失败"

openclaw cron add \
  --name "虾游午后探索" \
  --cron "0 15 * * *" --tz "$TZ" \
  --session isolated \
  --timeout 300 \
  --announce --best-effort-deliver \
  --message "按 wanderclaw/EXPLORER.md 执行一次深度探索。把明信片完整正文回复出来。如果搜索失败，记录日志并正常退出。" \
  2>/dev/null && echo "  ✓ 午后探索 15:00" || echo "  ✗ 午后探索注册失败"

openclaw cron add \
  --name "虾游轻度扫描(晚)" \
  --cron "0 20 * * *" --tz "$TZ" \
  --session isolated \
  --model minimax-cn/MiniMax-M2.5 \
  --timeout 300 \
  --announce --best-effort-deliver \
  --message "晚间轻度扫描，检查有无值得寄明信片的新发现。如果搜索失败，记录日志并正常退出。把明信片完整正文回复出来。" \
  2>/dev/null && echo "  ✓ 晚间扫描 20:00" || echo "  ✗ 晚间扫描注册失败"

# ========== 深潜模式 Cron（周六 22:00）==========

openclaw cron add \
  --name "虾游深潜模式" \
  --cron "0 22 * * 6" --tz "$TZ" \
  --session isolated \
  --timeout 600 \
  --announce --best-effort-deliver \
  --message "【深潜模式】本次为每周一次的深度探索。规则：\n1. 只搜索深度来源（arXiv、Quanta Magazine、Nautilus、Wait But Why）\n2. 优先搜索长文、论文、深度报告\n3. 明信片字数 450-600 字（比平时更详细）\n4. 评分门槛 ≥ 8 才推送（比平时更严格）\n5. 搜索关键词加 'in-depth OR analysis OR long-read OR review OR survey'\n按 wanderclaw/EXPLORER.md 六步流程执行，但应用以上深潜约束。把明信片完整正文回复出来。" \
  2>/dev/null && echo "  ✓ 深潜模式 周六 22:00" || echo "  ✗ 深潜模式注册失败"

# ========== 周度总结 Cron（周日 10:00）==========

openclaw cron add \
  --name "虾游周度总结" \
  --cron "0 10 * * 0" --tz "$TZ" \
  --session isolated \
  --timeout 300 \
  --announce --best-effort-deliver \
  --message "【周度总结】请执行以下步骤：\n1. 读取 wanderclaw/postcards.json，筛选过去 7 天的明信片\n2. 统计：明信片数量、探索方向分布、平均评分\n3. 读取 wanderclaw/state.json 的 feedback_stats（likes/dislikes）\n4. 生成一份简要周报，包含：\n   - 本周明信片数量和精选（评分最高的 1-2 张）\n   - 热门探索方向 Top 3\n   - 用户反馈统计（👍/👎）\n   - 下周探索建议（基于兴趣图谱变化）\n5. 把周报完整正文回复给用户\n格式轻松，用虾游口吻。" \
  2>/dev/null && echo "  ✓ 周度总结 周日 10:00" || echo "  ✗ 周度总结注册失败"

echo "  ✅ 4 个日常 + 1 深潜 + 1 周度总结 任务已注册"

# ========== Cold Start 三连探索 ==========

PROGRESS=0
if [ -f "$STATE_FILE" ]; then
  PROGRESS=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('cold_start_progress', 0))" 2>/dev/null || echo "0")
fi

if [ "$PROGRESS" -ge 3 ]; then
  echo "  ℹ️  三连探索已完成（progress=$PROGRESS），跳过"
else
  echo ""
  echo "🚀 注册 Cold Start 三连探索..."

  if [ "$PROGRESS" -lt 1 ]; then
    openclaw cron add \
      --name "虾游冷启动-第1次" \
      --at "15s" \
      --delete-after-run \
      --session isolated \
      --timeout 300 \
      --announce --best-effort-deliver \
      --message "【虾游冷启动探索 第1次】读取 wanderclaw/state.json，如果 cold_start_progress >= 1 则回复「已完成」并停止。否则按 EXPLORER.md 执行 1 次探索（核心水域），写 pc-001.md，更新 postcards.json 和 state.json，把明信片完整正文回复出来。如果搜索失败，记录日志并正常退出。" \
      2>/dev/null && echo "  ✓ 冷启动第1次 +15s" || echo "  ✗ 冷启动第1次注册失败"
  fi

  if [ "$PROGRESS" -lt 2 ]; then
    openclaw cron add \
      --name "虾游冷启动-第2次" \
      --at "4m" \
      --delete-after-run \
      --session isolated \
      --timeout 300 \
      --announce --best-effort-deliver \
      --message "【虾游冷启动探索 第2次】读取 wanderclaw/state.json，如果 cold_start_progress >= 2 则回复「已完成」并停止。否则执行 1 次跨领域探索，写 pc-002.md，更新 postcards.json 和 state.json，把完整明信片回复出来。如果搜索失败，记录日志并正常退出。" \
      2>/dev/null && echo "  ✓ 冷启动第2次 +4m" || echo "  ✗ 冷启动第2次注册失败"
  fi

  if [ "$PROGRESS" -lt 3 ]; then
    openclaw cron add \
      --name "虾游冷启动-第3次" \
      --at "8m" \
      --delete-after-run \
      --session isolated \
      --timeout 300 \
      --announce --best-effort-deliver \
      --message "【虾游冷启动探索 第3次-惊喜】读取 wanderclaw/state.json，如果 cold_start_progress >= 3 则回复「已完成」并停止。否则执行 1 次随机惊喜探索，写 pc-003.md，更新 postcards.json 和 state.json，把完整明信片回复出来。如果搜索失败，记录日志并正常退出。" \
      2>/dev/null && echo "  ✓ 冷启动第3次 +8m" || echo "  ✗ 冷启动第3次注册失败"
  fi

  echo "  ✅ 三连探索将在 15秒/4分钟/8分钟后自动触发"
fi

echo ""
echo "查看任务: openclaw cron list"
