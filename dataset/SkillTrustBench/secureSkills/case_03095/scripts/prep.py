#!/usr/bin/env python3
"""
心理咨询准备核心逻辑 - therapy-prep skill 核心模块
帮助用户整理思绪、明确目标、准备咨询议题
"""

import json
from pathlib import Path
from typing import Optional, List, Dict


class TherapyPrep:
    """
    心理咨询准备引导器

    流程：基本信息 -> 近期状态 -> 核心议题 -> 要点清单 -> 咨询后跟进
    任何时候发现危机信号立即转介
    """

    def __init__(self):
        self.crisis = CrisisDetector()
        self.phases_data = self._load_phases()
        self._reset()

    def _load_phases(self) -> dict:
        p = Path(__file__).parent.parent / "references" / "prep_phases.json"
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _reset(self):
        self.phase = 1
        self.sub_step = 0
        self.data = {
            "basic_info": {},
            "recent_state": {},
            "topics": [],
            "post_session": {},
        }
        self.notes = []  # 收集的所有笔记

    # ---- 公共接口 ----

    def check_crisis(self, text: str) -> Optional[dict]:
        return self.crisis.detect(text)

    def process(self, text: str) -> dict:
        """处理用户输入，返回引导结果"""
        # 危机检测
        crisis_result = self.crisis.detect(text)
        if crisis_result["has_crisis"]:
            return {
                "phase": "crisis",
                "content": crisis_result["response"],
                "crisis_result": crisis_result,
                "data": self.data,
            }

        # 正常流程
        return self._process_normal(text)

    def get_welcome(self) -> str:
        return (
            "🪪 **心理咨询准备**\n\n"
            "我们来帮你整理思绪，让咨询更有效。不需要一次说很多，一点一点来就好。\n\n"
            f"**第1步 - 基本信息**\n{self._get_current_question()}\n\n"
            f"⚠️ **免责声明**：本工具仅提供一般性咨询准备支持，不替代心理咨询或治疗。"
        )

    # ---- 内部流程控制 ----

    def _process_normal(self, text: str) -> dict:
        """正常流程处理"""
        self.notes.append({"phase": self.phase, "step": self.sub_step, "input": text})

        # 收集数据
        self._collect_data(text)

        # 推进步骤
        self._advance()

        if self.phase > 5:
            return self._wrap_up()

        return {
            "phase": f"phase_{self.phase}",
            "content": self._build_phase_content(),
            "crisis_result": None,
            "data": self.data,
        }

    def _collect_data(self, text: str):
        """根据当前阶段收集数据"""
        if self.phase == 1:
            # 基本信息：3个问题
            keys = ["next_session_time", "first_or_ongoing", "expectations"]
            idx = min(self.sub_step - 1, len(keys) - 1)
            if self.sub_step > 0:
                self.data["basic_info"][keys[idx]] = text
        elif self.phase == 2:
            keys = ["main_concern", "emotional_state", "events", "daily_function"]
            idx = min(self.sub_step - 1, len(keys) - 1)
            if self.sub_step > 0:
                self.data["recent_state"][keys[idx]] = text
        elif self.phase == 3:
            if self.sub_step == 0:
                self.data["topics"].append(text)
            elif self.sub_step == 4:
                # 最后一个问题：之前尝试的方法
                if self.data["topics"]:
                    self.data["topics"][-1]["previous_approaches"] = text

    def _advance(self):
        """推进到下一步"""
        phases = self.phases_data["phases"]
        current_phase_data = phases[self.phase - 1]
        questions = current_phase_data.get("questions", [])

        self.sub_step += 1

        if self.phase == 3 and self.sub_step == 1:
            # 阶段3：第一个问题是核心议题
            self.data["topics"].append({})
            self.data["topics"][-1]["issue"] = ""
            return

        if self.sub_step > len(questions):
            self.phase += 1
            self.sub_step = 0

    def _build_phase_content(self) -> str:
        """构建当前阶段的内容"""
        phases = self.phases_data["phases"]
        current = phases[self.phase - 1]
        questions = current.get("questions", [])

        if self.phase == 4:
            return self._build_topic_summary()
        elif self.phase == 5:
            return self._build_post_session_note()
        else:
            q = questions[self.sub_step - 1] if self.sub_step <= len(questions) else None
            return f"**第{self.phase}步 - {current['name']}**\n{q}" if q else ""

    def _get_current_question(self) -> str:
        phases = self.phases_data["phases"]
        current = phases[self.phase - 1]
        questions = current.get("questions", [])
        if self.phase == 4:
            return "（以下是要点清单，请查收）"
        return questions[self.sub_step] if self.sub_step < len(questions) else ""

    def _build_topic_summary(self) -> str:
        """生成议题清单（阶段4）"""
        topics = self.data.get("topics", [])
        lines = ["📋 **你的咨询要点清单**\n"]
        lines.append(f"下次咨询：{self.data.get('basic_info', {}).get('next_session_time', '未填写')}")
        lines.append(f"咨询类型：{self.data.get('basic_info', {}).get('first_or_ongoing', '未填写')}")
        lines.append("")

        if topics:
            for i, topic in enumerate(topics, 1):
                issue = topic.get("issue", topic if isinstance(topic, str) else "")
                lines.append(f"**议题{i}**：{issue}")
                prev = topic.get("previous_approaches", "")
                if prev:
                    lines.append(f"  之前试过：{prev}")
        else:
            lines.append("（暂无明确议题）")

        lines.append("")
        lines.append("💡 **小建议**：把这些要点记下来，咨询时主动提出来，")
        lines.append("   这样可以让有限的咨询时间用在最重要的地方。")

        return "\n".join(lines)

    def _build_post_session_note(self) -> str:
        """生成咨询后跟进模板（阶段5）"""
        return (
            "📝 **咨询后跟进记录**\n\n"
            "咨询结束后，可以在这里记下：\n"
            "1. 今天印象最深的一点是什么？\n"
            "2. 有什么新的收获或想法？\n"
            "3. 咨询师给了什么建议或安排？\n"
            "4. 下次咨询前你打算做什么？\n\n"
            "💡 记得按时服药（如有），继续保持记录习惯。"
        )

    def _wrap_up(self) -> dict:
        """完成时的总结"""
        summary = self._build_topic_summary()
        disclaimer = (
            "\n\n⚠️ **免责声明**：本工具仅提供一般性咨询准备支持，"
            "不替代心理咨询、诊断或治疗。如有需要，请联系心理健康专业人士。"
        )
        return {
            "phase": "done",
            "content": summary + disclaimer,
            "crisis_result": None,
            "data": self.data,
        }


