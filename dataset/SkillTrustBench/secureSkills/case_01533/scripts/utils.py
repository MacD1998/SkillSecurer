"""
工具函数模块
"""

import os
import logging
from pathlib import Path
from datetime import datetime


def setup_logging(level=logging.INFO):
    """配置日志"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def save_output(filepath: Path, content: str):
    """保存输出文件"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    logging.info(f"文件已保存: {filepath}")


def generate_filename(org_name: str, person_name: str, template_type: str) -> str:
    """生成文件名"""
    # 格式: {编码}_{组织名}_{姓名}_{时间维度}填写规范.md
    
    # 简化版：使用组织名+个人名
    name_parts = [org_name]
    if person_name:
        name_parts.append(person_name)
    name_parts.append(f"{template_type}填写规范")
    
    filename = "_".join(name_parts) + ".md"
    
    # 清理文件名中的非法字符
    filename = filename.replace("/", "_").replace("\\", "_")
    
    return filename


def get_current_period() -> str:
    """获取当前周期（月/季/半年/年）"""
    now = datetime.now()
    month = now.month
    
    # 判断季度
    quarter = (month - 1) // 3 + 1
    
    # 判断半年
    half = 1 if month <= 6 else 2
    
    return {
        "month": month,
        "quarter": quarter,
        "half": half,
        "year": now.year
    }


def format_bp_code(code: str) -> str:
    """格式化 BP 编码"""
    if not code:
        return "[待确认编码]"
    
    # 标准化格式
    code = code.strip()
    
    return code


def calculate_deviation(actual: float, target: float) -> dict:
    """计算偏离度"""
    if target == 0:
        return {"deviation": 0, "status": "无法计算"}
    
    deviation = (actual - target) / target * 100
    
    # 判断颜色
    if abs(deviation) > 5:
        status = "红"
    elif abs(deviation) > 3:
        status = "黄"
    else:
        status = "绿"
    
    return {
        "deviation": deviation,
        "deviation_str": f"{deviation:+.1f}%",
        "status": status
    }


if __name__ == "__main__":
    # 测试
    print(generate_filename("产品中心", "林刚", "月报"))
    print(get_current_period())
    print(calculate_deviation(95, 100))
    print(calculate_deviation(85, 100))
