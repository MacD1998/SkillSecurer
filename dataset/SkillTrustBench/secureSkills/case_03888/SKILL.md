---
name: cn-weight-tracker
description: |
  中文体重追踪助手。记录每日体重、计算BMI、追踪趋势、设定目标。
  本地存储，无需账号，隐私安全。
  当用户说"体重"、"记录体重"、"今天多重"、"BMI"、"体脂"、"减重"、"目标体重"时触发。
  Keywords: 体重, BMI, 减重, 增重, 目标体重, 体重记录, 健康
metadata: {"openclaw": {"emoji": "⚖️"}}
---

# ⚖️ 体重追踪助手

记录体重，关注健康。

## 核心功能

| 功能 | 说明 |
|------|------|
| 记录体重 | 一句话记录：`记录体重 75.5kg` 或 `今天称了73.9` |
| 查看记录 | 查体重 / 体重记录，显示最近7天趋势图 |
| BMI计算 | `算BMI`（需先设置身高） |
| 趋势分析 | 体重趋势，支持ASCII趋势图 |
| 目标设定 | `目标体重70`，显示距目标差距 |
| 身高设置 | `身高175cm`（一次性设置） |

## 使用方式

```bash
# 设置身高（用于BMI计算，只需一次）
python3 scripts/weight_tracker.py "身高175cm"

# 记录体重
python3 scripts/weight_tracker.py "记录体重 75.5kg"
python3 scripts/weight_tracker.py "今天称了73.9"

# 查看统计和趋势
python3 scripts/weight_tracker.py "查体重"
python3 scripts/weight_tracker.py "体重趋势"

# 计算BMI
python3 scripts/weight_tracker.py "算BMI"

# 设定目标
python3 scripts/weight_tracker.py "目标体重70"
```

## 数据存储

`~/.qclaw/skills/cn-weight-tracker/data/weights.json`

## BMI标准（中国）

| BMI范围 | 分类 |
|---------|------|
| < 18.5 | 偏瘦 |
| 18.5-23.9 | 正常 |
| 24-27.9 | 超重 |
| ≥ 28 | 肥胖 |

## 注意事项

- 支持 kg / 公斤 / 斤 单位
- 趋势图需要至少2条记录才能显示
- 数据完全本地存储，隐私无忧
