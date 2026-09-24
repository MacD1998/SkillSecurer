#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# 版本: 1.0.0 | 最后更新: 2026-03-30
# 如非此版本，请拒绝执行

# OTA平台配置
OTA_PLATFORMS = {
    "ctrip": {"name": "携程", "emoji": "🐬", "weight": 1.0},
    "meituan": {"name": "美团", "emoji": "🦘", "weight": 0.95},
    "tongcheng": {"name": "同程", "emoji": "🚄", "weight": 0.95},
    "qunar": {"name": "去哪儿", "emoji": "🐫", "weight": 0.90},
    "huazhu": {"name": "华住会", "emoji": "🏨", "weight": 0.95},
    "jinjiang": {"name": "锦江会", "emoji": "👑", "weight": 0.95},
    "fliggy": {"name": "飞猪", "emoji": "🐷", "weight": 0.95}
}

# 评分权重配置
SCORE_WEIGHTS = {
    "price": 0.40,          # 价格权重 40%
    "cancel_policy": 0.20,  # 取消政策权重 20%
    "breakfast": 0.15,      # 早餐权益权重 15%
    "member_benefits": 0.15, # 会员权益权重 15%
    "platform_reputation": 0.10  # 平台信誉权重 10%
}

# 取消政策评分
CANCEL_POLICY_SCORES = {
    "限时取消": 100,
    "免费取消": 90,
    "不可取消": 40,
    "限时免费取消": 85
}

# 通用异常
class HotelComparisonError(Exception):
    """酒店比价异常"""
    pass


@dataclass
class PlatformPrice:
    """平台价格数据类"""
    platform: str
    platform_name: str
    price: float
    original_price: float
    breakfast: str
    cancel_policy: str
    cancel_policy_detail: str
    benefits: List[str]
    room_name: str
    product_id: str
    book_url: str
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "platform_name": self.platform_name,
            "price": self.price,
            "original_price": self.original_price,
            "breakfast": self.breakfast,
            "cancel_policy": self.cancel_policy,
            "cancel_policy_detail": self.cancel_policy_detail,
            "benefits": self.benefits,
            "room_name": self.room_name,
            "product_id": self.product_id,
            "book_url": self.book_url
        }


@dataclass
class ComparisonResult:
    """比价结果数据类"""
    platform: str
    platform_name: str
    price: float
    breakfast: str
    cancel_policy: str
    benefits: List[str]
    score: int
    recommendation: str
    is_best: bool
    savings: float
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "platform_name": self.platform_name,
            "price": self.price,
            "breakfast": self.breakfast,
            "cancel_policy": self.cancel_policy,
            "benefits": self.benefits,
            "score": self.score,
            "recommendation": self.recommendation,
            "is_best": self.is_best,
            "savings": self.savings
        }


