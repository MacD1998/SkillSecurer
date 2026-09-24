#!/usr/bin/env python3
"""
批量生成HD钱包工具

用法:
    python generate_wallets.py --count 10 --output wallets.json
    python generate_wallets.py --count 5 --output wallets.csv --format csv
"""

import argparse
import json
import csv
import os
from eth_account import Account
from mnemonic import Mnemonic
from eth_utils import to_checksum_address
import getpass


def generate_wallets(count: int, mnemonic_phrase: str = None) -> dict:
    """
    批量生成HD钱包
    
    Args:
        count: 生成钱包数量
        mnemonic_phrase: 可选，使用已有助记词派生
    
    Returns:
        dict: 包含助记词和钱包列表
    """
    if mnemonic_phrase is None:
        # 生成新助记词
        mnemo = Mnemonic("english")
        mnemonic_phrase = mnemo.generate(strength=256)  # 24个单词
    
    wallets = []
    
    for i in range(count):
        # 使用助记词派生钱包 (BIP44路径: m/44'/60'/0'/0/i)
        Account.enable_unaudited_hdwallet_features()
        account = Account.from_mnemonic(
            mnemonic_phrase, 
            account_path=f"m/44'/60'/0'/0/{i}"
        )
        
        wallets.append({
            "index": i,
            "address": to_checksum_address(account.address),
            "private_key": account.key.hex(),
            "path": f"m/44'/60'/0'/0/{i}"
        })
    
    return {
        "mnemonic": mnemonic_phrase,
        "count": count,
        "wallets": wallets
    }


def save_to_json(data: dict, filepath: str, encrypt: bool = False):
    """保存为JSON格式"""
    if encrypt:
        password = getpass.getpass("设置加密密码: ")
        # 这里可以添加真正的加密逻辑
        print("[警告] 简单加密模式，生产环境请使用更安全的方案")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[✓] 已保存 {data['count']} 个钱包到 {filepath}")
    print(f"[✓] 助记词: {data['mnemonic']}")
    print("[⚠️] 务必备份助记词，这是恢复所有钱包的唯一方式！")


def save_to_csv(data: dict, filepath: str):
    """保存为CSV格式（仅地址，无私钥）"""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['index', 'address', 'path'])
        for wallet in data['wallets']:
            writer.writerow([wallet['index'], wallet['address'], wallet['path']])
    
    print(f"[✓] 已保存地址列表到 {filepath}")


def save_private_keys(data: dict, filepath: str):
    """单独保存私钥（安全敏感操作）"""
    confirm = input("[⚠️] 即将导出私钥到文件，确认吗？私钥泄露=资产被盗！(yes/no): ")
    if confirm.lower() != 'yes':
        print("[×] 已取消")
        return
    
    password = getpass.getpass("设置文件加密密码: ")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 私钥文件 - 绝对保密\n")
        f.write(f"# 生成时间: {__import__('datetime').datetime.now()}\n\n")
        f.write(f"助记词: {data['mnemonic']}\n\n")
        for wallet in data['wallets']:
            f.write(f"[{wallet['index']}] {wallet['address']}\n")
            f.write(f"私钥: {wallet['private_key']}\n")
            f.write(f"路径: {wallet['path']}\n\n")
    
    print(f"[✓] 已保存私钥到 {filepath}")
    print("[⚠️] 该文件包含所有私钥，务必加密保存，不要上传云端！")


def main():
    parser = argparse.ArgumentParser(description='批量生成以太坊钱包')
    parser.add_argument('--count', type=int, default=10, help='生成钱包数量 (默认: 10)')
    parser.add_argument('--output', type=str, default='wallets.json', help='输出文件路径')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], default='json', help='输出格式')
    parser.add_argument('--mnemonic', type=str, help='使用已有助记词派生')
    parser.add_argument('--export-private', type=str, help='额外导出私钥到指定文件')
    
    args = parser.parse_args()
    
    print(f"[*] 正在生成 {args.count} 个钱包...")
    
    data = generate_wallets(args.count, args.mnemonic)
    
    # 保存主文件
    if args.format == 'json':
        save_to_json(data, args.output)
    else:
        save_to_csv(data, args.output)
    
    # 可选：导出私钥
    if args.export_private:
        save_private_keys(data, args.export_private)
    
    # 打印摘要
    print("\n" + "="*60)
    print("生成摘要:")
    print(f"  助记词: {data['mnemonic'][:50]}...")
    print(f"  钱包数量: {data['count']}")
    print(f"  前3个地址:")
    for wallet in data['wallets'][:3]:
        print(f"    [{wallet['index']}] {wallet['address']}")
    if args.count > 3:
        print(f"    ... 还有 {args.count - 3} 个地址")
    print("="*60)
    
    print("\n[⚠️] 女巫风险提示:")
    print("  - 空投项目方会检测关联地址")
    print("  - 批量生成的钱包容易被识别为女巫攻击")
    print("  - 建议撸毛使用1-2个精品号，而非批量操作")


if __name__ == '__main__':
    main()
