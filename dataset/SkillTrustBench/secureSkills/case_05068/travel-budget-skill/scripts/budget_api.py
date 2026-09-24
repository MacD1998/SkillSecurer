#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI旅行预算技能 - 核心API
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import sys
sys.path.append('../../shared')
from travel_models import BudgetItem, TravelBudget


class BudgetError(Exception):
    """预算计算异常"""
    pass


# 目的地消费水平数据库
DESTINATION_COST_DB = {
    "东京": {
        "level": "high",
        "currency": "JPY",
        "exchange_rate": 0.048,  # 1 JPY = 0.048 CNY
        "daily_cost": {
            "ECONOMY": {"hotel": 200, "food": 150, "transport": 50, "attractions": 50, "other": 50},
            "STANDARD": {"hotel": 600, "food": 400, "transport": 150, "attractions": 200, "other": 150},
            "COMFORT": {"hotel": 1200, "food": 800, "transport": 300, "attractions": 500, "other": 300},
            "LUXURY": {"hotel": 3000, "food": 2000, "transport": 500, "attractions": 1000, "other": 1000}
        }
    },
    "大阪": {
        "level": "medium",
        "currency": "JPY",
        "exchange_rate": 0.048,
        "daily_cost": {
            "ECONOMY": {"hotel": 180, "food": 140, "transport": 45, "attractions": 45, "other": 45},
            "STANDARD": {"hotel": 500, "food": 350, "transport": 130, "attractions": 180, "other": 130},
            "COMFORT": {"hotel": 1000, "food": 700, "transport": 250, "attractions": 450, "other": 250},
            "LUXURY": {"hotel": 2500, "food": 1800, "transport": 450, "attractions": 900, "other": 900}
        }
    },
    "京都": {
        "level": "medium",
        "currency": "JPY",
        "exchange_rate": 0.048,
        "daily_cost": {
            "ECONOMY": {"hotel": 180, "food": 140, "transport": 40, "attractions": 60, "other": 45},
            "STANDARD": {"hotel": 550, "food": 380, "transport": 120, "attractions": 250, "other": 140},
            "COMFORT": {"hotel": 1100, "food": 750, "transport": 240, "attractions": 500, "other": 280},
            "LUXURY": {"hotel": 2800, "food": 1900, "transport": 450, "attractions": 1000, "other": 950}
        }
    },
    "巴黎": {
        "level": "high",
        "currency": "EUR",
        "exchange_rate": 7.8,  # 1 EUR = 7.8 CNY
        "daily_cost": {
            "ECONOMY": {"hotel": 300, "food": 200, "transport": 80, "attractions": 100, "other": 70},
            "STANDARD": {"hotel": 800, "food": 500, "transport": 200, "attractions": 300, "other": 200},
            "COMFORT": {"hotel": 1500, "food": 1000, "transport": 400, "attractions": 600, "other": 400},
            "LUXURY": {"hotel": 4000, "food": 2500, "transport": 800, "attractions": 1500, "other": 1000}
        }
    },
    "曼谷": {
        "level": "low",
        "currency": "THB",
        "exchange_rate": 0.20,  # 1 THB = 0.20 CNY
        "daily_cost": {
            "ECONOMY": {"hotel": 80, "food": 60, "transport": 20, "attractions": 30, "other": 20},
            "STANDARD": {"hotel": 250, "food": 150, "transport": 60, "attractions": 100, "other": 60},
            "COMFORT": {"hotel": 500, "food": 300, "transport": 120, "attractions": 200, "other": 120},
            "LUXURY": {"hotel": 1200, "food": 800, "transport": 300, "attractions": 500, "other": 300}
        }
    }
}

# 机票价格参考（往返，CNY）
FLIGHT_PRICE_DB = {
    "东京": {"北京": 3000, "上海": 2800, "广州": 3500, "成都": 3200},
    "大阪": {"北京": 2800, "上海": 2600, "广州": 3300, "成都": 3000},
    "京都": {"北京": 3000, "上海": 2800, "广州": 3500, "成都": 3200},  # 飞大阪
    "巴黎": {"北京": 6000, "上海": 5500, "广州": 6500, "成都": 7000},
    "曼谷": {"北京": 2500, "上海": 2200, "广州": 1800, "成都": 2800}
}

