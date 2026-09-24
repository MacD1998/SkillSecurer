"""
BP 解析模块

从 BP 数据中提取结构化信息
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class BPGoal:
    """BP 目标"""
    id: str
    code: str
    name: str
    type: str
    measure_standard: Optional[str] = None
    number_anchors: List[str] = None
    key_results: List[Dict] = None
    status: Optional[str] = None


@dataclass
class BPData:
    """BP 数据容器"""
    org_name: str
    person_name: str
    period: str
    goals: List[BPGoal]


def _field(item: Any, *keys: str, default=None):
    for key in keys:
        if isinstance(item, dict) and key in item:
            return item.get(key)
        if hasattr(item, key):
            return getattr(item, key)
    return default


def parse_bp_from_api(api_data: dict) -> BPData:
    """从 API 返回数据解析为 BPData"""

    if not api_data:
        return BPData(goals=[], org_name="", person_name="", period="")

    org_name = api_data.get("org_name", "")
    person_name = api_data.get("person_name", "")
    period = api_data.get("period", "")

    goals = []
    for g in api_data.get("goals", []):
        code = str(_field(g, "code", "levelNumber", default="") or "")
        measure_standard = str(_field(g, "measure_standard", "measureStandard", default="") or "")
        goal = BPGoal(
            id=str(_field(g, "id", default="") or ""),
            code=code,
            name=str(_field(g, "name", default="") or ""),
            type="personal" if code.startswith("P") else "org",
            measure_standard=measure_standard,
            number_anchors=extract_number_anchors(measure_standard),
            key_results=_field(g, "key_results", "keyResults", default=[]) or [],
            status=_field(g, "status"),
        )
        goals.append(goal)

    return BPData(
        org_name=org_name,
        person_name=person_name,
        period=period,
        goals=goals,
    )


def parse_bp_from_file(file_path: str) -> BPData:
    """从文件解析 BP 数据（优先 JSON，兼容 Markdown 占位）"""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"BP 文件不存在: {file_path}")

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            return parse_bp_from_api(raw)
        raise ValueError("JSON BP 文件格式错误：根节点必须为对象")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Markdown 简化回退：仅提取文档标题作为组织名线索
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    org_name = title_match.group(1).strip() if title_match else path.stem

    return BPData(
        org_name=org_name,
        person_name="",
        period="",
        goals=[],
    )


def extract_number_anchors(text: str) -> List[str]:
    """从文本中提取数字锚点"""
    if not text:
        return []
    
    anchors = []
    
    # 匹配模式
    patterns = [
        r"[≥<>≤]\s*\d+\.?\d*%?",  # 百分比
        r"\d+月\d+日",              # 日期
        r"\d+个",                   # 数量
        r"\d+亿",                  # 金额
    ]
    
    for pattern in patterns:
        anchors.extend(re.findall(pattern, text))
    
    return anchors


if __name__ == "__main__":
    # 测试
    bp_data = {
        "org_name": "产品中心",
        "person_name": "林刚",
        "period": "2026年度计划BP",
        "goals": [
            {
                "id": "1",
                "levelNumber": "A3-1",
                "name": "上市得分",
                "measureStandard": "年度上市得分≥7分",
                "keyResults": [{"name": "完成2个产品上市"}],
                "status": "green"
            }
        ]
    }
    
    result = parse_bp_from_api(bp_data)
    print(f"组织: {result.org_name}")
    print(f"目标数: {len(result.goals)}")
    for goal in result.goals:
        print(f"  - {goal.code}: {goal.name}")
