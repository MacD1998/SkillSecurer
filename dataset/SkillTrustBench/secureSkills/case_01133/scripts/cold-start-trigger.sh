#!/bin/bash
# cold-start-trigger.sh — 注册 3 个一次性 cron 完成三连探索
# 由 agent 在 onboarding Step 5 调用
# 每个 cron 间隔 2 分钟，独立 session，各做 1 次探索

set -e

echo "🦐 注册三连探索 cron..."

# 第 1 次：立刻触发（+10s 缓冲）
openclaw cron add \
  --name "虾游冷启动-第1次" \
  --at "+10s" \
  --delete-after-run \
  --session isolated \
  --timeout-seconds 120 \
  --message "读取 wanderclaw/state.json 的 cold_start_progress。如果 >= 3 则回复「三连探索已完成」。如果 < 3，执行 1 次探索：
1. 读 wanderclaw/interest-graph.json，选权重最高的兴趣方向
2. web_search 搜 2-3 组关键词
3. web_fetch 最佳 2 个 URL
4. 用虾游口吻写明信片，保存到 wanderclaw/postcards/ 目录
5. 更新 wanderclaw/postcards.json（读取→追加→写回）
6. 更新 wanderclaw/state.json：cold_start_progress +1，postcard_count +1
7. 把明信片完整正文回复给用户
只做 1 次，做完停止。" \
  2>&1

# 第 2 次：+3分钟
openclaw cron add \
  --name "虾游冷启动-第2次" \
  --at "+3m" \
  --delete-after-run \
  --session isolated \
  --timeout-seconds 120 \
  --message "读取 wanderclaw/state.json 的 cold_start_progress。如果 >= 3 则回复「三连探索已完成」。如果 < 3，执行 1 次探索：
1. 读 wanderclaw/interest-graph.json，选一个和上次不同的兴趣方向（检查 state.json 的 exploration_history 避免重复）
2. web_search 搜 2-3 组关键词，尝试跨领域交叉
3. web_fetch 最佳 2 个 URL
4. 用虾游口吻写明信片，保存到 wanderclaw/postcards/ 目录
5. 更新 wanderclaw/postcards.json（读取→追加→写回）
6. 更新 wanderclaw/state.json：cold_start_progress +1，postcard_count +1
7. 把明信片完整正文回复给用户
只做 1 次，做完停止。" \
  2>&1

# 第 3 次：+6分钟
openclaw cron add \
  --name "虾游冷启动-第3次" \
  --at "+6m" \
  --delete-after-run \
  --session isolated \
  --timeout-seconds 120 \
  --message "读取 wanderclaw/state.json 的 cold_start_progress。如果 >= 3 则回复「三连探索已完成」。如果 < 3，执行 1 次探索：
1. 这次不按用户兴趣，随机选一个意外方向（科学发现、历史趣闻、前沿技术等）
2. web_search 搜 2-3 组关键词
3. web_fetch 最佳 2 个 URL
4. 用虾游口吻写明信片，保存到 wanderclaw/postcards/ 目录
5. 更新 wanderclaw/postcards.json（读取→追加→写回）
6. 更新 wanderclaw/state.json：cold_start_progress +1，postcard_count +1
7. 把明信片完整正文回复给用户
只做 1 次，做完停止。" \
  2>&1

echo "✅ 三连探索已注册：10秒/3分钟/6分钟后触发"
