#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI目的地指南技能 - 核心API
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import sys
sys.path.append('../../shared')
from travel_models import Destination


class DestinationError(Exception):
    """目的地指南异常"""
    pass


# 模拟目的地数据库
DESTINATIONS_DB = {
    "东京": {
        "destination_id": "dest_tokyo_001",
        "name": "东京",
        "name_en": "Tokyo",
        "name_local": "東京",
        "country": "日本",
        "country_en": "Japan",
        "description": "日本首都，世界级大都市，传统与现代完美融合。既有浅草寺、明治神宫等传统文化景点，也有涩谷、新宿等时尚购物区。美食、购物、文化体验一应俱全。",
        "best_season": "春季（3-5月樱花季）和秋季（9-11月红叶季）",
        "avg_temperature": {
            "spring": "15-20°C",
            "summer": "25-30°C",
            "autumn": "15-22°C",
            "winter": "5-10°C"
        },
        "currency": "日元",
        "currency_code": "JPY",
        "currency_symbol": "¥",
        "language": "日语",
        "timezone": "JST (UTC+9)",
        "voltage": "100V",
        "plug_type": "A/B",
        "top_attractions": ["浅草寺", "东京晴空塔", "明治神宫", "涩谷十字路口", "东京塔"],
        "local_foods": ["寿司", "拉面", "天妇罗", "烧鸟", "和牛"],
        "safety_level": "safe",
        "tips": [
            "地铁内请保持安静，手机调至静音",
            "垃圾分类严格，请随身携带垃圾袋",
            "日本没有小费文化，不需要给小费",
            "很多地方只收现金，请准备足够日元",
            "公共场所禁烟，请在指定区域吸烟"
        ]
    },
    "大阪": {
        "destination_id": "dest_osaka_001",
        "name": "大阪",
        "name_en": "Osaka",
        "name_local": "大阪",
        "country": "日本",
        "country_en": "Japan",
        "description": "日本第二大城市，关西地区的经济文化中心。以美食闻名，有'天下的厨房'之称。大阪人热情开朗，方言独特。道顿堀、心斋桥是购物美食的天堂。",
        "best_season": "春季（3-5月）和秋季（10-11月）",
        "avg_temperature": {
            "spring": "15-20°C",
            "summer": "25-32°C",
            "autumn": "15-22°C",
            "winter": "5-10°C"
        },
        "currency": "日元",
        "currency_code": "JPY",
        "currency_symbol": "¥",
        "language": "日语（关西方言）",
        "timezone": "JST (UTC+9)",
        "voltage": "100V",
        "plug_type": "A/B",
        "top_attractions": ["大阪城", "道顿堀", "心斋桥", "环球影城", "通天阁"],
        "local_foods": ["章鱼烧", "大阪烧", "串炸", "河豚料理", "螃蟹料理"],
        "safety_level": "safe",
        "tips": [
            "大阪人比较热情直接，不用太拘谨",
            "道顿堀晚上最热闹，建议傍晚前往",
            "环球影城建议提前购买快速通关券",
            "大阪周游卡很划算，包含多个景点",
            "站在手扶梯右侧，左侧留给急行的人"
        ]
    },
    "京都": {
        "destination_id": "dest_kyoto_001",
        "name": "京都",
        "name_en": "Kyoto",
        "name_local": "京都",
        "country": "日本",
        "country_en": "Japan",
        "description": "日本千年古都，拥有17处世界遗产，是体验日本传统文化的最佳地点。寺庙、神社、庭园、艺伎文化，处处散发着古典美。",
        "best_season": "春季（3-4月樱花季）和秋季（11月红叶季）",
        "avg_temperature": {
            "spring": "10-20°C",
            "summer": "25-32°C",
            "autumn": "10-22°C",
            "winter": "0-10°C"
        },
        "currency": "日元",
        "currency_code": "JPY",
        "currency_symbol": "¥",
        "language": "日语（京都方言）",
        "timezone": "JST (UTC+9)",
        "voltage": "100V",
        "plug_type": "A/B",
        "top_attractions": ["清水寺", "金阁寺", "伏见稻荷大社", "岚山", "二条城"],
        "local_foods": ["怀石料理", "汤豆腐", "抹茶甜点", "京都拉面", "渍物"],
        "safety_level": "safe",
        "tips": [
            "寺庙神社参拜时注意礼仪",
            "穿和服游览更有氛围，可租借",
            "岚山小火车需提前预约",
            "清水寺清晨人少，建议早去",
            "祗园可能遇到艺伎，请勿阻挡拍照"
        ]
    },
    "巴黎": {
        "destination_id": "dest_paris_001",
        "name": "巴黎",
        "name_en": "Paris",
        "name_local": "Paris",
        "country": "法国",
        "country_en": "France",
        "description": "法国首都，世界艺术、时尚、美食之都。埃菲尔铁塔、卢浮宫、凯旋门等标志性建筑闻名世界。塞纳河畔的浪漫，咖啡馆的悠闲，让巴黎成为无数人的梦想之地。",
        "best_season": "春季（4-6月）和秋季（9-10月）",
        "avg_temperature": {
            "spring": "10-18°C",
            "summer": "18-25°C",
            "autumn": "10-18°C",
            "winter": "3-8°C"
        },
        "currency": "欧元",
        "currency_code": "EUR",
        "currency_symbol": "€",
        "language": "法语",
        "timezone": "CET (UTC+1)",
        "voltage": "230V",
        "plug_type": "C/E",
        "top_attractions": ["埃菲尔铁塔", "卢浮宫", "凯旋门", "圣母院", "蒙马特高地"],
        "local_foods": ["法式长棍", "可颂", "马卡龙", "鹅肝", "法式洋葱汤"],
        "safety_level": "caution",
        "tips": [
            "注意保管好随身物品，防范小偷",
            "餐厅用餐需要给小费（账单的10-15%）",
            "很多商店周日不营业",
            "学几句基本法语会更受欢迎",
            "博物馆通票很划算，可免排队"
        ]
    }
}

