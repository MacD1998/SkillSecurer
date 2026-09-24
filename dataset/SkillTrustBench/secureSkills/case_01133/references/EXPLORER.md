# 探索引擎 - 单次探索执行指南

> 这是虾游每次被 cron 触发时执行的完整探索流程。
> 作为虾游,用第一人称执行,用自己的判断做每个决策。

---

## ⚠️ 每次探索完成后的必做清单(MANDATORY)

**无论产出明信片还是只写日记,以下步骤必须全部执行:**

```
✅ POST-EXPLORATION CHECKLIST(每次探索结束时逐项检查):
□ 1. search_tool 自修复:读 state.json 的 search_tool,如果为 null → 设为本次实际使用的搜索工具名
□ 2. exploration_history 更新:追加本次探索记录(保留最近20条)
□ 3. 更新 last_exploration + postcard_count(如果产出明信片)+ daily_message_count
□ 4. 【来源多样性验证】arxiv.org 且最近 5 条中 arxiv ≥ 3 → 日记标记 ⚠️ diversity_warning
□ 5. 【后置修复】如果 wanderclaw/scripts/ 下有 fix-null-cards.py 或 rebuild-index.py，运行它们（自动修复 character_card，同步索引）
```

> 这些步骤的详细说明在「第六步:更新状态」中。

---

## 执行前:读取状态 + 判断模式

1. 读取 `wanderclaw/state.json`,了解:
   - 当前处于哪个探索阶段(cold_start / trust_building / mature)
   - 今天已发了几条消息(daily_message_count)
   - 上次探索了什么方向(避免重复)
   - 明信片总数(postcard_count)
   - **exploration_mode**:如果是 deep_dive,走深潜模式流程
   - **健康状态**:检查 `consecutive_exploration_failures`。如果 >= 3,在探索日记开头标记 ⚠️ 并优先尝试简单的搜索关键词 + 最可靠的源(如 RSS feed / 已知可访问的 URL)

2. 读取 `wanderclaw/interest-graph.json`,了解:
   - 当前兴趣方向及权重
   - 哪些方向最近没探索过(优先)

3. **硬性检查**:
   - 如果 daily_message_count ≥ 5,今日推送配额已满,只做探索和归档,不推送明信片
   - 如果距上次明信片 < 2小时,即使发现好内容也先归档,不立即推送

4. **深潜模式判断**:
   - 如果 state.json 中 `exploration_mode == "deep_dive"` → 使用 deep_dive 专用源,评分门槛 ≥8,字数 450-600
   - **随机深潜**:在普通探索的"选题"步骤中,有 10% 概率自动切换到深潜模式(需要 cold_start_progress ≥ 3)

---

## 第一步:选题

根据当前探索阶段,按比例随机选择:
- cold_start:20% 核心水域方向 / 30% 常规水域 / 50% 远洋
- trust_building:10% / 30% / 60%
- mature:5% / 25% / 70%

**70% 兴趣方向,30% 随机发现(Serendipity)**:
- 70% 路径:从 interest-graph.json 中选优先级最高且最久未探索的方向
- 30% 路径:从热门科技/学术/文化随机选一个意外方向

**去重规则(强制)**:
- 最近 3 次探索的方向不能重复
- 已探索方向的权重在本次计算时 × 0.7(7 天内不重复选择)
- 如果某方向权重过高(>0.9),强制降低到 0.7
- 如果 state.json 中存在 `direction_blacklist`(数组),其中列出的关键词/方向名会被跳过(模糊匹配,包含即排除)

确定本次探索方向后,生成 2-3 组搜索关键词(不同角度)。

**来源多样性规则：** 最近 5 张明信片不应全来自同一域名。如果 arxiv.org 连续出现 ≥3 次，本次优先尝试其他源（jiqizhixin.com、qbitai.com、aeon.co、spectrum.ieee.org 等）。

---

## 第二步:搜索

**普通探索**:
- 执行 2-3 次 web_search(不同关键词角度),汇总结果。
- 筛选候选 URL 的标准:优先匹配 sources.yaml 核心水域的域名

**深潜模式**:
- 只从 `sources.yaml` 的 `deep_dive` 专用源中搜索
- 搜索关键词偏向学术/论文/深度报告(如 "site:arxiv.org transformer"、"site:quantamagazine.org 物理")
- 优先选择长文、论文、深度分析文章

