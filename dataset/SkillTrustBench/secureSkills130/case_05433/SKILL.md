---
name: waizao-stockapi
description: 通过 ** 歪枣网（www.waizaowang.com）** 查询中国股市综合数据。获取 A 股 / 港股 / 美股 K 线、实时行情、基金数据、技术指标（超 100 种 TA-Lib 指标）、涨跌停池、龙虎榜、北向资金流向、财务报表。当用户需要股市数据、量化分析或金融研究时调用。需配置 WAIZAO_TOKEN 环境变量。
---

# Waizao StockAPI Skill (歪枣网)

通过歪枣网 API 查询全面的股票市场数据。支持 A 股/港股/美股、基金、技术指标、资金流向、财务报表等。

## 配置

### 设置 Token（必需）

在使用前必须设置 `WAIZAO_TOKEN` 环境变量：

```bash
# Linux/Mac
export WAIZAO_TOKEN='your_token_here'

# Windows (PowerShell)
$env:WAIZAO_TOKEN="your_token_here"
```

**获取 Token：**
1. 访问 http://www.waizaowang.com/ 注册账号
2. 登录后获取 API Token
3. Token 免费使用，但有调用频率限制

### 安装依赖

```bash
pip install waizao pandas requests
```

### 验证配置

```bash
cd /home/admin/openclaw/workspace/skills/waizao-stockapi
python3 scripts/waizao-stockapi.py test
```

## 快速使用

### 获取股票列表

```bash
# 上证 A 股列表
python3 scripts/waizao-stockapi.py stock list --type 1

# 创业板股票
python3 scripts/waizao-stockapi.py stock list --type 6

# 科创板股票
python3 scripts/waizao-stockapi.py stock list --type 7
```

### 查询股票日线数据

```bash
python3 scripts/waizao-stockapi.py stock daily \
  --code 600004 \
  --start 2024-01-01 \
  --end 2024-01-10
```

### 查询实时行情

```bash
python3 scripts/waizao-stockapi.py stock realtime --code 600004
```

### 查询涨停/跌停股票

```bash
# 今日涨停
python3 scripts/waizao-stockapi.py limit up --date 2024-01-15

# 今日跌停
python3 scripts/waizao-stockapi.py limit down --date 2024-01-15
```

### 查询技术指标

```bash
# MACD 指标
python3 scripts/waizao-stockapi.py indicator macd \
  --code 600004 \
  --start 2024-01-01 \
  --end 2024-01-10

# RSI 指标
python3 scripts/waizao-stockapi.py indicator rsi \
  --code 600004 \
  --start 2024-01-01 \
  --end 2024-01-10
```

### 查询基金数据

```bash
# 基金净值
python3 scripts/waizao-stockapi.py fund nav \
  --code 161725 \
  --start 2024-01-01 \
  --end 2024-01-10

# 基金排行
python3 scripts/waizao-stockapi.py fund rank --type 2
```

### 查询沪深港通资金

```bash
# 资金流向
python3 scripts/waizao-stockapi.py hsgt money \
  --start 2024-01-01 \
  --end 2024-01-10

# 北上资金持股榜
python3 scripts/waizao-stockapi.py hsgt stock --date 2024-01-15
```

### 查询龙虎榜

```bash
python3 scripts/waizao-stockapi.py longhu \
  --code 600004 \
  --start 2024-01-01 \
  --end 2024-01-10
```

## 命令参考

### 股票数据 (stock)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `stock list --type N` | 获取股票列表 | --type (1|上证 A 股; 2|深证 A 股; 6|创业板; 7|科创板) |
| `stock daily` | 日线 K 线 | --code, --start, --end |
| `stock realtime` | 实时行情 | --code |

### 指数数据 (index)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `index daily` | 指数日线 | --code, --start, --end |

### 涨跌停池 (limit)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `limit up` | 涨停池 | --date |
| `limit down` | 跌停池 | --date |

### 基金数据 (fund)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `fund nav` | 基金净值 | --code, --start, --end |
| `fund rank` | 基金排行 | --type (可选) |

### 技术指标 (indicator)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `indicator macd` | MACD 指标 | --code, --start, --end |
| `indicator rsi` | RSI 指标 | --code, --start, --end |