# 景点详细数据库
ATTRACTIONS_DB = {
    "东京": [
        {
            "id": "tokyo_001",
            "name": "浅草寺",
            "name_en": "Senso-ji",
            "description": "东京最古老的寺庙，建于628年。标志性的雷门大灯笼高3.9米，重700公斤。寺庙前的仲见世通是购买纪念品的好地方。",
            "rating": 4.5,
            "review_count": 85420,
            "open_time": "06:00-17:00（主殿）",
            "price": 0,
            "duration": "2小时",
            "area": "浅草",
            "tags": ["寺庙", "历史", "购物"],
            "tips": "早晨6点开门，人少适合拍照；每月18日有庙会"
        },
        {
            "id": "tokyo_002",
            "name": "东京晴空塔",
            "name_en": "Tokyo Skytree",
            "description": "高634米，是世界第一高塔。350米和450米两处观景台可俯瞰整个东京。塔下是Solamachi购物中心。",
            "rating": 4.4,
            "review_count": 62300,
            "open_time": "08:00-22:00",
            "price": 2100,
            "duration": "3小时",
            "area": "押上",
            "tags": ["观景台", "地标", "购物"],
            "tips": "提前网上购票可省排队时间；傍晚登塔可同时看日落和夜景"
        },
        {
            "id": "tokyo_003",
            "name": "明治神宫",
            "name_en": "Meiji Shrine",
            "description": "供奉明治天皇和昭宪皇太后，是东京最大的神社。占地70公顷，是城市中的绿洲。",
            "rating": 4.6,
            "review_count": 45800,
            "open_time": "日出-日落",
            "price": 0,
            "duration": "1.5小时",
            "area": "原宿",
            "tags": ["神社", "自然", "文化"],
            "tips": "周末可能遇到传统婚礼；原宿口进，涩谷口出最顺路"
        },
        {
            "id": "tokyo_004",
            "name": "涩谷十字路口",
            "name_en": "Shibuya Crossing",
            "description": "世界上最繁忙的人行横道，每分钟约3,000人通过。周边是年轻人文化的发源地，充满时尚活力。",
            "rating": 4.3,
            "review_count": 38200,
            "open_time": "全天",
            "price": 0,
            "duration": "30分钟",
            "area": "涩谷",
            "tags": ["地标", "拍照", "购物"],
            "tips": "星巴克二楼是最佳观赏点；忠犬八公像也在附近"
        },
        {
            "id": "tokyo_005",
            "name": "东京塔",
            "name_en": "Tokyo Tower",
            "description": "东京地标，高333米，红白相间的塔身灵感来自埃菲尔铁塔。海贼王主题乐园位于3-5楼。",
            "rating": 4.2,
            "review_count": 52100,
            "open_time": "09:00-23:00",
            "price": 1200,
            "duration": "2小时",
            "area": "芝公园",
            "tags": ["观景台", "地标", "娱乐"],
            "tips": "夜晚灯光会根据季节变化颜色；芝公园是赏樱胜地"
        }
    ],
    "大阪": [
        {
            "id": "osaka_001",
            "name": "大阪城",
            "name_en": "Osaka Castle",
            "description": "日本三大名城之一，丰臣秀吉所建。天守阁内是历史博物馆，周围公园是赏樱胜地。",
            "rating": 4.4,
            "review_count": 45600,
            "open_time": "09:00-17:00",
            "price": 600,
            "duration": "2.5小时",
            "area": "中央区",
            "tags": ["城堡", "历史", "樱花"],
            "tips": "天守阁电梯通常排队，建议走楼梯；春天樱花季最美"
        },
        {
            "id": "osaka_002",
            "name": "道顿堀",
            "name_en": "Dotonbori",
            "description": "大阪最繁华的商业区，以巨大的霓虹灯广告牌和美食闻名。格力高跑步人广告牌是标志性景观。",
            "rating": 4.5,
            "review_count": 67800,
            "open_time": "全天（店铺约11:00-23:00）",
            "price": 0,
            "duration": "3小时",
            "area": "中央区",
            "tags": ["美食", "购物", "夜景"],
            "tips": "晚上最热闹，建议傍晚前往；必尝章鱼烧和大阪烧"
        }
    ],
    "京都": [
        {
            "id": "kyoto_001",
            "name": "清水寺",
            "name_en": "Kiyomizu-dera",
            "description": "京都最古老的寺院，建于778年。著名的清水舞台悬空而建，不使用一根钉子。",
            "rating": 4.6,
            "review_count": 72300,
            "open_time": "06:00-18:00",
            "price": 400,
            "duration": "2小时",
            "area": "东山区",
            "tags": ["寺庙", "世界遗产", "樱花"],
            "tips": "清晨6点开门，人少适合拍照；三年坂二年坂适合穿和服漫步"
        },
        {
            "id": "kyoto_002",
            "name": "金阁寺",
            "name_en": "Kinkaku-ji",
            "description": "正式名称为鹿苑寺，因金箔覆盖的三层楼阁建筑而闻名。倒映在镜湖池中的金阁是最经典的画面。",
            "rating": 4.5,
            "review_count": 58900,
            "open_time": "09:00-17:00",
            "price": 400,
            "duration": "1小时",
            "area": "北区",
            "tags": ["寺庙", "世界遗产", "庭院"],
            "tips": "晴天时金阁最耀眼；门票是写有祝福语的御守，值得收藏"
        }
    ]
}

