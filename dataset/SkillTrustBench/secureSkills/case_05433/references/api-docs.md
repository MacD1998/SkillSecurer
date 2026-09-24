# 歪枣网 Waizao API 参考文档

歪枣网提供全面、准确、稳定的财经数据接口服务。

## 官方网站
- 网站：http://www.waizaowang.com/

## 获取 Token

1. 访问 http://www.waizaowang.com/ 注册账号
2. 登录后获取 API Token
3. 设置环境变量：`export WAIZAO_TOKEN='your_token'`

## Python 库安装

```bash
pip install waizao -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade
```

## 主要数据类别

### 1. 股票基础数据

| 接口函数 | 说明 |
|---------|------|
| `getBaseInfo` | 沪深京 A 股、B 股、港股、美股等基本信息 |
| `getStockType` | 按类型获取股票列表（上证 A 股、创业板、科创板等） |
| `getStockHSABaseInfo` | 沪深京 A 股基本信息 |
| `getStockHKBaseInfo` | 港股基本信息 |
| `getStockUSABaseInfo` | 美股基本信息 |

### 2. K 线数据

| 接口函数 | 说明 |
|---------|------|
| `getStockHSADayKLine` | 沪深京 A 股日线、周线、月线 |
| `getStockHKDayKLine` | 港股 K 线 |
| `getStockUSADayKLine` | 美股 K 线 |
| `getIndexDayKLine` | 指数 K 线 |
| `getHourKLine` | 小时 K 线（5/15/30/60 分钟） |
| `getMinuteKLine` | 分钟 K 线（1 分钟） |

### 3. 实时行情

| 接口函数 | 说明 |
|---------|------|
| `getStockHSADailyMarket` | 沪深京 A 股每日行情 |
| `getStockHKDailyMarket` | 港股每日行情 |
| `getStockUSADailyMarket` | 美股每日行情 |
| `getIndexDailyMarket` | 指数每日行情 |

### 4. 涨跌停池

| 接口函数 | 说明 |
|---------|------|
| `getPoolZT` | 涨停池（不含 ST 及科创板） |
| `getPoolDT` | 跌停池 |
| `getPoolQS` | 强势池 |
| `getPoolCX` | 创新池 |
| `getPoolZB` | 炸板池 |

### 5. 基金数据

| 接口函数 | 说明 |
|---------|------|
| `getFundBaseInfo` | 基金基本信息 |
| `getFundNav` | 基金净值 |
| `getFundRank` | 基金排行 |
| `getFundPosition` | 基金持仓 |
| `getCnFundDayKLine` | 场内基金 K 线 |

### 6. 技术指标

TA-Lib 系列指标（100+ 个）：

| 类别 | 函数示例 |
|------|---------|
| 趋势指标 | `getIndicatorTaSma`, `getIndicatorTaEma`, `getIndicatorTaMacd` |
| 动量指标 | `getIndicatorTaRsi`, `getIndicatorTaKdj`, `getIndicatorTaCci` |
| 波动率指标 | `getIndicatorTaBbands`, `getIndicatorTaAtr` |
| K 线形态 | `getIndicatorTaCdlEngulfing`, `getIndicatorTaCdlDoji` 等 60+ 个 |

### 7. 资金流向

| 接口函数 | 说明 |
|---------|------|
| `getIndicatorMoney` | 资金情况 |
| `getHSGTMoney` | 沪深港通资金流向 |
| `getHSGTStockRank` | 北上资金持股榜 |
| `getRzRjMarket` | 融资融券市场数据 |

### 8. 龙虎榜/机构调研

| 接口函数 | 说明 |
|---------|------|
| `getLonghbDetail` | 龙虎榜详情 |
| `getLonghbActive` | 活跃营业部 |
| `getLonghbJigou` | 机构专用 |
| `getJiGouDiaoYanXiangXi` | 机构调研详情 |

### 9. 财务报表

| 接口函数 | 说明 |
|---------|------|
| `getReportYugao` | 业绩预告 |
| `getReportKuaiBao` | 业绩快报 |
| `getReportNianBao` | 年报 |
| `getFinanceHSDebt` | 沪深负债表 |

## 通用参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码，支持批量（逗号分隔，最多 50 个） |
| startDate | str | 开始日期（YYYY-MM-DD） |
| endDate | str | 结束日期（YYYY-MM-DD） |
| fields | str | 数据字段，多个用逗号分隔，all 表示全部 |
| export | int | 导出类型：0|Txt; 1|Json; 2|Txt 文件; 3|Json 文件; 4|Csv; 5|DataFrame |
| token | str | API 令牌（必需） |
| filter | str | 过滤参数，如 `filter=open>=15` |
| method | str | 请求方法：get/post |

## 股票代码类型

| flags | 类型 |
|-------|------|
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

| ktype | 类型 |
|-------|------|
| 101 | 日线 |
| 102 | 周线 |
| 103 | 月线 |

## 复权类型

| fq | 类型 |
|----|------|
| 0 | 不复权 |
| 1 | 前复权 |
| 2 | 后复权 |

## Python 使用示例

### 获取股票列表
```python
from waizao.api_demo import stock_api

data = stock_api.getStockType(
    flags=1,  # 上证 A 股
    fields="code,name",
    export=5,  # DataFrame
    token="your_token",
    filter=""
)
print(data)
```

### 获取日线数据
```python
data = stock_api.getStockHSADayKLine(
    code="600004",
    ktype=101,  # 日线
    fq=0,  # 不复权
    startDate="2024-01-01",
    endDate="2024-01-10",
    fields="all",
    export=5,
    token="your_token",
    filter=""
)
print(data)
```

### 获取涨停池
```python
data = stock_api.getPoolZT(
    startDate="2024-01-15",
    endDate="2024-01-15",
    fields="all",
    export=5,
    token="your_token",
    filter=""
)
print(data)
```

### 获取 MACD 指标
```python
data = stock_api.getIndicatorTaMacd(
    code="600004",
    startDate="2024-01-01",
    endDate="2024-01-10",
    fields="all",
    export=5,
    token="your_token",
    filter=""
)
print(data)
```

## 注意事项

1. **Token 安全**：不要将 Token 提交到代码仓库
2. **请求频率**：注意 API 调用频率限制
3. **数据范围**：部分数据可能有延迟
4. **批量查询**：code 参数最多支持 50 个股票代码
5. **日期格式**：必须使用 YYYY-MM-DD 格式

## 常见问题

### Token 无效
确保从官网正确获取 Token 并设置到环境变量

### 数据为空
- 检查日期范围是否为交易日
- 检查股票代码是否正确
- 检查 Token 是否有效

### 导入错误
```bash
pip install waizao pandas requests -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