# 省钱攻略数据库
SAVINGS_TIPS_DB = {
    "通用": {
        "flight": [
            "提前2-3个月预订机票可节省20-30%",
            "周二周三出发通常比周末便宜",
            "使用比价网站：Skyscanner、Google Flights、Kayak",
            "考虑中转航班，可能比直飞便宜30%",
            "设置价格提醒，低价时立即购买"
        ],
        "hotel": [
            "选择地铁沿线酒店，不必住在市中心",
            "使用Booking.com、Agoda、携程比价",
            "考虑民宿或胶囊旅馆",
            "连住多晚可能有折扣",
            "淡季出行酒店价格更低"
        ],
        "food": [
            "便利店早餐便宜又好吃",
            "午餐定食屋性价比高",
            "超市晚上打折食品",
            "避开景区餐厅，去当地人去的店",
            "尝试街头小吃"
        ],
        "transport": [
            "购买多日交通券",
            "步行游览近距离景点",
            "使用共享单车",
            "避免打车，使用公共交通"
        ]
    },
    "东京": {
        "flight": ["成田机场进羽田机场出，或反之，可能更便宜"],
        "hotel": ["新宿、涩谷周边酒店交通便利且选择多"],
        "food": ["午餐选择定食屋比晚餐便宜50%", "便利店饭团和便当质量很高"],
        "transport": ["购买东京地铁3日券无限次乘坐", "JR Pass适合跨城市旅行"],
        "attractions": ["很多寺庙神社免费参观", "东京都厅观景台免费"]
    },
    "大阪": {
        "flight": ["关西机场进出最方便"],
        "hotel": ["难波、梅田是交通枢纽，酒店选择多"],
        "food": ["道顿堀美食街各种价位都有", "超市的便当和炸物很划算"],
        "transport": ["大阪周游卡包含景点门票和交通", "ICOCA卡充值方便"],
        "attractions": ["大阪城公园免费进入，天守阁收费", "道顿堀、心斋桥免费逛街"]
    }
}


