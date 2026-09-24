---
name: ai-travel-skill-package
description: AI智能旅行助手套装，包含行程规划、目的地指南、预算管理、签证办理、天气打包等一站式旅行服务。Invoke when user needs comprehensive travel planning, itinerary creation, destination information, budget calculation, visa guidance, or travel preparation assistance.
version: 1.0.0
metadata: {"openclaw": {"emoji": "✈️", "category": "travel", "tags": ["AI旅行", "智能行程", "旅行规划", "目的地指南", "旅行预算", "签证办理", "天气打包"], "requires": {"bins": ["python3"]}, "required": true}}
---
# AI智能旅行助手套装 (ai-travel-skill-package)

## 技能包描述

AI智能旅行助手套装是一套完整的旅行规划与辅助工具，利用人工智能技术为用户提供从行程规划到出行准备的全流程服务。包含5个核心子技能，覆盖旅行前、中、后的各种需求。

---

⚠️ 【重要约束】
- 所有推荐必须基于真实数据和算法计算
- 禁止编造景点信息、价格或签证政策
- 行程规划需考虑实际交通时间和开放时间
- 预算计算应包含税费和隐性消费
- 签证信息需标注更新日期和政策来源

---

## 技能包架构

```
ai-travel-skill-package/
├── SKILL.md                          # 技能包主文档
├── itinerary-skill/                  # 行程规划技能
│   ├── SKILL.md
│   └── scripts/
│       ├── itinerary_api.py
│       └── openai_adapter.py
├── destination-guide-skill/          # 目的地指南技能
│   ├── SKILL.md
│   └── scripts/
│       ├── destination_api.py
│       └── openai_adapter.py
├── travel-budget-skill/              # 旅行预算技能
│   ├── SKILL.md
│   └── scripts/
│       ├── budget_api.py
│       └── openai_adapter.py
├── visa-documents-skill/             # 签证证件技能
│   ├── SKILL.md
│   └── scripts/
│       ├── visa_api.py
│       └── openai_adapter.py
├── weather-packing-skill/            # 天气打包技能
│   ├── SKILL.md
│   └── scripts/
│       ├── weather_api.py
│       └── openai_adapter.py
└── shared/                           # 共享组件
    ├── travel_models.py
    ├── utils.py
    └── constants.py
```

## 子技能列表

### 1. 行程规划技能 (itinerary-skill)

**核心功能**：
- 智能行程生成（基于天数、兴趣、预算）
- 路线优化（最短路径、最少换乘）
- 景点推荐与排序
- 餐厅推荐
- 实时调整与备选方案

**触发场景**：
- "帮我规划一个5天4晚的东京行程"
- "我想去云南玩一周，有什么推荐路线？"
- "带老人和孩子的三亚亲子游怎么安排？"

### 2. 目的地指南技能 (destination-guide-skill)

**核心功能**：
- 目的地概览（文化、历史、气候）
- 必去景点介绍
- 当地美食推荐
- 交通指南
- 实用信息（时差、电压、货币）
- 安全提示

**触发场景**：
- "巴黎有什么好玩的？"
- "第一次去泰国需要注意什么？"
- "京都的最佳旅游季节是什么时候？"

### 3. 旅行预算技能 (travel-budget-skill)

**核心功能**：
- 费用预估（机票、酒店、餐饮、交通、门票）
- 预算分配建议
- 省钱攻略
- 实时价格监控
- 多人分摊计算

**触发场景**：
- "去日本玩7天大概要花多少钱？"
- "帮我算一下三亚5日游的预算"
- "欧洲15天游，人均2万够吗？"

### 4. 签证证件技能 (visa-documents-skill)

**核心功能**：
- 签证政策查询
- 材料清单生成
- 办理流程指导
- 办理时间预估
- 免签/落地签信息
- 护照/证件提醒

**触发场景**：
- "去日本需要办签证吗？"
- "申根签证需要什么材料？"
- "我的护照快过期了，还能出国吗？"

### 5. 天气打包技能 (weather-packing-skill)

**核心功能**：
- 目的地天气预报
- 智能打包清单
- 穿衣建议
- 特殊物品提醒（雨伞、防晒霜等）
- 行李重量预估

**触发场景**：
- "3月份去云南穿什么？"
- "帮我列一下去泰国的打包清单"
- "北海道冬天需要带什么？"

## 数据共享机制

### 共享数据模型

```python
# shared/travel_models.py

@dataclass
class TravelPlan:
    """旅行计划"""
    destination: str
    start_date: str
    end_date: str
    duration_days: int
    travelers: int
    budget_range: str
    interests: List[str]
    itinerary: List[DayPlan]

@dataclass
class DayPlan:
    """每日行程"""
    day_number: int
    date: str
    morning: List[Activity]
    afternoon: List[Activity]
    evening: List[Activity]
    accommodation: str
    meals: List[str]

@dataclass
class Destination:
    """目的地信息"""
    name: str
    country: str
    description: str
    best_season: str
    avg_temperature: Dict
    currency: str
    language: str
    timezone: str
    voltage: str
    top_attractions: List[str]
```

### 技能间协作

```
用户: "帮我规划一个去日本的7天行程，预算1.5万"

itinerary-skill ──► 生成基础行程框架
       │
       ▼
destination-guide-skill ──► 补充景点详情、美食推荐
       │
       ▼
travel-budget-skill ──► 计算费用、优化预算分配
       │
       ▼
visa-documents-skill ──► 检查签证要求、提醒证件
       │
       ▼
weather-packing-skill ──► 根据日期提供天气和打包建议
```

## 统一响应格式

### 成功响应

```json
{
  "code": 0,
  "msg": "success",
  "skill": "itinerary-skill",
  "data": {
    // 技能特定的数据
  },
  "meta": {
    "request_id": "req_123456",
    "timestamp": "2026-03-30T10:00:00Z",
    "related_skills": ["destination-guide-skill", "travel-budget-skill"]
  }
}
```

### 失败响应

```json
{
  "code": 500,
  "msg": "Destination not supported",
  "skill": "itinerary-skill",
  "data": null,
  "meta": {
    "request_id": "req_123456",
    "timestamp": "2026-03-30T10:00:00Z"
  }
}
```

## 使用示例

### 完整旅行规划流程

```
用户: 我想去日本关西玩5天，预算1万左右，有什么建议？

AI: 好的！我来为您规划关西5日游。首先让我了解一下目的地信息和预算情况。

[调用 destination-guide-skill] 获取关西地区概览
[调用 travel-budget-skill] 计算5天预算分配

AI: 根据您的预算和需求，我建议以下行程：

📍 关西5日经典游
💰 预估费用：¥9,800/人

Day 1: 大阪
- 上午：抵达关西机场 → 酒店入住
- 下午：道顿堀、心斋桥购物
- 晚上：道顿堀美食街

Day 2: 京都
...

[调用 visa-documents-skill] 检查签证要求
[调用 weather-packing-skill] 提供打包建议

AI: 
📋 签证提醒：日本单次旅游签证需提前15天办理
🌤️ 天气建议：3月关西平均气温10-18°C，建议带薄外套
🧳 打包清单：已为您生成，请查看...
```

## 扩展计划

未来可添加的子技能：
- **机票比价技能** - 多平台机票价格对比
- **酒店推荐技能** - 基于偏好的智能酒店推荐
- **当地体验技能** - 特色活动、一日游预订
- **紧急救援技能** - 海外紧急联系方式、保险理赔
- **翻译助手技能** - 实时翻译、常用语手册