class CrisisDetector:
    """本地危机检测器（同 emotion-journal 逻辑）"""
    def __init__(self):
        self.crisis_data = self._load()

    def _load(self) -> dict:
        refs = Path(__file__).parent.parent / "references" / "crisis_keywords.json"
        with open(refs, 'r', encoding='utf-8') as f:
            return json.load(f)

    def detect(self, text: str) -> dict:
        text_lower = text.lower()
        signals = self.crisis_data.get("crisis_signals", {})
        results = {"has_crisis": False, "level": None, "type": None,
                   "matched_keywords": [], "response": None}

        for kw_list, ctype in [
            (signals.get("suicide", []), "suicide"),
            (signals.get("self_harm", []), "self_harm"),
            (signals.get("severe_breakdown", []), "breakdown"),
        ]:
            matched = [kw for kw in kw_list if kw in text_lower]
            if matched:
                results.update({
                    "has_crisis": True,
                    "level": "high" if ctype in ("suicide", "self_harm") else "medium",
                    "type": ctype,
                    "matched_keywords": matched,
                })
                break

        if results["has_crisis"]:
            results["response"] = self._generate_response(results["type"])
        return results

    def _generate_response(self, crisis_type: str) -> str:
        t = self.crisis_data.get("response_templates", {})
        hotline = self.crisis_data.get("professional_resources", {}).get("national_hotline", "400-161-9995")
        parts = [
            t.get("immediate", ""),
            t.get("hotline", "").replace("400-161-9995", f"**{hotline}**"),
            t.get("local", ""),
            t.get("emergency", ""),
        ]
        return "\n\n".join([p for p in parts if p])


if __name__ == "__main__":
    prep = TherapyPrep()
    print(prep.get_welcome())
    print("\n--- 模拟输入 ---\n")
    inputs = [
        "下周三下午两点",
        "持续在做的咨询，大概半年了",
        "希望能谈谈工作压力的问题",
        "最近工作压力特别大，睡眠也不好",
        "情绪起伏大，有时候特别低落",
        "有个项目搞砸了，领导批评了我",
        "白天没精神，食欲也差了一些",
        "最近总是担心被裁员",
        "做了一些放松训练，有点用",
        # 跳过议题详细问题，走快速流
    ]
    for inp in inputs:
        print(f"\n用户: {inp}")
        r = prep.process(inp)
        print(f"阶段: {r['phase']}")
        print(f"内容: {r['content'][:150] if len(r['content']) > 150 else r['content']}")
        if r['phase'] == 'done':
            break