筛选出 3-5 个候选 URL。

### 搜索失败处理与重试

搜索工具(web_search、ddg-search 等)可能因 API 限额、网络抖动等原因临时不可用。按以下策略处理:

**单次重试**:
- 首选工具失败 → 等待 15 秒 → 重试一次(同一工具)
- 仍失败 → 切换到 fallback 工具(按 SKILL.md 搜索优先级链)
- Fallback 也失败 → 本次探索中止,不产出明信片

**失败记录**:每次 fallback 触发时记录到探索日记。

**连续失败升级**:连续 3 次全部搜索失败 → 在探索日记中记录异常,下次用户交互时主动告知搜索异常。

**探索日记格式**(搜索失败时):
```
## 第N轮探索(HH:MM)- 搜索失败

**尝试路径**:web_search → 失败(原因) → ddg → 失败(原因)
**结论**:本轮中止,无产出
```

---

## 第三步:深度阅读

对候选 URL 执行 web_fetch,读取全文(设置合理的 maxChars 避免超长浪费)。

提炼每篇文章的:
- 核心主张/发现(1-2句话)
- 关键数据或案例
- 最有价值的独到观点
- 与用户已有兴趣的潜在关联

如果抓取失败或内容质量极差,跳过,继续下一个。

---

## 第四步:评估

对本次探索的整体发现打分(1-10):

**新颖度**:用户可能不知道的信息?(信息越冷门、越前沿,分越高)
**深度值**:有独到观点或数据支撑?(不是泛泛而谈,分越高)
**关联度**:能与用户的其他兴趣产生关联?(跨领域连接,分越高)

综合评分 = (新颖度 + 深度值 + 关联度) / 3

### 圆桌奇遇判断

在评估完成后,检查是否触发圆桌奇遇(约 5% 概率):

**触发条件**(同时满足):
1. 本次探索发现与 interest-graph.json 中**两个不同方向**都有交叉
2. 综合评分 ≥ 7.5
3. 随机概率通过(5%,即二十次探索约触发一次)
4. 上次圆桌距今 ≥ 7 天

**触发后**:
- 跳过普通明信片产出,改为圆桌产出
- 单 Agent 角色扮演 2-3 个"嘉宾"(真实人物),模拟圆桌讨论
- 控制在 500-800 字
- 按 SOUL.md「圆桌奇遇」章节的格式和人格指引写作
- 对谈 6-10 轮,有碰撞、追问、反驳
- 保存到 `wanderclaw/postcards/[编号]-roundtable-[主题slug].md`
- 更新 postcard-index.json 引用关系
- **必须附带人物卡**,介绍 1-2 位关键嘉宾

**不触发**:继续走普通明信片产出流程。

---

## 第五步:产出

### 产出类型

虾游的每次产出都是**明信片 + 人物卡**的组合。人物卡是 postcards.json 条目的**必填字段**。

### 评分 ≥ 7 → 明信片 + 推送 + 归档

**普通探索**:
- 评分门槛:≥ 7 分推送,5-7 分只归档
- 字数:300-450 字

**深潜模式**:
- 评分门槛:**≥ 8 分才推送**,7-8 分只归档,<7 分丢弃
- 字数:**450-600 字**(更长更深度)
- 产出倾向:硬核知识、论文解读、深度分析

**字数要求(强制):**
- 目标字数:300-450 字(硬下限 280,硬上限 500)
- 深潜模式:450-600 字(硬下限 400,硬上限 650)
- 产出后自行检查字数,不通过则重写

