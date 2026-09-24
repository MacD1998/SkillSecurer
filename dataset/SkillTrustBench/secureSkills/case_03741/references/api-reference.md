# mcporter MCP API 参考

## 工具调用说明

本技能使用 `mcporter call` 命令调用恒生聚源 MCP 服务获取银行理财产品数据。所有工具入参均为 `query` 参数。

**服务前缀说明：**
- `jy-financedata-tool` - 工具类接口（产品数据查询）
- `jy-financedata-api` - API 类接口（宏观数据、舆情等）

---

## 1. ProductBasicInfoList - 产品基本信息

### 用途
获取理财产品的基础信息，用于报告第一章。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| product_name | 产品全称 | 招银理财招智进取固收增强一号 |
| product_code | 产品代码 | ZYLC2023001 |
| manager_name | 管理人名称 | 招银理财有限责任公司 |
| risk_level | 风险等级 | R2/中低风险 |
| product_type_l1 | 产品一级分类 | 固定收益类 |
| product_type_l2 | 产品二级分类 | 固收增强 |
| operation_mode | 运作模式 | 开放式净值型 |
| raising_mode | 募集方式 | 公募 |
| latest_scale | 最新规模（元） | 5000000000 |
| benchmark_lower | 业绩比较基准下限 | 3.5% |
| benchmark_upper | 业绩比较基准上限 | 4.5% |
| establish_date | 成立日期 | 2023-01-15 |
| maturity_date | 到期日 | 无固定期限/2028-01-15 |

### 调用命令

```bash
mcporter call jy-financedata-tool.ProductBasicInfoList query="ZYLC2023001"
```

---

## 2. ProductPerformance - 产品业绩表现

### 用途
获取产品历史收益数据，用于报告第二章。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| latest_7d_annualized | 最新 7 日年化收益 (%) | 4.15 |
| latest_10k_return | 最新万份收益 (元) | 1.12 |
| return_1y_cumulative | 近 1 年累计收益 (%) | 4.23 |
| return_1y_annualized | 近 1 年年化收益 (%) | 4.23 |
| return_3y_cumulative | 近 3 年累计收益 (%) | 12.85 |
| return_3y_annualized | 近 3 年年化收益 (%) | 4.11 |
| return_5y_cumulative | 近 5 年累计收益 (%) | 21.50 |
| return_5y_annualized | 近 5 年年化收益 (%) | 3.98 |
| return_since_establish_cumulative | 设立以来累计收益 (%) | 25.30 |
| return_since_establish_annualized | 设立以来年化收益 (%) | 4.05 |
| peer_avg_1y | 同类均值近 1 年 (%) | 3.85 |
| peer_avg_3y | 同类均值近 3 年 (%) | 3.65 |
| peer_avg_5y | 同类均值近 5 年 (%) | 3.55 |
| excess_benchmark_return | 超基准收益率 (%) | 0.35 |

### 调用命令

```bash
mcporter call jy-financedata-tool.ProductPerformance query="ZYLC2023001"
```

---

## 3. ProductReturnRiskIndicator - 收益风险指标

### 用途
获取产品风险指标，用于报告第三章。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| max_drawdown_1y | 近 1 年最大回撤 (%) | -1.85 |
| max_drawdown_3y | 近 3 年最大回撤 (%) | -2.50 |
| max_drawdown_5y | 近 5 年最大回撤 (%) | -3.20 |
| max_drawdown_since_establish | 设立以来最大回撤 (%) | -3.50 |
| std_dev_1y | 近 1 年收益标准差 (%) | 0.85 |
| std_dev_3y | 近 3 年收益标准差 (%) | 0.92 |
| std_dev_5y | 近 5 年收益标准差 (%) | 1.05 |
| sharpe_ratio_1y | 近 1 年夏普比率 | 1.35 |
| sharpe_ratio_3y | 近 3 年夏普比率 | 1.28 |
| sharpe_ratio_5y | 近 5 年夏普比率 | 1.22 |
| calmar_ratio | 卡玛比率 | 2.15 |
| information_ratio | 信息比率 | 0.85 |
| drawdown_recovery_days | 最大回撤修复天数 | 45 |
| peer_avg_max_drawdown | 同类均值最大回撤 (%) | -2.80 |
| peer_avg_std_dev | 同类均值标准差 (%) | 1.15 |
| peer_avg_sharpe | 同类均值夏普比率 | 1.05 |

