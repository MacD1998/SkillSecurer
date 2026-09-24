#!/bin/bash

# 简单测试脚本 - 运行基础查询示例

echo "🏨 Hotel Recommendation Skill 测试脚本"
echo "====================================="
echo ""

# 测试1: 最简单的查询
echo "📋 测试1: 简单城市查询"
echo "查询: [{\"subQuery\":\"东京酒店\"}]"
echo ""
../scripts/searchHotels.sh '[{"subQuery":"东京酒店"}]'

echo ""
echo "====================================="
echo ""

# 测试2: 带城市的查询
echo "📋 测试2: 指定城市查询"
echo "查询: [{\"subQuery\":\"大阪酒店\",\"city\":\"大阪\"}]"
echo ""
../scripts/searchHotels.sh '[{"subQuery":"大阪酒店","city":"大阪"}]'

echo ""
echo "====================================="
echo ""

# 测试3: 验证查询格式
echo "📋 测试3: 验证查询格式"
echo "查询: [{\"subQuery\":\"测试查询\"}]"
echo ""
../scripts/validate_query.sh '[{"subQuery":"测试查询"}]'

echo ""
echo "====================================="
echo "🏁 测试完成"