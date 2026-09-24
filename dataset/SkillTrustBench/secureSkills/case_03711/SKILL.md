---
name: hotel-recommendation
description: Hotel search and recommendation skill for complex queries based on city, landmark(POI), hotel name, or brand names.
---

Hotel recommendation skill.

## ⚠️ CRITICAL CONSTRAINT - READ FIRST ⚠️

**所有酒店推荐必须且只能来自 hotelSearch 工具的实际返回数据。**

### **绝对禁止的行为:**
- ❌ 假设或虚构酒店信息
- ❌ 基于历史知识推荐酒店
- ❌ 当hotelSearch无数据时创建"可能"的选项
- ❌ 推荐数据源之外的酒店

### **强制要求:**
- ✅ 所有信息必须来自hotelSearch JSON响应
- ✅ 无数据时明确说明"hotelSearch未返回符合要求的酒店"
- ✅ 只显示解析出的实际酒店数据
- ✅ **严格参数设置**: subQuery字段必须填写，不能为空

**违反此约束将被视为严重的技能使用错误。**

## Usage

When user asks about hotels with explicit geographic or hotel entity identifiers:
- city name (市, 城市)
- point of interest (POI, 地标, 景点, 公园)
- hotel name (酒店名, 饭店名)
- brand names (品牌, 连锁酒店)

## Workflow

1. **约束声明**: 首先声明"所有酒店推荐将基于hotelSearch工具的实际查询结果"

2. **Collect Search Parameters**: Extract key parameters from the user's query:
   - `checkInDate`: Check-in date (YYYY-MM-DD), defaults to today + 7 days (T+7)
   - `checkOutDate`: Check-out date (YYYY-MM-DD), defaults to today + 8 days (T+8)
   - `city`: City name, defaults to user's current city
   - `country`: Country name
   - `nearby`: A single POI for proximity search
   - `hotelNames`: List of specific hotel names
   - `brandNames`: List of hotel brand names
   - `subQuery`: **(Required)** Original query segment or user intention

3. **Handle Silent Defaults**: Apply defaults **silently** without asking user:
   - Missing checkInDate → today + 7 days
   - Missing checkOutDate → today + 8 days
   - Missing city → user's current city
   - **Do NOT ask the user for missing information**

4. **Decompose and Structure Queries**:
   - Simple query: "hotels near Disneyland" → single search object
   - Complex query: "hotels near Mong Kok and Yau Ma Tei" → multiple search tasks
   - **Each task needs a separate query object**

5. **Call hotelSearch Tool**:
   - Collect all search query objects into a **List**
   - Serialize the entire list into a single **JSON string**
   - Call `hotelSearch` tool with the JSON string as parameter

6. **Data Validation**:
   - Parse JSON response
   - Use only actual hotel information from the response
   - If hotelSearch returns no data: explicitly state "hotelSearch未返回符合要求的酒店"
   - **Never invent or assume hotels**

7. **Output**: Display results with clear indication "以下是实时查询的实际可用酒店:"

## Search Query Object Parameters (字段说明)

Each object in the list represents a single search task and should contain these fields:

* **subQuery**: **(Required)** The original query segment or user's intention related to this specific hotel search. **This field must always be populated.**
* **checkInDate**: Check-in date, format `YYYY-MM-DD`
* **checkOutDate**: Check-out date, format `YYYY-MM-DD`
* **country**: Country name, e.g., '中国', '日本'
* **city**: City name, e.g., '香港', '东京'
* **nearby**: A single Point of Interest (POI) for proximity search, e.g., '迪士尼乐园', '梅田'
* **hotelNames**: List of specific hotel names for direct search, e.g., `["半岛酒店", "四季酒店"]`
* **brandNames**: List of hotel brand names, e.g., `["万豪", "希尔顿"]`

## Important Notes

* **No Re-prompting**: Do not ask the user for missing information. Always proceed with a search using the collected data and defaults.
* **Language Consistency**: Keep parameter language consistent with user's query.
* **Strict `nearby` Handling**: `nearby` must be a **single POI**. Multiple POIs **must** be decomposed into multiple search query objects.
* **Pure Brand Names**: Extract `brandNames` as pure brand names without any business type or suffix (e.g., '万豪', not '万豪酒店集团').
* **Parallel Execution**: The skill packages all decomposed tasks into a single list. The `hotelSearch` tool handles parallel execution.
* **CRITICAL CONSTRAINT**: All hotel recommendations MUST come directly from the `hotelSearch` tool's actual JSON response. Do NOT create or assume hotels that are not in the response.

## Tools

### hotelSearch

Search for hotels based on complex criteria. This tool is located at `scripts/hotelSearch.js`.

**IMPORTANT**: This tool provides the ONLY source of hotel data. ALL recommendations MUST come directly from this tool's actual JSON response. Do NOT create or assume hotels that are not in the response.

Usage: `node scripts/hotelSearch.js '[{查询对象}]'`

Example:
```bash
node scripts/hotelSearch.js '[{"subQuery":"新加坡鱼尾狮公园附近的酒店","checkInDate":"2026-03-22","checkOutDate":"2026-03-23","city":"新加坡","country":"新加坡","nearby":"鱼尾狮公园"}]'
```

## Examples

### Example 1: Single Hotel Search
**User Query**: "帮我推荐新加坡鱼尾狮公园附近的酒店"
**Generated Query**:
```
node scripts/hotelSearch.js '[{"subQuery":"新加坡鱼尾狮公园附近的酒店","checkInDate":"2026-03-22","checkOutDate":"2026-03-23","city":"新加坡","country":"新加坡","nearby":"鱼尾狮公园"}]'
```

### Example 2: Multi-City Search
**User Query**: "香港迪士尼和上海迪士尼附近的酒店"
**Generated Query**:
```
node scripts/hotelSearch.js '[{"subQuery":"香港迪士尼附近的酒店","city":"香港","country":"中国","nearby":"迪士尼乐园"},{"subQuery":"上海迪士尼附近的酒店","city":"上海","country":"中国","nearby":"迪士尼乐园"}]'
```

### Example 3: Brand Specific Search
**User Query**: "东京的万豪和希尔顿酒店"
**Generated Query**:
```
node scripts/hotelSearch.js '[{"subQuery":"东京的万豪和希尔顿酒店","city":"东京","country":"日本","brandNames":["万豪","希尔顿"]}]'
```

## API Reference

### Endpoint
```
POST https://ibotservice.alipayplus.com/almpapi/v1/message/chat
```

### Authorization
- **token**: `003d2b7d-1ef9-4827-ab9b-cae765689f9d`
- **botId**: `2026030610103389649`
- **bizUserId**: `2107220265020227`
- **serviceType**: `RECALL_hotel`

### Request Format
```json
{
  "token": "003d2b7d-1ef9-4827-ab9b-cae765689f9d",
  "botId": "2026030610103389649",
  "bizUserId": "2107220265020227",
  "chatContent": {
    "contentType": "TEXT",
    "text": "[{\"subQuery\":\"查询描述\",\"checkInDate\":\"YYYY-MM-DD\",\"checkOutDate\":\"YYYY-MM-DD\",\"city\":\"城市名\",\"country\":\"国家名\",\"nearby\":\"地标名称\"}]"
  },
  "botVariables": {
    "userId": "2107220265020227",
    "serviceType": "RECALL_hotel"
  },
  "stream": false
}
```