#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报销技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('.')
from expense_api import ExpenseApi, ExpenseError

# 初始化API实例
expense_api = ExpenseApi()

# OpenAI函数描述
EXPENSE_FUNCTIONS = [
    {
        "name": "create_expense",
        "description": "创建费用记录，支持录入各类差旅费用",
        "parameters": {
            "type": "object",
            "properties": {
                "expense_type": {
                    "type": "string",
                    "description": "费用类型：TRANSPORT/HOTEL/MEAL/COMMUNICATION/OFFICE/ALLOWANCE/OTHER"
                },
                "amount": {
                    "type": "number",
                    "description": "金额"
                },
                "expense_date": {
                    "type": "string",
                    "description": "费用发生日期，格式yyyy-MM-dd"
                },
                "description": {
                    "type": "string",
                    "description": "费用说明"
                },
                "currency": {
                    "type": "string",
                    "description": "货币，默认CNY"
                },
                "invoice_no": {
                    "type": "string",
                    "description": "发票号码"
                },
                "city": {
                    "type": "string",
                    "description": "消费城市"
                },
                "related_order": {
                    "type": "string",
                    "description": "关联订单号"
                }
            },
            "required": ["expense_type", "amount", "expense_date", "description"]
        }
    },
    {
        "name": "get_expense_list",
        "description": "查询费用列表",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "状态过滤"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期"
                },
                "expense_type": {
                    "type": "string",
                    "description": "费用类型过滤"
                }
            }
        }
    },
    {
        "name": "create_report",
        "description": "创建报销单，将多个费用合并提交",
        "parameters": {
            "type": "object",
            "properties": {
                "expense_ids": {
                    "type": "array",
                    "description": "费用ID列表",
                    "items": {"type": "string"}
                },
                "trip_id": {
                    "type": "string",
                    "description": "关联差旅申请ID"
                },
                "remarks": {
                    "type": "string",
                    "description": "备注说明"
                }
            },
            "required": ["expense_ids"]
        }
    },
    {
        "name": "submit_report",
        "description": "提交报销单进行审批",
        "parameters": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type": "string",
                    "description": "报销单ID"
                }
            },
            "required": ["report_id"]
        }
    },
    {
        "name": "approve_report",
        "description": "审批报销单",
        "parameters": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type": "string",
                    "description": "报销单ID"
                },
                "action": {
                    "type": "string",
                    "description": "操作：approve/reject"
                },
                "comment": {
                    "type": "string",
                    "description": "审批意见"
                }
            },
            "required": ["report_id", "action"]
        }
    },
    {
        "name": "get_report_detail",
        "description": "查询报销单详情",
        "parameters": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type": "string",
                    "description": "报销单ID"
                }
            },
            "required": ["report_id"]
        }
    },
    {
        "name": "get_expense_stats",
        "description": "获取费用统计报表",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "开始日期"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期"
                },
                "group_by": {
                    "type": "string",
                    "description": "分组方式：type/date"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "format_expense",
        "description": "格式化费用信息为易读文本",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "费用查询结果"
                }
            },
            "required": ["result"]
        }
    },
    {
        "name": "format_report",
        "description": "格式化报销单为易读文本",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "报销单查询结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiExpenseAdapter:
    """OpenAI报销适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """
        调用报销函数
        
        :param function_name: 函数名称
        :param function_arguments: 函数参数（JSON字符串）
        :return: 调用结果
        """
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "create_expense": lambda **kwargs: expense_api.create_expense(
                    expense_type=kwargs["expense_type"],
                    amount=kwargs["amount"],
                    expense_date=kwargs["expense_date"],
                    description=kwargs["description"],
                    currency=kwargs.get("currency", "CNY"),
                    invoice_no=kwargs.get("invoice_no"),
                    city=kwargs.get("city"),
                    related_order=kwargs.get("related_order")
                ),
                "get_expense_list": lambda **kwargs: expense_api.get_expense_list(
                    status=kwargs.get("status"),
                    start_date=kwargs.get("start_date"),
                    end_date=kwargs.get("end_date"),
                    expense_type=kwargs.get("expense_type")
                ),
                "create_report": lambda **kwargs: expense_api.create_report(
                    expense_ids=kwargs["expense_ids"],
                    trip_id=kwargs.get("trip_id"),
                    remarks=kwargs.get("remarks")
                ),
                "submit_report": lambda **kwargs: expense_api.submit_report(
                    report_id=kwargs["report_id"]
                ),
                "approve_report": lambda **kwargs: expense_api.approve_report(
                    report_id=kwargs["report_id"],
                    action=kwargs["action"],
                    comment=kwargs.get("comment")
                ),
                "get_report_detail": lambda **kwargs: expense_api.get_report_detail(
                    report_id=kwargs["report_id"]
                ),
                "get_expense_stats": lambda **kwargs: expense_api.get_expense_stats(
                    start_date=kwargs["start_date"],
                    end_date=kwargs["end_date"],
                    group_by=kwargs.get("group_by", "type")
                ),
                "format_expense": lambda **kwargs: {
                    "formatted_text": expense_api.format_expense(kwargs["result"])
                },
                "format_report": lambda **kwargs: {
                    "formatted_text": expense_api.format_report(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return {
                    "code": 404,
                    "msg": f"函数{function_name}不存在",
                    "data": None
                }
            
            result = function_map[function_name](**args)
            return result
            
        except json.JSONDecodeError as e:
            return {
                "code": 400,
                "msg": f"参数格式错误: {str(e)}",
                "data": None
            }
        except ExpenseError as e:
            return {
                "code": 500,
                "msg": str(e),
                "data": None
            }
        except Exception as e:
            return {
                "code": 500,
                "msg": f"未知错误: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def get_functions() -> list:
        """获取所有可用函数描述"""
        return EXPENSE_FUNCTIONS


if __name__ == "__main__":
    adapter = OpenaiExpenseAdapter()
    
    # 测试创建费用
    print("=" * 60)
    print("测试创建费用")
    print("=" * 60)
    func_args = json.dumps({
        "expense_type": "TRANSPORT",
        "amount": 850.00,
        "expense_date": "2026-03-25",
        "description": "北京-上海机票",
        "invoice_no": "1234567890",
        "city": "上海"
    })
    result = adapter.call_function("create_expense", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试格式化
    print("\n" + "=" * 60)
    print("测试格式化费用")
    print("=" * 60)
    func_args = json.dumps({"result": result})
    formatted = adapter.call_function("format_expense", func_args)
    print(formatted.get("data", {}).get("formatted_text", ""))