### 指标解读

- **最大回撤**：负值，绝对值越小越好
- **标准差**：波动性，越小越稳定
- **夏普比率**：>1 为良好，>1.5 为优秀
- **卡玛比率**：收益/最大回撤，越高越好
- **信息比率**：主动管理能力，>0.5 为良好
- **修复天数**：越短恢复能力越强

### 调用命令

```bash
mcporter call jy-financedata-tool.ProductReturnRiskIndicator query="ZYLC2023001"
```

---

## 4. ProductPositionFeature - 持仓特征

### 用途
获取产品资产配置数据，用于报告第四章。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| cash_market_value | 现金类资产市值 (元) | 500000000 |
| cash_ratio | 现金类占比 (%) | 10.0 |
| fund_market_value | 基金资产市值 (元) | 750000000 |
| fund_ratio | 基金占比 (%) | 15.0 |
| bond_market_value | 债券资产市值 (元) | 3500000000 |
| bond_ratio | 债券占比 (%) | 70.0 |
| equity_market_value | 权益类资产市值 (元) | 200000000 |
| equity_ratio | 权益类占比 (%) | 4.0 |
| debt_market_value | 债权资产市值 (元) | 0 |
| debt_ratio | 债权占比 (%) | 0.0 |
| qdii_market_value | QDII 资产市值 (元) | 0 |
| qdii_ratio | QDII 占比 (%) | 0.0 |
| derivative_market_value | 金融衍生品市值 (元) | 0 |
| derivative_ratio | 金融衍生品占比 (%) | 0.0 |
| other_market_value | 其他资产市值 (元) | 50000000 |
| other_ratio | 其他资产占比 (%) | 1.0 |
| holding_codes | 持仓标的代码列表 | ["190001.XB","102345678.IB"] |
| holding_names | 持仓标的名称列表 | ["23 国债 01","23 农发 02"] |
| manager_type | 管理人类型 | 银行理财子公司 |

### 调用命令

```bash
mcporter call jy-financedata-tool.ProductPositionFeature query="ZYLC2023001"
```

---

## 5. WealthProdFilterStats - 同类产品筛选统计

### 用途
获取同类产品统计数据，用于报告第六章综合排名。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| peer_count | 同类产品数量 | 256 |
| peer_avg_return_1y | 同类平均收益近 1 年 (%) | 3.85 |
| peer_median_return_1y | 同类中位收益近 1 年 (%) | 3.75 |
| peer_top_10pct_return_1y | 同类前 10% 收益近 1 年 (%) | 5.20 |
| peer_avg_sharpe | 同类平均夏普比率 | 1.05 |
| peer_avg_max_drawdown | 同类平均最大回撤 (%) | -2.80 |
| product_return_rank | 产品收益排名 | 45 |
| product_sharpe_rank | 产品夏普比率排名 | 38 |
| product_drawdown_rank | 产品回撤排名 | 52 |
| product_percentile | 产品百分位排名 | 82.5 |

### 调用命令

```bash
mcporter call jy-financedata-tool.WealthProdFilterStats query="ZYLC2023001"
```

---

## 6. MacroIndustryEDB - 宏观行业经济数据

