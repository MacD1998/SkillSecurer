# 使用说明

## 依赖

### Python 包
```bash
pip install akshare pandas tushare matplotlib
```

### API 密钥

#### 必需
- `TUSHARE_TOKEN` 环境变量

## 数据来源

### A股数据源
| 数据源 | 接口/库 | 用途 |
|--------|---------|------|
| Tushare Pro | `index_daily` | 三大指数 + 风格指数 K 线数据 |
| Tushare Pro | `trade_cal` | 交易日历 |
| Tushare Pro | `daily_basic` | 股票估值、市值数据 |
| Tushare Pro | `daily` | 股票涨跌幅、成交额 |
| Tushare Pro | `stock_basic` | 股票基础信息（名称、行业） |
| AKShare | `stock_market_activity_legu` | 市场情绪指标（涨跌家数、涨停跌停） |

## 覆盖指数

### 三大指数
- 上证指数 (000001.SH)
- 深证成指 (399001.SZ) — 仅用于成交额汇总
- 创业板指 (399006.SZ)
- 科创 50 (000688.SH)

### 风格指数
| 代码 | 名称 | 描述 |
|------|------|------|
| 000016.SH | 上证50 | 超大盘 |
| 000300.SH | 沪深300 | 大盘 |
| 000905.SH | 中证500 | 中盘 |
| 000852.SH | 中证1000 | 小盘 |
| 399376.SZ | 小盘成长 | 成长风格 |
| 000015.SH | 红利指数 | 红利策略 |

## 输出结构

`snapshot_{trade_date}.json` 包含以下顶层字段：

```json
{
  "trade_date": "2026-03-13",
  "input_date": "2026-03-13",
  "force_date": true,
  "lookback_days": 120,
  "market_data": {
    "index_kline": {...},           // 三大指数120日K线
    "index_turnover_today": [...],  // 当日指数成交额
    "market_turnover_amount_sum": ..., // 成交额(千元)
    "market_turnover_unit": "...",
    "market_turnover_sum_scope": [...],
    "market_activity_legu": {...},  // 市场情绪指标
    "style_index_kline": {...}      // 风格指数K线
  },
  "stock_universe": {
    "total_after_filters": 5000,    // 过滤后股票数
    "filters": {...},               // 过滤规则说明
    "daily_basic_plus_daily_fields": [...],
    "pct_distribution": [...]       // 涨跌幅分布
  },
  "groups": {
    "top_100_gainers": [...],
    "top_100_losers": [...]
  },
  "technical_analysis": {           // 技术面深度分析
    "sh": {
      "name": "上证指数",
      "current_price": 4049.91,
      "macd": {"dif": -1.89, "dea": 7.54, "hist": -9.56, "signal": "..."},
      "kdj": {"k": 28.5, "d": 25.3, "j": 5.1, "signal": "..."},
      "rsi": {"rsi6": 30.6, "rsi12": 31.7, "rsi24": 48.5, "signal": "..."},
      "ma": {"ma5": 4098.54, "ma10": 4102.77, "ma20": 4119.18, "ma60": 4066.63, "trend": "..."},
      "bollinger": {"upper": 4280.50, "middle": 4120.30, "lower": 3960.10},
      "support_resistance": {"support": 4048.09, "resistance": 4197.23},
      "patterns": [...]
    },
    "cyb": {...},                   // 创业板指
    "kcb": {...}                    // 科创板指
  }
}
```

### 分组详情

#### top_100_gainers / top_100_losers
字段：ts_code, symbol, name, trade_date, close, pct_chg, amount, amount_yi, total_mv_yi, industry, market, ...

### 涨跌幅分布区间
- `>20%`
- `10%~20%`
- `5%~10%`
- `3%~5%`
- `0%~3%`
- `-3%~0%`
- `-5%~-3%`
- `-10%~-5%`
- `<-10%`

## 技术面分析模块

本技能集成了专业的技术面分析模块 `technical_analysis.py`，提供全面的指标计算和形态识别。

### 支持的指标

