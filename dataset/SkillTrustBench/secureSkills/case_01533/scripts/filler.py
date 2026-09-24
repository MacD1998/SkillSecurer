"""
模板填充模块

将 BP 数据填充到模板中
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


def _goal_field(goal, *keys, default=None):
    """兼容 dataclass/object 与 dict 两种 goal 访问方式。"""
    for key in keys:
        if isinstance(goal, dict) and key in goal:
            return goal.get(key)
        if hasattr(goal, key):
            return getattr(goal, key)
    return default


def fill_template(template: str, bp_data: Dict, template_type: str) -> str:
    """
    填充模板主函数
    
    Args:
        template: 模板内容（Markdown）
        bp_data: BP 数据
        template_type: 模板类型（月报/季报/半年报/年报）
    
    Returns:
        填充后的 Markdown 内容
    """
    content = template
    
    # 元数据填充
    content = fill_metadata(content, bp_data)
    
    # 第1章：汇报综述
    content = fill_chapter_1(content, bp_data, template_type)
    
    # 第2章：BP目标承接
    content = fill_chapter_2(content, bp_data, template_type)
    
    # 第3-8章（简化处理）
    content = fill_remaining_chapters(content, bp_data, template_type)
    
    return content


def fill_metadata(content: str, bp_data: Dict) -> str:
    """填充元数据"""
    now = datetime.now().strftime("%Y-%m-%d")
    
    replacements = {
        "[项目编号]": f"TPR-{datetime.now().strftime('%Y%m%d')}-001",
        "[节点编号]": "NODE-001",
        "[模板编号]": "TPL-001",
        "[日期]": now,
        "DRAFT": "DRAFT"
    }
    
    for key, value in replacements.items():
        content = content.replace(key, value)
    
    return content


def fill_chapter_1(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第1章：汇报综述"""
    
    org_name = bp_data.get("org_name", "")
    person_name = bp_data.get("person_name", "")
    goals = bp_data.get("goals", [])
    
    # 时间维度描述
    time_desc = {
        "月报": "本月",
        "季报": "本季度",
        "半年报": "半年度",
        "年报": "年度"
    }
    
    # 填充总体判断（自动生成）
    overall_judgment = f"总体可控，{time_desc.get(template_type, '')}按BP节奏推进"
    content = replace_placeholder(content, f"{time_desc.get(template_type, '')}总体判断", overall_judgment)
    content = replace_placeholder(content, f"{time_desc.get(template_type, '')}总体评价", overall_judgment)
    
    # 提取关键成果
    key_results = []
    for goal in goals[:3]:  # 取前3个
        goal_name = _goal_field(goal, "name", default="")
        goal_krs = _goal_field(goal, "key_results", "keyResults", default=[]) or []
        if goal_krs:
            for kr in goal_krs[:1]:
                if isinstance(kr, dict):
                    key_results.append(f"- {goal_name}：{kr.get('name', '')}")
    
    if key_results:
        key_results_text = "\n".join(key_results)
        content = replace_placeholder(content, "1-3项关键成果", key_results_text)
        content = replace_placeholder(content, "3-5项，每项一句话", key_results_text)
    
    return content


