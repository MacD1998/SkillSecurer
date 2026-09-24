#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI旅行助手套装 - 共享数据模型
定义所有子技能通用的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class TravelStyle(Enum):
    """旅行风格"""
    RELAXED = "休闲"
    ADVENTURE = "探险"
    CULTURE = "文化"
    FOODIE = "美食"
    SHOPPING = "购物"
    FAMILY = "亲子"
    ROMANTIC = "浪漫"
    BUSINESS = "商务"


class BudgetLevel(Enum):
    """预算等级"""
    ECONOMY = "经济型"
    STANDARD = "标准型"
    COMFORT = "舒适型"
    LUXURY = "豪华型"


@dataclass
class Traveler:
    """旅行者信息"""
    name: str = ""
    age: int = 0
    type: str = "adult"  # adult, child, senior
    preferences: List[str] = field(default_factory=list)
    dietary_restrictions: List[str] = field(default_factory=list)


@dataclass
class TravelPlan:
    """旅行计划"""
    plan_id: str = ""
    destination: str = ""
    country: str = ""
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    travelers: List[Traveler] = field(default_factory=list)
    budget_level: str = "STANDARD"
    budget_amount: float = 0.0
    currency: str = "CNY"
    travel_style: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    itinerary: List['DayPlan'] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "destination": self.destination,
            "country": self.country,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration_days": self.duration_days,
            "travelers": [t.__dict__ for t in self.travelers],
            "budget_level": self.budget_level,
            "budget_amount": self.budget_amount,
            "currency": self.currency,
            "travel_style": self.travel_style,
            "interests": self.interests,
            "itinerary": [day.to_dict() for day in self.itinerary],
            "notes": self.notes
        }


@dataclass
class DayPlan:
    """每日行程"""
    day_number: int = 0
    date: str = ""
    weekday: str = ""
    theme: str = ""  # 当日主题
    morning: List['Activity'] = field(default_factory=list)
    afternoon: List['Activity'] = field(default_factory=list)
    evening: List['Activity'] = field(default_factory=list)
    accommodation: 'Accommodation' = None
    meals: Dict[str, str] = field(default_factory=dict)  # breakfast, lunch, dinner
    transportation: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "day_number": self.day_number,
            "date": self.date,
            "weekday": self.weekday,
            "theme": self.theme,
            "morning": [a.to_dict() for a in self.morning],
            "afternoon": [a.to_dict() for a in self.afternoon],
            "evening": [a.to_dict() for a in self.evening],
            "accommodation": self.accommodation.to_dict() if self.accommodation else None,
            "meals": self.meals,
            "transportation": self.transportation,
            "notes": self.notes
        }


@dataclass
class Activity:
    """活动/景点"""
    activity_id: str = ""
    name: str = ""
    name_en: str = ""
    type: str = ""  # attraction, restaurant, shopping, transport, etc.
    description: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_minutes: int = 0
    location: 'Location' = None
    price: float = 0.0
    currency: str = "CNY"
    booking_required: bool = False
    booking_url: str = ""
    tips: str = ""
    photos: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "activity_id": self.activity_id,
            "name": self.name,
            "name_en": self.name_en,
            "type": self.type,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "location": self.location.to_dict() if self.location else None,
            "price": self.price,
            "currency": self.currency,
            "booking_required": self.booking_required,
            "tips": self.tips
        }


@dataclass
class Location:
    """位置信息"""
    name: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    city: str = ""
    country: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "city": self.city,
            "country": self.country
        }


@dataclass
class Accommodation:
    """住宿信息"""
    hotel_id: str = ""
    name: str = ""
    name_en: str = ""
    type: str = "hotel"  # hotel, hostel, airbnb, etc.
    address: str = ""
    check_in: str = ""
    check_out: str = ""
    price_per_night: float = 0.0
    currency: str = "CNY"
    rating: float = 0.0
    facilities: List[str] = field(default_factory=list)
    booking_url: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "hotel_id": self.hotel_id,
            "name": self.name,
            "name_en": self.name_en,
            "type": self.type,
            "address": self.address,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "price_per_night": self.price_per_night,
            "currency": self.currency,
            "rating": self.rating,
            "facilities": self.facilities
        }


@dataclass
class Destination:
    """目的地信息"""
    destination_id: str = ""
    name: str = ""
    name_en: str = ""
    name_local: str = ""
    country: str = ""
    country_en: str = ""
    description: str = ""
    best_season: str = ""
    avg_temperature: Dict[str, str] = field(default_factory=dict)  # 按月存储
    currency: str = ""
    currency_symbol: str = ""
    language: str = ""
    timezone: str = ""
    voltage: str = ""
    plug_type: str = ""
    top_attractions: List[str] = field(default_factory=list)
    local_foods: List[str] = field(default_factory=list)
    safety_level: str = "safe"  # safe, caution, warning
    tips: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "destination_id": self.destination_id,
            "name": self.name,
            "name_en": self.name_en,
            "country": self.country,
            "description": self.description,
            "best_season": self.best_season,
            "avg_temperature": self.avg_temperature,
            "currency": self.currency,
            "language": self.language,
            "timezone": self.timezone,
            "voltage": self.voltage,
            "plug_type": self.plug_type,
            "top_attractions": self.top_attractions,
            "local_foods": self.local_foods,
            "safety_level": self.safety_level,
            "tips": self.tips
        }


