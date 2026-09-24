#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI旅行助手套装 - 共享工具函数
"""

import json
from typing import Dict, Any
from datetime import datetime


def format_response(success: bool, data: Any = None, message: str = "", code: int = 0) -> Dict:
    """
    格式化API响应
    
    :param success: 是否成功
    :param data: 响应数据
    :param message: 响应消息
    :param code: 状态码
    :return: 格式化后的响应字典
    """
    return {
        "code": code if success else (code or 500),
        "msg": message or ("success" if success else "error"),
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


def validate_date(date_str: str) -> bool:
    """
    验证日期格式
    
    :param date_str: 日期字符串
    :return: 是否有效
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def calculate_days_between(start_date: str, end_date: str) -> int:
    """
    计算两个日期之间的天数
    
    :param start_date: 开始日期 yyyy-MM-dd
    :param end_date: 结束日期 yyyy-MM-dd
    :return: 天数
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except ValueError:
        return 0


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析JSON字符串
    
    :param json_str: JSON字符串
    :param default: 解析失败时的默认值
    :return: 解析结果
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    :param text: 原文本
    :param max_length: 最大长度
    :param suffix: 后缀
    :return: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_season_by_month(month: int) -> str:
    """
    根据月份获取季节
    
    :param month: 月份 1-12
    :return: 季节名称
    """
    if 3 <= month <= 5:
        return "spring"
    elif 6 <= month <= 8:
        return "summer"
    elif 9 <= month <= 11:
        return "autumn"
    else:
        return "winter"


def format_currency(amount: float, currency: str = "CNY") -> str:
    """
    格式化货币显示
    
    :param amount: 金额
    :param currency: 货币代码
    :return: 格式化后的字符串
    """
    symbols = {
        "CNY": "¥",
        "USD": "$",
        "EUR": "€",
        "JPY": "¥",
        "GBP": "£"
    }
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.0f}"


if __name__ == "__main__":
    # 测试工具函数
    print("测试 format_response:")
    print(format_response(True, {"test": "data"}, "操作成功"))
    
    print("\n测试 validate_date:")
    print(f"2026-04-01: {validate_date('2026-04-01')}")
    print(f"invalid: {validate_date('invalid')}")
    
    print("\n测试 calculate_days_between:")
    print(f"2026-04-01 至 2026-04-05: {calculate_days_between('2026-04-01', '2026-04-05')}天")
    
    print("\n测试 format_currency:")
    print(f"CNY 15000: {format_currency(15000, 'CNY')}")
    print(f"USD 2000: {format_currency(2000, 'USD')}")
