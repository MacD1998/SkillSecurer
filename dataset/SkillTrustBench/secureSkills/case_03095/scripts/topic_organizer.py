#!/usr/bin/env python3
"""
咨询议题组织器 - therapy-prep skill 模块
帮助整理和优先级排序咨询议题
"""

import json
from pathlib import Path
from typing import List, Dict


class TopicOrganizer:
    """
    议题组织器

    帮助用户：
    - 识别多个潜在议题
    - 按紧迫度和重要性排序
    - 生成结构化的议题描述
    """

    def __init__(self):
        self.phases_data = self._load_phases()
        self.topics = []

    def _load_phases(self) -> dict:
        p = Path(__file__).parent.parent / "references" / "prep_phases.json"
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_topic(self, topic_text: str, metadata: Dict = None):
        self.topics.append({
            "text": topic_text,
            "metadata": metadata or {},
        })

    def get_topic_prompts(self) -> List[str]:
        return self.phases_data.get("topic_prompts", [])

    def organize(self, user_priorities: str = None) -> List[Dict]:
        """
        组织并排序议题

        Args:
            user_priorities: 用户自己认为的优先级描述

        Returns:
            List of ordered topic dicts
        """
        if not self.topics:
            return []

        # 按议题文本长度简单排序（长文本通常更具体 = 更高优先级）
        sorted_topics = sorted(
            self.topics,
            key=lambda t: len(t.get("text", "")),
            reverse=True
        )

        for i, topic in enumerate(sorted_topics, 1):
            topic["order"] = i

        return sorted_topics

    def generate_summary(self) -> str:
        """生成议题摘要"""
        if not self.topics:
            return "暂无议题记录。"

        organized = self.organize()
        lines = ["📋 **议题摘要**\n"]

        for topic in organized:
            lines.append(f"{topic['order']}. {topic['text']}")

        lines.append(f"\n（共 {len(organized)} 个议题）")
        return "\n".join(lines)


if __name__ == "__main__":
    org = TopicOrganizer()
    org.add_topic("工作压力太大，担心被裁员")
    org.add_topic("和老婆经常吵架，沟通困难")
    org.add_topic("睡眠一直不好，入睡困难")
    print(org.generate_summary())
