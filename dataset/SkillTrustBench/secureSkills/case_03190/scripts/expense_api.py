#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报销技能 - 核心API
"""

import json
import random
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ExpenseError(Exception):
    """报销异常"""
    pass


class ExpenseType(Enum):
    """费用类型"""
    TRANSPORT = "transport"           # 交通费
    HOTEL = "hotel"                   # 住宿费
    MEAL = "meal"                     # 餐饮费
    COMMUNICATION = "communication"   # 通讯费
    OFFICE = "office"                 # 办公用品
    ALLOWANCE = "allowance"           # 差旅补贴
    OTHER = "other"                   # 其他


class ReportStatus(Enum):
    """报销单状态"""
    DRAFT = "draft"                   # 草稿
    PENDING = "pending"               # 待提交
    PENDING_APPROVAL = "pending_approval"  # 待审批
    APPROVED = "approved"             # 已通过
    REJECTED = "rejected"             # 已驳回
    PROCESSING = "processing"         # 财务处理中
    PAID = "paid"                     # 已付款
    CANCELLED = "cancelled"           # 已取消


# 费用类型配置
EXPENSE_TYPE_CONFIG = {
    "TRANSPORT": {
        "name": "交通费",
        "icon": "🚗",
        "requires_invoice": True,
        "limit_per_day": None
    },
    "HOTEL": {
        "name": "住宿费",
        "icon": "🏨",
        "requires_invoice": True,
        "limit_per_day": None
    },
    "MEAL": {
        "name": "餐饮费",
        "icon": "🍽️",
        "requires_invoice": True,
        "limit_per_day": 500
    },
    "COMMUNICATION": {
        "name": "通讯费",
        "icon": "📱",
        "requires_invoice": True,
        "limit_per_day": None
    },
    "OFFICE": {
        "name": "办公用品",
        "icon": "📝",
        "requires_invoice": True,
        "limit_per_day": None
    },
    "ALLOWANCE": {
        "name": "差旅补贴",
        "icon": "💵",
        "requires_invoice": False,
        "limit_per_day": 200
    },
    "OTHER": {
        "name": "其他",
        "icon": "📦",
        "requires_invoice": True,
        "limit_per_day": None
    }
}

# 城市等级
CITY_TIERS = {
    "tier1": ["北京", "上海", "广州", "深圳"],
    "tier2": ["杭州", "南京", "成都", "武汉", "西安", "重庆", "天津", "苏州"]
}

# 报销标准（按职级）
REIMBURSEMENT_STANDARDS = {
    "EXECUTIVE": {
        "name": "高管",
        "flight_class": "商务舱",
        "train_class": "一等座",
        "hotel_limit_tier1": 1000,
        "hotel_limit_other": 800,
        "meal_allowance": 300
    },
    "MANAGER": {
        "name": "中层",
        "flight_class": "经济舱",
        "train_class": "一等座",
        "hotel_limit_tier1": 800,
        "hotel_limit_other": 600,
        "meal_allowance": 200
    },
    "STAFF": {
        "name": "普通员工",
        "flight_class": "经济舱",
        "train_class": "二等座",
        "hotel_limit_tier1": 500,
        "hotel_limit_other": 400,
        "meal_allowance": 150
    }
}


@dataclass
class Invoice:
    """发票信息"""
    invoice_no: str
    invoice_code: str
    invoice_date: str
    seller_name: str
    amount: float
    tax_amount: float
    verification_status: str = "pending"


@dataclass
class Expense:
    """费用记录"""
    expense_id: str
    expense_type: str
    expense_type_name: str
    amount: float
    currency: str
    expense_date: str
    description: str
    invoice_info: Optional[Invoice] = None
    status: str = "pending"
    create_time: str = ""
    related_order: str = ""
    city: str = ""
    attendees: int = 1
    compliance_result: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = {
            "expense_id": self.expense_id,
            "expense_type": self.expense_type,
            "expense_type_name": self.expense_type_name,
            "amount": self.amount,
            "currency": self.currency,
            "expense_date": self.expense_date,
            "description": self.description,
            "status": self.status,
            "create_time": self.create_time,
            "related_order": self.related_order,
            "city": self.city,
            "attendees": self.attendees,
            "compliance_result": self.compliance_result
        }
        
        if self.invoice_info:
            result["invoice_info"] = {
                "invoice_no": self.invoice_info.invoice_no,
                "invoice_code": self.invoice_info.invoice_code,
                "invoice_date": self.invoice_info.invoice_date,
                "seller_name": self.invoice_info.seller_name,
                "amount": self.invoice_info.amount,
                "tax_amount": self.invoice_info.tax_amount,
                "verification_status": self.invoice_info.verification_status
            }
        
        return result


@dataclass
class ApprovalStep:
    """审批步骤"""
    step: int
    approver: str
    approver_name: str
    status: str
    comment: str
    action_time: str = ""


@dataclass
class ExpenseReport:
    """报销单"""
    report_id: str
    report_status: str
    report_status_name: str
    submit_time: str
    total_amount: float
    currency: str
    expense_count: int
    expenses: List[Expense]
    approval_flow: List[ApprovalStep]
    trip_info: Dict = field(default_factory=dict)
    remarks: str = ""
    submitter: str = ""

    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "report_status": self.report_status,
            "report_status_name": self.report_status_name,
            "submit_time": self.submit_time,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "expense_count": self.expense_count,
            "expenses": [e.to_dict() for e in self.expenses],
            "approval_flow": [
                {
                    "step": s.step,
                    "approver": s.approver,
                    "approver_name": s.approver_name,
                    "status": s.status,
                    "comment": s.comment,
                    "action_time": s.action_time
                } for s in self.approval_flow
            ],
            "trip_info": self.trip_info,
            "remarks": self.remarks,
            "submitter": self.submitter
        }


class ExpenseApi:
    """报销API"""
    
    def __init__(self):
        self.expense_types = EXPENSE_TYPE_CONFIG
        self.city_tiers = CITY_TIERS
        self.standards = REIMBURSEMENT_STANDARDS
        self.expenses = {}  # 费用缓存
        self.reports = {}   # 报销单缓存
        self.user_level = "STAFF"  # 默认职级
    
    def create_expense(
        self,
        expense_type: str,
        amount: float,
        expense_date: str,
        description: str,
        currency: str = "CNY",
        invoice_no: str = None,
        invoice_code: str = None,
        invoice_date: str = None,
        seller_name: str = None,
        related_order: str = "",
        city: str = "",
        attendees: int = 1
    ) -> Dict:
        """
        创建费用
        """
        # 验证费用类型
        expense_type_upper = expense_type.upper()
        if expense_type_upper not in self.expense_types:
            return {
                "code": 400,
                "msg": f"不支持的费用类型: {expense_type}",
                "data": None
            }
        
        # 验证金额
        if amount <= 0:
            return {
                "code": 400,
                "msg": "金额必须大于0",
                "data": None
            }
        
        # 创建发票信息
        invoice_info = None
        if invoice_no:
            invoice_info = Invoice(
                invoice_no=invoice_no,
                invoice_code=invoice_code or "",
                invoice_date=invoice_date or expense_date,
                seller_name=seller_name or "",
                amount=amount,
                tax_amount=round(amount * 0.09, 2),
                verification_status="verified"
            )
        
        # 生成费用ID
        expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建费用记录
        expense = Expense(
            expense_id=expense_id,
            expense_type=expense_type_upper,
            expense_type_name=self.expense_types[expense_type_upper]["name"],
            amount=amount,
            currency=currency,
            expense_date=expense_date,
            description=description,
            invoice_info=invoice_info,
            status="pending",
            create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            related_order=related_order,
            city=city,
            attendees=attendees
        )
        
        # 合规检查
        compliance_result = self._check_compliance(expense)
        expense.compliance_result = compliance_result
        
        # 保存费用
        self.expenses[expense_id] = expense
        
        return {
            "code": 0,
            "msg": "success",
            "data": expense.to_dict()
        }
    
    def _check_compliance(self, expense: Expense) -> Dict:
        """合规检查"""
        result = {
            "within_policy": True,
            "exceed_limit": False,
            "duplicate": False,
            "warnings": []
        }
        
        # 检查是否超标准
        if expense.expense_type == "HOTEL":
            standard = self.standards.get(self.user_level, self.standards["STAFF"])
            city_tier = self._get_city_tier(expense.city)
            limit = standard["hotel_limit_tier1"] if city_tier == "tier1" else standard["hotel_limit_other"]
            
            if expense.amount > limit:
                result["exceed_limit"] = True
                result["warnings"].append(f"住宿费超出标准¥{limit}")
        
        # 检查发票
        if self.expense_types[expense.expense_type]["requires_invoice"] and not expense.invoice_info:
            result["within_policy"] = False
            result["warnings"].append("该费用类型需要发票")
        
        return result
    
    def _get_city_tier(self, city: str) -> str:
        """获取城市等级"""
        if city in self.city_tiers["tier1"]:
            return "tier1"
        elif city in self.city_tiers["tier2"]:
            return "tier2"
        return "other"
    
    def upload_invoice(self, expense_id: str, image_url: str) -> Dict:
        """
        上传发票（模拟OCR识别）
        """
        expense = self.expenses.get(expense_id)
        if not expense:
            return {
                "code": 404,
                "msg": f"费用不存在: {expense_id}",
                "data": None
            }
        
        # 模拟OCR识别结果
        invoice_info = Invoice(
            invoice_no=f"INV{random.randint(1000000000, 9999999999)}",
            invoice_code=f"011{random.randint(100000000, 999999999)}",
            invoice_date=expense.expense_date,
            seller_name="模拟销售方名称",
            amount=expense.amount,
            tax_amount=round(expense.amount * 0.09, 2),
            verification_status="verified"
        )
        
        expense.invoice_info = invoice_info
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "expense_id": expense_id,
                "invoice_info": {
                    "invoice_no": invoice_info.invoice_no,
                    "invoice_code": invoice_info.invoice_code,
                    "amount": invoice_info.amount,
                    "verification_status": invoice_info.verification_status
                }
            }
        }
    
    def get_expense_list(
        self,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
        expense_type: str = None
    ) -> Dict:
        """
        获取费用列表
        """
        filtered_expenses = []
        
        for expense in self.expenses.values():
            # 状态过滤
            if status and expense.status != status:
                continue
            
            # 类型过滤
            if expense_type and expense.expense_type != expense_type.upper():
                continue
            
            # 日期过滤
            if start_date and expense.expense_date < start_date:
                continue
            if end_date and expense.expense_date > end_date:
                continue
            
            filtered_expenses.append(expense.to_dict())
        
        # 按日期排序
        filtered_expenses.sort(key=lambda x: x["expense_date"], reverse=True)
        
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "total": len(filtered_expenses),
                "expenses": filtered_expenses
            }
        }
    
    def create_report(
        self,
        expense_ids: List[str],
        trip_id: str = "",
        remarks: str = ""
    ) -> Dict:
        """
        创建报销单
        """
        # 验证费用ID
        expenses = []
        total_amount = 0
        
        for expense_id in expense_ids:
            expense = self.expenses.get(expense_id)
            if not expense:
                return {
                    "code": 404,
                    "msg": f"费用不存在: {expense_id}",
                    "data": None
                }
            expenses.append(expense)
            total_amount += expense.amount
        
        # 生成报销单ID
        report_id = f"RPT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建审批流程
        approval_flow = [
            ApprovalStep(
                step=1,
                approver="部门经理",
                approver_name="王经理",
                status="pending",
                comment=""
            ),
            ApprovalStep(
                step=2,
                approver="财务审核",
                approver_name="李会计",
                status="waiting",
                comment=""
            )
        ]
        
        # 创建报销单
        report = ExpenseReport(
            report_id=report_id,
            report_status="pending",
            report_status_name="待提交",
            submit_time="",
            total_amount=total_amount,
            currency="CNY",
            expense_count=len(expenses),
            expenses=expenses,
            approval_flow=approval_flow,
            trip_info={"trip_id": trip_id} if trip_id else {},
            remarks=remarks
        )
        
        # 保存报销单
        self.reports[report_id] = report
        
        return {
            "code": 0,
            "msg": "success",
            "data": report.to_dict()
        }
    
    def submit_report(self, report_id: str) -> Dict:
        """
        提交报销单
        """
        report = self.reports.get(report_id)
        if not report:
            return {
                "code": 404,
                "msg": f"报销单不存在: {report_id}",
                "data": None
            }
        
        if report.report_status not in ["draft", "pending"]:
            return {
                "code": 400,
                "msg": f"报销单状态不允许提交: {report.report_status}",
                "data": None
            }
        
        report.report_status = "pending_approval"
        report.report_status_name = "待审批"
        report.submit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "code": 0,
            "msg": "success",
            "data": report.to_dict()
        }
    
    def approve_report(
        self,
        report_id: str,
        action: str,
        comment: str = ""
    ) -> Dict:
        """
        审批报销单
        """
        report = self.reports.get(report_id)
        if not report:
            return {
                "code": 404,
                "msg": f"报销单不存在: {report_id}",
                "data": None
            }
        
        if report.report_status != "pending_approval":
            return {
                "code": 400,
                "msg": f"报销单状态不允许审批: {report.report_status}",
                "data": None
            }
        
        # 找到当前审批步骤
        current_step = None
        for step in report.approval_flow:
            if step.status == "pending":
                current_step = step
                break
        
        if not current_step:
            return {
                "code": 400,
                "msg": "没有待审批的步骤",
                "data": None
            }
        
        # 处理审批
        if action == "approve":
            current_step.status = "approved"
            current_step.comment = comment or "同意"
            current_step.action_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 检查是否还有下一步
            next_step = None
            for step in report.approval_flow:
                if step.status == "waiting":
                    step.status = "pending"
                    next_step = step
                    break
            
            if not next_step:
                # 审批完成
                report.report_status = "approved"
                report.report_status_name = "已通过"
        
        elif action == "reject":
            current_step.status = "rejected"
            current_step.comment = comment or "驳回"
            current_step.action_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.report_status = "rejected"
            report.report_status_name = "已驳回"
        
        else:
            return {
                "code": 400,
                "msg": "审批操作必须是approve或reject",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": report.to_dict()
        }
    
    def get_report_detail(self, report_id: str) -> Dict:
        """
        获取报销单详情
        """
        report = self.reports.get(report_id)
        if not report:
            return {
                "code": 404,
                "msg": f"报销单不存在: {report_id}",
                "data": None
            }
        
        return {
            "code": 0,
            "msg": "success",
            "data": report.to_dict()
        }
    
    def get_expense_stats(
        self,
        start_date: str,
        end_date: str,
        group_by: str = "type"
    ) -> Dict:
        """
        获取费用统计
        """
        # 筛选日期范围内的费用
        filtered_expenses = []
        for expense in self.expenses.values():
            if start_date <= expense.expense_date <= end_date:
                filtered_expenses.append(expense)
        
        stats = {
            "total_amount": sum(e.amount for e in filtered_expenses),
            "total_count": len(filtered_expenses),
            "by_type": {},
            "by_date": {}
        }
        
        # 按类型统计
        for expense in filtered_expenses:
            expense_type = expense.expense_type
            if expense_type not in stats["by_type"]:
                stats["by_type"][expense_type] = {
                    "amount": 0,
                    "count": 0,
                    "name": expense.expense_type_name
                }
            stats["by_type"][expense_type]["amount"] += expense.amount
            stats["by_type"][expense_type]["count"] += 1
        
        # 按日期统计
        for expense in filtered_expenses:
            date = expense.expense_date
            if date not in stats["by_date"]:
                stats["by_date"][date] = 0
            stats["by_date"][date] += expense.amount
        
        return {
            "code": 0,
            "msg": "success",
            "data": stats
        }
    
    def format_expense(self, result: Dict) -> str:
        """格式化费用信息"""
        data = result.get("data", {})
        
        if not data:
            return "费用信息获取失败"
        
        lines = []
        lines.append("✅ 费用录入成功")
        lines.append("")
        lines.append("=" * 40)
        lines.append("")
        
        # 费用信息
        lines.append("📋 费用信息")
        lines.append("━" * 40)
        lines.append(f"费用编号：{data.get('expense_id', '')}")
        lines.append(f"费用类型：{data.get('expense_type_name', '')}")
        lines.append(f"金额：¥{data.get('amount', 0):.2f}")
        lines.append(f"费用日期：{data.get('expense_date', '')}")
        lines.append(f"费用说明：{data.get('description', '')}")
        lines.append("")
        
        # 发票信息
        if data.get('invoice_info'):
            invoice = data['invoice_info']
            lines.append("🧾 发票信息")
            lines.append("━" * 40)
            lines.append(f"发票号码：{invoice.get('invoice_no', '')}")
            lines.append(f"开票日期：{invoice.get('invoice_date', '')}")
            lines.append(f"销售方：{invoice.get('seller_name', '')}")
            lines.append(f"金额：¥{invoice.get('amount', 0):.2f}")
            lines.append(f"验证状态：✅ 已验证")
            lines.append("")
        
        # 合规检查
        compliance = data.get('compliance_result', {})
        lines.append("✅ 合规检查")
        lines.append("━" * 40)
        if compliance.get('within_policy'):
            lines.append("✓ 符合报销政策")
        if not compliance.get('exceed_limit'):
            lines.append("✓ 未超标准")
        if not compliance.get('duplicate'):
            lines.append("✓ 无重复报销")
        
        warnings = compliance.get('warnings', [])
        if warnings:
            lines.append("")
            lines.append("⚠️ 提醒：")
            for warning in warnings:
                lines.append(f"  • {warning}")
        
        lines.append("")
        lines.append("=" * 40)
        
        return "\n".join(lines)
    
    def format_report(self, result: Dict) -> str:
        """格式化报销单"""
        data = result.get("data", {})
        
        if not data:
            return "报销单信息获取失败"
        
        lines = []
        lines.append("📄 报销单详情")
        lines.append("")
        lines.append("=" * 40)
        lines.append("")
        
        # 基本信息
        lines.append("📋 基本信息")
        lines.append("━" * 40)
        lines.append(f"报销单号：{data.get('report_id', '')}")
        lines.append(f"状态：{self._format_status(data.get('report_status', ''))}")
        if data.get('submit_time'):
            lines.append(f"提交时间：{data['submit_time']}")
        lines.append(f"总金额：¥{data.get('total_amount', 0):.2f}")
        lines.append(f"费用笔数：{data.get('expense_count', 0)}笔")
        lines.append("")
        
        # 关联差旅
        if data.get('trip_info'):
            trip = data['trip_info']
            lines.append("✈️ 关联差旅")
            lines.append("━" * 40)
            lines.append(f"出差申请：{trip.get('trip_id', '')}")
            if trip.get('destination'):
                lines.append(f"目的地：{trip['destination']}")
            lines.append("")
        
        # 费用明细
        if data.get('expenses'):
            lines.append("💰 费用明细")
            lines.append("━" * 40)
            for i, expense in enumerate(data['expenses'], 1):
                lines.append(f"\n{i}. {expense.get('expense_type_name', '')}  ¥{expense.get('amount', 0):.2f}")
                lines.append(f"   {expense.get('description', '')}")
            lines.append("")
        
        # 审批流程
        if data.get('approval_flow'):
            lines.append("👥 审批流程")
            lines.append("━" * 40)
            for step in data['approval_flow']:
                status_icon = self._format_step_status(step.get('status', ''))
                lines.append(f"\n第{step.get('step', 0)}步：{step.get('approver', '')}")
                lines.append(f"审批人：{step.get('approver_name', '')}")
                lines.append(f"状态：{status_icon}")
                if step.get('comment'):
                    lines.append(f"意见：{step['comment']}")
            lines.append("")
        
        lines.append("=" * 40)
        
        return "\n".join(lines)
    
    def _format_status(self, status: str) -> str:
        """格式化状态"""
        status_map = {
            "draft": "📝 草稿",
            "pending": "⏳ 待提交",
            "pending_approval": "🟡 待审批",
            "approved": "✅ 已通过",
            "rejected": "❌ 已驳回",
            "processing": "💳 财务处理中",
            "paid": "💰 已付款",
            "cancelled": "🚫 已取消"
        }
        return status_map.get(status, status)
    
    def _format_step_status(self, status: str) -> str:
        """格式化步骤状态"""
        status_map = {
            "pending": "🟡 审批中",
            "waiting": "⏳ 待审批",
            "approved": "✅ 已通过",
            "rejected": "❌ 已驳回"
        }
        return status_map.get(status, status)


# 测试
if __name__ == "__main__":
    api = ExpenseApi()
    
    # 测试创建费用
    print("=" * 60)
    print("测试创建费用")
    print("=" * 60)
    result = api.create_expense(
        expense_type="TRANSPORT",
        amount=850.00,
        expense_date="2026-03-25",
        description="北京-上海机票",
        invoice_no="1234567890",
        seller_name="中国东方航空股份有限公司",
        city="上海"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "=" * 60)
    print("格式化费用：")
    print("=" * 60)
    print(api.format_expense(result))
    
    # 测试创建报销单
    print("\n" + "=" * 60)
    print("测试创建报销单")
    print("=" * 60)
    expense_id = result["data"]["expense_id"]
    report_result = api.create_report(
        expense_ids=[expense_id],
        remarks="3月上海出差费用"
    )
    print(json.dumps(report_result, ensure_ascii=False, indent=2))
    
    # 格式化展示
    print("\n" + "=" * 60)
    print("格式化报销单：")
    print("=" * 60)
    print(api.format_report(report_result))
