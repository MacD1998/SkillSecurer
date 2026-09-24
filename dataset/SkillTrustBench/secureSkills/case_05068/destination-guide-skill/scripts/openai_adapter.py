#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI目的地指南技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('../../shared')
sys.path.append('.')
from destination_api import DestinationGuide, DestinationError
from utils import format_response

# 初始化API实例
destination_guide = DestinationGuide()

# OpenAI函数描述
DESTINATION_FUNCTIONS = [
    {
        "name": "get_destination_overview",
        "description": "获取目的地概览信息",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地名称"
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "get_attractions",
        "description": "获取目的地景点列表",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地名称"
                },
                "count": {
                    "type": "integer",
                    "description": "返回数量",
                    "default": 5
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "format_destination_guide",
        "description": "格式化目的地指南",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "查询结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiDestinationAdapter:
    """OpenAI目的地指南适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """调用目的地指南函数"""
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "get_destination_overview": lambda **kwargs: destination_guide.get_destination_overview(
                    destination=kwargs["destination"]
                ),
                "get_attractions": lambda **kwargs: destination_guide.get_attractions(
                    destination=kwargs["destination"],
                    count=kwargs.get("count", 5)
                ),
                "format_destination_guide": lambda **kwargs: {
                    "formatted_text": destination_guide.format_destination_guide(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return format_response(False, error=f"函数{function_name}不存在", code=404)
            
            result = function_map[function_name](**args)
            return format_response(True, data=result)
            
        except json.JSONDecodeError:
            return format_response(False, error="参数格式错误", code=400)
        except DestinationError as e:
            return format_response(False, error=str(e), code=500)
        except Exception as e:
            return format_response(False, error=f"未知错误: {str(e)}", code=500)


if __name__ == "__main__":
    adapter = OpenaiDestinationAdapter()
    
    # 测试
    func_args = json.dumps({"destination": "东京"})
    result = adapter.call_function("get_destination_overview", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
