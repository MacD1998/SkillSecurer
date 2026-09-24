---
name: crypto-wallet-tools
description: 加密货币钱包批量生成、资金管理和DEX交互工具集。用于批量创建HD钱包、资金分发归集、DEX自动化交易。当用户需要批量生成钱包地址、管理多个钱包资金、接入DEX进行自动化交易时使用。
---

# Crypto Wallet Tools 加密钱包工具集

批量钱包管理、资金分发归集、DEX交互的完整工具集。

## ⚠️ 重要风险提示

### 女巫攻击（Sybil Attack）风险
- 空投项目方有严格的反女巫检测机制
- 批量生成的钱包容易被识别为关联地址
- 可能导致全部地址被封禁，空投归零
- **建议**：撸毛空投使用1-2个精品号，避免批量操作

### 资金安全
- 私钥一旦泄露，资产将被盗取
- 私钥文件务必加密保存，不要上传云端
- 测试时使用小额资金，确认安全后再大额操作

## 核心功能

### 1. 批量生成钱包
- HD钱包派生，一个助记词管理多个地址
- 导出地址和私钥到加密文件
- 支持以太坊及EVM兼容链

### 2. 资金管理
- 资金分发：主钱包→多个子钱包
- 资金归集：多个子钱包→主钱包
- 余额查询和监控

### 3. DEX交互
- Uniswap V2/V3 交易封装
- 自动滑点计算
- 交易确认和失败重试

## 使用场景

| 场景 | 说明 | 风险等级 |
|------|------|----------|
| 测试网开发 | 批量生成测试地址 | 低 |
| 内部资金管理 | 多账户资金归集 | 中 |
| DEX量化交易 | 多账户策略交易 | 中 |
| 空投撸毛 | 批量养号 | **极高** |

## 工具列表

- `generate_wallets.py` - 批量生成HD钱包
- `wallet_manager.py` - 钱包管理CLI（余额查询、导出、估算）
- `distribute.py` - 资金分发到多个子钱包
- `collect.py` - 从多个子钱包归集资金
- `dex_trader.py` - DEX交易接口（Uniswap等）

## 参考资料

- **风控指南**：`references/risk-guide.md` - 女巫攻击风险和反检测策略
- **DEX集成指南**：`references/dex-integration.md` - Uniswap等DEX交互详解

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 生成钱包
```bash
python scripts/generate_wallets.py --count 10 --output wallets.json
```

### 3. 管理钱包
```bash
# 查看余额
python scripts/wallet_manager.py --file wallets.json --rpc RPC_URL balance

# 导出地址
python scripts/wallet_manager.py --file wallets.json export --format csv --output addresses.csv

# 估算Gas成本
python scripts/wallet_manager.py --file wallets.json --rpc RPC_URL estimate
```

### 4. 资金分发
```bash
python scripts/distribute.py --from-key 主钱包私钥 --to-file wallets.json --amount 0.1 --rpc RPC_URL
```

### 5. 资金归集
```bash
python scripts/collect.py --to-key 主钱包私钥 --from-file wallets.json --min-balance 0.001 --rpc RPC_URL
```

### 6. DEX交易
```bash
# ETH -> USDC
python scripts/dex_trader.py --wallet-key 私钥 --token-in ETH --token-out USDC --amount 0.1 --rpc RPC_URL

# USDC -> ETH
python scripts/dex_trader.py --wallet-key 私钥 --token-in USDC --token-out ETH --amount 100 --rpc RPC_URL
```

## 安全建议

1. **私钥管理**：使用.env文件或硬件钱包，不要硬编码
2. **Gas费用**：预留足够ETH作为Gas费
3. **分批操作**：大额资金分多笔转账
4. **测试先行**：主网操作前先在测试网验证
5. **日志记录**：保存所有交易哈希以备查询

---

*工具无罪，使用有责。请遵守当地法律法规，谨慎操作。*
