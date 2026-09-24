#!/usr/bin/env python3
"""
DEX交易工具 - 接入Uniswap等DEX进行自动化交易

用法:
    # ETH -> USDC 交易
    python dex_trader.py --wallet-key 私钥 --token-in WETH --token-out USDC --amount 0.1
    
    # 指定DEX和滑点
    python dex_trader.py --wallet-key 私钥 --token-in USDC --token-out WETH --amount 100 --dex uniswap_v3 --slippage 1.0
"""

import argparse
import json
from web3 import Web3
from eth_account import Account
from typing import Dict, Optional
from decimal import Decimal

# Uniswap V2 Router ABI (简化版)
UNISWAP_V2_ROUTER_ABI = json.loads('''[
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}
]''')

# ERC20 Token ABI (简化版)
ERC20_ABI = json.loads('''[
    {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}
]''')

# 常见代币地址 (Ethereum Mainnet)
TOKENS = {
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDC': '0xA0b86a33E6441E6C7D3D4B4f6c7D8e9f0a1b2c3d',  # 示例地址，请替换
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
}

# DEX Router地址
DEX_ROUTERS = {
    'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
    'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
}


class DEXTrader:
    """DEX交易器"""
    
    def __init__(self, w3: Web3, dex_name: str = 'uniswap_v2'):
        self.w3 = w3
        self.dex_name = dex_name
        self.router_address = w3.to_checksum_address(DEX_ROUTERS.get(dex_name, DEX_ROUTERS['uniswap_v2']))
        self.router = w3.eth.contract(address=self.router_address, abi=UNISWAP_V2_ROUTER_ABI)
    
    def get_token_address(self, symbol: str) -> str:
        """获取代币地址"""
        symbol = symbol.upper()
        if symbol in TOKENS:
            return self.w3.to_checksum_address(TOKENS[symbol])
        # 如果输入的是地址，直接返回
        if self.w3.is_address(symbol):
            return self.w3.to_checksum_address(symbol)
        raise ValueError(f"未知代币: {symbol}")
    
    def get_token_info(self, token_address: str) -> Dict:
        """获取代币信息"""
        token = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        return {
            'symbol': token.functions.symbol().call(),
            'decimals': token.functions.decimals().call(),
            'address': token_address
        }
    
    def get_amounts_out(self, amount_in: int, path: list) -> int:
        """获取预期输出金额"""
        amounts = self.router.functions.getAmountsOut(amount_in, path).call()
        return amounts[-1]
    
    def approve_token(self, token_address: str, spender: str, amount: int, account) -> str:
        """授权代币"""
        token = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # 检查当前授权
        current_allowance = token.functions.allowance(account.address, spender).call()
        if current_allowance >= amount:
            return None  # 已授权足够金额
        
        # 发送授权交易
        tx = token.functions.approve(spender, amount).build_transaction({
            'from': account.address,
            'nonce': self.w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return tx_hash.hex() if receipt.status == 1 else None
    
    def swap_exact_eth_for_tokens(self, amount_in_eth: float, token_out: str, 
                                   account, slippage: float = 0.5) -> Dict:
        """
        ETH -> Token 交易
        
        Args:
            amount_in_eth: 输入ETH数量
            token_out: 输出代币符号或地址
            account: 交易账户
            slippage: 滑点容忍度(%)
        """
        try:
            token_out_address = self.get_token_address(token_out)
            amount_in_wei = self.w3.to_wei(amount_in_eth, 'ether')
            
            # 获取预期输出
            path = [self.get_token_address('WETH'), token_out_address]
            expected_out = self.get_amounts_out(amount_in_wei, path)
            min_out = int(expected_out * (1 - slippage / 100))
            
            # 构建交易
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 300  # 5分钟
            
            tx = self.router.functions.swapExactETHForTokens(
                min_out,
                path,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'value': amount_in_wei,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # 签名并发送
            signed_tx = self.w3.eth.account.sign_transaction(tx, account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                'success': receipt.status == 1,
                'tx_hash': tx_hash.hex(),
                'amount_in': amount_in_eth,
                'token_out': token_out,
                'expected_out': expected_out,
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def swap_exact_tokens_for_eth(self, token_in: str, amount_in: float, 
                                   account, slippage: float = 0.5) -> Dict:
        """
        Token -> ETH 交易
        
        Args:
            token_in: 输入代币符号或地址
            amount_in: 输入代币数量
            account: 交易账户
            slippage: 滑点容忍度(%)
        """
        try:
            token_in_address = self.get_token_address(token_in)
            token_info = self.get_token_info(token_in_address)
            
            amount_in_wei = int(amount_in * (10 ** token_info['decimals']))
            
            # 授权代币
            print(f"[*] 授权 {token_in}...")
            approve_tx = self.approve_token(token_in_address, self.router_address, amount_in_wei, account)
            if approve_tx:
                print(f"  [✓] 授权交易: {approve_tx[:40]}...")
            
            # 获取预期输出
            path = [token_in_address, self.get_token_address('WETH')]
            expected_out = self.get_amounts_out(amount_in_wei, path)
            min_out = int(expected_out * (1 - slippage / 100))
            
            # 构建交易
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 300
            
            tx = self.router.functions.swapExactTokensForETH(
                amount_in_wei,
                min_out,
                path,
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                'success': receipt.status == 1,
                'tx_hash': tx_hash.hex(),
                'token_in': token_in,
                'amount_in': amount_in,
                'expected_out_eth': self.w3.from_wei(expected_out, 'ether'),
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='DEX交易工具')
    parser.add_argument('--wallet-key', type=str, required=True, help='钱包私钥')
    parser.add_argument('--token-in', type=str, required=True, help='输入代币 (ETH, USDC, 或地址)')
    parser.add_argument('--token-out', type=str, required=True, help='输出代币 (ETH, USDC, 或地址)')
    parser.add_argument('--amount', type=float, required=True, help='交易数量')
    parser.add_argument('--dex', type=str, default='uniswap_v2', choices=['uniswap_v2', 'sushiswap'], help='DEX选择')
    parser.add_argument('--slippage', type=float, default=0.5, help='滑点容忍度(%)')
    parser.add_argument('--rpc', type=str, default='https://eth.llamarpc.com', help='RPC节点')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    
    args = parser.parse_args()
    
    # 初始化
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    if not w3.is_connected():
        print("[×] 无法连接到RPC节点")
        return
    
    account = Account.from_key(args.wallet_key)
    print(f"[*] 交易钱包: {account.address}")
    print(f"[*] DEX: {args.dex}")
    print(f"[*] 交易: {args.amount} {args.token_in} -> {args.token_out}")
    print(f"[*] 滑点容忍: {args.slippage}%")
    
    if args.dry_run:
        print("\n[*] 模拟运行模式")
        return
    
    # 确认
    confirm = input(f"\n[⚠️] 确认执行交易? (yes/no): ")
    if confirm.lower() != 'yes':
        print("[×] 已取消")
        return
    
    # 执行交易
    trader = DEXTrader(w3, args.dex)
    
    token_in = args.token_in.upper()
    token_out = args.token_out.upper()
    
    if token_in == 'ETH':
        # ETH -> Token
        result = trader.swap_exact_eth_for_tokens(args.amount, token_out, account, args.slippage)
    elif token_out == 'ETH':
        # Token -> ETH
        result = trader.swap_exact_tokens_for_eth(token_in, args.amount, account, args.slippage)
    else:
        print("[×] Token -> Token 交易暂未实现，请先兑换为ETH")
        return
    
    # 输出结果
    if result['success']:
        print(f"\n[✓] 交易成功!")
        print(f"  交易哈希: {result['tx_hash']}")
        print(f"  Gas使用: {result['gas_used']}")
    else:
        print(f"\n[×] 交易失败: {result.get('error', 'Unknown')}")


if __name__ == '__main__':
    main()
