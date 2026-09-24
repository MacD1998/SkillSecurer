#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI签证证件技能 - 核心API
"""

import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import sys
sys.path.append('../../shared')
from travel_models import VisaInfo


class VisaError(Exception):
    """签证查询异常"""
    pass


# 签证政策数据库
VISA_POLICY_DB = {
    ("日本", "中国"): {
        "visa_type": "visa_required",
        "visa_type_name": "需提前办理签证",
        "max_stay_days": 90,
        "processing_time": {
            "normal": "5-7个工作日",
            "express": "3个工作日",
            "rush": "1-2个工作日"
        },
        "fee": {
            "single_entry": 200,
            "multiple_entry": 400,
            "currency": "CNY"
        },
        "required_documents": [
            {"name": "护照原件", "description": "有效期6个月以上，至少2页空白页", "required": True, "notes": "旧护照如有也需提供"},
            {"name": "签证申请表", "description": "在线填写并打印，签名", "required": True, "template_url": "https://www.vfsglobal.cn/japan/china/"},
            {"name": "证件照片", "description": "2张2寸白底彩色证件照", "required": True, "specifications": "35mm×45mm，近6个月内拍摄"},
            {"name": "身份证复印件", "description": "正反面复印在同一页A4纸上", "required": True},
            {"name": "户口本复印件", "description": "全本复印（除空白页）", "required": True},
            {"name": "在职证明", "description": "单位抬头纸打印，加盖公章", "required": True, "notes": "需包含姓名、职务、收入、准假信息"},
            {"name": "营业执照复印件", "description": "加盖公章", "required": True},
            {"name": "银行流水", "description": "近6个月银行流水", "required": True, "notes": "余额建议3万以上"},
            {"name": "行程单", "description": "详细的旅行计划", "required": True},
            {"name": "机票酒店预订单", "description": "往返机票+全程酒店", "required": True}
        ],
        "application_process": [
            "准备材料",
            "在线预约",
            "递交材料",
            "缴纳费用",
            "等待审核",
            "领取护照"
        ],
        "tips": [
            "建议提前1个月申请",
            "材料需真实有效，虚假材料会导致拒签",
            "首次申请建议申请单次签证",
            "保持电话畅通，可能接到电调"
        ],
        "last_updated": "2026-03-30"
    },
    ("泰国", "中国"): {
        "visa_type": "visa_free",
        "visa_type_name": "免签",
        "max_stay_days": 30,
        "processing_time": None,
        "fee": None,
        "required_documents": [
            {"name": "护照原件", "description": "有效期6个月以上", "required": True},
            {"name": "往返机票", "description": "30天内返程机票", "required": True},
            {"name": "酒店预订单", "description": "全程酒店预订", "required": True},
            {"name": "现金", "description": "个人10000泰铢/家庭20000泰铢等值现金", "required": True, "notes": "可能抽查"}
        ],
        "application_process": None,
        "tips": [
            "免签入境可停留30天",
            "需准备往返机票和酒店订单",
            "建议携带足够现金以备抽查",
            "护照需有至少6个月有效期"
        ],
        "last_updated": "2026-03-30"
    },
    ("新加坡", "中国"): {
        "visa_type": "visa_free",
        "visa_type_name": "免签",
        "max_stay_days": 30,
        "processing_time": None,
        "fee": None,
        "required_documents": [
            {"name": "护照原件", "description": "有效期6个月以上", "required": True},
            {"name": "往返机票", "description": "30天内返程机票", "required": True},
            {"name": "酒店预订单", "description": "全程酒店预订", "required": True}
        ],
        "application_process": None,
        "tips": [
            "免签入境可停留30天",
            "需提前3天填写电子入境卡（SG Arrival Card）",
            "禁止携带口香糖入境"
        ],
        "last_updated": "2026-03-30"
    },
    ("美国", "中国"): {
        "visa_type": "visa_required",
        "visa_type_name": "需提前办理签证（需面签）",
        "max_stay_days": 180,
        "processing_time": {
            "normal": "面谈后3-5个工作日",
            "express": "面谈后1-2个工作日"
        },
        "fee": {
            "single_entry": 1100,
            "currency": "CNY"
        },
        "required_documents": [
            {"name": "护照原件", "description": "有效期6个月以上", "required": True},
            {"name": "DS-160确认页", "description": "在线填写后打印", "required": True},
            {"name": "面签预约确认页", "description": "预约成功后打印", "required": True},
            {"name": "证件照片", "description": "2寸白底彩色照片1张", "required": True, "specifications": "51mm×51mm"},
            {"name": "在职证明", "description": "单位抬头纸打印", "required": True},
            {"name": "银行流水", "description": "近6个月", "required": True},
            {"name": "资产证明", "description": "房产证、车辆证等", "required": False},
            {"name": "行程单", "description": "详细旅行计划", "required": True},
            {"name": "简历", "description": "英文简历", "required": True, "notes": "IT/科研等敏感行业需详细说明"}
        ],
        "application_process": [
            "在线填写DS-160表格",
            "缴纳签证费",
            "预约面签时间",
            "准备面签材料",
            "前往使馆面签",
            "等待护照寄回"
        ],
        "tips": [
            "建议提前3个月申请",
            "面签时需诚实回答",
            "敏感行业可能被行政审查（需额外2-4周）",
            "B1/B2签证有效期通常10年"
        ],
        "last_updated": "2026-03-30"
    },
    ("申根", "中国"): {
        "visa_type": "visa_required",
        "visa_type_name": "需提前办理申根签证",
        "max_stay_days": 90,
        "processing_time": {
            "normal": "10-15个工作日",
            "express": "5-7个工作日"
        },
        "fee": {
            "single_entry": 600,
            "currency": "CNY"
        },
        "required_documents": [
            {"name": "护照原件", "description": "有效期3个月以上，2页空白页", "required": True},
            {"name": "申根签证申请表", "description": "在线填写打印", "required": True},
            {"name": "证件照片", "description": "2张白底彩色照片", "required": True, "specifications": "35mm×45mm"},
            {"name": "旅行保险", "description": "保额3万欧元以上", "required": True},
            {"name": "在职证明", "description": "英文版，加盖公章", "required": True},
            {"name": "银行流水", "description": "近3-6个月", "required": True, "notes": "余额建议3-5万"},
            {"name": "行程单", "description": "详细行程", "required": True},
            {"name": "机票预订单", "description": "往返机票", "required": True},
            {"name": "酒店预订单", "description": "全程酒店", "required": True}
        ],
        "application_process": [
            "确定主申请国（停留时间最长的国家）",
            "在线预约",
            "准备材料",
            "递交材料并录指纹",
            "等待审核",
            "领取护照"
        ],
        "tips": [
            "需向停留时间最长的国家申请",
            "首次申请需本人到场录指纹",
            "建议提前1-2个月申请",
            "旅行保险必须覆盖整个申根区"
        ],
        "last_updated": "2026-03-30"
    }
}

# 使馆/签证中心信息
EMBASSY_DB = {
    "日本": [
        {"city": "北京", "address": "北京市朝阳区东三环北路38号院3号楼", "phone": "010-84004999", "hours": "周一至周五 08:00-15:00"},
        {"city": "上海", "address": "上海市黄浦区四川中路213号", "phone": "021-51859766", "hours": "周一至周五 08:00-15:00"},
        {"city": "广州", "address": "广州市天河区体育西路189号城建大厦", "phone": "020-38038563", "hours": "周一至周五 08:00-15:00"}
    ],
    "美国": [
        {"city": "北京", "address": "北京市朝阳区安家楼路55号", "phone": "010-56794700", "hours": "需预约"},
        {"city": "上海", "address": "上海市南京西路1038号梅龙镇广场8楼", "phone": "021-51915200", "hours": "需预约"},
        {"city": "广州", "address": "广州市天河区珠江新城华夏路", "phone": "020-38145200", "hours": "需预约"}
    ]
}


class VisaService:
    """签证服务"""
    
    def __init__(self):
        self.visa_policy_db = VISA_POLICY_DB
        self.embassy_db = EMBASSY_DB
    
    def check_visa_requirement(
        self,
        destination: str,
        nationality: str = "中国"
    ) -> Dict:
        """查询签证要求"""
        key = (destination, nationality)
        policy = self.visa_policy_db.get(key)
        
        if not policy:
            return {
                "code": 404,
                "msg": f"暂不支持查询{destination}的签证信息",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "nationality": nationality,
                **policy
            }
        }
    
    def get_document_checklist(
        self,
        destination: str,
        visa_type: str = "tourist"
    ) -> Dict:
        """获取材料清单"""
        result = self.check_visa_requirement(destination)
        
        if result["code"] != 0:
            return result
        
        documents = result["data"].get("required_documents", [])
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "visa_type": visa_type,
                "total_documents": len(documents),
                "required_documents": [d for d in documents if d.get("required")],
                "optional_documents": [d for d in documents if not d.get("required")]
            }
        }
    
    def get_application_process(self, destination: str) -> Dict:
        """获取办理流程"""
        result = self.check_visa_requirement(destination)
        
        if result["code"] != 0:
            return result
        
        process = result["data"].get("application_process")
        
        if not process:
            return {
                "code": 200,
                "msg": "该目的地无需办理签证",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "steps": process
            }
        }
    
    def check_passport_validity(
        self,
        passport_expiry: str,
        destination: str
    ) -> Dict:
        """检查护照有效性"""
        try:
            expiry_date = datetime.strptime(passport_expiry, "%Y-%m-%d")
            today = datetime.now()
            days_until_expiry = (expiry_date - today).days
            
            # 获取目的地要求
            result = self.check_visa_requirement(destination)
            required_months = 6  # 默认要求6个月
            
            if result["code"] == 0:
                # 从材料要求中提取
                for doc in result["data"].get("required_documents", []):
                    if "护照" in doc.get("name", ""):
                        desc = doc.get("description", "")
                        if "3个月" in desc:
                            required_months = 3
                            break
            
            required_days = required_months * 30
            
            if days_until_expiry < 0:
                status = "expired"
                message = f"⚠️ 护照已过期，请立即更换"
            elif days_until_expiry < required_days:
                status = "warning"
                message = f"⚠️ 护照有效期不足{required_months}个月，建议尽快更换"
            else:
                status = "valid"
                message = f"✅ 护照有效期充足（剩余{days_until_expiry}天）"
            
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "passport_expiry": passport_expiry,
                    "days_until_expiry": days_until_expiry,
                    "required_months": required_months,
                    "status": status,
                    "message": message
                }
            }
        except ValueError:
            return {
                "code": 400,
                "msg": "护照日期格式错误，应为yyyy-MM-dd",
                "data": None
            }
    
    def get_embassy_info(self, destination: str, city: str = None) -> Dict:
        """获取使馆/签证中心信息"""
        embassies = self.embassy_db.get(destination, [])
        
        if not embassies:
            return {
                "code": 404,
                "msg": f"暂不支持查询{destination}的使馆信息",
                "data": None
            }
        
        if city:
            embassies = [e for e in embassies if e["city"] == city]
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "destination": destination,
                "embassies": embassies
            }
        }
    
    def format_visa_info(self, result: Dict) -> str:
        """格式化签证信息"""
        data = result.get("data", {})
        
        if not data:
            return "暂无签证信息"
        
        lines = []
        lines.append(f"📋 {data.get('destination', '')}签证指南")
        lines.append("")
        lines.append("=" * 40)
        lines.append("")
        
        # 签证要求
        lines.append("🛂 签证要求")
        lines.append("━" * 40)
        lines.append(f"🇨🇳 国籍：{data.get('nationality', '中国')}")
        lines.append(f"🇯🇵 目的地：{data.get('destination', '')}")
        lines.append(f"📋 签证类型：{data.get('visa_type_name', '')}")
        max_days = data.get('max_stay_days')
        if max_days:
            lines.append(f"⏱️ 最长停留：{max_days}天")
        lines.append("")
        
        # 办理时间
        processing = data.get('processing_time')
        if processing:
            lines.append("⏰ 办理时间")
            lines.append("━" * 40)
            if isinstance(processing, dict):
                for key, value in processing.items():
                    key_name = {"normal": "📅 正常办理", "express": "⚡ 加急办理", "rush": "🚀 特急办理"}.get(key, key)
                    lines.append(f"{key_name}：{value}")
            else:
                lines.append(f"📅 办理时间：{processing}")
            lines.append("")
        
        # 费用
        fee = data.get('fee')
        if fee:
            lines.append("💰 签证费用")
            lines.append("━" * 40)
            currency = fee.get('currency', 'CNY')
            if 'single_entry' in fee:
                lines.append(f"🎫 单次入境：{currency}{fee['single_entry']}")
            if 'multiple_entry' in fee:
                lines.append(f"🎫 多次入境：{currency}{fee['multiple_entry']}")
            lines.append("")
        
        # 材料清单
        documents = data.get('required_documents', [])
        if documents:
            lines.append("📄 所需材料清单")
            lines.append("━" * 40)
            for i, doc in enumerate(documents, 1):
                name = doc.get('name', '')
                desc = doc.get('description', '')
                notes = doc.get('notes', '')
                lines.append(f"\n{i}. {name}")
                lines.append(f"   📋 {desc}")
                if notes:
                    lines.append(f"   💡 {notes}")
            lines.append("")
        
        # 办理流程
        process = data.get('application_process')
        if process:
            lines.append("📝 办理流程")
            lines.append("━" * 40)
            for i, step in enumerate(process, 1):
                lines.append(f"Step {i}: {step}")
            lines.append("")
        
        # 提示
        tips = data.get('tips', [])
        if tips:
            lines.append("💡 重要提示")
            lines.append("━" * 40)
            for tip in tips:
                lines.append(f"• {tip}")
            lines.append("")
        
        # 更新日期
        last_updated = data.get('last_updated')
        if last_updated:
            lines.append(f"\n📅 政策更新日期：{last_updated}")
            lines.append("⚠️ 以上信息仅供参考，请以官方最新要求为准")
        
        return "\n".join(lines)


# 测试
if __name__ == "__main__":
    service = VisaService()
    
    # 测试查询日本签证
    result = service.check_visa_requirement("日本")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "="*60)
    print("格式化签证信息：")
    print("="*60)
    print(service.format_visa_info(result))
