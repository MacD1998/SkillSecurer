"""
测试模块
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from input_handler import parse_user_input
from parser import parse_bp_from_file
from reviewer import review_template


class TestInputHandler(unittest.TestCase):
    """输入解析测试"""
    
    def test_parse_template_types(self):
        """测试模板类型解析"""
        test_cases = [
            ("生成四套", ["月报", "季报", "半年报", "年报"]),
            ("只做季报", ["季报"]),
            ("月报和年报", ["月报", "年报"]),
            ("把季报和半年报给我", ["季报", "半年报"]),
        ]
        
        for input, expected in test_cases:
            result = parse_user_input(input)
            self.assertEqual(result["template_types"], expected)
    
    def test_parse_org_name(self):
        """测试组织名解析"""
        result = parse_user_input("为产品中心生成四套")
        self.assertEqual(result["org_name"], "产品中心")

    def test_require_template_selection_when_default_off(self):
        """未指定模板且 default_all=False 时，必须返回空列表等待选择"""
        result = parse_user_input("为产品中心生成", default_all=False)
        self.assertEqual(result["template_types"], [])


class TestReviewer(unittest.TestCase):
    """审查器测试"""

    def test_review_template_pass(self):
        """测试审查通过"""
        content = """
### 2.1 [上市得分]

**对标BP：** P4432-1.1（个人）/ A3-1（组织）

**本月承接重点：**
- 年度上市得分≥7分

**当前状态：**
- 量化指标：≥7分
- 偏离判断：绿
"""

        bp_data = {
            "goals": [{"code": "A3-1", "name": "上市得分"}]
        }

        result = review_template(content, bp_data)
        self.assertTrue(result["passed"])

    def test_review_template_fail_on_missing_code(self):
        """存在待确认编码时应判定失败"""
        content = """
### 2.1 [上市得分]
**对标BP：** [对应个人BP编码]（个人）/ [待确认编码]（组织）
**当前状态：**
- 量化指标：≥7分
- 偏离判断：绿
"""
        result = review_template(content, {"goals": []})
        self.assertFalse(result["passed"])
        self.assertTrue(any(i["type"] == "编码缺失" and i["severity"] == "error" for i in result["issues"]))

    def test_review_template_detects_zero_tolerance_hit(self):
        """零容忍项命中应输出 error"""
        content = """
## 6. 风险预警
- 重大合规事故：已发生1起
- 偏离判断：红
"""
        result = review_template(content, {"goals": []})
        self.assertFalse(result["passed"])
        self.assertTrue(any(i["type"] == "零容忍项命中" for i in result["issues"]))

    def test_review_template_alert_threshold_mismatch(self):
        """偏离率与颜色不一致时应给出告警"""
        content = """
### 2.1 [上市得分]
**对标BP：** P4432-1.1（个人）/ A3-1（组织）
**当前状态：**
- 量化指标：95%
- 偏离判断：绿
**是否偏离预期：**
- 是，8%
"""
        result = review_template(content, {"goals": []})
        self.assertTrue(any(i["type"] == "颜色阈值不一致" for i in result["issues"]))

    def test_review_template_zero_tolerance_no_false_positive(self):
        """零容忍项正常描述不应误报"""
        content = """
## 6. 风险预警
- 重大合规事故：未发生0起
- 偏离判断：绿
"""
        result = review_template(content, {"goals": []})
        self.assertFalse(any(i["type"] == "零容忍项命中" for i in result["issues"]))


class TestParser(unittest.TestCase):
    """文件回退解析测试"""

    def test_parse_bp_from_file_json(self):
        sample = {
            "org_name": "产品中心",
            "person_name": "林刚",
            "period": "2026年度计划BP",
            "goals": [
                {
                    "id": "g1",
                    "code": "A3-1",
                    "name": "上市得分",
                    "measure_standard": "年度上市得分≥7分",
                    "key_results": [{"name": "完成2个产品上市"}],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "bp.json"
            f.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
            parsed = parse_bp_from_file(str(f))

        self.assertEqual(parsed.org_name, "产品中心")
        self.assertEqual(len(parsed.goals), 1)
        self.assertEqual(parsed.goals[0].code, "A3-1")


if __name__ == "__main__":
    unittest.main()