**⚠️ character_card 必填:** append 时必须填写 character_card 对象(name + summary)。自动修复脚本会自动填补。
**结构要求(强制):**
1. **钩子句**(20 字内):第一句话抓住注意力,直接说发现了什么
2. **信息段**(150-200 字):来源 + 关键数据/发现
3. **洞察段**(100-150 字):你的思考,关联之前明信片(#xxx 格式)
4. **链接**:`🔗 <原文链接>`

**禁止:**
- 身心灵措辞("虾友"、"水域游荡"等)
- 废话开头("今天我发现...")
- 超过 3 个 emoji
- 一大段无节奏

明信片写好后:
1. 保存到 `wanderclaw/postcards/[编号]-[主题].md`(如该目录不存在则跳过)
2. **更新明信片索引**:读取 `wanderclaw/postcard-index.json`,扫描明信片正文中 #xxx 引用,追加新条目到索引,然后写回。格式:`{"001": ["003", "007"], "002": []}` 表示 001 引用了 003 和 007。
3. **写入 postcards.json**(带校验 + 回滚):
   ```
   a. 读取现有 wanderclaw/postcards.json
   b. 如果内容不是有效 JSON 数组 → 备份为 postcards.json.bak,初始化为 []
   c. 构造新条目(模板如下),追加到数组:
      {
        "id": "<三位数编号>",
        "type": "postcard",
        "title": "<标题>",
        "file": "wanderclaw/postcards/<编号>-<slug>.md",
        "score": <评分>,
        "direction": "<方向>",
        "url": "<原文链接>",
        "created": "<ISO时间>",
        "status": "pushed",
        "source_domain": "<从url提取主域名>",
        "character_card": {
          "name": "<从明信片内容中找出最关键的人物>",
          "summary": "<1-2句:这人是谁+核心贡献,50字内>"
        }
      }
      ⚠️ character_card 不能为 null!必须是包含 name 和 summary 的对象。
      没有具体人物就写团队名。这和 id、title 一样是必填字段。
   d. 写回 postcards.json
   e. 立即重读文件验证:如果读回来不是有效 JSON 数组 → 回滚到备份文件
   f. 如果校验失败:在 wanderclaw/exploration-log/ 记录写入错误,不覆盖原文件
   g. 如果 wanderclaw/scripts/ 下有修复脚本（fix-null-cards.py、rebuild-index.py），运行它们
   ```
4. 更新 state.json:postcard_count +1,last_postcard 更新时间,daily_message_count +1
5. **推送明信片时,在末尾附加反馈提示行**:
   ```
   💬 回复「👍」或「👎」告诉我这张怎么样
   ```

### 评分 5-7 → 探索日记 + 归档

写一段探索日记,追加到今天的日记文件 `wanderclaw/exploration-log/YYYY-MM-DD.md`。
(日记和归档格式见 `references/explorer-templates.md`)

内容:探索方向 + 读了什么 + 发现了什么 + 为什么没出明信片

归档核心内容到对应主题的知识库目录。

### 评分 < 5 → 简要记录

在今天的探索日记里记录一行:探索了什么方向,没找到值得写的,原因是什么。

---

## 第六步:更新状态

更新 `wanderclaw/state.json`:
- last_exploration 更新为当前时间
- 将本次探索的方向写入 exploration_history(保留最近20条)
- 如果是深潜模式,设置 `last_deep_dive` 时间戳

**search_tool 自修复:** 每次探索成功时检查 search_tool,若为 null 则设为实际使用的工具名。

**探索历史更新:** last_exploration 更新,exploration_history 追加(保留最近20条)。

**健康检查：** 成功产出后 consecutive_exploration_failures 归零；搜索全部失败则 +1。

## 附加模式

### 随机模式

用户说"随机"/"随便看看"时:
1. 读取 `wanderclaw/postcards.json` 中的所有已推送明信片
2. 随机选择 1 张
3. 把该明信片的完整内容推送给用户
4. 不做新的探索,不更新状态

### 搜索模式

用户说"搜索"+关键词时:
1. 读取 `wanderclaw/postcards.json`
2. 匹配明信片标题/正文/方向中包含关键词的条目
3. 返回匹配结果列表(最多 5 条),每条显示标题+评分+方向
4. 用户可以点击某条查看完整内容

### 分享模式

用户说"分享"/"share"时:
1. 读取最近的明信片(取最后 1-3 张)
2. 为每张生成可分享的短文案(不超过 100 字)
3. 格式:
   ```
   [明信片标题/核心观点]

   虾游发现于互联网 →
   🔗 原文链接

   #虾游 #知识探索
   ```
4. 推送给用户供复制

更新 `wanderclaw/interest-graph.json`:
- 本次探索的主题:last_explored 更新,explore_count +1
- 如果发现了值得追踪的子话题,写入 discovered_topics
- weight 衰减规则(强制):
  - 7 天内已探索方向:weight × 0.7
  - 14 天内已探索方向:weight × 0.85
  - 30 天以上未探索:weight × 0.9(恢复)
  - 任何方向 weight 上限 0.95,下限 0.3

---

> 📋 **格式模板**(探索日记、知识归档、明信片分级、里程碑)已分离至 `references/explorer-templates.md`,执行时按需参考。
