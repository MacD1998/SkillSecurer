"""
模板管理模块

管理四种模板（月报/季报/半年报/年报）
"""

import os
from pathlib import Path
from typing import Dict, Optional


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # 默认使用 skill 根目录下的 references 目录
            self.template_dir = Path(__file__).resolve().parent.parent / "references"
        
        self.templates = {}
        self._load_all_templates()
    
    def _load_all_templates(self):
        """加载所有模板"""
        template_files = {
            "月报": "基础模板_月报.md",
            "季报": "基础模板_季报.md",
            "半年报": "基础模板_半年报.md",
            "年报": "基础模板_年报.md"
        }
        
        for template_type, filename in template_files.items():
            filepath = self.template_dir / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    self.templates[template_type] = f.read()
            else:
                print(f"⚠️ 模板文件不存在: {filepath}")
    
    def load_template(self, template_type: str) -> str:
        """加载指定类型的模板"""
        if template_type not in self.templates:
            raise ValueError(f"未知模板类型: {template_type}")
        
        return self.templates[template_type]
    
    def get_template_types(self) -> list:
        """获取所有模板类型"""
        return list(self.templates.keys())
    
    def get_template_structure(self, template_type: str) -> Dict:
        """获取模板章节结构"""
        template = self.load_template(template_type)
        
        # 解析章节
        chapters = []
        lines = template.split("\n")
        
        for line in lines:
            if line.startswith("## "):
                chapter_name = line[3:].strip()
                chapters.append(chapter_name)
        
        return {
            "type": template_type,
            "chapters": chapters
        }


if __name__ == "__main__":
    manager = TemplateManager()
    
    print("可用模板类型:", manager.get_template_types())
    
    for t_type in manager.get_template_types():
        structure = manager.get_template_structure(t_type)
        print(f"\n{t_type} 章节结构:")
        for chapter in structure["chapters"]:
            print(f"  - {chapter}")
