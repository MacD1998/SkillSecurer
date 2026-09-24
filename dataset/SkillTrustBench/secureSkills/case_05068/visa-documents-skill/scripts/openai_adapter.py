#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI签证证件技能 - OpenAI适配器
"""

import json
import sys
from typing import Dict, Any

sys.path.append('../../shared')
sys.path.append('.')
from visa_api import VisaService, VisaError
from utils import format_response

# 初始化API实例
visa_service = VisaService()

# OpenAI函数描述
VISA_FUNCTIONS = [
    {
        "name": "check_visa_requirement",
        "description": "查询签证要求",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地国家"
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "get_document_checklist",
        "description": "获取签证材料清单",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "目的地国家"
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "format_visa_info",
        "description": "格式化签证信息",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "签证查询结果"
                }
            },
            "required": ["result"]
        }
    }
]


class OpenaiVisaAdapter:
    """OpenAI签证适配器"""
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """调用签证函数"""
        try:
            args = json.loads(function_arguments)
            
            function_map = {
                "check_visa_requirement": lambda **kwargs: visa_service.check_visa_requirement(
                    destination=kwargs["destination"]
                ),
                "get_document_checklist": lambda **kwargs: visa_service.get_document_checklist(
                    destination=kwargs["destination"]
                ),
                "format_visa_info": lambda **kwargs: {
                    "formatted_text": visa_service.format_visa_info(kwargs["result"])
                }
            }
            
            if function_name not in function_map:
                return format_response(False, error=f"函数{function_name}不存在", code=404)
            
            result = function_map[function_name](**args)
            return format_response(True, data=result)
            
        except json.JSONDecodeError:
            return format_response(False, error="参数格式错误", code=400)
        except VisaError as e:
            return format_response(False, error=str(e), code=500)
        except Exception as e:
            return format_response(False, error=f"未知错误: {str(e)}", code=500)


if __name__ == "__main__":
    adapter = OpenaiVisaAdapter()
    
    # 测试
    func_args = json.dumps({"destination": "日本"})
    result = adapter.call_function("check_visa_requirement", func_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
