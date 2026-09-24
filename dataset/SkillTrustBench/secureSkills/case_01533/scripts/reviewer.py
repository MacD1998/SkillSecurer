"""
审查模块

审查填充后的模板，检查：
1. BP 编码对齐
2. 数字锚点完整性
3. 衡量标准引用
4. 颜色预警正确性
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@lru_cache(maxsize=1)
def _load_alert_rule_config() -> Dict:
    """加载预警阈值配置，失败时回退默认值。"""
    default = {
        "red": 5.0,
        "yellow_low": 3.0,
        "yellow_high": 5.0,
    }

    cfg_path = Path(__file__).resolve().parent.parent / "references" / "alert_rules.yaml"
    if not cfg_path.exists():
        return default

    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        financial = ((data.get("alert_rules") or {}).get("financial") or {})
        red = _extract_first_number(str(financial.get("red", ">5%"))) or default["red"]
        yellow_low, yellow_high = _extract_range(str(financial.get("yellow", "3-5%")))
        return {
            "red": red,
            "yellow_low": yellow_low if yellow_low is not None else default["yellow_low"],
            "yellow_high": yellow_high if yellow_high is not None else default["yellow_high"],
        }
    except Exception:
        return default


def _extract_first_number(text: str) -> Optional[float]:
    nums = re.findall(r"\d+\.?\d*", text or "")
    if not nums:
        return None
    return float(nums[0])


def _extract_range(text: str) -> Tuple[Optional[float], Optional[float]]:
    nums = re.findall(r"\d+\.?\d*", text or "")
    if not nums:
        return None, None
    if len(nums) == 1:
        v = float(nums[0])
        return v, v
    return float(nums[0]), float(nums[1])


def _expected_alert_color_by_deviation(rate: float) -> str:
    cfg = _load_alert_rule_config()
    abs_rate = abs(rate)
    if abs_rate > cfg["red"]:
        return "红"
    if cfg["yellow_low"] <= abs_rate <= cfg["yellow_high"]:
        return "黄"
    return "绿"


def review_template(content: str, bp_data: Dict) -> Dict:
    """
    审查填充后的模板
    
    Returns:
        {
            "passed": bool,
            "issues": List[Dict]  # [{"type": str, "detail": str, "severity": str}]
        }
    """
    issues = []
    
    # 1. BP 编码对齐检查
    issues.extend(check_bp_codes(content, bp_data))
    
    # 2. 数字锚点检查
    issues.extend(check_number_anchors(content))
    
    # 3. 衡量标准检查
    issues.extend(check_measure_standards(content))
    
    # 4. 颜色预警检查
    issues.extend(check_alert_rules(content))
    
    # 5. 占位符检查
    issues.extend(check_placeholders(content))

    # 6. 零容忍项检查
    issues.extend(check_zero_tolerance(content, bp_data))

    return {
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues
    }


def check_bp_codes(content: str, bp_data: Dict) -> List[Dict]:
    """检查 BP 编码对齐"""
    issues = []
    
    # 提取内容中的编码
    code_pattern = r"[PA]\d+-?\d*\.?\d*"
    found_codes = set(re.findall(code_pattern, content))
    
    # 检查是否有 [待确认编码] 标记
    if "[待确认编码]" in content:
        issues.append({
            "type": "编码缺失",
            "detail": "存在未确认的 BP 编码",
            "severity": "error"
        })
    
    if "[对应个人BP编码]" in content or "[对应组织BP编码]" in content:
        issues.append({
            "type": "编码缺失",
            "detail": "存在未映射的个人/组织 BP 编码占位符",
            "severity": "error"
        })

    # 检查编码格式
    for code in found_codes:
        # P 系列应该是 PXXXX-X.X 格式
        if code.startswith("P") and not re.match(r"P\d+-\d+\.\d+", code):
            # 可能是不完整的编码，但如果是 P1001 这种也是合法的
            if not re.match(r"P\d+", code):
                issues.append({
                    "type": "编码格式",
                    "detail": f"编码 {code} 格式可能不正确",
                    "severity": "warning"
                })
    
    return issues


def check_number_anchors(content: str) -> List[Dict]:
    """检查数字锚点"""
    issues = []
    
    # 检查是否有数字锚点
    number_patterns = [
        r"≥\d+",   # ≥90
        r"≤\d+",   # ≤5
        r">=\d+",  # >=90
        r"<=\d+",  # <=5
        r"\d+%",   # 100%
    ]
    
    has_numbers = any(re.search(p, content) for p in number_patterns)
    
    # 检查量化指标章节是否有数字
    quant_match = re.search(r"量化指标[：:](.*?)(?:\n|$)", content)
    if quant_match:
        quant_content = quant_match.group(1)
        if not any(re.search(p, quant_content) for p in number_patterns):
            issues.append({
                "type": "数字锚点缺失",
                "detail": "量化指标章节缺少具体数字",
                "severity": "warning"
            })
    
    return issues


def check_measure_standards(content: str) -> List[Dict]:
    """检查衡量标准"""
    issues = []
    
    # 检查是否有 [待确认衡量标准] 标记
    if "[待确认衡量标准]" in content or "[待补充衡量标准]" in content:
        issues.append({
            "type": "衡量标准缺失",
            "detail": "存在未确认的衡量标准",
            "severity": "error"
        })
    
    return issues


def check_alert_rules(content: str) -> List[Dict]:
    """检查颜色预警规则（含阈值一致性校验）"""
    issues = []

    # 先做基础格式检查
    alert_sections = re.findall(r"偏离判断[：:](.*?)(?:\n|$)", content)
    for section in alert_sections:
        text = section.strip()
        if "[红/黄/绿]" in text:
            issues.append({
                "type": "颜色预警未填写",
                "detail": "偏离判断仍为占位符 [红/黄/绿]",
                "severity": "warning"
            })
            continue

        if not any(color in text for color in ["红", "黄", "绿"]):
            issues.append({
                "type": "颜色预警缺失",
                "detail": f"偏离判断缺少颜色标记: {text}",
                "severity": "warning"
            })

    # 再做阈值一致性检查（按章节配对）
    section_blocks = re.findall(r"###\s+2\.\d+[\s\S]*?(?=###\s+2\.\d+|##\s+3\.|$)", content)
    for idx, sec in enumerate(section_blocks, start=1):
        m_alert = re.search(r"偏离判断[：:]\s*([红黄绿])", sec)
        m_rate = re.search(r"是否偏离预期[\s\S]*?[-：:]\s*[是否]\s*[，,]\s*([+-]?\d+\.?\d*)%", sec)
        if not m_alert or not m_rate:
            continue

        actual = m_alert.group(1)
        rate = float(m_rate.group(1))
        expected = _expected_alert_color_by_deviation(rate)
        if actual != expected:
            issues.append({
                "type": "颜色阈值不一致",
                "detail": f"第{idx}项偏离率 {rate}% 对应应为{expected}，当前为{actual}",
                "severity": "warning"
            })

    return issues


def check_placeholders(content: str) -> List[Dict]:
    """检查是否有未替换的占位符"""
    issues = []

    # 常见占位符模式
    placeholder_patterns = [
        r"\[待填写.*?\]",
        r"\[填写：.*?\]",
        r"\[示例.*?\]",
        r"\[描述\]",
        r"\[量化\]",
        r"\[是/否\]",
        r"\[偏离率\]",
    ]

    critical_tokens = ["BP编码", "待确认编码", "待补充衡量标准"]

    for pattern in placeholder_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            severity = "error" if any(token in match for token in critical_tokens) else "warning"
            issues.append({
                "type": "占位符未替换",
                "detail": f"存在未替换的占位符: {match}",
                "severity": severity
            })

    return issues


def check_zero_tolerance(content: str, bp_data: Dict) -> List[Dict]:
    """检查零容忍项"""
    issues = []

    zero_tolerance_items = [
        "重大合规事故",
        "BP签约率",
        "奖金发放",
        "重大法律败诉",
        "核心产品重大延期",
    ]

    negative_patterns = [
        r"发生",
        r"出现",
        r"命中",
        r"delay",
        r"延期",
        r"逾期",
        r"未达标",
        r"未按时",
        r"<\s*100%",
        r"[1-9]\d*起",
    ]

    for item in zero_tolerance_items:
        if item not in content:
            continue

        # 取包含该词的一行进行判断
        line = next((ln.strip() for ln in content.splitlines() if item in ln), "")
        lowered = line.lower()
        if any(s in lowered for s in ["无", "未发生", "=0", "0起"]):
            continue

        if any(re.search(pat, lowered) for pat in negative_patterns):
            issues.append({
                "type": "零容忍项命中",
                "detail": f"检测到零容忍风险项：{line or item}",
                "severity": "error"
            })

    return issues


if __name__ == "__main__":
    # 测试
    test_content = """
### 2.1 [上市得分]

**对标BP：** P4432-1.1（个人）/ A3-1（组织）

**本月承接重点：**
- 年度上市得分≥7分

**当前状态：**
- 量化指标：≥7分
- 偏离判断：绿

**是否偏离预期：**
- 否
"""
    
    bp_data = {
        "goals": [
            {"code": "A3-1", "name": "上市得分"}
        ]
    }
    
    result = review_template(test_content, bp_data)
    print(f"通过: {result['passed']}")
    print(f"问题: {len(result['issues'])}")
    for issue in result['issues']:
        print(f"  - [{issue['severity']}] {issue['type']}: {issue['detail']}")