### 用途
获取宏观经济数据，用于报告第五章（舆情缺失时的替代）。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| deposit_rate_1y | 1 年期定存利率 (%) | 1.75 |
| deposit_rate_3y | 3 年期定存利率 (%) | 2.60 |
| lpr_1y | 1 年期 LPR (%) | 3.45 |
| lpr_5y | 5 年期 LPR (%) | 4.20 |
| shibor_overnight | 隔夜 Shibor (%) | 1.85 |
| shibor_3m | 3 个月 Shibor (%) | 2.15 |
| treasury_10y | 10 年期国债收益率 (%) | 2.75 |
| cpi_yoy | CPI 同比 (%) | 0.8 |
| ppi_yoy | PPI 同比 (%) | -1.2 |
| gdp_growth_yoy | GDP 同比增速 (%) | 5.2 |

### 调用命令

```bash
mcporter call jy-financedata-api.MacroIndustryEDB query="银行理财 利率环境"
```

---

## 7. MacroNewslist - 宏观舆情资讯

### 用途
获取央行货币政策资讯，用于报告第五章。

### 主要返回字段

| 字段名 | 说明 | 示例 |
|-------|------|------|
| news_title | 新闻标题 | 央行召开货币政策委员会例会 |
| news_date | 发布日期 | 2024-01-15 |
| news_source | 新闻来源 | 中国人民银行 |
| news_summary | 新闻摘要 | 会议强调保持流动性合理充裕... |
| sentiment | 舆情倾向 | 中性/正面/负面 |
| relevance_score | 相关度评分 | 0.85 |

### 调用命令

```bash
mcporter call jy-financedata-api.MacroNewslist query="央行 货币政策 银行理财"
```

---

## 错误处理

### 常见错误及应对

| 错误类型 | 处理方式 |
|---------|---------|
| 产品代码不存在 | 提示用户确认产品代码，建议提供产品全称 |
| 数据暂缺 | 在报告中标注"数据暂缺"，继续生成其他章节 |
| API 超时 | 重试 1 次，仍失败则标注数据不可用 |
| 权限不足 | 提示用户检查 JY_API_KEY 配置 |

### 数据质量检查

- 检查各字段是否为空
- 检查数值是否合理（如收益率是否在 -10% ~ 50% 范围）
- 检查日期格式是否正确
- 发现异常数据时在报告中标注说明

---

## 调用顺序建议

### 并行调用策略（推荐）

```bash
# 【组 1 - 核心数据 - 并行调用】
mcporter call jy-financedata-tool.ProductBasicInfoList query="ZYLC2023001" &
mcporter call jy-financedata-tool.ProductPerformance query="ZYLC2023001" &
mcporter call jy-financedata-tool.ProductReturnRiskIndicator query="ZYLC2023001" &
wait

# 【组 2/3 - 扩展数据 - 并行调用】
mcporter call jy-financedata-tool.ProductPositionFeature query="ZYLC2023001" &
mcporter call jy-financedata-tool.WealthProdFilterStats query="ZYLC2023001" &
mcporter call jy-financedata-api.MacroNewslist query="央行 货币政策" &
mcporter call jy-financedata-api.MacroIndustryEDB query="银行理财 利率" &
wait
```

**说明：** 
- 组 1 为核心数据，必须全部成功才能继续
- 组 2/3 为扩展数据，部分失败可降级处理
- 使用 `&` 和 `wait` 实现并行调用

### 串行调用（备用）

如环境不支持并行调用，按以下顺序：

```bash
mcporter call jy-financedata-tool.ProductBasicInfoList query="ZYLC2023001"
mcporter call jy-financedata-tool.ProductPerformance query="ZYLC2023001"
mcporter call jy-financedata-tool.ProductReturnRiskIndicator query="ZYLC2023001"
mcporter call jy-financedata-tool.ProductPositionFeature query="ZYLC2023001"
mcporter call jy-financedata-tool.WealthProdFilterStats query="ZYLC2023001"
mcporter call jy-financedata-api.MacroNewslist query="央行 货币政策"
mcporter call jy-financedata-api.MacroIndustryEDB query="银行理财 利率"
```
