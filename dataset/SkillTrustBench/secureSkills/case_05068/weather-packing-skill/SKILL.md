---
name: ai-weather-packing-skill
description: AI天气打包助手，提供目的地天气预报、智能打包清单生成、穿衣建议、特殊物品提醒、行李重量预估等一站式出行准备服务。Invoke when user wants to check weather, get packing list, or need clothing advice for travel.
version: 1.0.0
metadata: {"openclaw": {"emoji": "🌤️", "category": "travel", "tags": ["天气预报", "打包清单", "穿衣建议", "行李准备", "出行指南"], "requires": {"bins": ["python3"]}, "required": true}}
---
# AI天气打包助手 (ai-weather-packing-skill)

## 技能描述

AI天气打包助手提供目的地天气预报查询、智能打包清单自动生成、穿衣搭配建议、特殊物品提醒、行李重量预估等一站式出行准备服务。让用户不再为"带什么"而烦恼，轻松做好出行准备。

---

⚠️ 【重要约束】
- 天气预报仅供参考，实际以当地为准
- 打包清单需根据旅行天数和季节调整
- 特殊物品提醒需考虑目的地特点
- 行李重量限制需符合航空公司规定

---

## 核心功能

### 1. 天气预报
- 目的地未来7-15天天气预报
- 温度、降水、湿度、风力等信息
- 天气趋势分析
- 穿衣指数建议

### 2. 智能打包清单
- 根据目的地和季节自动生成
- 分类整理（衣物、洗漱、电子、证件等）
- 必备物品和可选物品区分
- 可自定义增减物品

### 3. 穿衣建议
- 根据天气推荐穿搭
- 洋葱式穿衣法建议
- 特殊场合着装提醒
- 颜色搭配建议

### 4. 特殊物品提醒
- 雨伞/雨衣提醒
- 防晒霜/墨镜提醒
- 转换插头提醒
- 药品/急救包提醒
- 根据活动类型特殊装备提醒

### 5. 行李重量预估
- 预估行李总重量
- 分类重量统计
- 航空公司限额对比
- 超重预警

## 触发场景

1. **天气查询**
   - "3月份去云南穿什么？"
   - "东京下周天气怎么样？"
   - "北海道冬天需要带什么？"

2. **打包清单**
   - "帮我列一下去泰国的打包清单"
   - "去日本5天需要带多少衣服？"
   - "海边度假需要带什么？"

3. **穿衣建议**
   - "巴黎4月份穿什么合适？"
   - "去高原地区怎么穿？"
   - "商务出差怎么打包？"

4. **特殊提醒**
   - "去海边需要带防晒霜吗？"
   - "日本需要带转换插头吗？"
   - "高原地区需要准备什么药品？"

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| destination | string | 是 | 目的地城市 |
| travel_dates | string | 是 | 旅行日期范围 |
| duration_days | int | 是 | 旅行天数 |
| travel_style | string | 否 | 旅行风格：leisure/business/adventure/beach |
| gender | string | 否 | 性别：male/female，用于穿衣建议 |
| special_activities | array | 否 | 特殊活动：hiking/diving/skiing等 |

## 输出格式

### 天气打包信息

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "destination": "东京",
    "travel_dates": "2026-04-01 至 2026-04-05",
    "duration_days": 5,
    "weather_forecast": [
      {
        "date": "2026-04-01",
        "weekday": "周三",
        "condition": "多云",
        "temp_high": 18,
        "temp_low": 12,
        "precipitation_chance": 20,
        "humidity": 60,
        "wind_level": "3级",
        "clothing_index": "建议穿薄外套+长袖"
      }
    ],
    "weather_summary": {
      "avg_temp": 15,
      "temp_range": "12-18°C",
      "dominant_condition": "多云",
      "rainy_days": 1,
      "overall_advice": "春季天气，早晚温差大，建议洋葱式穿衣"
    },
    "packing_list": {
      "clothing": [
        {"item": "薄外套", "quantity": 1, "essential": true, "notes": "早晚温差大时使用"},
        {"item": "长袖T恤", "quantity": 3, "essential": true},
        {"item": "长裤", "quantity": 2, "essential": true},
        {"item": "内衣裤", "quantity": 5, "essential": true},
        {"item": "袜子", "quantity": 5, "essential": true},
        {"item": "舒适步行鞋", "quantity": 1, "essential": true}
      ],
      "toiletries": [
        {"item": "洗漱用品", "quantity": 1, "essential": true},
        {"item": "防晒霜", "quantity": 1, "essential": true, "notes": "SPF30+，春季紫外线强"}
      ],
      "electronics": [
        {"item": "手机充电器", "quantity": 1, "essential": true},
        {"item": "转换插头", "quantity": 1, "essential": true, "notes": "日本使用A/B型插头"}
      ],
      "documents": [
        {"item": "护照", "quantity": 1, "essential": true},
        {"item": "签证", "quantity": 1, "essential": true}
      ],
      "medical": [
        {"item": "常用药品", "quantity": 1, "essential": false, "notes": "肠胃药、感冒药、创可贴"}
      ],
      "other": [
        {"item": "雨伞", "quantity": 1, "essential": true, "notes": "春季多雨，建议携带"}
      ]
    },
    "special_reminders": [
      "日本春季花粉较多，过敏体质建议带口罩",
      "东京地铁内空调较冷，建议带薄外套",
      "日本100V电压，需带转换插头"
    ],
    "luggage_estimate": {
      "total_weight_kg": 8.5,
      "clothing_weight": 3.0,
      "toiletries_weight": 1.5,
      "electronics_weight": 2.0,
      "other_weight": 2.0,
      "carry_on_limit": 10,
      "status": "符合手提行李限额"
    }
  }
}
```

## 展示格式示例

```
🌤️ 东京5日游天气与打包指南

