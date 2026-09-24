#!/usr/bin/env python3
"""
危机检测器 - therapy-prep skill 模块
"""

import json
from pathlib import Path


class CrisisDetector:
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
    d = CrisisDetector()
    for t in ["我下周咨询", "活着没意思", "想伤害自己", "坚持不住了"]:
        r = d.detect(t)
        print(f"{t!r}: has_crisis={r['has_crisis']}, type={r['type']}")