### 沪深港通 (hsgt)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `hsgt money` | 资金流向 | --start, --end |
| `hsgt stock` | 持股榜 | --date |

### 龙虎榜 (longhu)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `longhu` | 龙虎榜详情 | --code, --start, --end |

### 财报数据 (finance)

| 命令 | 说明 | 必需参数 |
|------|------|----------|
| `finance --type yugao` | 业绩预告 | --code, --start, --end |
| `finance --type kuibao` | 业绩快报 | --code, --start, --end |

### 输出格式

```bash
# JSON 格式（默认）
python3 scripts/waizao-stockapi.py stock realtime --code 600004 --format json

# 表格格式
python3 scripts/waizao-stockapi.py stock daily --code 600004 --start 2024-01-01 --end 2024-01-10 --format table

# CSV 格式
python3 scripts/waizao-stockapi.py stock daily --code 600004 --start 2024-01-01 --end 2024-01-10 --format csv
```

## 常见使用场景

### 1. 获取某板块全部股票

```bash
# 获取全部创业板股票
python3 scripts/waizao-stockapi.py stock list --type 6
```

### 2. 分析股票近期走势

```bash
python3 scripts/waizao-stockapi.py stock daily \
  --code 000001 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --format table
```

### 3. 监控涨停股票

```bash
python3 scripts/waizao-stockapi.py limit up --date 2024-01-15
```

### 4. 技术分析多指标

```bash
# MACD
python3 scripts/waizao-stockapi.py indicator macd \
  --code 600004 --start 2024-01-01 --end 2024-01-31

# RSI
python3 scripts/waizao-stockapi.py indicator rsi \
  --code 600004 --start 2024-01-01 --end 2024-01-31
```

### 5. 追踪北向资金

```bash
# 查看近期资金流向
python3 scripts/waizao-stockapi.py hsgt money \
  --start 2024-01-01 --end 2024-01-15

# 查看持股榜
python3 scripts/waizao-stockapi.py hsgt stock --date 2024-01-15
```

### 6. 基金研究

```bash
# 查看股票型基金排行
python3 scripts/waizao-stockapi.py fund rank --type 2

# 查看某基金历史净值
python3 scripts/waizao-stockapi.py fund nav \
  --code 161725 --start 2024-01-01 --end 2024-01-31
```

## 支持的股票类型

| --type 值 | 类型 |
|----------|------|
| 1 | 上证 A 股 |
| 2 | 深证 A 股 |
| 3 | 北证 A 股 |
| 4 | 沪深京 B 股 |
| 5 | 新股 |
| 6 | 创业板 |
| 7 | 科创板 |
| 8 | 沪股通 (港>沪) |
| 9 | 深股通 (港>深) |
| 10 | ST 股票 |
| 11 | 港股通 (沪>港) |
| 12 | 港股通 (深>港) |

## K 线类型

| --ktype 值 | 类型 |
|-----------|------|
| 101 | 日线 |
| 102 | 周线 |
| 103 | 月线 |

## 复权类型

| --fq 值 | 类型 |
|--------|------|
| 0 | 不复权 |
| 1 | 前复权 |
| 2 | 后复权 |

## 常见问题

### Token 错误

```
Error: WAIZAO_TOKEN not set
```

**解决：**
```bash
export WAIZAO_TOKEN='your_token'
```

### 导入错误

```
ModuleNotFoundError: No module named 'waizao'
```

**解决：**
```bash
pip install waizao pandas requests -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

### 数据为空

可能原因：
- 日期范围包含非交易日（周末/节假日）
- 股票代码不存在
- Token 无效

## 更多资源

- **详细 API 文档**：见 `references/api-docs.md`
- **官方网站**：http://www.waizaowang.com/
- **Python 库**：`pip install waizao`

## 注意事项

1. **Token 安全**：不要将 Token 硬编码到代码中
2. **批量限制**：code 参数最多支持 50 个股票代码
3. **数据延迟**：实时数据可能有延迟
4. **投资风险提示**：数据仅供参考，不构成投资建议
5. **调用频率**：免费 Token 有调用次数限制
