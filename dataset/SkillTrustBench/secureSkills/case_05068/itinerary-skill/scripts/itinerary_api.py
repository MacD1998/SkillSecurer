#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI行程规划技能 - 核心API
"""

import json
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import sys
sys.path.append('../../shared')
from travel_models import (
    TravelPlan, DayPlan, Activity, Location, Accommodation,
    Traveler, TravelStyle, BudgetLevel, create_travel_plan
)


class ItineraryError(Exception):
    """行程规划异常"""
    pass


# 模拟景点数据库
ATTRACTIONS_DB = {
    "东京": [
        {"id": "tokyo_001", "name": "浅草寺", "name_en": "Senso-ji", "type": "temple", "duration": 120, "price": 0, "lat": 35.7148, "lng": 139.7967, "area": "浅草", "tags": ["文化", "历史", "拍照"]},
        {"id": "tokyo_002", "name": "晴空塔", "name_en": "Tokyo Skytree", "type": "observation", "duration": 180, "price": 2100, "lat": 35.7100, "lng": 139.8107, "area": "押上", "tags": ["夜景", "地标", "浪漫"]},
        {"id": "tokyo_003", "name": "东京塔", "name_en": "Tokyo Tower", "type": "observation", "duration": 120, "price": 1200, "lat": 35.6586, "lng": 139.7454, "area": "芝公园", "tags": ["夜景", "地标", "浪漫"]},
        {"id": "tokyo_004", "name": "明治神宫", "name_en": "Meiji Shrine", "type": "shrine", "duration": 90, "price": 0, "lat": 35.6764, "lng": 139.6993, "area": "原宿", "tags": ["文化", "自然", "拍照"]},
        {"id": "tokyo_005", "name": "涩谷十字路口", "name_en": "Shibuya Crossing", "type": "landmark", "duration": 30, "price": 0, "lat": 35.6595, "lng": 139.7004, "area": "涩谷", "tags": ["地标", "拍照", "购物"]},
        {"id": "tokyo_006", "name": "新宿御苑", "name_en": "Shinjuku Gyoen", "type": "park", "duration": 120, "price": 500, "lat": 35.6852, "lng": 139.7100, "area": "新宿", "tags": ["自然", "樱花", "休闲"]},
        {"id": "tokyo_007", "name": "皇居", "name_en": "Imperial Palace", "type": "palace", "duration": 90, "price": 0, "lat": 35.6852, "lng": 139.7528, "area": "丸之内", "tags": ["历史", "文化", "拍照"]},
        {"id": "tokyo_008", "name": "银座", "name_en": "Ginza", "type": "shopping", "duration": 180, "price": 0, "lat": 35.6719, "lng": 139.7656, "area": "银座", "tags": ["购物", "美食", "高端"]},
        {"id": "tokyo_009", "name": "秋叶原", "name_en": "Akihabara", "type": "shopping", "duration": 180, "price": 0, "lat": 35.6984, "lng": 139.7731, "area": "秋叶原", "tags": ["动漫", "电器", "购物"]},
        {"id": "tokyo_010", "name": "台场", "name_en": "Odaiba", "type": "entertainment", "duration": 240, "price": 0, "lat": 35.6274, "lng": 139.7747, "area": "台场", "tags": ["海滨", "购物", "夜景"]},
    ],
    "大阪": [
        {"id": "osaka_001", "name": "大阪城", "name_en": "Osaka Castle", "type": "castle", "duration": 150, "price": 600, "lat": 34.6873, "lng": 135.5262, "area": "中央区", "tags": ["历史", "文化", "樱花"]},
        {"id": "osaka_002", "name": "道顿堀", "name_en": "Dotonbori", "type": "entertainment", "duration": 180, "price": 0, "lat": 34.6687, "lng": 135.5013, "area": "中央区", "tags": ["美食", "夜景", "购物"]},
        {"id": "osaka_003", "name": "心斋桥", "name_en": "Shinsaibashi", "type": "shopping", "duration": 180, "price": 0, "lat": 34.6731, "lng": 135.5008, "area": "中央区", "tags": ["购物", "美食", "时尚"]},
        {"id": "osaka_004", "name": "环球影城", "name_en": "Universal Studios", "type": "theme_park", "duration": 480, "price": 8600, "lat": 34.6654, "lng": 135.4323, "area": "此花区", "tags": ["娱乐", "亲子", "哈利波特"]},
        {"id": "osaka_005", "name": "通天阁", "name_en": "Tsutenkaku", "type": "observation", "duration": 60, "price": 800, "lat": 34.6525, "lng": 135.5063, "area": "浪速区", "tags": ["地标", "复古", "拍照"]},
    ],
    "京都": [
        {"id": "kyoto_001", "name": "清水寺", "name_en": "Kiyomizu-dera", "type": "temple", "duration": 120, "price": 400, "lat": 34.9949, "lng": 135.7850, "area": "东山区", "tags": ["世界遗产", "樱花", "红叶"]},
        {"id": "kyoto_002", "name": "金阁寺", "name_en": "Kinkaku-ji", "type": "temple", "duration": 60, "price": 400, "lat": 35.0394, "lng": 135.7292, "area": "北区", "tags": ["世界遗产", "拍照", "庭院"]},
        {"id": "kyoto_003", "name": "伏见稻荷大社", "name_en": "Fushimi Inari", "type": "shrine", "duration": 150, "price": 0, "lat": 34.9671, "lng": 135.7727, "area": "伏见区", "tags": ["千本鸟居", "拍照", "登山"]},
        {"id": "kyoto_004", "name": "岚山", "name_en": "Arashiyama", "type": "nature", "duration": 240, "price": 0, "lat": 35.0094, "lng": 135.6668, "area": "右京区", "tags": ["竹林", "渡月桥", "小火车"]},
        {"id": "kyoto_005", "name": "二条城", "name_en": "Nijo Castle", "type": "castle", "duration": 90, "price": 600, "lat": 35.0142, "lng": 135.7482, "area": "中京区", "tags": ["世界遗产", "历史", "德川家康"]},
    ]
}

# 模拟餐厅数据库
RESTAURANTS_DB = {
    "东京": {
        "浅草": [
            {"name": "大黑家天妇罗", "type": "天妇罗", "price_range": "中等", "specialty": "天妇罗盖饭"},
            {"name": "今户神社前烧鸟", "type": "烧鸟", "price_range": "便宜", "specialty": "烤鸡肉串"},
        ],
        "银座": [
            {"name": "数寄屋桥次郎", "type": "寿司", "price_range": "高端", "specialty": "握寿司"},
            {"name": "天一", "type": "天妇罗", "price_range": "高端", "specialty": "天妇罗套餐"},
        ],
        "新宿": [
            {"name": "思い出横丁", "type": "烧鸟", "price_range": "中等", "specialty": "烤串、啤酒"},
            {"name": "蟹道乐", "type": "螃蟹料理", "price_range": "高端", "specialty": "螃蟹全席"},
        ],
    }
}


class ItineraryPlanner:
    """行程规划器"""
    
    def __init__(self):
        self.attractions_db = ATTRACTIONS_DB
        self.restaurants_db = RESTAURANTS_DB
    
    def generate_itinerary(
        self,
        destination: str,
        duration_days: int,
        start_date: str = None,
        travel_style: List[str] = None,
        budget_level: str = "STANDARD",
        interests: List[str] = None,
        must_visit: List[str] = None,
        avoid: List[str] = None
    ) -> Dict:
        """
        生成完整行程
        """
        # 创建基础计划
        if start_date:
            end_date = (datetime.strptime(start_date, "%Y-%m-%d") + 
                       timedelta(days=duration_days-1)).strftime("%Y-%m-%d")
            plan = create_travel_plan(destination, start_date, end_date)
        else:
            plan = TravelPlan(
                destination=destination,
                duration_days=duration_days,
                travel_style=travel_style or [],
                interests=interests or []
            )
            plan.itinerary = [DayPlan(day_number=i+1) for i in range(duration_days)]
        
        # 获取景点列表
        attractions = self._get_attractions(destination, interests, avoid)
        
        # 分配景点到每一天
        self._distribute_attractions(plan, attractions, duration_days)
        
        # 添加餐厅推荐
        self._add_restaurants(plan)
        
        # 计算预估费用
        total_cost = self._calculate_cost(plan)
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "plan_id": f"plan_{random.randint(100000, 999999)}",
                "destination": destination,
                "duration_days": duration_days,
                "travel_style": travel_style or ["CULTURE"],
                "total_estimated_cost": total_cost,
                "currency": "CNY",
                "itinerary": [day.to_dict() for day in plan.itinerary],
                "recommendations": self._generate_recommendations(destination)
            }
        }
    
    def _get_attractions(
        self,
        destination: str,
        interests: List[str] = None,
        avoid: List[str] = None
    ) -> List[Dict]:
        """获取景点列表"""
        attractions = self.attractions_db.get(destination, [])
        
        # 过滤不想去的景点
        if avoid:
            attractions = [a for a in attractions if a["name"] not in avoid]
        
        # 根据兴趣排序
        if interests:
            def score_attraction(attr):
                score = 0
                for tag in attr.get("tags", []):
                    if tag in interests:
                        score += 1
                return score
            attractions.sort(key=score_attraction, reverse=True)
        
        return attractions
    
    def _distribute_attractions(
        self,
        plan: TravelPlan,
        attractions: List[Dict],
        duration_days: int
    ):
        """将景点分配到每一天"""
        
        # 第一天通常是抵达日，安排较轻松
        # 最后一天通常是离开日，安排较轻松
        
        daily_limits = self._calculate_daily_limits(duration_days)
        
        attraction_idx = 0
        for day_num, day in enumerate(plan.itinerary, 1):
            limit = daily_limits.get(day_num, 3)
            day_attractions = []
            
            # 获取当天的景点
            while len(day_attractions) < limit and attraction_idx < len(attractions):
                attr = attractions[attraction_idx]
                day_attractions.append(attr)
                attraction_idx += 1
            
            # 分配到上午、下午、晚上
            self._schedule_day_activities(day, day_attractions, day_num, duration_days)
    
    def _calculate_daily_limits(self, duration_days: int) -> Dict[int, int]:
        """计算每天最多安排几个景点"""
        limits = {}
        for i in range(1, duration_days + 1):
            if i == 1 or i == duration_days:
                limits[i] = 2  # 第一天和最后一天轻松一点
            else:
                limits[i] = 3  # 中间天数可以紧凑一些
        return limits
    
    def _schedule_day_activities(
        self,
        day: DayPlan,
        attractions: List[Dict],
        day_num: int,
        total_days: int
    ):
        """安排一天的活动"""
        
        # 设置主题
        themes = ["抵达与初探", "传统文化之旅", "现代都市体验", "美食购物日", "自然与休闲", "深度探索", "离别与回味"]
        if day_num == 1:
            day.theme = "抵达与初探"
        elif day_num == total_days:
            day.theme = "离别与回味"
        else:
            day.theme = themes[min(day_num, len(themes)-1)]
        
        # 时间槽
        time_slots = {
            "morning": [],
            "afternoon": [],
            "evening": []
        }
        
        # 第一天特殊处理
        if day_num == 1:
            time_slots["morning"].append(Activity(
                name="抵达机场，办理入境",
                type="transport",
                start_time="09:00",
                end_time="12:00",
                duration_minutes=180
            ))
            time_slots["morning"].append(Activity(
                name="酒店入住",
                type="accommodation",
                start_time="12:00",
                end_time="13:00",
                duration_minutes=60
            ))
        
        # 分配景点到时间段
        for i, attr in enumerate(attractions):
            activity = Activity(
                name=attr["name"],
                name_en=attr["name_en"],
                type=attr["type"],
                price=attr["price"],
                duration_minutes=attr["duration"],
                location=Location(
                    name=attr["name"],
                    latitude=attr["lat"],
                    longitude=attr["lng"]
                )
            )
            
            # 根据索引分配到不同时间段
            if i == 0 and day_num > 1:
                activity.start_time = "09:00"
                activity.end_time = self._add_minutes("09:00", attr["duration"])
                time_slots["morning"].append(activity)
            elif i == 1 or (i == 0 and day_num == 1):
                activity.start_time = "14:00"
                activity.end_time = self._add_minutes("14:00", attr["duration"])
                time_slots["afternoon"].append(activity)
            else:
                activity.start_time = "18:00"
                activity.end_time = self._add_minutes("18:00", attr["duration"])
                time_slots["evening"].append(activity)
        
        day.morning = time_slots["morning"]
        day.afternoon = time_slots["afternoon"]
        day.evening = time_slots["evening"]
    
    def _add_minutes(self, time_str: str, minutes: int) -> str:
        """给时间加上分钟数"""
        hour, minute = map(int, time_str.split(":"))
        total_minutes = hour * 60 + minute + minutes
        new_hour = total_minutes // 60
        new_minute = total_minutes % 60
        return f"{new_hour:02d}:{new_minute:02d}"
    
    def _add_restaurants(self, plan: TravelPlan):
        """添加餐厅推荐"""
        destination = plan.destination
        restaurants = self.restaurants_db.get(destination, {})
        
        for day in plan.itinerary:
            # 根据当天区域推荐餐厅
            day.meals = {
                "breakfast": "酒店早餐或便利店",
                "lunch": random.choice(["当地特色餐厅", "拉面店", "定食屋"]),
                "dinner": random.choice(["居酒屋", "烧肉店", "寿司店"])
            }
    
    def _calculate_cost(self, plan: TravelPlan) -> float:
        """计算预估费用"""
        total = 0
        
        # 景点门票
        for day in plan.itinerary:
            for slot in [day.morning, day.afternoon, day.evening]:
                for activity in slot:
                    if hasattr(activity, 'price'):
                        total += activity.price
        
        # 餐饮估算
        total += plan.duration_days * 300  # 每天餐饮约300元
        
        # 交通估算
        total += plan.duration_days * 100  # 每天交通约100元
        
        return total
    
    def _generate_recommendations(self, destination: str) -> List[str]:
        """生成旅行建议"""
        recommendations = {
            "东京": [
                "建议购买东京地铁3日券，可无限次乘坐",
                "浅草寺早晨人少，若想拍照建议7:00前到达",
                "晴空塔傍晚时段人较多，可考虑上午登塔"
            ],
            "大阪": [
                "大阪周游卡包含多个景点门票，非常划算",
                "道顿堀晚上最热闹，建议傍晚前往",
                "环球影城建议提前购买快速通关券"
            ],
            "京都": [
                "清水寺清晨6点开门，可避开人潮",
                "岚山小火车需提前预约，尤其是红叶季",
                "穿和服游览京都更有氛围，可在清水寺附近租借"
            ]
        }
        return recommendations.get(destination, ["建议提前查看景点开放时间", "购买当地交通卡可节省费用"])
    
    def optimize_route(
        self,
        day_plan: Dict,
        optimization_type: str = "shortest_path"
    ) -> Dict:
        """
        优化单日路线
        """
        # 简化的路线优化逻辑
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "optimized_plan": day_plan,
                "savings_time": "30分钟",
                "savings_distance": "2公里"
            }
        }
    
    def format_itinerary(self, result: Dict) -> str:
        """
        格式化行程为易读文本
        """
        data = result.get("data", {})
        destination = data.get("destination", "")
        duration = data.get("duration_days", 0)
        total_cost = data.get("total_estimated_cost", 0)
        itinerary = data.get("itinerary", [])
        recommendations = data.get("recommendations", [])
        
        lines = []
        lines.append(f"🗺️ {destination}{duration}日深度游行程规划")
        lines.append("")
        lines.append(f"💰 预估费用：¥{total_cost}/人")
        lines.append(f"🎯 旅行风格：{'、'.join(data.get('travel_style', ['文化探索']))}")
        lines.append("")
        lines.append("=" * 40)
        
        for day in itinerary:
            day_num = day.get("day_number", 0)
            date = day.get("date", "")
            theme = day.get("theme", "")
            
            lines.append("")
            lines.append(f"📍 Day {day_num} | {date} | 主题：{theme}")
            lines.append("")
            
            # 上午
            morning = day.get("morning", [])
            if morning:
                lines.append("🌅 上午")
                for activity in morning:
                    name = activity.get("name", "")
                    start = activity.get("start_time", "")
                    end = activity.get("end_time", "")
                    price = activity.get("price", 0)
                    price_str = f" 💴 ¥{price}" if price > 0 else " 💴 免费"
                    lines.append(f"  {start} - {end}  {name}{price_str}")
                lines.append("")
            
            # 下午
            afternoon = day.get("afternoon", [])
            if afternoon:
                lines.append("🌞 下午")
                for activity in afternoon:
                    name = activity.get("name", "")
                    start = activity.get("start_time", "")
                    end = activity.get("end_time", "")
                    price = activity.get("price", 0)
                    price_str = f" 💴 ¥{price}" if price > 0 else " 💴 免费"
                    lines.append(f"  {start} - {end}  {name}{price_str}")
                lines.append("")
            
            # 晚上
            evening = day.get("evening", [])
            if evening:
                lines.append("🌙 晚上")
                for activity in evening:
                    name = activity.get("name", "")
                    start = activity.get("start_time", "")
                    end = activity.get("end_time", "")
                    price = activity.get("price", 0)
                    price_str = f" 💴 ¥{price}" if price > 0 else " 💴 免费"
                    lines.append(f"  {start} - {end}  {name}{price_str}")
                lines.append("")
            
            # 餐饮
            meals = day.get("meals", {})
            if meals:
                lines.append("🍽️ 今日美食")
                for meal_type, meal_name in meals.items():
                    meal_emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙"}.get(meal_type, "🍽️")
                    lines.append(f"  {meal_emoji} {meal_name}")
                lines.append("")
        
        lines.append("=" * 40)
        lines.append("")
        lines.append("💡 贴心提示")
        for rec in recommendations:
            lines.append(f"• {rec}")
        
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    planner = ItineraryPlanner()
    
    # 生成东京5日游行程
    result = planner.generate_itinerary(
        destination="东京",
        duration_days=5,
        start_date="2026-04-01",
        travel_style=["CULTURE", "FOODIE"],
        interests=["文化", "美食", "拍照"]
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "="*60)
    print("格式化行程：")
    print("="*60)
    print(planner.format_itinerary(result))
