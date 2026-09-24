#!/usr/bin/env python3
"""
therapy-prep 基础测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from prep import TherapyPrep, CrisisDetector
from topic_organizer import TopicOrganizer


def test_crisis_detector():
    print("=== 测试 CrisisDetector ===")
    d = CrisisDetector()
    cases = [
        ("我下周有咨询", False, None),
        ("活着没意思", True, "suicide"),
        ("想伤害自己", True, "self_harm"),
        ("坚持不住了", True, "breakdown"),
    ]
    passed = 0
    for text, exp_crisis, exp_type in cases:
        r = d.detect(text)
        ok = r["has_crisis"] == exp_crisis
        if ok and exp_type:
            ok = r["type"] == exp_type
        print(f"{'✅' if ok else '❌'} {text!r}")
        if ok:
            passed += 1
    print(f"通过: {passed}/{len(cases)}\n")
    return passed == len(cases)


def test_prep_flow():
    print("=== 测试 TherapyPrep 流程 ===")
    prep = TherapyPrep()
    welcome = prep.get_welcome()
    ok = "心理咨询准备" in welcome
    print(f"{'✅' if ok else '❌'} 欢迎语生成")
    return ok


def test_crisis_interrupts_prep():
    print("=== 测试危机中断准备流程 ===")
    prep = TherapyPrep()
    prep.process("下周三咨询")
    r = prep.process("活着没意思")
    ok = r["phase"] == "crisis" and r["crisis_result"]["type"] == "suicide"
    print(f"{'✅' if ok else '❌'} 危机信号中断: phase={r['phase']}, type={r['crisis_result']['type']}\n")
    return ok


def test_topic_organizer():
    print("=== 测试 TopicOrganizer ===")
    org = TopicOrganizer()
    org.add_topic("工作压力大")
    org.add_topic("睡眠不好")
    summary = org.generate_summary()
    ok = "工作压力大" in summary and "睡眠不好" in summary
    print(f"{'✅' if ok else '❌'} 议题摘要生成")
    return ok


def test_file_structure():
    print("=== 测试文件结构 ===")
    base = os.path.dirname(os.path.dirname(__file__))
    required = [
        "SKILL.md", "skill.json",
        "scripts/prep.py", "scripts/crisis_detector.py", "scripts/topic_organizer.py",
        "references/crisis_keywords.json", "references/prep_phases.json",
    ]
    passed = 0
    for f in required:
        path = os.path.join(base, f)
        exists = os.path.exists(path)
        print(f"{'✅' if exists else '❌'} {f}")
        if exists:
            passed += 1
    print(f"通过: {passed}/{len(required)}\n")
    return passed == len(required)


def main():
    results = [
        ("文件结构", test_file_structure()),
        ("危机检测", test_crisis_detector()),
        ("准备流程", test_prep_flow()),
        ("危机中断", test_crisis_interrupts_prep()),
        ("议题组织", test_topic_organizer()),
    ]
    print("=" * 50)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    all_ok = all(r[1] for r in results)
    print(f"\n总体: {'✅ 全部通过' if all_ok else '❌ 存在问题'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