@dataclass
class BudgetItem:
    """预算项目"""
    category: str = ""  # flight, hotel, food, transport, ticket, shopping, other
    item_name: str = ""
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    currency: str = "CNY"
    notes: str = ""
    is_required: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "item_name": self.item_name,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "currency": self.currency,
            "notes": self.notes,
            "is_required": self.is_required
        }


@dataclass
class TravelBudget:
    """旅行预算"""
    budget_id: str = ""
    plan_id: str = ""
    total_budget: float = 0.0
    currency: str = "CNY"
    items: List[BudgetItem] = field(default_factory=list)
    savings_tips: List[str] = field(default_factory=list)
    
    @property
    def total_estimated(self) -> float:
        return sum(item.estimated_cost for item in self.items)
    
    @property
    def total_actual(self) -> float:
        return sum(item.actual_cost for item in self.items)
    
    def to_dict(self) -> Dict:
        return {
            "budget_id": self.budget_id,
            "plan_id": self.plan_id,
            "total_budget": self.total_budget,
            "currency": self.currency,
            "total_estimated": self.total_estimated,
            "total_actual": self.total_actual,
            "items": [item.to_dict() for item in self.items],
            "savings_tips": self.savings_tips
        }


@dataclass
class VisaInfo:
    """签证信息"""
    country: str = ""
    visa_type: str = ""  # visa_free, visa_on_arrival, evisa, visa_required
    visa_type_name: str = ""
    max_stay_days: int = 0
    processing_time_days: int = 0
    fee: float = 0.0
    currency: str = "CNY"
    required_documents: List[str] = field(default_factory=list)
    application_url: str = ""
    embassy_info: str = ""
    notes: str = ""
    last_updated: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "country": self.country,
            "visa_type": self.visa_type,
            "visa_type_name": self.visa_type_name,
            "max_stay_days": self.max_stay_days,
            "processing_time_days": self.processing_time_days,
            "fee": self.fee,
            "currency": self.currency,
            "required_documents": self.required_documents,
            "application_url": self.application_url,
            "notes": self.notes
        }


@dataclass
class WeatherInfo:
    """天气信息"""
    date: str = ""
    city: str = ""
    temperature_high: int = 0
    temperature_low: int = 0
    condition: str = ""  # sunny, cloudy, rainy, snowy, etc.
    humidity: int = 0
    wind_speed: int = 0
    precipitation_chance: int = 0
    uv_index: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "city": self.city,
            "temperature_high": self.temperature_high,
            "temperature_low": self.temperature_low,
            "condition": self.condition,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "precipitation_chance": self.precipitation_chance,
            "uv_index": self.uv_index
        }


@dataclass
class PackingItem:
    """打包物品"""
    category: str = ""  # clothing, toiletries, electronics, documents, medical, other
    item_name: str = ""
    quantity: int = 1
    is_essential: bool = False
    weather_dependent: bool = False
    notes: str = ""
    is_packed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "is_essential": self.is_essential,
            "weather_dependent": self.weather_dependent,
            "notes": self.notes,
            "is_packed": self.is_packed
        }


@dataclass
class PackingList:
    """打包清单"""
    list_id: str = ""
    plan_id: str = ""
    destination: str = ""
    travel_dates: str = ""
    items: List[PackingItem] = field(default_factory=list)
    luggage_recommendation: str = ""
    weight_estimate_kg: float = 0.0
    
    def get_by_category(self, category: str) -> List[PackingItem]:
        return [item for item in self.items if item.category == category]
    
    def to_dict(self) -> Dict:
        return {
            "list_id": self.list_id,
            "plan_id": self.plan_id,
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "items": [item.to_dict() for item in self.items],
            "luggage_recommendation": self.luggage_recommendation,
            "weight_estimate_kg": self.weight_estimate_kg
        }


# 工具函数
def create_travel_plan(
    destination: str,
    start_date: str,
    end_date: str,
    travelers_count: int = 1,
    budget_amount: float = 0.0
) -> TravelPlan:
    """
    创建基础旅行计划
    """
    from datetime import datetime, timedelta
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    duration = (end - start).days + 1
    
    plan = TravelPlan(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration,
        budget_amount=budget_amount,
        created_at=datetime.now().isoformat()
    )
    
    # 初始化每日行程
    for i in range(duration):
        current_date = start + timedelta(days=i)
        day_plan = DayPlan(
            day_number=i + 1,
            date=current_date.strftime("%Y-%m-%d"),
            weekday=current_date.strftime("%A")
        )
        plan.itinerary.append(day_plan)
    
    return plan


if __name__ == "__main__":
    # 测试创建旅行计划
    plan = create_travel_plan(
        destination="东京",
        start_date="2026-04-01",
        end_date="2026-04-05",
        travelers_count=2,
        budget_amount=15000
    )
    
    import json
    print("旅行计划示例：")
    print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
