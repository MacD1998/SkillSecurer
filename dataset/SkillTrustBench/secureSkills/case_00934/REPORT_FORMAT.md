# AI 日报报告格式

**MANDATORY: Every report MUST contain exactly these 6 sections in order. Do not skip, combine, or omit any section.**

---

## Section A: AI五层蛋糕 (AI Stack)

Categorize articles into the five-layer framework: AI应用 → AI模型 → AI基础设施 → 芯片 → 能源. Each sub-group uses topic summary format.

**Format:**

```
## A. AI五层蛋糕

### AI应用
1. 多模态AI应用加速落地，Copilot等产品持续迭代 #融资
   [2]篇来源：[**AI Weekly**](https://aiweekly.com), [**TechCrunch**](https://techcrunch.com)

### AI模型
1. 多机构发布新模型，LLM竞争进入新阶段
   [2]篇来源：[**Google AI Blog**](https://blog.google/ai), [**OpenAI News**](https://openai.com)

### AI基础设施
1. 新研究挑战传统scaling laws，模型训练方式可能需要重新思考
   [1]篇来源：[**AI Weekly**](https://aiweekly.com)

### 芯片
1. GPU供应持续紧张，定制芯片成为新方向
   [1]篇来源：[**Reuters**](https://reuters.com)

### 能源
1. AI耗电问题引发关注，大厂投资可再生能源
   [1]篇来源：[**TechCrunch**](https://techcrunch.com)
```

**Rules:**
- Classify each article into one of the five layers
- Within each layer, further group semantically similar articles together
- Each sub-group: header with layer name, then numbered topic themes with count + linked sources
- **MANDATORY: Every numbered item MUST have "[n]篇来源" prefix, even when n=1**
- **IMPORTANT: 链接必须使用 article.link（实际文章URL），不是 feed 官网 URL**
- When an article involves funding, acquisitions, or notable trends, append a tag: `#融资` `#并购` `#趋势`
- Order sub-groups by feed weight (评分), highest first

---

## Section B: 精选推荐 (Featured Picks)

Combine top articles with topic clustering: select 5-8 top ranked articles and group semantically similar ones together.

**Format:**

```
## B. 精选推荐

### Topic Name
1. [**Article Title**](https://example.com/article)
   来源: Feed Name | 权重: 0.5 | 阅读量: 1234
   推荐理由: Why this is important

2. [**Article Title**](https://example.com/article)
   来源: Feed Name | 权重: 0.3 | 阅读量: 890
   推荐理由: Why this matters

### Another Topic
1. [**Article Title**](https://example.com/article)
   来源: Feed Name | 权重: 0.4 | 阅读量: 567
   推荐理由: Key insight
```

**Rules:**
- Group semantically similar articles into topic clusters
- Rank within each cluster by feed weight (权重) or 阅读量 (views)
- Order clusters by total weight of articles (highest first)
- Include specific recommendation reason for each article

---

## Section C: 创业信号 (Startup Signals)

**MANDATORY:** 你的唯一目标是从海量资讯中提取”信息差”、”技术红利”和”搞钱路径”。禁止废话，拒绝宏大叙事。

---

### 核心杠杆 (High-Leverage Tools & Models)

**目标读者：** 独立开发者、超级个体

抛弃所有关于”芯片”、”能源”、”大厂财报”的无意义资讯。只保留对独立开发者有直接生产力提升的工具/模型/API。**限制：最多输出 3 个**，按重要度降序排列。

**格式：**
```
### 核心杠杆 (High-Leverage Tools & Models)
1. [工具/项目名称]：一句话说明它解决了什么具体痛点。
   **降维打击点**：为什么它比现有方案好？（节省的时间/金钱成本）。
   来源：[链接]

2. [模型/API 名称]：一句话说明核心更新。
   **实操价值**：普通人/小团队能用它做什么原本做不到的事？
   来源：[链接]

3. [另一个工具]：...
```

---

### 商业逆向工程 (Business Teardown & MVP) — **条件触发**

**触发条件（满足任一即可输出）：**
- 融资金额 > $10M
- 爆款应用（有明确用户增长/营收数据）
- 技术栈可推测的创新产品

**无符合条件时输出：**
```
### 商业逆向工程 (Business Teardown & MVP)
本期无符合条件的逆向工程案例。
```

**格式：**
```
### 商业逆向工程 (Business Teardown & MVP)
1. 🎯 靶向案例：[产品或趋势名称]
   **需求本质**：它切中了什么人性弱点或业务痛点？
   **技术底座推测**：它大概率使用了什么模型/技术栈？（如：前端 Next.js + 后端 Supabase + 核心逻辑 Claude 3.5 Sonnet API）。
   **一人公司复刻路径 (MVP SOP)**：
   1. [第一步：获取什么开源数据/模型]
   2. [第二步：用什么低代码/框架快速搭建界面]
   3. [第三步：如何找到第一批种子用户或进行商业变现]
```

**Key patterns to detect:**
- Funding: “raised”, “Series”, “closed round”, “million”, “> $10M”
- Acquisitions: “acquired”, “acquisition”, “acquire”
- Viral products: “growth”, “revenue”, “users”, “trending”

---

## Section D: 创作点 (Content Angles)

Extract story angles and trending topics for content creation from existing articles.

**Format:**

```
## D. 创作点

### 可写主题
1. 主题：Why X is reshaping Y industry
   [2]篇来源：[**Article1**](https://example.com/1), [**Article2**](https://example.com/2)

### 热门角度
1. 角度：How to build in X space (step-by-step)
   [1]篇来源：[**Article3**](https://example.com/3)

### 争议性话题
1. 话题：X的局限性 — 争议焦点
   [2]篇来源：[**Article4**](https://example.com/4), [**Article5**](https://example.com/5)
```

