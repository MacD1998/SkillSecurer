"""
输入解析模块

解析用户指令，识别：
- 组织名
- 个人名
- 生成类型（月报/季报/半年报/年报）
"""

import re
from typing import List, Optional, Dict


def parse_user_input(user_input: str, default_all: bool = True) -> Dict:
    """
    解析用户输入
    
    示例输入：
    - "为产品中心生成四套"
    - "给林刚做季报"
    - "人力资源中心 付忠明 月报和年报"
    - "只做季报"
    
    返回：
    {
        "org_name": str,
        "person_name": Optional[str],
        "template_types": List[str]
    }
    """
    result = {
        "org_name": None,
        "person_name": None,
        "template_types": []
    }
    
    # 1. 识别生成类型
    result["template_types"] = parse_template_types(user_input, default_all=default_all)
    
    # 2. 识别组织名和个人名
    org_name, person_name = parse_org_and_person(user_input)
    result["org_name"] = org_name
    result["person_name"] = person_name
    
    return result


def parse_template_types(user_input: str, default_all: bool = True) -> List[str]:
    """识别生成类型"""

    all_types = ["月报", "季报", "半年报", "年报"]

    # 检查"四套"/"全部"
    if re.search(r"四套|全部|都", user_input):
        return all_types

    # 避免“半年报”被误判为“年报”
    normalized = user_input
    has_half_year = "半年报" in normalized
    if has_half_year:
        normalized = normalized.replace("半年报", "__HALF_YEAR__")

    found_types: List[str] = []
    if "月报" in normalized:
        found_types.append("月报")
    if "季报" in normalized:
        found_types.append("季报")
    if has_half_year:
        found_types.append("半年报")
    if "年报" in normalized:
        found_types.append("年报")

    # 如果没有指定
    if not found_types:
        return all_types if default_all else []

    return found_types


def parse_org_and_person(user_input: str) -> tuple:
    """识别组织名和个人名"""
    
    # 已知组织名列表（可扩展）
    known_orgs = [
        "人力资源中心", "产品中心", "财务中心", "营销中心",
        "研发中心", "运营中心", "战略中心"
    ]
    
    # 已知个人名列表（可扩展）
    known_persons = [
        "付忠明", "林刚", "陈舒婷", "张伟", "李明"
    ]
    
    org_name = None
    person_name = None
    
    # 匹配组织名
    for org in known_orgs:
        if org in user_input:
            org_name = org
            break
    
    # 匹配个人名
    for person in known_persons:
        if person in user_input:
            person_name = person
            break
    
    return org_name, person_name


# 测试用例
if __name__ == "__main__":
    test_cases = [
        "为产品中心生成四套",
        "给林刚做季报",
        "人力资源中心 付忠明 月报和年报",
        "只做季报",
        "把月报和年报给我",
    ]
    
    for tc in test_cases:
        result = parse_user_input(tc)
        print(f"输入: {tc}")
        print(f"  组织: {result['org_name']}")
        print(f"  个人: {result['person_name']}")
        print(f"  类型: {result['template_types']}")
        print()