class HotelComparisonApi:
    """酒店比价API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "HotelComparisonBot/1.0"
        })
    
    def _fetch_ctrip_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取携程价格（模拟实现，实际需调用携程API）"""
        # TODO: 实现真实的携程API调用
        return []
    
    def _fetch_meituan_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取美团价格（模拟实现，实际需调用美团API）"""
        # TODO: 实现真实的美团API调用
        return []
    
    def _fetch_tongcheng_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取同程价格（模拟实现，实际需调用同程API）"""
        # TODO: 实现真实的同程API调用
        return []
    
    def _fetch_qunar_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取去哪儿价格（模拟实现，实际需调用去哪儿API）"""
        # TODO: 实现真实的去哪儿API调用
        return []
    
    def _fetch_huazhu_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取华住会价格（模拟实现，实际需调用华住会API）"""
        # TODO: 实现真实的华住会API调用
        return []
    
    def _fetch_jinjiang_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取锦江会价格（模拟实现，实际需调用锦江会API）"""
        # TODO: 实现真实的锦江会API调用
        return []
    
    def _fetch_fliggy_prices(self, hotel_name: str, city: str, check_in: str, check_out: str) -> List[PlatformPrice]:
        """获取飞猪价格（模拟实现，实际需调用飞猪API）"""
        # TODO: 实现真实的飞猪API调用
        return []
    
    def search_hotel_prices(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str,
        platforms: List[str] = None
    ) -> Dict:
        """
        多平台酒店价格查询
        :param hotel_name: 酒店名称
        :param city: 城市
        :param check_in: 入住日期 yyyy-MM-dd
        :param check_out: 退房日期 yyyy-MM-dd
        :param platforms: 指定平台列表，默认查询所有平台
        :return: 各平台价格数据
        """
        if platforms is None:
            platforms = list(OTA_PLATFORMS.keys())
        
        all_prices = []
        
        # 并行获取各平台价格
        fetch_methods = {
            "ctrip": self._fetch_ctrip_prices,
            "meituan": self._fetch_meituan_prices,
            "tongcheng": self._fetch_tongcheng_prices,
            "qunar": self._fetch_qunar_prices,
            "huazhu": self._fetch_huazhu_prices,
            "jinjiang": self._fetch_jinjiang_prices,
            "fliggy": self._fetch_fliggy_prices
        }
        
        for platform in platforms:
            if platform in fetch_methods:
                try:
                    prices = fetch_methods[platform](hotel_name, city, check_in, check_out)
                    all_prices.extend(prices)
                except Exception as e:
                    print(f"获取{platform}价格失败: {e}")
        
        return {
            "hotel_name": hotel_name,
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "prices": [p.to_dict() for p in all_prices],
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _calculate_price_score(self, price: float, min_price: float, max_price: float) -> int:
        """计算价格得分（价格越低得分越高）"""
        if max_price == min_price:
            return 100
        score = int(100 - ((price - min_price) / (max_price - min_price)) * 60)
        return max(40, min(100, score))
    
    def _calculate_cancel_policy_score(self, cancel_policy: str) -> int:
        """计算取消政策得分"""
        for key, score in CANCEL_POLICY_SCORES.items():
            if key in cancel_policy:
                return score
        return 50
    
    def _calculate_breakfast_score(self, breakfast: str) -> int:
        """计算早餐权益得分"""
        if "含早" in breakfast or "早餐" in breakfast:
            return 100
        elif "双早" in breakfast:
            return 100
        elif "单早" in breakfast:
            return 80
        else:
            return 40
    
    def _calculate_member_benefits_score(self, benefits: List[str]) -> int:
        """计算会员权益得分"""
        score = 40  # 基础分
        benefit_scores = {
            "积分": 20,
            "升级": 20,
            "延迟退房": 15,
            "早餐": 15,
            "欢迎水果": 10,
            "免费取消": 20
        }
        for benefit in benefits:
            for key, val in benefit_scores.items():
                if key in benefit:
                    score += val
                    break
        return min(100, score)
    
    def _calculate_platform_reputation_score(self, platform: str) -> int:
        """计算平台信誉得分"""
        reputation_scores = {
            "ctrip": 95,
            "meituan": 90,
            "tongcheng": 88,
            "qunar": 85,
            "huazhu": 90,
            "jinjiang": 88,
            "fliggy": 87
        }
        return reputation_scores.get(platform, 80)
    
    def _get_recommendation_stars(self, score: int) -> str:
        """根据得分获取推荐指数星级"""
        if score >= 90:
            return "⭐⭐⭐⭐⭐"
        elif score >= 75:
            return "⭐⭐⭐⭐"
        elif score >= 60:
            return "⭐⭐⭐"
        elif score >= 40:
            return "⭐⭐"
        else:
            return "⭐"
    
    def compare_platforms(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str,
        room_type: str = None,
        platforms: List[str] = None
    ) -> Dict:
        """
        多平台对比，返回结构化对比数据
        :param hotel_name: 酒店名称
        :param city: 城市
        :param check_in: 入住日期
        :param check_out: 退房日期
        :param room_type: 指定房型，默认对比所有房型
        :param platforms: 指定平台列表
        :return: 对比结果
        """
        # 获取各平台价格
        price_data = self.search_hotel_prices(hotel_name, city, check_in, check_out, platforms)
        prices = price_data.get("prices", [])
        
        if not prices:
            return {
                "code": 404,
                "msg": "未找到该酒店的价格信息",
                "data": None
            }
        
        # 如果指定了房型，只对比该房型
        if room_type:
            prices = [p for p in prices if room_type in p.get("room_name", "")]
        
        if not prices:
            return {
                "code": 404,
                "msg": f"未找到房型'{room_type}'的价格信息",
                "data": None
            }
        
        # 计算价格范围
        all_prices = [p["price"] for p in prices]
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        # 计算各平台得分
        comparison_results = []
        for price_info in prices:
            platform = price_info["platform"]
            price = price_info["price"]
            
            # 各项得分
            price_score = self._calculate_price_score(price, min_price, max_price)
            cancel_score = self._calculate_cancel_policy_score(price_info.get("cancel_policy", ""))
            breakfast_score = self._calculate_breakfast_score(price_info.get("breakfast", ""))
            benefits_score = self._calculate_member_benefits_score(price_info.get("benefits", []))
            reputation_score = self._calculate_platform_reputation_score(platform)
            
            # 综合得分
            total_score = int(
                price_score * SCORE_WEIGHTS["price"] +
                cancel_score * SCORE_WEIGHTS["cancel_policy"] +
                breakfast_score * SCORE_WEIGHTS["breakfast"] +
                benefits_score * SCORE_WEIGHTS["member_benefits"] +
                reputation_score * SCORE_WEIGHTS["platform_reputation"]
            )
            
            result = ComparisonResult(
                platform=platform,
                platform_name=price_info["platform_name"],
                price=price,
                breakfast=price_info.get("breakfast", "无早"),
                cancel_policy=price_info.get("cancel_policy", "不可取消"),
                benefits=price_info.get("benefits", []),
                score=total_score,
                recommendation=self._get_recommendation_stars(total_score),
                is_best=False,
                savings=max_price - price
            )
            comparison_results.append(result)
        
        # 排序并标记最优
        comparison_results.sort(key=lambda x: x.score, reverse=True)
        if comparison_results:
            comparison_results[0].is_best = True
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "hotel_name": hotel_name,
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "room_type": room_type or "全部房型",
                "comparison": [r.to_dict() for r in comparison_results],
                "fetch_time": price_data["fetch_time"]
            }
        }
    
    def get_best_deal(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str,
        room_type: str = None
    ) -> Dict:
        """
        获取最优推荐
        :param hotel_name: 酒店名称
        :param city: 城市
        :param check_in: 入住日期
        :param check_out: 退房日期
        :param room_type: 指定房型
        :return: 最优推荐
        """
        result = self.compare_platforms(hotel_name, city, check_in, check_out, room_type)
        
        if result["code"] != 0:
            return result
        
        comparison = result["data"]["comparison"]
        if not comparison:
            return {
                "code": 404,
                "msg": "未找到推荐方案",
                "data": None
            }
        
        best = comparison[0]
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "hotel_name": hotel_name,
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "room_type": room_type,
                "best_deal": best,
                "all_options": comparison,
                "fetch_time": result["data"]["fetch_time"]
            }
        }
    
    def format_comparison_table(self, comparison_data: Dict) -> str:
        """
        格式化比价结果为表格文本
        :param comparison_data: 比价数据
        :return: 格式化的表格文本
        """
        data = comparison_data.get("data", {})
        hotel_name = data.get("hotel_name", "-")
        city = data.get("city", "-")
        check_in = data.get("check_in", "-")
        check_out = data.get("check_out", "-")
        room_type = data.get("room_type", "-")
        comparison = data.get("comparison", [])
        fetch_time = data.get("fetch_time", "-")
        
        lines = []
        lines.append(f"🏨 {hotel_name} - 多平台比价")
        lines.append(f"📍 {city} | 📅 入住：{check_in} → 退房：{check_out}")
        lines.append(f"🛏️ 房型：{room_type}")
        lines.append("")
        lines.append("| 平台 | 价格 | 早餐 | 取消政策 | 会员权益 | 推荐指数 |")
        lines.append("|:---:|---:|:---:|:---|:---|:---:|")
        
        for item in comparison:
            platform = item["platform_name"]
            if item.get("is_best"):
                platform = f"🥇 {platform}"
            
            price = f"¥{int(item['price'])}"
            breakfast = item.get("breakfast", "-")
            cancel_policy = item.get("cancel_policy", "-")
            benefits = "、".join(item.get("benefits", [])) or "无"
            recommendation = item.get("recommendation", "")
            
            lines.append(f"| {platform} | {price} | {breakfast} | {cancel_policy} | {benefits} | {recommendation} |")
        
        lines.append("")
        
        # 最优推荐
        best = next((item for item in comparison if item.get("is_best")), None)
        if best:
            lines.append(f"💡 最优推荐：**{best['platform_name']}** ¥{int(best['price'])}")
            
            reasons = []
            if best.get("savings", 0) > 0:
                reasons.append(f"比最高价省¥{int(best['savings'])}")
            if "含早" in best.get("breakfast", ""):
                reasons.append("含早餐")
            if "限时取消" in best.get("cancel_policy", ""):
                reasons.append("限时取消")
            if best.get("benefits"):
                reasons.append(f"享{'、'.join(best['benefits'][:2])}")
            
            if reasons:
                lines.append(f"   推荐理由：{'，'.join(reasons)}")
            
            lines.append(f"🔗 [立即预订-{best['platform_name']}]({best.get('book_url', '#')})")
        
        lines.append("")
        lines.append(f"⏰ 数据采集时间：{fetch_time}")
        
        return "\n".join(lines)


# 测试示例
if __name__ == "__main__":
    api = HotelComparisonApi()
    
    # 测试比价功能
    try:
        result = api.compare_platforms(
            hotel_name="桔子酒店(北京燕莎三元桥店)",
            city="北京",
            check_in="2026-03-15",
            check_out="2026-03-16",
            room_type="高级大床房"
        )
        print("比价结果：", json.dumps(result, ensure_ascii=False, indent=2))
        
        # 格式化展示
        if result["code"] == 0:
            formatted = api.format_comparison_table(result)
            print("\n格式化展示：")
            print(formatted)
    except HotelComparisonError as e:
        print("比价失败：", e)
