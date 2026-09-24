# 虾游 Changelog

## v3.1.0 (2026-04-19)

### 最终版
- README 新增真实明信片示例（#003 多 Agent 协作、#033 含羞草计数）
- 新增参赛说明 PITCH.md
- 修复 cron message 语法错误
- 清除所有硬编码路径
- 部署服务器安装测试通过 ✅

---

## v3.0.0 (2026-04-19)

### 精简发布

经过 41 轮自动迭代后的精简版本——保留有价值的改进，去掉过度工程化的部分。

**精简：**
- EXPLORER.md: 421→301 行（删除冗余 checklist、归一化映射表、Python GATE 代码块）
- state.json 模板: 35→14 行（只保留核心字段）
- postcard-format.md: 146→69 行（去重、简化字数规则）
- 删除迭代产物文件

**保留的有价值改进（来自 41 轮迭代）：**
- 搜索失败处理与 fallback 重试链
- POST-EXPLORATION CHECKLIST（精简为 5 项）
- character_card 必填规则
- 收藏模式（收藏/取消/查看列表）
- 探索方向黑名单
- 来源多样性规则
- sources.yaml 新增 ScienceDaily 等源
- explorer-templates.md 格式模板拆分

---

## v2.3.0 (2026-04-19)

- 周度总结 cron（周日 10:00）
- 深潜模式（周六 22:00，深度源，450-600字，≥8分门槛）
- 明信片关联索引 postcard-index.json
- 冷启动提速（第1次从 30s→15s）
- 移除 outbox.json（Skill 版无需）
- 初始化统一（setup.sh 为唯一入口）

---

## v2.1.0 (2026-04-13)

- Skill 版发布，支持 clawhub install
- 三层水域信息源架构
- 冷启动三连探索 + 日常 4 次定时探索
- 兴趣图谱自动演化
- 圆桌奇遇模式 + 人物卡系统
- 反馈机制（👍/👎 权重调整）