# 美食数据库
FOODS_DB = {
    "东京": [
        {
            "name": "寿司",
            "description": "日本最具代表性的美食，新鲜的海鲜配上醋饭，简单却极致美味。",
            "recommended_places": ["筑地市场", "银座数寄屋桥次郎", "回转寿司根室花丸"],
            "avg_price": "¥2,000-10,000",
            "must_try": ["金枪鱼", "海胆", "鲑鱼子"]
        },
        {
            "name": "拉面",
            "description": "东京拉面以酱油豚骨汤底闻名，面条劲道，配料丰富。",
            "recommended_places": ["一兰拉面", "AFURI", "入鹿"],
            "avg_price": "¥800-1,500",
            "must_try": ["豚骨拉面", "沾面", "鸡白汤拉面"]
        },
        {
            "name": "天妇罗",
            "description": "酥脆的面衣包裹新鲜食材，油炸却不油腻，是江户前料理的代表。",
            "recommended_places": ["浅草大黑家", "银座天一", "土手之伊势屋"],
            "avg_price": "¥1,500-5,000",
            "must_try": ["虾天妇罗", "穴子天妇罗", "天妇罗盖饭"]
        }
    ],
    "大阪": [
        {
            "name": "章鱼烧",
            "description": "大阪的灵魂美食，外酥内软，章鱼肉Q弹，配上美乃滋和木鱼花。",
            "recommended_places": ["本家大たこ", "たこ家道顿堀くくる", "甲賀流"],
            "avg_price": "¥500-800",
            "must_try": ["原味章鱼烧", "芝士章鱼烧", "葱味章鱼烧"]
        },
        {
            "name": "大阪烧",
            "description": "日式 savory pancake，卷心菜、猪肉、海鲜混合煎制，淋上特制酱汁。",
            "recommended_places": ["美津の", "千房", "ぼてぢゅう"],
            "avg_price": "¥800-1,500",
            "must_try": ["猪肉大阪烧", "海鲜大阪烧", "摩登烧"]
        }
    ]
}


