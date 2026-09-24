#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI行程规划技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('../../shared')
sys.path.append('.')
from itinerary_api import ItineraryPlanner, ItineraryError
from utils import format_response

# 初始化API实例
itinerary_planner = ItineraryPlanner()

# OpenAI函数描述
ITINERARY_FUNCTIONS = [
    {
        "name": "generate_itinerary",
        "description": "生成完整旅行行程，包含每日活动安排、景点推荐、餐厅推荐等",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地城市，如东京、大阪、京都"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "旅行天数"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式yyyy-MM-dd"
                },
                "travel_style": {
                    "type": "array",
                    "description": "旅行风格，如['CULTURE', 'FOODIE']",
                    "items": {"type": "string"}
                },
                "budget_level": {
                    "type": "string",
                    "description": "预算等级：ECONOMY/STANDARD/COMFORT/LUXURY",
                    "default": "STANDARD"
                },
                "interests": {
                    "type": "array",
                    "description": "兴趣标签，如['文化', '美食', '购物']",
                    "items": {"type": "string"}
                }
            },
            "required": ["destination", "duration_days"]
        }
    },
    {
        "name": "format_itinerary",
        "description": "将行程结果格式化为易读的文本",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "generate_itinerary返回的结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiItineraryAdapter:
    """OpenAI行程规划适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """调用行程规划函数"""
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "generate_itinerary": lambda **kwargs: itinerary_planner.generate_itinerary(
                    destination=kwargs["destination"],
                    duration_days=kwargs["duration_days"],
                    start_date=kwargs.get("start_date"),
                    travel_style=kwargs.get("travel_style"),
                    budget_level=kwargs.get("budget_level", "STANDARD"),
                    interests=kwargs.get("interests")
                ),
                "format_itinerary": lambda **kwargs: {
                    "formatted_text": itinerary_planner.format_itinerary(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return format_response(False, error=f"函数{function_name}不存在", code=404)
            
            result = function_map[function_name](**args)
            return format_response(True, data=result)
            
        except json.JSONDecodeError:
            return format_response(False, error="参数格式错误", code=400)
        except ItineraryError as e:
            return format_response(False, error=str(e), code=500)
        except Exception as e:
            return format_response(False, error=f"未知错误: {str(e)}", code=500)


if __name__ == "__main__":
    adapter = OpenaiItineraryAdapter()
    
    # 测试
    func_args = json.dumps({
        "destination": "东京",
        "duration_days": 5,
        "start_date": "2026-04-01",
        "travel_style": ["CULTURE", "FOODIE"]
    })
    
    result = adapter.call_function("generate_itinerary", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
