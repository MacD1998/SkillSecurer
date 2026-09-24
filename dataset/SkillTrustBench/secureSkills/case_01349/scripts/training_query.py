#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
民兵军事训练查询脚本

功能：
1. 按模块查询训练内容
2. 按级别提供训练指导
3. 相关训练推荐

用法：
    python training_query.py --module air-defense --topic "防原子" --level basic
"""

import argparse
import json
import sys

# 训练模块数据库
TRAINING_MODULES = {
    "air-defense": {
        "name": "防空防原子防化学",
        "topics": ["空袭警报", "疏散隐蔽", "防原子", "防化学", "防护器材使用"],
        "reference": "air-defense.md"
    },
    "shooting": {
        "name": "射击训练",
        "topics": ["武器构造", "武器保养", "射击动作", "瞄准击发", "刺杀", "手榴弹", "地雷"],
        "reference": "shooting.md"
    },
    "combat": {
        "name": "战斗动作",
        "topics": ["地形利用", "方位判定", "距离测量", "观察目标", "信号暗号", "夜间行动", "进攻战斗", "防御战斗", "小组战术"],
        "reference": "combat.md"
    },
    "combat-service": {
        "name": "战斗勤务",
        "topics": ["侦察", "警戒", "观察", "行军", "宿营"],
        "reference": "combat-service.md"
    }
}

# 训练级别
LEVELS = {
    "basic": {
        "name": "初级",
        "description": "适合新兵，提供基础知识和基本技能"
    },
    "intermediate": {
        "name": "中级",
        "description": "适合有基础者，提供进阶技巧和综合训练"
    },
    "advanced": {
        "name": "高级",
        "description": "适合骨干，提供专业训练和组织方法"
    }
}


def query_training(module, topic, level="basic"):
    """查询训练内容"""
    result = {
        "输入参数": {
            "模块": module,
            "主题": topic,
            "级别": level
        },
        "查询结果": {
            "模块名称": "",
            "主题列表": [],
            "参考文件": "",
            "训练建议": []
        }
    }
    
    if module in TRAINING_MODULES:
        module_info = TRAINING_MODULES[module]
        result["查询结果"]["模块名称"] = module_info["name"]
        result["查询结果"]["主题列表"] = module_info["topics"]
        result["查询结果"]["参考文件"] = module_info["reference"]
        
        if level in LEVELS:
            result["查询结果"]["训练建议"] = [
                f"建议从{LEVELS[level]['name']}开始训练",
                LEVELS[level]["description"],
                "详细内容请参考对应的参考文件"
            ]
    else:
        result["查询结果"]["训练建议"] = [
            f"未找到模块: {module}",
            "可用模块: " + ", ".join(TRAINING_MODULES.keys())
        ]
    
    return result


def list_modules():
    """列出所有训练模块"""
    result = {
        "训练模块列表": []
    }
    
    for key, info in TRAINING_MODULES.items():
        result["训练模块列表"].append({
            "代码": key,
            "名称": info["name"],
            "主题数量": len(info["topics"]),
            "参考文件": info["reference"]
        })
    
    return result


def main():
    parser = argparse.ArgumentParser(description="民兵军事训练查询工具")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 查询命令
    query_parser = subparsers.add_parser("query", help="查询训练内容")
    query_parser.add_argument("--module", required=True, help="训练模块")
    query_parser.add_argument("--topic", help="具体主题")
    query_parser.add_argument("--level", choices=["basic", "intermediate", "advanced"], 
                             default="basic", help="训练级别")
    
    # 列表命令
    list_parser = subparsers.add_parser("list", help="列出训练模块")
    
    args = parser.parse_args()
    
    if args.command == "query":
        result = query_training(args.module, args.topic, args.level)
    elif args.command == "list":
        result = list_modules()
    else:
        parser.print_help()
        return
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