═══════════════════════════════════════

📅 旅行时间：2026年4月1日 - 4月5日（5天）

═══════════════════════════════════════

🌡️ 天气预报
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 整体概况
   平均气温：15°C（12-18°C）
   主要天气：多云为主
   降雨天数：1天
   💡 建议：春季天气，早晚温差大，建议洋葱式穿衣

📅 每日详情

4月1日（周三）  多云  12-18°C
   💧 降水概率：20%  💨 风力：3级
   👔 穿衣建议：薄外套+长袖

4月2日（周四）  晴  13-19°C
   💧 降水概率：10%  💨 风力：2级
   👔 穿衣建议：长袖+薄外套（备用）

4月3日（周五）  小雨  11-16°C
   💧 降水概率：80%  💨 风力：4级
   👔 穿衣建议：防水外套+长袖，带雨伞

4月4日（周六）  多云  12-17°C
   💧 降水概率：30%  💨 风力：3级
   👔 穿衣建议：薄外套+长袖

4月5日（周日）  晴  14-20°C
   💧 降水概率：10%  💨 风力：2级
   👔 穿衣建议：长袖+薄外套（备用）

═══════════════════════════════════════

🧳 智能打包清单
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👕 衣物类（预估重量：3.0kg）
   ✅ 薄外套 × 1（早晚温差大时使用）
   ✅ 长袖T恤 × 3
   ✅ 长裤 × 2
   ✅ 内衣裤 × 5
   ✅ 袜子 × 5
   ✅ 舒适步行鞋 × 1
   ⭕ 睡衣 × 1（可选）

🧴 洗漱用品（预估重量：1.5kg）
   ✅ 牙刷、牙膏
   ✅ 洗发水、沐浴露（小瓶装）
   ✅ 洗面奶、护肤品
   ✅ 防晒霜 SPF30+（春季紫外线强）
   ✅ 剃须刀/化妆品

📱 电子设备（预估重量：2.0kg）
   ✅ 手机+充电器
   ✅ 充电宝
   ✅ 转换插头（日本A/B型）
   ✅ 相机（可选）

📋 证件资料（预估重量：0.5kg）
   ✅ 护照+签证
   ✅ 机票预订单
   ✅ 酒店预订单
   ✅ 身份证（备用）
   ✅ 银行卡+现金

💊 药品急救（预估重量：0.5kg）
   ⭕ 肠胃药（可选）
   ⭕ 感冒药（可选）
   ⭕ 创可贴（可选）
   ⭕ 个人常用药

🎒 其他物品（预估重量：1.0kg）
   ✅ 雨伞（春季多雨，建议携带）
   ✅ 水杯
   ✅ 纸巾、湿巾
   ✅ 购物袋（备用）

═══════════════════════════════════════

💡 特别提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌸 季节提醒
   • 日本春季花粉较多，过敏体质建议带口罩
   • 樱花季人多，建议提前预约景点

🚇 当地提醒
   • 东京地铁内空调较冷，建议带薄外套
   • 日本100V电压，需带A/B型转换插头
   • 垃圾分类严格，随身携带垃圾袋

☔ 天气提醒
   • 4月3日有雨，记得带伞
   • 春季早晚温差大，注意增减衣物

═══════════════════════════════════════

⚖️ 行李重量预估
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 总重量：8.5kg

分类统计：
   衣物类：     3.0kg
   洗漱用品：   1.5kg
   电子设备：   2.0kg
   证件资料：   0.5kg
   药品急救：   0.5kg
   其他物品：   1.0kg

✅ 状态：符合手提行李限额（10kg）

═══════════════════════════════════════

💡 回复"增减物品"自定义打包清单
💡 回复"行李建议"获取行李箱推荐
```

## API接口列表

| 接口名称 | 功能 | 参数 |
|:---|:---|:---|
| get_weather_forecast | 获取天气预报 | destination, travel_dates |
| generate_packing_list | 生成打包清单 | destination, duration_days, travel_style |
| get_clothing_advice | 获取穿衣建议 | destination, weather, gender |
| get_special_reminders | 获取特殊提醒 | destination, activities |
| estimate_luggage_weight | 预估行李重量 | packing_list |
| check_luggage_limit | 检查行李限额 | weight, airline |

## 数据来源

- 天气预报：OpenWeatherMap、和风天气
- 穿衣建议：基于温度范围和活动类型的算法
- 特殊提醒：目的地特征数据库

## 扩展功能

- **拍照识物**：拍照识别物品自动加入清单
- **共享清单**：多人旅行共享打包清单
- **购买链接**：清单物品一键购买
- **行李追踪**：智能行李箱追踪
