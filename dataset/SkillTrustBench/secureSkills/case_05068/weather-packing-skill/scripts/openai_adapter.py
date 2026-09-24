#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI天气打包技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('../../shared')
sys.path.append('.')
from weather_api import WeatherPackingService, WeatherPackingError
from utils import format_response

# 初始化API实例
weather_service = WeatherPackingService()

# OpenAI函数描述
WEATHER_FUNCTIONS = [
    {
        "name": "get_weather_forecast",
        "description": "获取天气预报",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地城市"
                },
                "travel_dates": {
                    "type": "string",
                    "description": "旅行日期范围"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "旅行天数"
                }
            },
            "required": ["destination", "travel_dates", "duration_days"]
        }
    },
    {
        "name": "get_complete_guide",
        "description": "获取完整天气打包指南",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地城市"
                },
                "travel_dates": {
                    "type": "string",
                    "description": "旅行日期范围"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "旅行天数"
                }
            },
            "required": ["destination", "travel_dates", "duration_days"]
        }
    },
    {
        "name": "format_guide",
        "description": "格式化天气打包指南",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "天气打包结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiWeatherAdapter:
    """OpenAI天气打包适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """调用天气打包函数"""
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "get_weather_forecast": lambda **kwargs: weather_service.get_weather_forecast(
                    destination=kwargs["destination"],
                    travel_dates=kwargs["travel_dates"],
                    duration_days=kwargs["duration_days"]
                ),
                "get_complete_guide": lambda **kwargs: weather_service.get_complete_guide(
                    destination=kwargs["destination"],
                    travel_dates=kwargs["travel_dates"],
                    duration_days=kwargs["duration_days"]
                ),
                "format_guide": lambda **kwargs: {
                    "formatted_text": weather_service.format_guide(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return format_response(False, error=f"函数{function_name}不存在", code=404)
            
            result = function_map[function_name](**args)
            return format_response(True, data=result)
            
        except json.JSONDecodeError:
            return format_response(False, error="参数格式错误", code=400)
        except WeatherPackingError as e:
            return format_response(False, error=str(e), code=500)
        except Exception as e:
            return format_response(False, error=f"未知错误: {str(e)}", code=500)


if __name__ == "__main__":
    adapter = OpenaiWeatherAdapter()
    
    # 测试
    func_args = json.dumps({
        "destination": "东京",
        "travel_dates": "2026-04-01 至 2026-04-05",
        "duration_days": 5
    })
    result = adapter.call_function("get_complete_guide", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
