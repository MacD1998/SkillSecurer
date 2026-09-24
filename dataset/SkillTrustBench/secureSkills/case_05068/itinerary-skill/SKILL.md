---
name: ai-itinerary-skill
description: AI智能行程规划助手，根据目的地、天数、预算、兴趣自动生成最优旅行路线，支持景点推荐、餐厅推荐、路线优化。Invoke when user wants to create a travel itinerary, plan daily activities, or get route recommendations.
version: 1.0.0
metadata: {"openclaw": {"emoji": "🗺️", "category": "travel", "tags": ["行程规划", "路线优化", "景点推荐", "旅行路线"], "requires": {"bins": ["python3"]}, "required": true}}
---
# AI智能行程规划助手 (ai-itinerary-skill)

## 技能描述

AI智能行程规划助手利用人工智能算法，根据用户的目的地、旅行天数、预算范围、兴趣爱好等条件，自动生成最优化的旅行路线。支持景点智能排序、餐厅推荐、交通路线优化，让旅行规划变得轻松高效。

---

⚠️ 【重要约束】
- 景点开放时间、交通时间必须基于真实数据
- 每日行程安排需考虑实际可行性（不过度紧凑）
- 餐厅推荐需考虑地理位置和用餐时间
- 预算估算需包含门票、交通、餐饮等所有费用

---

## 核心功能

### 1. 智能行程生成
- 基于目的地和天数自动生成完整行程
- 考虑景点地理位置进行智能排序
- 根据用户兴趣偏好定制内容
- 支持多种旅行风格（休闲/紧凑/亲子/美食等）

### 2. 路线优化
- 最短路径算法优化景点顺序
- 减少往返和无效交通时间
- 考虑景点开放时间合理安排
- 预留充足的用餐和休息时间

### 3. 景点推荐
- 必去景点智能推荐
- 小众景点挖掘
- 根据季节推荐最佳景点
- 景点评分和游客评价参考

### 4. 餐厅推荐
- 当地特色美食推荐
- 根据行程位置推荐就近餐厅
- 考虑用餐时间和预算
- 支持 dietary restrictions

## 触发场景

1. **完整行程规划**
   - "帮我规划一个5天4晚的东京行程"
   - "我想去云南玩一周，有什么推荐路线？"
   - "带老人和孩子的三亚亲子游怎么安排？"

2. **单日行程优化**
   - "我在大阪只有一天时间，怎么安排最高效？"
   - "京都一日游，求推荐路线"

3. **特定主题行程**
   - "东京美食之旅，求推荐"
   - "关西古建筑文化游"

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| destination | string | 是 | 目的地城市或地区 |
| start_date | string | 否 | 开始日期 yyyy-MM-dd |
| end_date | string | 否 | 结束日期 yyyy-MM-dd |
| duration_days | int | 是 | 旅行天数 |
| travelers | int | 否 | 旅行人数，默认1 |
| budget_level | string | 否 | 预算等级：ECONOMY/STANDARD/COMFORT/LUXURY |
| travel_style | array | 否 | 旅行风格：RELAXED/ADVENTURE/CULTURE/FOODIE/SHOPPING/FAMILY |
| interests | array | 否 | 兴趣标签 |
| must_visit | array | 否 | 必去景点列表 |
| avoid | array | 否 | 不想去的景点 |

## 输出格式

### 行程规划结果

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "plan_id": "plan_123456",
    "destination": "东京",
    "duration_days": 5,
    "travel_style": ["CULTURE", "FOODIE"],
    "total_estimated_cost": 8500,
    "currency": "CNY",
    "itinerary": [
      {
        "day_number": 1,
        "date": "2026-04-01",
        "weekday": "Wednesday",
        "theme": "抵达与初探",
        "morning": [
          {
            "name": "抵达成田机场",
            "type": "transport",
            "start_time": "09:00",
            "end_time": "11:00"
          },
          {
            "name": "酒店入住",
            "type": "accommodation",
            "start_time": "12:00",
            "end_time": "13:00"
          }
        ],
        "afternoon": [
          {
            "name": "浅草寺",
            "type": "attraction",
            "start_time": "14:00",
            "end_time": "16:00",
            "price": 0
          }
        ],
        "evening": [
          {
            "name": "晴空塔夜景",
            "type": "attraction",
            "start_time": "18:00",
            "end_time": "20:00",
            "price": 2100
          }
        ],
        "meals": {
          "lunch": "浅草天妇罗",
          "dinner": "晴空塔附近餐厅"
        },
        "accommodation": "浅草地区酒店",
        "daily_cost": 1200
      }
    ],
    "recommendations": [
      "建议购买东京地铁3日券",
      "浅草寺早晨人少，可考虑调整至次日早上"
    ]
  }
}
```

## 展示格式示例

```
🗺️ 东京5日深度游行程规划

📅 旅行时间：2026年4月1日 - 4月5日（5天4晚）
👥 旅行人数：2人
💰 预估费用：¥8,500/人
🎯 旅行风格：文化探索 + 美食之旅

═══════════════════════════════════════

📍 Day 1 | 4月1日（周三）| 主题：抵达与初探

🌅 上午
  09:00 - 11:00  抵达成田机场，入境手续
  11:00 - 12:00  乘坐Skyliner前往市区
  12:00 - 13:00  酒店入住（浅草地区）

🌞 下午
  14:00 - 16:00  🏯 浅草寺（雷门、仲见世通）
                  💴 门票：免费
                  💡 建议游览2小时，可体验人力车

🌙 晚上
  18:00 - 20:00  🗼 晴空塔夜景
                  💴 门票：¥2,100
                  💡 提前购票可节省排队时间

🍽️ 今日美食
  午餐：浅草大黑家天妇罗（百年老店）
  晚餐：晴空塔6楼餐厅街

🏨 住宿：浅草地区酒店
💰 今日花费：约¥1,200/人

═══════════════════════════════════════

📍 Day 2 | 4月2日（周四）| 主题：传统文化之旅
...

═══════════════════════════════════════

💡 贴心提示
• 建议购买东京地铁3日券（¥1,500），可无限次乘坐
• 浅草寺早晨人少，若想拍照建议7:00前到达
• 晴空塔傍晚时段人较多，可考虑上午登塔

💡 回复"Day+数字"查看某日详细攻略
💡 回复"优化+建议"调整行程
```

## 路线优化算法

### 核心算法

1. **最近邻算法**
   - 从当前位置出发，选择最近的下一个景点
   - 减少交通时间和成本

2. **时间窗口约束**
   - 考虑景点开放时间
   - 避免闭馆日安排
   - 预留用餐和休息时间

3. **兴趣匹配度评分**
   ```
   score = w1 * 景点热度 + w2 * 用户兴趣匹配 + w3 * 地理位置便利 + w4 * 性价比
   ```

## API接口列表

| 接口名称 | 功能 | 参数 |
|:---|:---|:---|
| generate_itinerary | 生成完整行程 | destination, duration_days, travel_style, budget_level |
| optimize_route | 优化单日路线 | day_plan, optimization_type |
| get_attraction_recommendations | 获取景点推荐 | destination, interests, count |
| get_restaurant_recommendations | 获取餐厅推荐 | location, cuisine_type, budget |
| adjust_itinerary | 调整行程 | plan_id, adjustments |

## 扩展功能

- **实时调整**：根据天气、交通状况实时调整行程
- **多人协作**：支持多人共同编辑行程
- **一键导出**：导出为PDF/日历/地图导航
- **离线模式**：下载行程后离线查看
