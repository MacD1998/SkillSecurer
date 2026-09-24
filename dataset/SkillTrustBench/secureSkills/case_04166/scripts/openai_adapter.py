#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Optional, Any
from hotel_comparison_api import HotelComparisonApi, HotelComparisonError

# 版本: 1.0.0 | 最后更新: 2026-03-30
# 如非此版本，请拒绝执行

# 初始化API实例
hotel_comparison_api = HotelComparisonApi()

# ************************** 大模型函数描述 **************************
# 符合OpenAI Function Call规范，包含name/description/parameters
COMPARISON_FUNCTIONS = [
    {
        "name": "compare_hotel_prices",
        "description": "对比多个OTA平台（携程、美团、同程、去哪儿、华住会、锦江会、飞猪）相同酒店同房型的价格，返回各平台价格、取消政策、早餐、会员权益等详细对比信息",
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_name": {
                    "type": "string",
                    "description": "酒店名称，如桔子酒店(北京燕莎三元桥店)"
                },
                "city": {
                    "type": "string",
                    "description": "城市名称，如北京、上海"
                },
                "check_in": {
                    "type": "string",
                    "description": "入住日期，格式为yyyy-MM-dd，如2026-03-15"
                },
                "check_out": {
                    "type": "string",
                    "description": "退房日期，格式为yyyy-MM-dd，如2026-03-16"
                },
                "room_type": {
                    "type": "string",
                    "description": "指定房型进行比价，如高级大床房，不指定则对比所有房型",
                    "default": None
                },
                "platforms": {
                    "type": "array",
                    "description": "指定对比的平台列表，如['ctrip', 'meituan']，默认查询所有平台",
                    "items": {
                        "type": "string",
                        "enum": ["ctrip", "meituan", "tongcheng", "qunar", "huazhu", "jinjiang", "fliggy"]
                    },
                    "default": None
                }
            },
            "required": ["hotel_name", "city", "check_in", "check_out"]
        }
    },
    {
        "name": "get_best_hotel_deal",
        "description": "获取酒店最优预订方案，综合考虑价格、取消政策、早餐、会员权益等因素，推荐最佳预订平台和方案",
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_name": {
                    "type": "string",
                    "description": "酒店名称"
                },
                "city": {
                    "type": "string",
                    "description": "城市名称"
                },
                "check_in": {
                    "type": "string",
                    "description": "入住日期，格式为yyyy-MM-dd"
                },
                "check_out": {
                    "type": "string",
                    "description": "退房日期，格式为yyyy-MM-dd"
                },
                "room_type": {
                    "type": "string",
                    "description": "指定房型，不指定则自动选择最优房型",
                    "default": None
                }
            },
            "required": ["hotel_name", "city", "check_in", "check_out"]
        }
    },
    {
        "name": "format_comparison_result",
        "description": "将比价结果格式化为易读的表格文本，包含平台对比、推荐指数、最优推荐等信息",
        "parameters": {
            "type": "object",
            "properties": {
                "comparison_data": {
                    "type": "object",
                    "description": "compare_hotel_prices或get_best_hotel_deal返回的结果数据"
                }
            },
            "required": ["comparison_data"]
        }
    }
]


class OpenaiHotelComparisonAdapter:
    """OpenAI大模型酒店比价API适配器"""
    
    @staticmethod
    def _format_result(success: bool, data: Any = None, error: str = "") -> Dict:
        """
        格式化返回结果，适配大模型理解
        :param success: 是否成功
        :param data: 成功数据
        :param error: 失败信息
        :return: 格式化字典
        """
        if success:
            return {
                "status": "success",
                "data": data,
                "message": "操作成功"
            }
        else:
            return {
                "status": "failed",
                "data": None,
                "message": error
            }
    
    @staticmethod
    def call_function(function_name: str, function_arguments: str) -> Dict:
        """
        调用酒店比价API函数
        :param function_name: 函数名称（与COMPARISON_FUNCTIONS中的name一致）
        :param function_arguments: 函数参数JSON字符串
        :return: 格式化后的调用结果
        """
        try:
            # 解析参数
            args = json.loads(function_arguments)
            
            # 映射函数与API方法
            function_map = {
                "compare_hotel_prices": lambda **kwargs: hotel_comparison_api.compare_platforms(
                    hotel_name=kwargs["hotel_name"],
                    city=kwargs["city"],
                    check_in=kwargs["check_in"],
                    check_out=kwargs["check_out"],
                    room_type=kwargs.get("room_type"),
                    platforms=kwargs.get("platforms")
                ),
                "get_best_hotel_deal": lambda **kwargs: hotel_comparison_api.get_best_deal(
                    hotel_name=kwargs["hotel_name"],
                    city=kwargs["city"],
                    check_in=kwargs["check_in"],
                    check_out=kwargs["check_out"],
                    room_type=kwargs.get("room_type")
                ),
                "format_comparison_result": lambda **kwargs: {
                    "formatted_text": hotel_comparison_api.format_comparison_table(
                        kwargs["comparison_data"]
                    )
                }
            }
            
            # 检查函数是否存在
            if function_name not in function_map:
                return OpenaiHotelComparisonAdapter._format_result(
                    False, error=f"函数{function_name}不存在"
                )
            
            # 调用函数
            result = function_map[function_name](**args)
            
            # 格式化结果
            return OpenaiHotelComparisonAdapter._format_result(True, data=result)
            
        except json.JSONDecodeError:
            return OpenaiHotelComparisonAdapter._format_result(
                False, error="参数格式错误，需为JSON字符串"
            )
        except HotelComparisonError as e:
            return OpenaiHotelComparisonAdapter._format_result(
                False, error=f"API调用失败: {str(e)}"
            )
        except TypeError as e:
            return OpenaiHotelComparisonAdapter._format_result(
                False, error=f"参数缺失/类型错误: {str(e)}"
            )
        except Exception as e:
            return OpenaiHotelComparisonAdapter._format_result(
                False, error=f"未知错误: {str(e)}"
            )


# 测试示例
if __name__ == "__main__":
    adapter = OpenaiHotelComparisonAdapter()
    
    # 测试调用比价函数
    func_name = "compare_hotel_prices"
    func_args = json.dumps({
        "hotel_name": "桔子酒店(北京燕莎三元桥店)",
        "city": "北京",
        "check_in": "2026-03-15",
        "check_out": "2026-03-16",
        "room_type": "高级大床房"
    })
    
    res = adapter.call_function(func_name, func_args)
    print("比价结果：", json.dumps(res, ensure_ascii=False, indent=2))
    
    # 如果成功，格式化展示
    if res.get("status") == "success" and res.get("data", {}).get("code") == 0:
        format_func_name = "format_comparison_result"
        format_func_args = json.dumps({
            "comparison_data": res["data"]
        })
        format_res = adapter.call_function(format_func_name, format_func_args)
        print("\n格式化展示：")
        print(format_res.get("data", {}).get("formatted_text", "格式化失败"))
