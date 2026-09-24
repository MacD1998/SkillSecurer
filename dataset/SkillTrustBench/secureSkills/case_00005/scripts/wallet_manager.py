#!/usr/bin/env python3
"""
钱包管理CLI工具 - 综合管理多个钱包

用法:
    # 查看钱包列表和余额
    python wallet_manager.py --file wallets.json --rpc https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY balance
    
    # 导出地址列表
    python wallet_manager.py --file wallets.json export --format csv --output addresses.csv
    
    # 批量查询交易记录
    python wallet_manager.py --file wallets.json --rpc RPC_URL txs
"""

import argparse
import json
import csv
from web3 import Web3
from typing import List, Dict


def load_wallets(filepath: str) -> List[Dict]:
    """加载钱包文件"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    wallets = data.get('wallets', [])
    return wallets


def check_balances(w3: Web3, wallets: List[Dict]) -> List[Dict]:
    """查询所有钱包余额"""
    results = []
    total_eth = 0
    
    print(f"[*] 查询 {len(wallets)} 个钱包余额...")
    print("-" * 70)
    print(f"{'Index':<6} {'Address':<42} {'Balance (ETH)':<15}")
    print("-" * 70)
    
    for wallet in wallets:
        address = wallet['address']
        try:
            balance_wei = w3.eth.get_balance(address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            total_eth += balance_eth
            
            print(f"{wallet['index']:<6} {address:<42} {balance_eth:<15.6f}")
            
            results.append({
                'index': wallet['index'],
                'address': address,
                'balance_wei': balance_wei,
                'balance_eth': balance_eth
            })
        except Exception as e:
            print(f"{wallet['index']:<6} {address:<42} {'Error':<15}")
            results.append({
                'index': wallet['index'],
                'address': address,
                'error': str(e)
            })
    
    print("-" * 70)
    print(f"总计: {total_eth:.6f} ETH")
    print(f"平均: {total_eth / len(wallets):.6f} ETH/钱包")
    
    return results


def export_addresses(wallets: List[Dict], output_path: str, format_type: str):
    """导出地址列表"""
    if format_type == 'csv':
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'address', 'path'])
            for wallet in wallets:
                writer.writerow([wallet['index'], wallet['address'], wallet.get('path', '')])
    elif format_type == 'txt':
        with open(output_path, 'w') as f:
            for wallet in wallets:
                f.write(f"{wallet['address']}\n")
    elif format_type == 'json':
        addresses = [{'index': w['index'], 'address': w['address']} for w in wallets]
        with open(output_path, 'w') as f:
            json.dump(addresses, f, indent=2)
    
    print(f"[✓] 已导出 {len(wallets)} 个地址到 {output_path}")


def estimate_gas_cost(w3: Web3, wallets_count: int, tx_per_wallet: int = 2) -> Dict:
    """估算Gas成本"""
    gas_price = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
    
    # 估算每笔交易Gas
    eth_transfer_gas = 21000
    token_transfer_gas = 65000
    swap_gas = 200000
    
    # 计算总成本
    total_gas = wallets_count * tx_per_wallet * (eth_transfer_gas + token_transfer_gas + swap_gas)
    total_cost_eth = w3.from_wei(total_gas * gas_price, 'ether')
    
    return {
        'wallets_count': wallets_count,
        'tx_per_wallet': tx_per_wallet,
        'gas_price_gwei': gas_price_gwei,
        'total_gas_units': total_gas,
        'estimated_cost_eth': total_cost_eth
    }


def show_summary(wallets: List[Dict]):
    """显示钱包摘要"""
    print("=" * 60)
    print("钱包摘要")
    print("=" * 60)
    print(f"总钱包数: {len(wallets)}")
    print(f"助记词: {wallets[0].get('mnemonic', 'N/A')[:50]}...")
    print(f"\n前5个地址:")
    for wallet in wallets[:5]:
        print(f"  [{wallet['index']}] {wallet['address']}")
    if len(wallets) > 5:
        print(f"  ... 还有 {len(wallets) - 5} 个地址")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='钱包管理CLI')
    parser.add_argument('--file', type=str, default='wallets.json', help='钱包JSON文件')
    parser.add_argument('--rpc', type=str, default='https://eth.llamarpc.com', help='RPC节点')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # balance 命令
    balance_parser = subparsers.add_parser('balance', help='查询余额')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出地址')
    export_parser.add_argument('--format', type=str, choices=['csv', 'txt', 'json'], default='csv')
    export_parser.add_argument('--output', type=str, default='addresses.csv')
    
    # summary 命令
    summary_parser = subparsers.add_parser('summary', help='显示摘要')
    
    # estimate 命令
    estimate_parser = subparsers.add_parser('estimate', help='估算Gas成本')
    estimate_parser.add_argument('--tx-count', type=int, default=2, help='每个钱包交易数')
    
    args = parser.parse_args()
    
    # 加载钱包
    try:
        wallets = load_wallets(args.file)
        print(f"[*] 已加载 {len(wallets)} 个钱包")
    except Exception as e:
        print(f"[×] 无法加载钱包文件: {e}")
        return
    
    if args.command == 'balance':
        w3 = Web3(Web3.HTTPProvider(args.rpc))
        if not w3.is_connected():
            print("[×] 无法连接到RPC节点")
            return
        check_balances(w3, wallets)
    
    elif args.command == 'export':
        export_addresses(wallets, args.output, args.format)
    
    elif args.command == 'summary':
        show_summary(wallets)
    
    elif args.command == 'estimate':
        w3 = Web3(Web3.HTTPProvider(args.rpc))
        if not w3.is_connected():
            print("[×] 无法连接到RPC节点")
            return
        result = estimate_gas_cost(w3, len(wallets), args.tx_count)
        print(f"\nGas成本估算:")
        print(f"  钱包数量: {result['wallets_count']}")
        print(f"  每钱包交易: {result['tx_per_wallet']}")
        print(f"  Gas价格: {result['gas_price_gwei']:.2f} Gwei")
        print(f"  预估总Gas: {result['total_gas_units']:,} units")
        print(f"  预估总成本: {result['estimated_cost_eth']:.6f} ETH")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
