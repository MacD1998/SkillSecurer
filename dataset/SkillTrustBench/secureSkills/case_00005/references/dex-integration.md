# DEX集成指南

## 支持的DEX

| DEX | 版本 | Router地址 | 支持网络 |
|-----|------|------------|----------|
| Uniswap | V2 | 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D | Ethereum |
| Uniswap | V3 | 0xE592427A0AEce92De3Edee1F18E0157C05861564 | Ethereum |
| SushiSwap | V2 | 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F | Ethereum |
| PancakeSwap | V2 | 0x10ED43C718714eb63d5aA57B78B54704E256024E | BSC |

## 常见代币地址

### Ethereum Mainnet
```python
TOKENS = {
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDC': '0xA0b86a33E6441E6C7D3D4B4f6c7D8e9f0a1b2c3d',  # 请验证
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
}
```

### 如何获取代币地址
1. CoinGecko: https://www.coingecko.com/
2. Etherscan: https://etherscan.io/
3. 项目官方文档

**注意**：务必验证地址正确性，假币合约很多！

## 交易类型

### 1. ETH → Token (swapExactETHForTokens)
```python
# 用ETH购买代币
result = trader.swap_exact_eth_for_tokens(
    amount_in_eth=0.1,        # 输入0.1 ETH
    token_out='USDC',         # 输出USDC
    account=wallet,           # 钱包
    slippage=0.5              # 0.5%滑点
)
```

### 2. Token → ETH (swapExactTokensForETH)
```python
# 卖出代币换取ETH
result = trader.swap_exact_tokens_for_eth(
    token_in='USDC',          # 输入USDC
    amount_in=100,            # 100 USDC
    account=wallet,           # 钱包
    slippage=0.5              # 0.5%滑点
)
```

### 3. Token → Token (swapExactTokensForTokens)
需要先用Router合约的swapExactTokensForTokens函数，参考Uniswap文档。

## 滑点设置

| 市场状态 | 建议滑点 | 说明 |
|----------|----------|------|
| 正常 | 0.5% | 低滑点，更优价格 |
| 波动大 | 1-2% | 避免交易失败 |
| 新币/低流动性 | 5-10% | 避免被夹子攻击 |

## Gas优化

### 自动Gas价格
```python
gas_price = w3.eth.gas_price  # 使用网络建议价格
```

### 加速交易
```python
# 使用比建议高10-20%的价格
gas_price = int(w3.eth.gas_price * 1.2)
```

### Gas限制
- ETH转账: 21,000
- Token转账: 65,000
- Swap交易: 150,000-200,000
- 复杂合约: 300,000+

## 错误处理

### 常见错误

#### INSUFFICIENT_OUTPUT_AMOUNT
**原因**：滑点设置过低，实际输出低于最小预期
**解决**：增加slippage参数

#### TRANSFER_FROM_FAILED
**原因**：代币授权不足或未授权
**解决**：先执行approve

#### INSUFFICIENT_FUNDS
**原因**：ETH余额不足以支付Gas费
**解决**：确保有足够ETH

#### EXPIRED
**原因**：交易超时（超过deadline）
**解决**：重新提交交易

## 测试网练习

### Sepolia测试网
```python
RPC = "https://rpc.sepolia.org"
DEX = "Uniswap V2 on Sepolia"
```

### 获取测试币
- Sepolia ETH: https://sepoliafaucet.com/
- 测试网代币：使用水龙头或自己部署

## 高级功能

### 限价单（通过监控实现）
```python
# 持续监控价格，达到目标时自动交易
while True:
    price = get_token_price('USDC')
    if price >= target_price:
        execute_swap()
        break
    time.sleep(60)
```

### 多DEX比价
```python
# 比较多个DEX的价格，选择最优
uniswap_price = get_price_uniswap(amount)
sushiswap_price = get_price_sushiswap(amount)
best_dex = 'uniswap' if uniswap_price > sushiswap_price else 'sushiswap'
```

### MEV保护
- 使用Flashbots RPC避免抢跑
- 设置合理的滑点防止夹子攻击
- 大额交易拆分成多笔

## 安全提醒

1. **验证合约地址**：假币合约很多
2. **检查授权**：定期使用revoke.cash检查
3. **小额测试**：新合约先用小额测试
4. **Gas预留**：确保有足够ETH支付Gas
5. **私钥安全**：不要硬编码，使用环境变量

## 参考资源

- [Uniswap V2 文档](https://docs.uniswap.org/contracts/v2/overview)
- [Uniswap V3 文档](https://docs.uniswap.org/contracts/v3/overview)
- [Ethereum ABI 规范](https://docs.soliditylang.org/en/latest/abi-spec.html)
- [Web3.py 文档](https://web3py.readthedocs.io/)