class BudgetCalculator:
    """旅行预算计算器"""
    
    def __init__(self):
        self.destination_cost_db = DESTINATION_COST_DB
        self.flight_price_db = FLIGHT_PRICE_DB
        self.savings_tips_db = SAVINGS_TIPS_DB
    
    def calculate_budget(
        self,
        destination: str,
        duration_days: int,
        travelers: int = 1,
        budget_level: str = "STANDARD",
        departure_city: str = "北京",
        include_flight: bool = True
    ) -> Dict:
        """
        计算旅行预算
        """
        # 获取目的地消费水平
        dest_cost = self.destination_cost_db.get(destination)
        if not dest_cost:
            return {
                "code": 404,
                "msg": f"暂不支持{destination}的预算计算",
                "data": None
            }
        
        # 获取每日费用标准
        daily_cost = dest_cost["daily_cost"].get(budget_level, dest_cost["daily_cost"]["STANDARD"])
        
        # 计算各项费用
        items = []
        
        # 1. 机票
        if include_flight:
            flight_price = self._get_flight_price(destination, departure_city)
            items.append(BudgetItem(
                category="flight",
                item_name="往返机票",
                estimated_cost=flight_price * travelers,
                notes=f"{departure_city}-{destination}往返，淡季参考价格",
                is_required=True
            ))
        
        # 2. 酒店
        hotel_cost = daily_cost["hotel"] * duration_days * travelers
        items.append(BudgetItem(
            category="hotel",
            item_name="酒店住宿",
            estimated_cost=hotel_cost,
            notes=f"{duration_days}晚，¥{daily_cost['hotel']}/晚/人",
            is_required=True
        ))
        
        # 3. 餐饮
        food_cost = daily_cost["food"] * duration_days * travelers
        items.append(BudgetItem(
            category="food",
            item_name="餐饮",
            estimated_cost=food_cost,
            notes=f"¥{daily_cost['food']}/天/人",
            is_required=True
        ))
        
        # 4. 交通
        transport_cost = daily_cost["transport"] * duration_days * travelers
        items.append(BudgetItem(
            category="transport",
            item_name="当地交通",
            estimated_cost=transport_cost,
            notes=f"公共交通、出租车等",
            is_required=True
        ))
        
        # 5. 景点门票
        attractions_cost = daily_cost["attractions"] * duration_days * travelers
        items.append(BudgetItem(
            category="attractions",
            item_name="景点门票",
            estimated_cost=attractions_cost,
            notes=f"主要景点门票",
            is_required=False
        ))
        
        # 6. 购物/其他
        other_cost = daily_cost["other"] * duration_days * travelers
        items.append(BudgetItem(
            category="other",
            item_name="购物/其他",
            estimated_cost=other_cost,
            notes=f"纪念品、零食等",
            is_required=False
        ))
        
        # 7. 应急资金（总费用的5%）
        subtotal = sum(item.estimated_cost for item in items)
        emergency_cost = int(subtotal * 0.05)
        items.append(BudgetItem(
            category="emergency",
            item_name="应急资金",
            estimated_cost=emergency_cost,
            notes="预留5%应对突发情况",
            is_required=True
        ))
        
        # 计算总费用
        total_cost = sum(item.estimated_cost for item in items)
        
        # 获取省钱攻略
        savings_tips = self._get_savings_tips(destination)
        
        # 计算不同预算等级
        price_comparison = self._compare_budget_levels(destination, duration_days, travelers, departure_city, include_flight)
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "duration_days": duration_days,
                "travelers": travelers,
                "budget_level": budget_level,
                "currency": "CNY",
                "total_estimated": total_cost,
                "per_person": total_cost // travelers,
                "breakdown": {item.category: item.to_dict() for item in items},
                "savings_tips": savings_tips,
                "price_comparison": price_comparison
            }
        }
    
    def _get_flight_price(self, destination: str, departure_city: str) -> int:
        """获取机票价格"""
        flight_prices = self.flight_price_db.get(destination, {})
        return flight_prices.get(departure_city, 3000)  # 默认3000
    
    def _get_savings_tips(self, destination: str) -> List[str]:
        """获取省钱攻略"""
        tips = []
        
        # 通用省钱技巧
        general_tips = self.savings_tips_db.get("通用", {})
        for category, category_tips in general_tips.items():
            tips.extend(category_tips[:2])  # 每类取前2条
        
        # 目的地特定省钱技巧
        dest_tips = self.savings_tips_db.get(destination, {})
        for category, category_tips in dest_tips.items():
            tips.extend(category_tips[:1])  # 每类取1条
        
        return tips[:8]  # 最多返回8条
    
    def _compare_budget_levels(
        self,
        destination: str,
        duration_days: int,
        travelers: int,
        departure_city: str,
        include_flight: bool
    ) -> Dict:
        """对比不同预算等级"""
        levels = ["ECONOMY", "STANDARD", "COMFORT", "LUXURY"]
        comparison = {}
        
        for level in levels:
            result = self.calculate_budget(
                destination=destination,
                duration_days=duration_days,
                travelers=travelers,
                budget_level=level,
                departure_city=departure_city,
                include_flight=include_flight
            )
            if result["code"] == 0:
                comparison[level.lower()] = result["data"]["per_person"]
        
        return comparison
    
    def split_expenses(
        self,
        expenses: List[Dict],
        travelers: List[str],
        split_method: str = "equal"
    ) -> Dict:
        """
        费用分摊计算
        """
        if split_method == "equal":
            # 平均分摊
            total = sum(e.get("amount", 0) for e in expenses)
            per_person = total / len(travelers)
            
            split_result = {
                "method": "equal",
                "total": total,
                "per_person": round(per_person, 2),
                "details": []
            }
            
            for person in travelers:
                split_result["details"].append({
                    "person": person,
                    "amount": round(per_person, 2),
                    "items": expenses
                })
        else:
            # 按比例分摊（简化实现）
            split_result = {
                "method": "proportional",
                "total": sum(e.get("amount", 0) for e in expenses),
                "details": []
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": split_result
        }
    
    def format_budget(self, result: Dict) -> str:
        """格式化预算为易读文本"""
        data = result.get("data", {})
        
        if not data:
            return "预算计算失败"
        
        destination = data.get("destination", "")
        duration = data.get("duration_days", 0)
        travelers = data.get("travelers", 1)
        total = data.get("total_estimated", 0)
        per_person = data.get("per_person", 0)
        breakdown = data.get("breakdown", {})
        savings_tips = data.get("savings_tips", [])
        comparison = data.get("price_comparison", {})
        
        lines = []
        lines.append(f"💰 {destination}{duration}日游预算规划")
        lines.append("")
        lines.append("=" * 40)
        lines.append("")
        
        # 概览
        lines.append("📊 预算概览")
        lines.append("━" * 40)
        lines.append(f"👥 旅行人数：{travelers}人")
        lines.append(f"📅 旅行天数：{duration}天")
        lines.append(f"💴 预估总费用：¥{total:,}")
        lines.append(f"💴 人均费用：¥{per_person:,}")
        lines.append("")
        
        # 费用明细
        lines.append("📋 费用明细")
        lines.append("━" * 40)
        
        category_names = {
            "flight": "✈️ 往返机票",
            "hotel": "🏨 酒店住宿",
            "food": "🍜 餐饮",
            "transport": "🚇 当地交通",
            "attractions": "🎫 景点门票",
            "other": "🛍️ 购物/其他",
            "emergency": "🆘 应急资金"
        }
        
        for category, item in breakdown.items():
            name = category_names.get(category, category)
            cost = item.get("estimated_cost", 0)
            notes = item.get("notes", "")
            
            lines.append(f"\n{name}")
            lines.append(f"   💴 ¥{cost:,}")
            if notes:
                lines.append(f"   📝 {notes}")
        
        lines.append("")
        
        # 省钱攻略
        if savings_tips:
            lines.append("💡 省钱攻略")
            lines.append("━" * 40)
            for tip in savings_tips[:5]:
                lines.append(f"• {tip}")
            lines.append("")
        
        # 预算等级对比
        if comparison:
            lines.append("📊 不同预算等级对比")
            lines.append("━" * 40)
            level_names = {
                "economy": "💚 经济型",
                "standard": "💛 标准型",
                "comfort": "🧡 舒适型",
                "luxury": "❤️ 豪华型"
            }
            for level, cost in comparison.items():
                name = level_names.get(level, level)
                marker = " ⭐当前" if level.upper() == data.get("budget_level", "STANDARD") else ""
                lines.append(f"{name}     ¥{cost:,}/人{marker}")
            lines.append("")
        
        lines.append("=" * 40)
        
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    calculator = BudgetCalculator()
    
    # 计算东京5日游预算
    result = calculator.calculate_budget(
        destination="东京",
        duration_days=5,
        travelers=2,
        budget_level="STANDARD",
        departure_city="北京"
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "="*60)
    print("格式化预算：")
    print("="*60)
    print(calculator.format_budget(result))