#### 趋势指标
| 指标 | 参数 | 说明 |
|------|------|------|
| **MACD** | 12/26/9 | DIF、DEA、柱状图，识别趋势和背离 |
| **均线系统** | 5/10/20/60 | 多头排列/空头排列判断 |
| **布林带** | 20/2 | 上轨、中轨、下轨，波动区间分析 |

#### 动量指标
| 指标 | 参数 | 说明 |
|------|------|------|
| **KDJ** | 9/3/3 | K/D/J值，超买超卖判断 |
| **RSI** | 6/12/24 | 多周期RSI，强弱分析 |

#### 量价分析
- 顶背离/底背离检测
- 量价配合度评估

### 技术形态识别

#### 双底形态（W底）
- **识别条件**：两个低点接近（差距<5%），中间反弹>3%
- **突破确认**：价格突破颈线位
- **目标价**：颈线位 + （颈线位 - 低点）
- **可靠度**：高

#### 双顶形态（M头）
- **识别条件**：两个高点接近（差距<5%），中间回调>3%
- **跌破确认**：价格跌破颈线位
- **目标价**：颈线位 - （高点 - 颈线位）
- **可靠度**：高

#### 对称三角形
- **识别条件**：高点下降，低点上升，形成收敛三角形
- **突破方向**：等待方向选择
- **可靠度**：中

### 综合判断逻辑

系统根据以下信号进行多空判断：

| 信号来源 | 看涨条件 | 看跌条件 |
|---------|---------|---------|
| MACD | 多头/金叉 | 空头/死叉 |
| KDJ | 超卖/金叉 | 超买/死叉 |
| RSI | 超卖 | 超买 |
| 均线 | 多头排列 | 空头排列 |

**综合判断规则**：
- 强烈看多：≥3个看涨信号
- 偏多：2个看涨信号
- 震荡观望：其他情况
- 偏空：2个看跌信号
- 强烈看空：≥3个看跌信号

### 使用技术面分析模块

```python
from technical_analysis import generate_technical_summary, get_technical_summary_dict

# 生成文本报告
analysis_text = generate_technical_summary(df, "上证指数")
print(analysis_text)

# 获取结构化数据
analysis_dict = get_technical_summary_dict(df, "上证指数")
print(analysis_dict["macd"])
print(analysis_dict["patterns"])
```

## 默认过滤

- 去除 `ST`
- 去除名称包含 `退` 的股票
- 去除北交所股票
- 去除上市天数不足 `min_list_days` 的新股（默认60天）

## 典型命令

### 完整日报
```bash
python scripts/generate_market_report.py --output-dir datas/output_snapshot
```

### 指定日期
```bash
python scripts/generate_market_report.py --date 2026-03-13 --lookback-days 60 --min-list-days 90 --output-dir tmp/market_snapshot
```

### 仅抓数据
```bash
python scripts/fetch_market_and_stock_groups.py --date 2026-03-13 --force-date --output-dir datas/output_snapshot
```

### 仅生成图表
```bash
python scripts/render_market_chart.py --snapshot datas/output_snapshot/snapshot_2026-03-13.json
```

## 图表要求

- 标题固定为：`今日指数日K线`
- 子图固定为：上证指数、创业板指、科创板指
- 三张图必须放在同一行
- 默认使用 snapshot 中的最近 120 个交易日 K 线
- 红涨绿跌配色

## 报告要求

- 输出顺序必须是：先图片，后正文
- 用户给了日期时，抓取命令必须带 `--force-date`
- 正文开头固定为：`【YYYY-MM-DD】大盘数据`
- `涨幅前100` 和 `跌幅前100` 都必须压缩成严格 3 行
- 新增风格指数、涨跌幅分布、技术面深度分析等板块

## 一体化脚本输出

`generate_market_report.py` 会生成：

- `snapshot_{trade_date}.json` - 完整快照数据（含技术面分析）
- `top_100_gainers_{trade_date}.csv` - 涨幅前100
- `top_100_losers_{trade_date}.csv` - 跌幅前100
- `index_kline_{trade_date}.png` - K线图
- `market_report_{trade_date}.md` - 市场日报
