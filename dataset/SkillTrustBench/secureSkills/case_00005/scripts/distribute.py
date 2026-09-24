#!/usr/bin/env python3
"""
资金分发工具 - 从主钱包分发资金到多个子钱包

用法:
    python distribute.py --from-key 主钱包私钥 --to-file wallets.json --amount 0.1 --rpc https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
    python distribute.py --from-key 主钱包私钥 --to-addresses addr1,addr2,addr3 --amount 0.05
"""

import argparse
import json
import time
from web3 import Web3
from eth_account import Account
from typing import List, Dict


def load_wallets(filepath: str) -> List[str]:
    """从文件加载目标地址列表"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    addresses = []
    if 'wallets' in data:
        addresses = [w['address'] for w in data['wallets']]
    elif 'addresses' in data:
        addresses = data['addresses']
    else:
        addresses = list(data.values())
    
    return addresses


def send_transaction(w3: Web3, from_account, to_address: str, amount_eth: float, gas_price_gwei: int = None) -> Dict:
    """
    发送ETH转账
    
    Returns:
        dict: 交易结果
    """
    try:
        # 检查余额
        balance = w3.eth.get_balance(from_account.address)
        amount_wei = w3.to_wei(amount_eth, 'ether')
        
        # 估算Gas
        gas_limit = 21000  # 标准ETH转账
        if gas_price_gwei:
            gas_price = w3.to_wei(gas_price_gwei, 'gwei')
        else:
            gas_price = w3.eth.gas_price
        
        gas_cost = gas_limit * gas_price
        total_cost = amount_wei + gas_cost
        
        if balance < total_cost:
            return {
                'success': False,
                'error': f'余额不足. 需要: {w3.from_wei(total_cost, "ether")} ETH, 拥有: {w3.from_wei(balance, "ether")} ETH',
                'to': to_address
            }
        
        # 构建交易
        nonce = w3.eth.get_transaction_count(from_account.address)
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': amount_wei,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': w3.eth.chain_id
        }
        
        # 签名并发送
        signed_tx = w3.eth.account.sign_transaction(tx, from_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # 等待确认
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            'success': receipt.status == 1,
            'tx_hash': tx_hash.hex(),
            'to': to_address,
            'amount': amount_eth,
            'gas_used': receipt.gasUsed,
            'block_number': receipt.blockNumber
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'to': to_address
        }


def distribute_funds(w3: Web3, from_key: str, to_addresses: List[str], amount_eth: float, 
                     delay_sec: float = 1.0, randomize: bool = False) -> List[Dict]:
    """
    批量分发资金
    
    Args:
        w3: Web3实例
        from_key: 发送方私钥
        to_addresses: 接收地址列表
        amount_eth: 每个地址发送金额
        delay_sec: 每笔交易间隔（秒）
        randomize: 是否随机化金额（防女巫）
    
    Returns:
        list: 每笔交易的结果
    """
    from_account = Account.from_key(from_key)
    print(f"[*] 主钱包地址: {from_account.address}")
    print(f"[*] 主钱包余额: {w3.from_wei(w3.eth.get_balance(from_account.address), 'ether')} ETH")
    print(f"[*] 目标: 向 {len(to_addresses)} 个地址各发送 {amount_eth} ETH")
    print(f"[*] 预计总成本: {len(to_addresses) * amount_eth} ETH + Gas费")
    print()
    
    results = []
    
    for i, address in enumerate(to_addresses):
        print(f"[{i+1}/{len(to_addresses)}] 正在发送给 {address[:20]}...")
        
        # 随机化金额（±5%）防女巫检测
        send_amount = amount_eth
        if randomize:
            import random
            variation = random.uniform(-0.05, 0.05)
            send_amount = amount_eth * (1 + variation)
            send_amount = round(send_amount, 6)
        
        result = send_transaction(w3, from_account, address, send_amount)
        results.append(result)
        
        if result['success']:
            print(f"  [✓] 成功! TX: {result['tx_hash'][:30]}...")
        else:
            print(f"  [×] 失败: {result.get('error', 'Unknown')}")
        
        # 延迟，避免被检测为机器人
        if i < len(to_addresses) - 1 and delay_sec > 0:
            time.sleep(delay_sec)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='资金分发工具')
    parser.add_argument('--from-key', type=str, required=True, help='主钱包私钥')
    parser.add_argument('--to-file', type=str, help='目标地址JSON文件')
    parser.add_argument('--to-addresses', type=str, help='目标地址列表,逗号分隔')
    parser.add_argument('--amount', type=float, required=True, help='每个地址发送金额(ETH)')
    parser.add_argument('--rpc', type=str, default='https://eth.llamarpc.com', help='RPC节点URL')
    parser.add_argument('--delay', type=float, default=2.0, help='交易间隔(秒)')
    parser.add_argument('--randomize', action='store_true', help='随机化金额防女巫')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行,不发送交易')
    
    args = parser.parse_args()
    
    # 初始化Web3
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    if not w3.is_connected():
        print("[×] 无法连接到RPC节点")
        return
    
    print(f"[*] 已连接到网络: ChainID {w3.eth.chain_id}")
    
    # 加载目标地址
    if args.to_file:
        to_addresses = load_wallets(args.to_file)
    elif args.to_addresses:
        to_addresses = [addr.strip() for addr in args.to_addresses.split(',')]
    else:
        print("[×] 请提供 --to-file 或 --to-addresses")
        return
    
    # 验证地址格式
    valid_addresses = []
    for addr in to_addresses:
        if w3.is_address(addr):
            valid_addresses.append(w3.to_checksum_address(addr))
        else:
            print(f"[警告] 无效地址: {addr}")
    
    if args.dry_run:
        print("\n[*] 模拟运行模式,不会发送真实交易")
        print(f"[*] 将向 {len(valid_addresses)} 个地址发送 {args.amount} ETH")
        return
    
    # 确认
    confirm = input(f"\n[⚠️] 确认向 {len(valid_addresses)} 个地址发送 {args.amount} ETH? (yes/no): ")
    if confirm.lower() != 'yes':
        print("[×] 已取消")
        return
    
    # 执行分发
    results = distribute_funds(w3, args.from_key, valid_addresses, args.amount, 
                               args.delay, args.randomize)
    
    # 汇总
    success_count = sum(1 for r in results if r['success'])
    print("\n" + "="*60)
    print("分发完成:")
    print(f"  成功: {success_count}/{len(results)}")
    print(f"  失败: {len(results) - success_count}/{len(results)}")
    
    # 保存结果
    output_file = 'distribute_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  详细结果已保存到: {output_file}")


if __name__ == '__main__':
    main()
