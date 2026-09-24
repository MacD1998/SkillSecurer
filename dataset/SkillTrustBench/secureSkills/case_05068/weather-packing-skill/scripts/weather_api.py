#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI天气打包技能 - 核心API
"""

import json
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import sys
sys.path.append('../../shared')
from travel_models import WeatherInfo, PackingItem, PackingList


class WeatherPackingError(Exception):
    """天气打包异常"""
    pass


# 模拟天气数据库
WEATHER_DB = {
    "东京": {
        "spring": {"temp_range": (10, 20), "conditions": ["多云", "晴", "小雨"], "humidity": 60, "rainy_days": 2},
        "summer": {"temp_range": (25, 32), "conditions": ["晴", "多云", "雷阵雨"], "humidity": 75, "rainy_days": 3},
        "autumn": {"temp_range": (15, 23), "conditions": ["晴", "多云"], "humidity": 55, "rainy_days": 1},
        "winter": {"temp_range": (5, 12), "conditions": ["晴", "多云", "小雨"], "humidity": 50, "rainy_days": 1}
    },
    "大阪": {
        "spring": {"temp_range": (12, 22), "conditions": ["多云", "晴"], "humidity": 58, "rainy_days": 2},
        "summer": {"temp_range": (26, 33), "conditions": ["晴", "多云", "雷阵雨"], "humidity": 70, "rainy_days": 3},
        "autumn": {"temp_range": (16, 25), "conditions": ["晴", "多云"], "humidity": 52, "rainy_days": 1},
        "winter": {"temp_range": (6, 13), "conditions": ["晴", "多云"], "humidity": 48, "rainy_days": 1}
    },
    "京都": {
        "spring": {"temp_range": (10, 20), "conditions": ["多云", "晴", "小雨"], "humidity": 62, "rainy_days": 2},
        "summer": {"temp_range": (25, 32), "conditions": ["晴", "多云", "雷阵雨"], "humidity": 72, "rainy_days": 3},
        "autumn": {"temp_range": (12, 22), "conditions": ["晴", "多云"], "humidity": 55, "rainy_days": 1},
        "winter": {"temp_range": (3, 10), "conditions": ["晴", "多云", "小雨"], "humidity": 52, "rainy_days": 2}
    },
    "巴黎": {
        "spring": {"temp_range": (10, 18), "conditions": ["多云", "小雨", "晴"], "humidity": 65, "rainy_days": 3},
        "summer": {"temp_range": (18, 25), "conditions": ["晴", "多云"], "humidity": 60, "rainy_days": 2},
        "autumn": {"temp_range": (10, 18), "conditions": ["多云", "小雨"], "humidity": 68, "rainy_days": 3},
        "winter": {"temp_range": (3, 8), "conditions": ["多云", "小雨", "阴"], "humidity": 70, "rainy_days": 4}
    }
}

# 基础打包清单模板
BASE_PACKING_TEMPLATE = {
    "clothing": [
        {"item": "内衣裤", "essential": True, "weight_per_unit": 0.1},
        {"item": "袜子", "essential": True, "weight_per_unit": 0.05},
        {"item": "睡衣", "essential": False, "weight_per_unit": 0.3},
    ],
    "toiletries": [
        {"item": "牙刷、牙膏", "essential": True, "weight_per_unit": 0.1},
        {"item": "洗发水、沐浴露", "essential": True, "weight_per_unit": 0.3},
        {"item": "洗面奶、护肤品", "essential": True, "weight_per_unit": 0.4},
        {"item": "防晒霜", "essential": True, "weight_per_unit": 0.2},
        {"item": "剃须刀/化妆品", "essential": True, "weight_per_unit": 0.2},
    ],
    "electronics": [
        {"item": "手机充电器", "essential": True, "weight_per_unit": 0.2},
        {"item": "充电宝", "essential": True, "weight_per_unit": 0.3},
        {"item": "转换插头", "essential": True, "weight_per_unit": 0.1},
        {"item": "相机", "essential": False, "weight_per_unit": 0.5},
    ],
    "documents": [
        {"item": "护照+签证", "essential": True, "weight_per_unit": 0.1},
        {"item": "机票预订单", "essential": True, "weight_per_unit": 0.05},
        {"item": "酒店预订单", "essential": True, "weight_per_unit": 0.05},
        {"item": "身份证", "essential": True, "weight_per_unit": 0.05},
        {"item": "银行卡+现金", "essential": True, "weight_per_unit": 0.1},
    ],
    "medical": [
        {"item": "肠胃药", "essential": False, "weight_per_unit": 0.1},
        {"item": "感冒药", "essential": False, "weight_per_unit": 0.1},
        {"item": "创可贴", "essential": False, "weight_per_unit": 0.05},
        {"item": "个人常用药", "essential": False, "weight_per_unit": 0.2},
    ],
    "other": [
        {"item": "雨伞", "essential": True, "weight_per_unit": 0.3},
        {"item": "水杯", "essential": True, "weight_per_unit": 0.3},
        {"item": "纸巾、湿巾", "essential": True, "weight_per_unit": 0.2},
        {"item": "购物袋", "essential": False, "weight_per_unit": 0.05},
    ]
}

# 目的地特殊提醒
DESTINATION_REMINDERS = {
    "东京": [
        "日本春季花粉较多，过敏体质建议带口罩",
        "东京地铁内空调较冷，建议带薄外套",
        "日本100V电压，需带A/B型转换插头",
        "垃圾分类严格，随身携带垃圾袋"
    ],
    "大阪": [
        "大阪夏季炎热潮湿，注意防暑",
        "道顿堀人多拥挤，注意保管财物",
        "日本100V电压，需带A/B型转换插头"
    ],
    "京都": [
        "京都寺庙多，建议穿易脱的鞋子",
        "春秋季节游客多，建议提前预约",
        "日本100V电压，需带A/B型转换插头"
    ],
    "巴黎": [
        "巴黎天气多变，建议带雨伞",
        "欧洲电压230V，需带C/E型转换插头",
        "注意防范小偷，尤其是在景区和地铁"
    ]
}


class WeatherPackingService:
    """天气打包服务"""
    
    def __init__(self):
        self.weather_db = WEATHER_DB
        self.base_template = BASE_PACKING_TEMPLATE
        self.reminders_db = DESTINATION_REMINDERS
    
    def get_weather_forecast(
        self,
        destination: str,
        travel_dates: str,
        duration_days: int
    ) -> Dict:
        """获取天气预报"""
        # 解析日期获取季节
        try:
            start_date = datetime.strptime(travel_dates.split(" 至 ")[0], "%Y-%m-%d")
            month = start_date.month
            
            if 3 <= month <= 5:
                season = "spring"
                season_name = "春季"
            elif 6 <= month <= 8:
                season = "summer"
                season_name = "夏季"
            elif 9 <= month <= 11:
                season = "autumn"
                season_name = "秋季"
            else:
                season = "winter"
                season_name = "冬季"
        except:
            season = "spring"
            season_name = "春季"
        
        # 获取天气数据
        weather_data = self.weather_db.get(destination, self.weather_db["东京"])
        season_data = weather_data.get(season, weather_data["spring"])
        
        # 生成每日天气
        forecast = []
        temp_range = season_data["temp_range"]
        conditions = season_data["conditions"]
        
        for i in range(duration_days):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            weekday = (start_date + timedelta(days=i)).strftime("%A")
            
            temp_high = random.randint(temp_range[0] + 3, temp_range[1])
            temp_low = random.randint(temp_range[0], temp_range[1] - 3)
            condition = random.choice(conditions)
            
            forecast.append({
                "date": date,
                "weekday": weekday,
                "condition": condition,
                "temp_high": temp_high,
                "temp_low": temp_low,
                "precipitation_chance": 80 if "雨" in condition else random.randint(10, 40),
                "humidity": season_data["humidity"],
                "wind_level": f"{random.randint(2, 4)}级",
                "clothing_index": self._get_clothing_advice(temp_high, temp_low, condition)
            })
        
        # 计算平均值
        avg_temp = sum((d["temp_high"] + d["temp_low"]) / 2 for d in forecast) / len(forecast)
        rainy_days = sum(1 for d in forecast if "雨" in d["condition"])
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "season": season_name,
                "travel_dates": travel_dates,
                "duration_days": duration_days,
                "weather_forecast": forecast,
                "weather_summary": {
                    "avg_temp": round(avg_temp),
                    "temp_range": f"{min(d['temp_low'] for d in forecast)}-{max(d['temp_high'] for d in forecast)}°C",
                    "dominant_condition": max(set(d["condition"] for d in forecast), key=lambda x: sum(1 for d in forecast if d["condition"] == x)),
                    "rainy_days": rainy_days,
                    "overall_advice": f"{season_name}天气，建议洋葱式穿衣"
                }
            }
        }
    
    def _get_clothing_advice(self, temp_high: int, temp_low: int, condition: str) -> str:
        """根据温度给出穿衣建议"""
        avg_temp = (temp_high + temp_low) / 2
        
        if avg_temp < 5:
            return "厚外套+毛衣+保暖内衣"
        elif avg_temp < 10:
            return "大衣/羽绒服+毛衣"
        elif avg_temp < 15:
            return "薄外套+长袖"
        elif avg_temp < 20:
            return "长袖+薄外套（备用）"
        elif avg_temp < 25:
            return "短袖/长袖+薄外套"
        elif avg_temp < 30:
            return "短袖+防晒衣"
        else:
            return "短袖+短裤/裙子，注意防晒"
    
    def generate_packing_list(
        self,
        destination: str,
        duration_days: int,
        weather_forecast: List[Dict],
        travel_style: str = "leisure"
    ) -> Dict:
        """生成打包清单"""
        
        # 根据天气确定衣物
        avg_temp = sum((d["temp_high"] + d["temp_low"]) / 2 for d in weather_forecast) / len(weather_forecast)
        has_rain = any("雨" in d["condition"] for d in weather_forecast)
        
        # 生成衣物清单
        clothing_items = self._generate_clothing_items(avg_temp, duration_days, has_rain)
        
        # 基础物品
        packing_list = {
            "clothing": clothing_items,
            "toiletries": self._generate_items("toiletries", duration_days),
            "electronics": self._generate_items("electronics", 1),
            "documents": self._generate_items("documents", 1),
            "medical": self._generate_items("medical", 1),
            "other": self._generate_items("other", 1, has_rain=has_rain)
        }
        
        # 计算重量
        total_weight = self._calculate_weight(packing_list)
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "duration_days": duration_days,
                "packing_list": packing_list,
                "luggage_estimate": {
                    "total_weight_kg": round(total_weight, 1),
                    "carry_on_limit": 10,
                    "status": "符合手提行李限额" if total_weight <= 10 else "建议托运"
                }
            }
        }
    
    def _generate_clothing_items(self, avg_temp: float, days: int, has_rain: bool) -> List[Dict]:
        """生成衣物清单"""
        items = []
        
        # 基础衣物
        items.append({"item": "内衣裤", "quantity": days, "essential": True, "notes": ""})
        items.append({"item": "袜子", "quantity": days, "essential": True, "notes": ""})
        
        # 根据温度
        if avg_temp < 10:
            items.append({"item": "厚外套/羽绒服", "quantity": 1, "essential": True, "notes": "保暖必备"})
            items.append({"item": "毛衣", "quantity": 2, "essential": True, "notes": ""})
            items.append({"item": "长袖T恤", "quantity": days // 2 + 1, "essential": True, "notes": ""})
            items.append({"item": "长裤", "quantity": 2, "essential": True, "notes": ""})
        elif avg_temp < 20:
            items.append({"item": "薄外套", "quantity": 1, "essential": True, "notes": "早晚温差大时使用"})
            items.append({"item": "长袖T恤", "quantity": days // 2 + 1, "essential": True, "notes": ""})
            items.append({"item": "短袖T恤", "quantity": days // 3 + 1, "essential": True, "notes": ""})
            items.append({"item": "长裤", "quantity": 2, "essential": True, "notes": ""})
        else:
            items.append({"item": "短袖T恤", "quantity": days // 2 + 1, "essential": True, "notes": ""})
            items.append({"item": "短裤/裙子", "quantity": 2, "essential": True, "notes": ""})
            items.append({"item": "薄外套", "quantity": 1, "essential": True, "notes": "空调房使用"})
        
        items.append({"item": "舒适步行鞋", "quantity": 1, "essential": True, "notes": ""})
        items.append({"item": "睡衣", "quantity": 1, "essential": False, "notes": ""})
        
        if has_rain:
            items.append({"item": "防水外套", "quantity": 1, "essential": True, "notes": "雨天备用"})
        
        return items
    
    def _generate_items(self, category: str, days: int, has_rain: bool = False) -> List[Dict]:
        """生成其他类别物品"""
        items = []
        templates = self.base_template.get(category, [])
        
        for template in templates:
            item = {
                "item": template["item"],
                "quantity": 1,
                "essential": template["essential"]
            }
            
            # 特殊处理
            if template["item"] == "雨伞" and not has_rain:
                continue
            
            if template["item"] == "防晒霜":
                item["notes"] = "SPF30+，春季紫外线强"
            elif template["item"] == "转换插头":
                item["notes"] = "日本使用A/B型插头"
            
            items.append(item)
        
        return items
    
    def _calculate_weight(self, packing_list: Dict) -> float:
        """计算行李重量"""
        total_weight = 0.0
        
        # 衣物估算
        clothing_weights = {
            "内衣裤": 0.1, "袜子": 0.05, "睡衣": 0.3,
            "厚外套/羽绒服": 1.0, "毛衣": 0.5, "长袖T恤": 0.2,
            "短袖T恤": 0.15, "长裤": 0.4, "短裤/裙子": 0.2,
            "舒适步行鞋": 1.0, "防水外套": 0.5, "薄外套": 0.4
        }
        
        for item in packing_list.get("clothing", []):
            weight = clothing_weights.get(item["item"], 0.2)
            total_weight += weight * item.get("quantity", 1)
        
        # 其他物品估算
        other_weights = {
            "toiletries": 1.5,
            "electronics": 2.0,
            "documents": 0.5,
            "medical": 0.5,
            "other": 1.0
        }
        
        for category, weight in other_weights.items():
            total_weight += weight
        
        return total_weight
    
    def get_special_reminders(self, destination: str) -> Dict:
        """获取特殊提醒"""
        reminders = self.reminders_db.get(destination, [])
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "reminders": reminders
            }
        }
    
    def get_complete_guide(
        self,
        destination: str,
        travel_dates: str,
        duration_days: int
    ) -> Dict:
        """获取完整天气打包指南"""
        
        # 获取天气
        weather_result = self.get_weather_forecast(destination, travel_dates, duration_days)
        if weather_result["code"] != 0:
            return weather_result
        
        weather_data = weather_result["data"]
        forecast = weather_data["weather_forecast"]
        
        # 生成打包清单
        packing_result = self.generate_packing_list(destination, duration_days, forecast)
        if packing_result["code"] != 0:
            return packing_result
        
        # 获取特殊提醒
        reminders_result = self.get_special_reminders(destination)
        reminders = reminders_result["data"].get("reminders", []) if reminders_result["code"] == 0 else []
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                **weather_data,
                **packing_result["data"],
                "special_reminders": reminders
            }
        }
    
    def format_guide(self, result: Dict) -> str:
        """格式化指南为易读文本"""
        data = result.get("data", {})
        
        if not data:
            return "暂无天气打包信息"
        
        destination = data.get("destination", "")
        duration = data.get("duration_days", 0)
        dates = data.get("travel_dates", "")
        
        lines = []
        lines.append(f"🌤️ {destination}{duration}日游天气与打包指南")
        lines.append("")
        lines.append("=" * 40)
        lines.append("")
        
        # 天气概况
        summary = data.get("weather_summary", {})
        lines.append("🌡️ 天气预报")
        lines.append("━" * 40)
        lines.append(f"📊 整体概况")
        lines.append(f"   平均气温：{summary.get('avg_temp', 0)}°C（{summary.get('temp_range', '')}）")
        lines.append(f"   主要天气：{summary.get('dominant_condition', '')}")
        lines.append(f"   降雨天数：{summary.get('rainy_days', 0)}天")
        lines.append(f"   💡 {summary.get('overall_advice', '')}")
        lines.append("")
        
        # 每日详情
        forecast = data.get("weather_forecast", [])
        if forecast:
            lines.append("📅 每日详情")
            for day in forecast[:5]:  # 最多显示5天
                date = day.get("date", "")
                weekday = day.get("weekday", "")
                condition = day.get("condition", "")
                temp_high = day.get("temp_high", 0)
                temp_low = day.get("temp_low", 0)
                advice = day.get("clothing_index", "")
                
                lines.append(f"\n{date}（{weekday}） {condition} {temp_low}-{temp_high}°C")
                lines.append(f"   👔 {advice}")
        lines.append("")
        
        # 打包清单
        packing_list = data.get("packing_list", {})
        if packing_list:
            lines.append("🧳 智能打包清单")
            lines.append("━" * 40)
            
            category_names = {
                "clothing": "👕 衣物类",
                "toiletries": "🧴 洗漱用品",
                "electronics": "📱 电子设备",
                "documents": "📋 证件资料",
                "medical": "💊 药品急救",
                "other": "🎒 其他物品"
            }
            
            for category, items in packing_list.items():
                name = category_names.get(category, category)
                lines.append(f"\n{name}")
                for item in items:
                    item_name = item.get("item", "")
                    qty = item.get("quantity", 1)
                    essential = item.get("essential", False)
                    notes = item.get("notes", "")
                    
                    mark = "✅" if essential else "⭕"
                    line = f"   {mark} {item_name} × {qty}"
                    if notes:
                        line += f"（{notes}）"
                    lines.append(line)
        lines.append("")
        
        # 特殊提醒
        reminders = data.get("special_reminders", [])
        if reminders:
            lines.append("💡 特别提醒")
            lines.append("━" * 40)
            for reminder in reminders:
                lines.append(f"• {reminder}")
            lines.append("")
        
        # 行李重量
        luggage = data.get("luggage_estimate", {})
        if luggage:
            lines.append("⚖️ 行李重量预估")
            lines.append("━" * 40)
            lines.append(f"📦 总重量：{luggage.get('total_weight_kg', 0)}kg")
            lines.append(f"✅ {luggage.get('status', '')}")
        
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    service = WeatherPackingService()
    
    # 获取东京天气打包指南
    result = service.get_complete_guide(
        destination="东京",
        travel_dates="2026-04-01 至 2026-04-05",
        duration_days=5
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "="*60)
    print("格式化指南：")
    print("="*60)
    print(service.format_guide(result))