class DestinationGuide:
    """目的地指南"""
    
    def __init__(self):
        self.destinations_db = DESTINATIONS_DB
        self.attractions_db = ATTRACTIONS_DB
        self.foods_db = FOODS_DB
    
    def get_destination_overview(
        self,
        destination: str,
        language: str = "zh"
    ) -> Dict:
        """获取目的地概览"""
        dest_data = self.destinations_db.get(destination)
        
        if not dest_data:
            return {
                "code": 404,
                "msg": f"未找到目的地：{destination}",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": dest_data
        }
    
    def get_attractions(
        self,
        destination: str,
        category: str = None,
        count: int = 5
    ) -> Dict:
        """获取景点列表"""
        attractions = self.attractions_db.get(destination, [])
        
        if not attractions:
            return {
                "code": 404,
                "msg": f"未找到{destination}的景点信息",
                "data": None
            }
        
        # 根据分类筛选
        if category:
            attractions = [a for a in attractions if category in a.get("tags", [])]
        
        # 按评分排序
        attractions.sort(key=lambda x: x["rating"], reverse=True)
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "total": len(attractions),
                "attractions": attractions[:count]
            }
        }
    
    def get_local_foods(
        self,
        destination: str,
        food_type: str = None
    ) -> Dict:
        """获取当地美食"""
        foods = self.foods_db.get(destination, [])
        
        if not foods:
            return {
                "code": 404,
                "msg": f"未找到{destination}的美食信息",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "foods": foods
            }
        }
    
    def get_transport_guide(self, destination: str) -> Dict:
        """获取交通指南"""
        transport_info = {
            "东京": {
                "airport": "成田机场(NRT)：主要国际航班，距市区60公里；羽田机场(HND)：主要国内航班，距市区20公里",
                "city_transport": "JR山手线（环状线）、东京地铁（13条线路）、都营地铁（4条线路）",
                "recommended_pass": "东京地铁3日券（¥1,500，无限次乘坐）；JR Pass（适合跨城市旅行）",
                "apps": ["Google Maps", "乘换案内", "Tokyo Metro App"]
            },
            "大阪": {
                "airport": "关西机场(KIX)：距市区50公里，可乘南海电铁或HARUKA特急",
                "city_transport": "大阪地铁、JR、阪急/阪神/南海私铁",
                "recommended_pass": "大阪周游卡（1日¥2,800，含景点门票）；ICOCA卡",
                "apps": ["Google Maps", "乘换案内"]
            },
            "京都": {
                "airport": "无机场，从关西机场乘HARUKA约75分钟",
                "city_transport": "市巴士（主要交通方式）、地铁（2条线路）、私铁",
                "recommended_pass": "京都巴士1日券（¥700）；关西周游卡",
                "apps": ["Google Maps", "京都巴士导航"]
            }
        }
        
        info = transport_info.get(destination)
        if not info:
            return {
                "code": 404,
                "msg": f"未找到{destination}的交通信息",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": info
        }
    
    def get_travel_tips(self, destination: str) -> Dict:
        """获取旅行贴士"""
        dest_data = self.destinations_db.get(destination)
        
        if not dest_data:
            return {
                "code": 404,
                "msg": f"未找到{destination}的信息",
                "data": None
            }
        
        tips = dest_data.get("tips", [])
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "safety_level": dest_data.get("safety_level"),
                "tips": tips
            }
        }
    
    def format_destination_guide(self, result: Dict, query_type: str = "all") -> str:
        """格式化目的地指南"""
        data = result.get("data", {})
        
        if not data:
            return "暂无该目的地信息"
        
        lines = []
        
        # 基本信息
        if query_type in ["all", "overview"]:
            lines.append(f"📍 {data.get('name', '')}目的地指南")
            lines.append("")
            lines.append("=" * 40)
            lines.append("")
            lines.append("🌟 基本信息")
            lines.append("━" * 40)
            lines.append(f"📍 位置：{data.get('country', '')}")
            lines.append(f"🗣️ 语言：{data.get('language', '')}")
            lines.append(f"💴 货币：{data.get('currency', '')} ({data.get('currency_symbol', '')})")
            lines.append(f"⏰ 时差：{data.get('timezone', '')}")
            lines.append(f"🔌 电压：{data.get('voltage', '')}，插头类型{data.get('plug_type', '')}")
            lines.append(f"🌡️ 最佳季节：{data.get('best_season', '')}")
            lines.append("")
            lines.append(f"📝 简介：{data.get('description', '')}")
            lines.append("")
        
        # 景点
        if query_type in ["all", "attractions"] and "attractions" in data:
            lines.append("🏯 必去景点")
            lines.append("━" * 40)
            for i, attr in enumerate(data["attractions"][:5], 1):
                lines.append(f"\n{i}. {attr.get('name', '')} ({attr.get('name_en', '')})")
                lines.append(f"   ⭐ 评分：{attr.get('rating', 0)}/5 ({attr.get('review_count', 0)}条评价)")
                lines.append(f"   🕐 开放时间：{attr.get('open_time', '')}")
                price = attr.get('price', 0)
                lines.append(f"   💴 门票：{'免费' if price == 0 else f'¥{price}'}")
                lines.append(f"   📝 {attr.get('description', '')[:60]}...")
                lines.append(f"   💡 贴士：{attr.get('tips', '')}")
            lines.append("")
        
        # 美食
        if query_type in ["all", "food"] and "foods" in data:
            lines.append("🍜 当地美食")
            lines.append("━" * 40)
            for food in data["foods"][:3]:
                lines.append(f"\n🍽️ {food.get('name', '')}")
                lines.append(f"   {food.get('description', '')}")
                lines.append(f"   📍 推荐：{', '.join(food.get('recommended_places', []))}")
                lines.append(f"   💰 人均：{food.get('avg_price', '')}")
            lines.append("")
        
        # 贴士
        if query_type in ["all", "tips"] and "tips" in data:
            lines.append("💡 实用贴士")
            lines.append("━" * 40)
            for tip in data["tips"]:
                lines.append(f"• {tip}")
            lines.append("")
        
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    guide = DestinationGuide()
    
    # 测试获取东京概览
    result = guide.get_destination_overview("东京")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60)
    print("格式化展示：")
    print("="*60)
    print(guide.format_destination_guide(result))