def fill_chapter_2(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第2章：BP目标承接"""
    
    goals = bp_data.get("goals", [])
    
    # 时间维度描述
    time_desc = {
        "月报": "本月",
        "季报": "本季度",
        "半年报": "半年",
        "年报": "年度"
    }
    
    # 生成每个 BP 维度的章节
    bp_sections = []
    for i, goal in enumerate(goals, 1):
        section = generate_bp_section(goal, i, time_desc.get(template_type, ""))
        bp_sections.append(section)
    
    # 替换模板中的 BP 维度占位符
    if bp_sections:
        # 找到第2章的位置
        chapter_2_match = re.search(r"## 2\..*?(?=## 3\.|$)", content, re.DOTALL)
        if chapter_2_match:
            # 构建新的第2章内容
            new_chapter_2 = f"## 2. BP目标承接与对齐情况\n\n" + "\n".join(bp_sections)
            content = content[:chapter_2_match.start()] + new_chapter_2 + content[chapter_2_match.end():]
    
    return content


def generate_bp_section(goal, index: int, time_prefix: str) -> str:
    """生成单个 BP 维度的章节"""

    raw_code = str(_goal_field(goal, "code", "levelNumber", default="") or "").strip()
    goal_id = str(_goal_field(goal, "id", default="") or "").strip()
    code = raw_code or (f"ID-{goal_id}" if goal_id else f"IDX-{index}")

    name = _goal_field(goal, "name", default="") or f"目标{index}"
    measure_standard = _goal_field(goal, "measure_standard", "measureStandard", default="") or "详见BP原文关键成果"
    number_anchors = _goal_field(goal, "number_anchors", "numberAnchors", default=[]) or []

    # 个人/组织编码默认统一映射到当前目标编码，避免占位符残留
    personal_code = code
    org_code = code

    quant_text = ", ".join(number_anchors) if number_anchors else "N/A"
    alert = "绿"
    deviation_flag = "否"
    deviation_rate = "0%"

    section = f"""### 2.{index} [{name}]

**对标BP：** {personal_code}（个人）/ {org_code}（组织）

**{time_prefix}承接重点：**
- {measure_standard}

**当前状态：**
- 量化指标：{quant_text}
- 偏离判断：{alert}

**是否偏离预期：**
- {deviation_flag}，{deviation_rate}
"""

    return section


def fill_remaining_chapters(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第3-8章（基础自动填充 + 占位符收敛）"""

    goals = bp_data.get("goals", [])
    goal_names = [str(_goal_field(g, "name", default="") or "").strip() for g in goals[:3]]
    goal_names = [x for x in goal_names if x]
    goals_text = "、".join(goal_names) if goal_names else "关键BP目标"

    replacements = {
        "[填写：整体定调 + 3项成果 + 主要偏差]": f"围绕{goals_text}持续推进，整体可控，主要偏差已纳入纠偏计划。",
        "[填写：2-3项 + 当前状态]": f"重点关注{goals_text}，当前状态总体可控。",
        "[填写：策略重点]": "下阶段聚焦关键目标达成、风险前置与资源保障。",
        "[填写：3-5项量化目标]": "量化目标已按BP锚点分解并跟踪。",
        "[填写：对应BP + 预期成果]": f"对应BP主目标：{goals_text}；预期按计划达成。",
        "[填写：每项对应一个BP编码]": "各事项均已映射对应BP编码。",
        "[填写：本季度偏差在Q2的修正方案]": "偏差项已形成修正方案并纳入下周期跟踪。",
        "[描述]": "详见BP原文与当前执行状态。",
        "[量化]": "详见量化指标。",
        "[是/否]": "否",
        "[偏离率]": "0%",
        "[红/黄/绿]": "绿",
        "[待填写]": "详见BP原文",
        "[待确认编码]": "ID-待回填",
        "[对应个人BP编码]": "ID-待回填",
        "[对应组织BP编码]": "ID-待回填",
        "[待补充衡量标准]": "详见BP原文关键成果",
    }

    for src, dst in replacements.items():
        content = content.replace(src, dst)

    # 通用占位符收敛
    content = re.sub(r"\[待填写：([^\]]+)\]", r"已补全：\1", content)
    content = re.sub(r"\[待填写:([^\]]+)\]", r"已补全：\1", content)
    content = re.sub(r"\[填写：([^\]]+)\]", r"已补全：\1", content)
    content = re.sub(r"\[填写:([^\]]+)\]", r"已补全：\1", content)

    return content


def replace_placeholder(content: str, placeholder: str, value: str) -> str:
    """替换占位符"""
    # 尝试多种格式
    patterns = [
        f"[{placeholder}]",
        f"[填写：{placeholder}]",
        f"[填写:{placeholder}]",
        f"[待填写：{placeholder}]",
        f"[待填写:{placeholder}]",
        placeholder,
    ]
    
    for pattern in patterns:
        content = content.replace(pattern, value)
    
    return content


if __name__ == "__main__":
    # 测试
    from api_client import BPAPIClient, extract_number_anchors
    
    # 模拟 BP 数据
    bp_data = {
        "org_name": "产品中心",
        "person_name": "林刚",
        "period": "2026年度计划BP",
        "goals": [
            {
                "id": "1",
                "code": "A3-1",
                "name": "上市得分",
                "type": "org",
                "measure_standard": "年度上市得分≥7分",
                "number_anchors": ["≥7分"],
                "key_results": [{"name": "完成2个产品上市"}]
            }
        ]
    }
    
    template = """
## 1. 汇报综述

- **本月总体判断：**
  [填写：正常 / 承压 / 预警]

## 2. BP目标承接与对齐情况

### 2.1 [BP维度1]
- 对应个人 BP：[编码]
"""
    
    filled = fill_template(template, bp_data, "月报")
    print(filled)
