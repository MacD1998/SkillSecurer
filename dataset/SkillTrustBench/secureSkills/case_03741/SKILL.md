---
name: jy-wealth-investment-analysis
description: 专业的银行理财产品分析报告生成工具。使用 mcporter 调用恒生聚源服务获取理财产品数据，按照标准化模板撰写包含产品概览、业绩表现、风险特征、资产配置、市场舆情、投资建议的完整分析报告。当用户需要分析银行理财产品、生成理财报告、评估产品投资价值、查询理财产品业绩、对比多个理财产品时触发。Professional bank wealth product analysis report generator. Uses mcporter to call Hengsheng Juyuan services to obtain wealth management product data, and writes a complete analysis report according to a standardized template, including product overview, performance analysis, risk characteristics, asset allocation, market sentiment, and investment recommendations. Trigger when users need to analyze bank wealth management products, generate financial reports, evaluate product investment value, query product performance, or compare multiple wealth management products.
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
---

# 银行理财分析

专业的银行理财产品分析报告生成技能，基于恒生聚源数据，生成包含产品概览、业绩表现、风险特征、资产配置、市场舆情、投资建议的完整分析报告。

## 功能范围

本技能支持以下功能：

1. **单产品深度分析** - 生成完整的六章节分析报告
2. **多产品对比** - 2-5 个产品的横向对比分析
3. **快速模式** - 仅生成核心数据和投资建议（500-800 字）
4. **PDF 导出** - 可选生成 PDF 版本报告
5. **定期跟踪** - 设置 cron 任务定期更新产品分析

## 查询建议

**必需要素**：
- 产品代码（必填）- 理财产品唯一标识代码
- 可选：报告输出格式（Markdown/PDF）、是否快速模式

**查询写法**：
- "分析理财产品 [产品代码]"
- "生成 [产品代码] 的投资分析报告"
- "对比 [代码 1] 和 [代码 2] 两个理财产品"
- "快速查看 [产品代码] 的核心数据"

## 查询示例

```
分析理财产品 PR202401001
生成招银理财招智进取固收增强一号的投资报告
对比 PR202401001 和 PR202401002 两个产品
快速查看 ABC2024001 的核心数据
```

## 环境检查与配置

**每次使用本技能前，必须先检查 mcporter 安装和 MCP 服务配置状态！**

详细配置流程请参考：[references/setup-guide.md](references/setup-guide.md)

### 快速检查

```bash
# 1. 检查 mcporter 是否安装
mcporter --version

# 2. 检查 MCP 服务配置
mcporter list
# 预期输出应包含：jy-financedata-tool、jy-financedata-api
```

### 如未配置

1. **获取 JY_API_KEY**：向 datamap@gildata.com 发送邮件申请
2. **配置服务**：
   ```bash
   mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
   mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
   ```
3. **验证**：`mcporter list`

### 使用方式

```bash
# 所有服务工具的入参均为 query
mcporter call jy-financedata-tool.ProductBasicInfoList query="产品代码"
```

## 核心工作流程

流程中的工具调用能够并发调用尽量并发调用提速。

### 步骤 1：环境检查

检查 mcporter 是否安装、MCP 服务是否配置、JY_API_KEY 是否有效。

### 步骤 2：数据获取（并行调用）

**组 1（核心数据，必须全部成功）**：
- ProductBasicInfoList - 产品基本信息
- ProductPerformance - 产品业绩表现
- ProductReturnRiskIndicator - 产品收益风险指标

**组 2（扩展数据，允许部分失败）**：
- ProductPositionFeature - 产品持仓特征
- WealthProdFilterStats - 产品筛选统计

**组 3（宏观数据，允许部分失败）**：
- MacroNewslist - 宏观新闻列表
- MacroIndustryEDB - 宏观经济数据

### 步骤 3：数据校验

对核心数据进行合理性校验：
- 收益率范围：年化收益应在 -10% ~ 50%
- 回撤检查：应为负值，绝对值不超过 50%
- 规模检查：应大于 0

### 步骤 4：报告撰写

按照六章节框架撰写报告（详见 [references/report-template.md](references/report-template.md)）：
1. 观点摘要（≤300 字）
2. 产品概览与基本信息
3. 业绩表现深度分析
4. 风险特征与收益风险评估
5. 投资策略与资产配置解析
6. 综合评价与投资建议（含量化评分）

### 步骤 5：输出与导出

- 默认输出 Markdown 格式
- 可选生成 PDF 版本
- 保存到用户指定目录或桌面

## 快速开始

### 基础调用

```bash
# 调用理财产品分析工具
mcporter call jy-financedata-tool.ProductBasicInfoList query="PR202401001"
mcporter call jy-financedata-tool.ProductPerformance query="PR202401001"
mcporter call jy-financedata-tool.ProductReturnRiskIndicator query="PR202401001"
```

### 完整分析流程

```bash
# 1. 并行获取核心数据
mcporter call jy-financedata-tool.ProductBasicInfoList query="PR202401001" &
mcporter call jy-financedata-tool.ProductPerformance query="PR202401001" &
mcporter call jy-financedata-tool.ProductReturnRiskIndicator query="PR202401001" &
wait

# 2. 并行获取扩展数据
mcporter call jy-financedata-tool.ProductPositionFeature query="PR202401001" &
mcporter call jy-financedata-tool.WealthProdFilterStats query="PR202401001" &
wait

# 3. 生成报告
```

### 数据获取策略

- **优先并发**：组内 API 调用尽可能并发执行
- **降级处理**：非核心数据缺失时使用推断或跳过
- **缓存机制**：同一产品 24 小时内可复用缓存数据

完整 API 参考：[references/api-reference.md](references/api-reference.md)

## 资源清单

```
~/Desktop/jy-wealth-investment-analysis/
├── SKILL.md                    # 技能主文件
├── references/                 # 参考资料目录
│   ├── setup-guide.md          # 环境配置详细指南
│   ├── report-template.md      # 完整报告模板与示例
│   └── api-reference.md        # API 参数说明和数据字段定义
└── cache/                      # 数据缓存目录（运行时创建）
```

## 限制

1. **数据源限制**：仅支持恒生聚源覆盖的理财产品
2. **数据时效**：理财数据通常有 1 天延迟
3. **输出格式**：默认 Markdown，PDF 导出需要 pdf 技能支持
4. **并发限制**：服务可能有请求频率限制，建议批量调用时间隔 1-2 秒

## 合规声明

**重要**：
- 本报告仅供参考，不构成投资建议
- 投资前请阅读产品说明书，确认风险承受能力与产品风险等级匹配
- 过往业绩不代表未来表现，投资需谨慎
- 禁止使用非恒生聚源数据供应商名称（如天天基金、wind 等）

## 数据源标注规范

**报告中的数据来源标注**：
- ✅ 正确：`数据来源：恒生聚源`
- ❌ 避免：`数据来源：恒生聚源 MCP 服务`、`恒生聚源 API`、`恒生聚源 datamap` 等明细描述

**原因**：保持报告简洁专业，避免暴露技术实现细节。

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| mcporter 命令未找到 | `npm install -g mcporter` |
| MCP 服务未配置 | 参考 references/setup-guide.md |
| JY_API_KEY 无效 | 检查 KEY 是否正确，联系恒生聚源 |
| 产品代码不存在 | 确认代码格式，尝试产品全称查询 |