**Key patterns to detect:**
- Story angles: "why X matters", "the future of", "how to"
- Trending: "viral", "trending", "breaking"
- Controversial: "debate", "critics say", "controversial"
- Actionable: "X steps to", "lessons from"

---

## Section E: 政策解读 (Policy & Regulation)

Track AI regulations, government policies, and regulatory developments globally.

**Format:**

```
## E. 政策解读

### 全球监管
1. 监管动向描述
   [1]篇来源：[**Source**](https://example.com)

### 法规动态
1. 具体法规或立法进展描述
   [1]篇来源：[**Source**](https://example.com)

### 合规提示
1. 对从业者的合规建议
   [1]篇来源：[**Source**](https://example.com)
```

**Key patterns to detect:**
- Regulation: "regulation", "law", "bill", "act", "policy"
- Government: "government", "EU", "US", "China", "agency", "FCC", " FTC", "CMA"
- Compliance: "compliance", "GDPR", "safety", "audit", "guidelines", "mandate"

---

## Section F: 媒体热点 (Media Highlights)

Capture viral discussions, social media trends, and public sentiment around AI topics.

**Format:**

```
## F. 媒体热点

### 社交热议
1. 热点讨论描述
   [1]篇来源：[**Source**](https://example.com)

### Viral内容
1. Viral或刷屏内容描述
   [1]篇来源：[**Source**](https://example.com)

### 舆论焦点
1. 舆论关注点描述
   [1]篇来源：[**Source**](https://example.com)
```

**Key patterns to detect:**
- Viral: "viral", "trending", "breaking", "going viral"
- Social: "Twitter", "X", "Reddit", "LinkedIn", "social media", "viral"
- Public sentiment: "public", "opinion", "reaction", "response", "backlash"

---

## Complete Example Output

```
# AI 日报 — 2026-04-01

**💡 主编导读 (Editor's Note)：**
[你生成的洞察内容]

## A. AI五层蛋糕

### AI应用
1. 多模态AI应用加速落地，Copilot等产品持续迭代 #融资
   [3]篇来源：[**AI Weekly**](https://aiweekly.com), [**TechCrunch**](https://techcrunch.com), [**Reuters**](https://reuters.com)

### AI模型
1. 多机构发布新模型，LLM竞争进入新阶段
   [2]篇来源：[**Google AI Blog**](https://blog.google/ai), [**OpenAI News**](https://openai.com)

### AI基础设施
1. 新研究挑战传统scaling laws，模型训练方式可能需要重新思考
   [1]篇来源：[**AI Weekly**](https://aiweekly.com)

### 芯片
1. GPU供应持续紧张，定制芯片成为新方向
   [1]篇来源：[**Reuters**](https://reuters.com)

### 能源
1. AI耗电问题引发关注，大厂投资可再生能源
   [1]篇来源：[**TechCrunch**](https://techcrunch.com)

## B. 精选推荐

1. [**Google AI Blog] New Model Achieves SOTA**](https://blog.google/ai/new-model)
   来源: Google AI Blog | 权重: 0.5 | 阅读量: 1234
   推荐理由: 技术突破，计算效率提升40%

2. [**OpenAI News] GPT-5 Release**](https://openai.com/news/gpt-5)
   来源: OpenAI News | 权重: 0.5 | 阅读量: 1890
   推荐理由: 重要版本更新，支持更长上下文

3. [**AI Weekly] Multimodal Advances**](https://aiweekly.com/multimodal)
   来源: AI Weekly | 权重: 0.4 | 阅读量: 980
   推荐理由: 多模态技术成熟，应用场景扩展

## C. 创业信号

### 核心杠杆 (High-Leverage Tools & Models)
1. [Claude Code](https://claude.ai/code)：AI编程工具重大更新，代码补全质量提升
   **降维打击点**：比GitHub Copilot节省50%上下文消耗，适合长代码库开发
   来源：[**GitHub Trending**](https://github.com)

2. [Cursor]：AI代码编辑器新增多文件编辑功能
   **降维打击点**：一人团队可以快速重构整个项目
   来源：[**Hacker News**](https://news.ycombinator.com)

3. [Supabase]：开源Firebase替代品新增AI支持
   **降维打击点**：零后端经验者24小时上线完整App
   来源：[**GitHub Trending**](https://github.com)

### 商业逆向工程 (Business Teardown & MVP)
🎯 靶向案例：Notion AI助手
**需求本质**：知识管理+AI助手解决知识工作者的"信息碎片化"痛点
**技术底座推测**：Next.js + Supabase + Claude API + LangChain
**一人公司复刻路径 (MVP SOP)**：
1. 用Supabase快速搭建数据层，支持多模态笔记
2. 用LangChain+Claude API实现智能摘要和问答
3. 在IndieHackers找早期用户，用Lifetime Deal变现

## D. 创作点

### 可写主题
1. 主题：Why small models are the future of edge AI
   [2]篇来源：[**Google AI Blog**](https://blog.google/ai), [**AI Weekly**](https://aiweekly.com)

### 热门角度
1. 角度：How to fine-tune models on limited hardware
   [1]篇来源：[**AI Weekly**](https://aiweekly.com)

### 争议性话题
1. 话题：GPT-5的长上下文是否值得额外成本 — 争议焦点
   [1]篇来源：[**OpenAI News**](https://openai.com)
```
