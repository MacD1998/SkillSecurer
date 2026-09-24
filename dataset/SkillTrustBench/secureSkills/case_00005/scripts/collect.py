#!/usr/bin/env python3
"""
资金归集工具 - 将多个子钱包的资金归集到主钱包

用法:
    python collect.py --to-key 主钱包私钥 --from-file wallets.json --min-balance 0.001 --rpc https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
    python collect.py --to-address 0x... --from-keys key1,key2,key3 --keep-gas 0.01
"""

import argparse
import json
import time
from web3 import Web3
from eth_account import Account
from typing import List, Dict


def load_private_keys(filepath: str) -> List[Dict]:
    """从文件加载私钥列表"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if 'wallets' in data:
        return [{'address': w['address'], 'private_key': w['private_key']} for w in data['wallets']]
    else:
        return data


def collect_from_wallet(w3: Web3, from_key: str, to_address: str, keep_eth: float = 0.005) -> Dict:
    """
    从单个钱包归集资金
    
    Args:
        w3: Web3实例
        from_key: 源钱包私钥
        to_address: 目标地址
        keep_eth: 保留的ETH金额（作为Gas费）
    
    Returns:
        dict: 交易结果
    """
    try:
        from_account = Account.from_key(from_key)
        from_address = from_account.address
        
        # 查询余额
        balance = w3.eth.get_balance(from_address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        if balance == 0:
            return {
                'success': False,
                'from': from_address,
                'error': '余额为0',
                'balance': 0
            }
        
        # 计算可发送金额（余额 - Gas费 - 保留金额）
        gas_limit = 21000
        gas_price = w3.eth.gas_price
        gas_cost = gas_limit * gas_price
        keep_wei = w3.to_wei(keep_eth, 'ether')
        
        send_amount = balance - gas_cost - keep_wei
        
        if send_amount <= 0:
            return {
                'success': False,
                'from': from_address,
                'error': f'余额不足以支付Gas费 (余额: {balance_eth} ETH)',
                'balance': balance_eth
            }
        
        # 构建交易
        nonce = w3.eth.get_transaction_count(from_address)
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': send_amount,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': w3.eth.chain_id
        }
        
        # 签名并发送
        signed_tx = w3.eth.account.sign_transaction(tx, from_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # 等待确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            'success': receipt.status == 1,
            'from': from_address,
            'to': to_address,
            'amount': w3.from_wei(send_amount, 'ether'),
            'tx_hash': tx_hash.hex(),
            'balance_before': balance_eth,
            'gas_used': receipt.gasUsed,
            'block_number': receipt.blockNumber
        }
        
    except Exception as e:
        return {
            'success': False,
            'from': Account.from_key(from_key).address if from_key else 'unknown',
            'error': str(e)
        }


def collect_all(w3: Web3, wallets: List[Dict], to_address: str, 
                keep_eth: float = 0.005, delay_sec: float = 1.0,
                min_balance: float = 0.0) -> List[Dict]:
    """
    批量归集资金
    
    Args:
        w3: Web3实例
        wallets: 源钱包列表 [{'address': ..., 'private_key': ...}]
        to_address: 目标地址
        keep_eth: 每个钱包保留金额
        delay_sec: 交易间隔
        min_balance: 最小归集余额（低于此值的跳过）
    
    Returns:
        list: 每笔交易的结果
    """
    print(f"[*] 目标地址: {to_address}")
    print(f"[*] 源钱包数量: {len(wallets)}")
    print(f"[*] 最小归集余额: {min_balance} ETH")
    print(f"[*] 保留Gas费: {keep_eth} ETH/钱包")
    print()
    
    results = []
    total_collected = 0
    
    for i, wallet in enumerate(wallets):
        address = wallet['address']
        private_key = wallet['private_key']
        
        # 检查余额
        balance = w3.from_wei(w3.eth.get_balance(address), 'ether')
        
        print(f"[{i+1}/{len(wallets)}] {address[:20]}... 余额: {balance:.6f} ETH", end='')
        
        if balance < min_balance:
            print(f" - 跳过 (低于最小值)")
            results.append({
                'success': False,
                'from': address,
                'error': f'余额 {balance} ETH 低于最小值 {min_balance} ETH',
                'balance': balance
            })
            continue
        
        print(f" - 归集中...")
        result = collect_from_wallet(w3, private_key, to_address, keep_eth)
        results.append(result)
        
        if result['success']:
            total_collected += result['amount']
            print(f"  [✓] 成功! 归集 {result['amount']:.6f} ETH")
            print(f"      TX: {result['tx_hash'][:40]}...")
        else:
            print(f"  [×] 失败: {result.get('error', 'Unknown')}")
        
        if i < len(wallets) - 1 and delay_sec > 0:
            time.sleep(delay_sec)
    
    print(f"\n[*] 总计归集: {total_collected:.6f} ETH")
    return results


def main():
    parser = argparse.ArgumentParser(description='资金归集工具')
    parser.add_argument('--to-key', type=str, help='主钱包私钥(用于获取地址)')
    parser.add_argument('--to-address', type=str, help='主钱包地址')
    parser.add_argument('--from-file', type=str, help='源钱包JSON文件(包含私钥)')
    parser.add_argument('--from-keys', type=str, help='源钱包私钥列表,逗号分隔')
    parser.add_argument('--rpc', type=str, default='https://eth.llamarpc.com', help='RPC节点URL')
    parser.add_argument('--keep-gas', type=float, default=0.005, help='每个钱包保留的ETH(默认0.005)')
    parser.add_argument('--min-balance', type=float, default=0.001, help='最小归集余额(默认0.001)')
    parser.add_argument('--delay', type=float, default=2.0, help='交易间隔(秒)')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    
    args = parser.parse_args()
    
    # 初始化Web3
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    if not w3.is_connected():
        print("[×] 无法连接到RPC节点")
        return
    
    print(f"[*] 已连接到网络: ChainID {w3.eth.chain_id}")
    
    # 确定目标地址
    if args.to_key:
        to_address = Account.from_key(args.to_key).address
    elif args.to_address:
        to_address = w3.to_checksum_address(args.to_address)
    else:
        print("[×] 请提供 --to-key 或 --to-address")
        return
    
    # 加载源钱包
    if args.from_file:
        wallets = load_private_keys(args.from_file)
    elif args.from_keys:
        keys = [k.strip() for k in args.from_keys.split(',')]
        wallets = [{'address': Account.from_key(k).address, 'private_key': k} for k in keys]
    else:
        print("[×] 请提供 --from-file 或 --from-keys")
        return
    
    if args.dry_run:
        print("\n[*] 模拟运行模式")
        print(f"[*] 将从 {len(wallets)} 个钱包归集资金到 {to_address}")
        for wallet in wallets:
            balance = w3.from_wei(w3.eth.get_balance(wallet['address']), 'ether')
            if balance >= args.min_balance:
                print(f"  {wallet['address'][:20]}... 余额: {balance:.6f} ETH - 将归集")
        return
    
    # 确认
    confirm = input(f"\n[⚠️] 确认归集 {len(wallets)} 个钱包的资金到 {to_address}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("[×] 已取消")
        return
    
    # 执行归集
    results = collect_all(w3, wallets, to_address, args.keep_gas, args.delay, args.min_balance)
    
    # 汇总
    success_count = sum(1 for r in results if r['success'])
    total_amount = sum(r.get('amount', 0) for r in results if r['success'])
    
    print("\n" + "="*60)
    print("归集完成:")
    print(f"  成功: {success_count}/{len(results)}")
    print(f"  总归集金额: {total_amount:.6f} ETH")
    
    # 保存结果
    output_file = 'collect_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  详细结果已保存到: {output_file}")


if __name__ == '__main__':
    main()
