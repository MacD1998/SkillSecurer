#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI旅行预算技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('../../shared')
sys.path.append('.')
from budget_api import BudgetCalculator, BudgetError
from utils import format_response

# 初始化API实例
budget_calculator = BudgetCalculator()

# OpenAI函数描述
BUDGET_FUNCTIONS = [
    {
        "name": "calculate_budget",
        "description": "计算旅行预算",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "旅行天数"
                },
                "travelers": {
                    "type": "integer",
                    "description": "旅行人数",
                    "default": 1
                },
                "budget_level": {
                    "type": "string",
                    "description": "预算等级",
                    "default": "STANDARD"
                }
            },
            "required": ["destination", "duration_days"]
        }
    },
    {
        "name": "format_budget",
        "description": "格式化预算显示",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "预算结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiBudgetAdapter:
    """OpenAI预算适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """调用预算函数"""
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "calculate_budget": lambda **kwargs: budget_calculator.calculate_budget(
                    destination=kwargs["destination"],
                    duration_days=kwargs["duration_days"],
                    travelers=kwargs.get("travelers", 1),
                    budget_level=kwargs.get("budget_level", "STANDARD")
                ),
                "format_budget": lambda **kwargs: {
                    "formatted_text": budget_calculator.format_budget(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return format_response(False, error=f"函数{function_name}不存在", code=404)
            
            result = function_map[function_name](**args)
            return format_response(True, data=result)
            
        except json.JSONDecodeError:
            return format_response(False, error="参数格式错误", code=400)
        except BudgetError as e:
            return format_response(False, error=str(e), code=500)
        except Exception as e:
            return format_response(False, error=f"未知错误: {str(e)}", code=500)


if __name__ == "__main__":
    adapter = OpenaiBudgetAdapter()
    
    # 测试
    func_args = json.dumps({
        "destination": "东京",
        "duration_days": 5,
        "travelers": 2
    })
    result = adapter.call_function("calculate_budget", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
