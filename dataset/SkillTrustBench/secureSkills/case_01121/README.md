# A股每日复盘

A股大盘快照与股票分组分析技能，用于抓取市场数据、生成技术分析报告和可视化图表。

## 功能

- 📊 **大盘数据抓取**：上证指数、创业板指、科创50的120日K线数据
- 📈 **技术面分析**：MACD、KDJ、RSI、均线系统、布林带、量价背离、技术形态识别
- 🎨 **风格指数跟踪**：上证50、沪深300、中证500、中证1000、小盘成长、红利指数
- 📉 **涨跌幅分布**：全市场涨跌分布统计
- 🏆 **股票分组**：涨幅前100、跌幅前100榜单
- 📄 **可视化报告**：自动生成市场日报（Markdown + K线图表）

## 触发方式

用户发送 "复盘 [日期]" 时触发此技能。

**日期格式**：
- `YYYY-MM-DD` (如: 2026-03-13)
- `YYYY/MM/DD` (如: 2026/03/13)
- 省略日期 → 默认使用今天（自动回退到最近交易日）

## 配置

需要设置 Tushare Token：

```bash
export TUSHARE_TOKEN="your_token_here"
```

或在 `.streamlit/secrets.toml` 中添加：
```toml
tushare_token = "your_token_here"
```

## 依赖

- Python 3.8+
- akshare
- pandas
- tushare
- matplotlib
- numpy

## 输出

- `snapshot_{date}.json` - 完整市场快照
- `top_100_gainers_{date}.csv` - 涨幅前100
- `top_100_losers_{date}.csv` - 跌幅前100
- `index_kline_{date}.png` - 三指数K线图
- `market_report_{date}.md` - 市场日报

## 使用示例

```bash
# 生成今日市场日报
python scripts/generate_market_report.py

# 生成指定日期报告
python scripts/generate_market_report.py --date 2026-03-13
```

## 过滤规则

- 去除 ST 股票
- 去除名称包含"退"的股票
- 去除北交所股票
- 去除上市天数不足60天的新股

## License

MIT
