#!/bin/bash
# 虾游 (WanderClaw) — 首次安装初始化
# 在 OpenClaw workspace 目录下运行

set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WC_DIR="wanderclaw"

echo "🦐 虾游初始化..."

# 检查依赖工具
echo "检查依赖..."
for tool in web_search web_fetch; do
  echo "  ✓ $tool (OpenClaw 内置工具，运行时检查)"
done

# 创建目录结构
echo "创建数据目录..."
mkdir -p "$WC_DIR/postcards"
mkdir -p "$WC_DIR/exploration-log"
mkdir -p "$WC_DIR/knowledge-base"

# 初始化数据文件（不覆盖已有数据）
if [ ! -f "$WC_DIR/state.json" ]; then
  cp "$SKILL_DIR/assets/state.json" "$WC_DIR/state.json"
  echo "  ✓ state.json 已创建"
else
  echo "  ○ state.json 已存在，跳过"
fi

if [ ! -f "$WC_DIR/interest-graph.json" ]; then
  cp "$SKILL_DIR/assets/interest-graph.json" "$WC_DIR/interest-graph.json"
  echo "  ✓ interest-graph.json 已创建"
else
  echo "  ○ interest-graph.json 已存在，跳过"
fi

if [ ! -f "$WC_DIR/postcards.json" ]; then
  echo "[]" > "$WC_DIR/postcards.json"
  echo "  ✓ postcards.json 已创建"
else
  echo "  ○ postcards.json 已存在，跳过"
fi

if [ ! -f "$WC_DIR/postcard-index.json" ]; then
  echo "{}" > "$WC_DIR/postcard-index.json"
  echo "  ✓ postcard-index.json 已创建"
else
  echo "  ○ postcard-index.json 已存在，跳过"
fi

# 复制信息源配置（不覆盖用户自定义）
if [ ! -f "$WC_DIR/sources.yaml" ]; then
  cp "$SKILL_DIR/references/sources.yaml" "$WC_DIR/sources.yaml"
  echo "  ✓ sources.yaml 已创建"
else
  echo "  ○ sources.yaml 已存在（用户自定义），跳过"
fi

# 复制核心引擎文件到 workspace（cron isolated session 需要直接访问）
cp "$SKILL_DIR/references/EXPLORER.md" "$WC_DIR/EXPLORER.md"
echo "  ✓ EXPLORER.md 已复制"
cp "$SKILL_DIR/references/SOUL.md" "$WC_DIR/SOUL.md"
echo "  ✓ SOUL.md 已复制"
cp "$SKILL_DIR/references/postcard-format.md" "$WC_DIR/postcard-format.md"
echo "  ✓ postcard-format.md 已复制"

echo ""
echo "✅ 虾游初始化完成！"
echo ""
echo "下一步："
echo "  1. 运行 bash scripts/schedule-cron.sh 注册定时探索"
echo "  2. 和虾游聊天，告诉它你的兴趣方向"
echo "  3. 或者直接说「探索一下」立刻出发"
