"""
运营报告生成脚本

支持日报、周报、月报、活动复盘等运营报告的自动生成。
依赖 crawler.py 的数据分析能力 + LLM 文案生成能力。

使用方式：
    # 日报
    python report_builder.py --type daily --account "用户ID" --data "data.json"

    # 周报
    python report_builder.py --type weekly --account "用户ID" --data "data.json"

    # 月报
    python report_builder.py --type monthly --account "用户ID" --data "data.json"

    # 活动复盘
    python report_builder.py --type campaign --campaign "双11大促" --data "data.json"

    # 爆款分析报告
    python report_builder.py --type viral-analysis --data "viral_data.json"
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────
# 模板系统
# ─────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent.parent / "assets" / "report-templates"


def load_template(template_name: str) -> str:
    """加载报告模板"""
    template_path = TEMPLATES_DIR / f"{template_name}.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


# ─────────────────────────────────────
# 数据分析
# ─────────────────────────────────────

def analyze_performance(data: dict) -> dict:
    """
    分析运营数据，生成统计指标

    Args:
        data: 包含笔记列表的数据

    Returns:
        统计指标
    """
    notes = data.get("notes", [])
    if not notes:
        return {"error": "无笔记数据"}

    total = len(notes)

    # 基础指标
    total_likes = sum(n.get("likes", 0) for n in notes)
    total_collects = sum(n.get("collects", 0) for n in notes)
    total_comments = sum(n.get("comments", 0) for n in notes)
    total_shares = sum(n.get("shares", 0) for n in notes)

    avg_likes = total_likes / total
    avg_collects = total_collects / total
    avg_comments = total_comments / total
    avg_shares = total_shares / total

    # 互动率
    interactions = [n.get("likes", 0) + n.get("collects", 0) + n.get("comments", 0) + n.get("shares", 0) for n in notes]
    avg_interaction = sum(interactions) / total

    # 爆款识别（Top 20%）
    sorted_notes = sorted(enumerate(notes), key=lambda x: x[1].get("interaction_rate", 0), reverse=True)
    top_count = max(1, total // 5)
    viral_indices = set(i for i, _ in sorted_notes[:top_count])
    viral_count = len(viral_indices)

    # 类型分布
    type_dist = {}
    for n in notes:
        t = n.get("type", "unknown")
        type_dist[t] = type_dist.get(t, 0) + 1

    # 标签分析
    all_tags = []
    for n in notes:
        all_tags.extend(n.get("tags", []))
    tag_freq = {}
    for tag in all_tags:
        tag_freq[tag] = tag_freq.get(tag, 0) + 1
    top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:15]

    # 最佳/最差笔记
    best = sorted_notes[0][1] if sorted_notes else {}
    worst = sorted_notes[-1][1] if sorted_notes else {}

    return {
        "period": {
            "total_notes": total,
            "start": data.get("start_date", ""),
            "end": data.get("end_date", ""),
        },
        "metrics": {
            "total_likes": total_likes,
            "total_collects": total_collects,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "avg_likes": round(avg_likes, 1),
            "avg_collects": round(avg_collects, 1),
            "avg_comments": round(avg_comments, 1),
            "avg_shares": round(avg_shares, 1),
            "avg_interaction": round(avg_interaction, 1),
            "viral_count": viral_count,
            "viral_rate": f"{viral_count / total * 100:.1f}%",
        },
        "type_distribution": type_dist,
        "top_tags": top_tags,
        "best_note": {
            "title": best.get("title", ""),
            "likes": best.get("likes", 0),
            "collects": best.get("collects", 0),
        },
        "worst_note": {
            "title": worst.get("title", ""),
            "likes": worst.get("likes", 0),
            "collects": worst.get("collects", 0),
        },
    }


# ─────────────────────────────────────
# 报告生成
# ─────────────────────────────────────

def build_daily_report(account: str, data: dict, analysis: dict) -> str:
    """生成运营日报"""
    today = datetime.now().strftime("%Y-%m-%d")
    m = analysis.get("metrics", {})

    report = f"""# 📊 小红书运营日报

**账号：** {account}
**日期：** {today}
**生成时间：** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 一、核心数据概览

| 指标 | 数值 |
|------|------|
| 发布笔记数 | {analysis['period']['total_notes']} |
| 总点赞数 | {m.get('total_likes', 0):,} |
| 总收藏数 | {m.get('total_collects', 0):,} |
| 总评论数 | {m.get('total_comments', 0):,} |
| 总分享数 | {m.get('total_shares', 0):,} |
| 平均互动量 | {m.get('avg_interaction', 0):,} |
| 爆款笔记数 | {m.get('viral_count', 0)} |

## 二、笔记表现 Top 5

"""

    notes = data.get("notes", [])
    sorted_notes = sorted(notes, key=lambda x: x.get("interaction_rate", 0), reverse=True)[:5]
    for i, note in enumerate(sorted_notes, 1):
        report += f"""### {i}. {note.get('title', '无标题')}

- **类型：** {'图文' if note.get('type') == 'normal' else '视频'}
- **点赞：** {note.get('likes', 0)} | **收藏：** {note.get('collects', 0)} | **评论：** {note.get('comments', 0)}
- **标签：** {', '.join(note.get('tags', [])[:5])}

"""

    report += """## 三、数据分析

"""

    # 标签分析
    top_tags = analysis.get("top_tags", [])
    if top_tags:
        report += "### 高频标签\n\n"
        report += "| 标签 | 使用次数 |\n|------|---------|\n"
        for tag, count in top_tags[:10]:
            report += f"| {tag} | {count} |\n"
        report += "\n"

    # 内容类型分布
    type_dist = analysis.get("type_distribution", {})
    if type_dist:
        report += "### 内容类型分布\n\n"
        report += "| 类型 | 数量 | 占比 |\n|------|------|------|\n"
        total = sum(type_dist.values())
        for t, c in type_dist.items():
            report += f"| {'图文' if t == 'normal' else t} | {c} | {c / total * 100:.1f}% |\n"
        report += "\n"

    report += """## 四、明日计划

- [ ] 待发布笔记标题
- [ ] 待互动回复的评论
- [ ] 待跟进的热点选题

---

*报告由 xiaohongshu-auto-skill 自动生成*
"""
    return report


def build_weekly_report(account: str, data: dict, analysis: dict) -> str:
    """生成运营周报"""
    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")
    m = analysis.get("metrics", {})

    report = f"""# 📈 小红书运营周报

**账号：** {account}
**周期：** {week_start} ~ {week_end}
**生成时间：** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 一、本周核心数据

| 指标 | 本周数据 | 日均 |
|------|---------|------|
| 发布笔记数 | {analysis['period']['total_notes']} | {analysis['period']['total_notes'] / 7:.1f} |
| 总点赞数 | {m.get('total_likes', 0):,} | {m.get('total_likes', 0) / 7:,.0f} |
| 总收藏数 | {m.get('total_collects', 0):,} | {m.get('total_collects', 0) / 7:,.0f} |
| 总评论数 | {m.get('total_comments', 0):,} | {m.get('total_comments', 0) / 7:,.0f} |
| 总分享数 | {m.get('total_shares', 0):,} | {m.get('total_shares', 0) / 7:,.0f} |
| 平均互动量 | {m.get('avg_interaction', 0):,} | - |
| 爆款率 | {m.get('viral_rate', '0%')} | - |

## 二、内容分析

### 2.1 爆款笔记

"""

    notes = data.get("notes", [])
    sorted_notes = sorted(notes, key=lambda x: x.get("interaction_rate", 0), reverse=True)[:3]
    for i, note in enumerate(sorted_notes, 1):
        report += f"""**Top {i}：{note.get('title', '无标题')}**
- 互动数据：👍 {note.get('likes', 0)} | ⭐ {note.get('collects', 0)} | 💬 {note.get('comments', 0)}
- 成功因素分析：
  - 标题策略：[待 LLM 分析]
  - 内容亮点：[待 LLM 分析]
  - 发布时间：{note.get('publish_time', '未知')}

"""

    report += """### 2.2 低表现笔记分析

"""

    worst_notes = sorted(notes, key=lambda x: x.get("interaction_rate", 0))[:3]
    for i, note in enumerate(worst_notes, 1):
        report += f"""- {note.get('title', '无标题')}：互动量 {note.get('interaction_rate', 0)}，可能原因：[待分析]

"""

    report += """### 2.3 标签效果分析

"""

    top_tags = analysis.get("top_tags", [])
    if top_tags:
        report += "| 排名 | 标签 | 使用次数 |\n|------|------|---------|\n"
        for i, (tag, count) in enumerate(top_tags[:10], 1):
            report += f"| {i} | {tag} | {count} |\n"

    report += """
## 三、粉丝增长分析

| 指标 | 数值 |
|------|------|
| 本周新增粉丝 | - |
| 总粉丝数 | - |
| 粉丝增长率 | - |

> 注：粉丝数据需要通过 API 获取账号信息

## 四、本周总结

### 做得好的地方
1. [待 LLM 分析填写]
2. ...

### 需要改进的地方
1. [待 LLM 分析填写]
2. ...

## 五、下周计划

| 日期 | 内容方向 | 数量 | 优先级 |
|------|---------|------|--------|
| 周一 | - | - | - |
| 周二 | - | - | - |
| 周三 | - | - | - |
| 周四 | - | - | - |
| 周五 | - | - | - |
| 周六 | - | - | - |
| 周日 | - | - | - |

---

*报告由 xiaohongshu-auto-skill 自动生成*
"""
    return report


def build_monthly_report(account: str, data: dict, analysis: dict) -> str:
    """生成运营月报"""
    now = datetime.now()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    m = analysis.get("metrics", {})

    report = f"""# 📊 小红书运营月报

**账号：** {account}
**月份：** {now.strftime("%Y年%m月")}
**生成时间：** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 一、月度核心数据

| 指标 | 本月数据 | 日均 |
|------|---------|------|
| 发布笔记数 | {analysis['period']['total_notes']} | {analysis['period']['total_notes'] / 30:.1f} |
| 总点赞数 | {m.get('total_likes', 0):,} | {m.get('total_likes', 0) / 30:,.0f} |
| 总收藏数 | {m.get('total_collects', 0):,} | {m.get('total_collects', 0) / 30:,.0f} |
| 总评论数 | {m.get('total_comments', 0):,} | {m.get('total_comments', 0) / 30:,.0f} |
| 总分享数 | {m.get('total_shares', 0):,} | {m.get('total_shares', 0) / 30:,.0f} |
| 爆款率 | {m.get('viral_rate', '0%')} | - |

## 二、月度趋势分析

### 2.1 数据趋势
（建议配合图表展示）

### 2.2 内容表现排行

| 排名 | 标题 | 点赞 | 收藏 | 评论 | 互动率 |
|------|------|------|------|------|--------|

### 2.3 内容类型分析

"""

    type_dist = analysis.get("type_distribution", {})
    total = sum(type_dist.values()) if type_dist else 1
    for t, c in type_dist.items():
        report += f"- {'图文' if t == 'normal' else t}: {c} 篇 ({c / total * 100:.1f}%)\n"

    report += """
## 三、ROI 分析

| 投入项 | 成本/时间 | 产出 |
|--------|----------|------|
| 内容创作 | - | - |
| 封面设计 | - | - |
| 互动管理 | - | - |

## 四、竞品对比

| 指标 | 本账号 | 竞品A | 竞品B |
|------|--------|-------|-------|
| 发布频率 | - | - | - |
| 平均互动 | - | - | - |
| 爆款率 | - | - | - |

## 五、月度总结与建议

### 核心发现
1. [待 LLM 分析]
2. ...

### 优化建议
1. [待 LLM 分析]
2. ...

### 下月目标
- [ ] 目标 1
- [ ] 目标 2
- [ ] 目标 3

---

*报告由 xiaohongshu-auto-skill 自动生成*
"""
    return report


def build_campaign_report(campaign: str, data: dict, analysis: dict) -> str:
    """生成活动复盘报告"""
    m = analysis.get("metrics", {})

    report = f"""# 🎯 活动复盘报告

**活动名称：** {campaign}
**活动周期：** {data.get('start_date', '')} ~ {data.get('end_date', '')}
**生成时间：** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 一、活动目标与达成

| 目标指标 | 目标值 | 实际值 | 达成率 |
|---------|--------|--------|--------|
| 发布笔记数 | - | {analysis['period']['total_notes']} | - |
| 总互动量 | - | {m.get('total_likes', 0) + m.get('total_collects', 0) + m.get('total_comments', 0):,} | - |
| 新增粉丝 | - | - | - |

## 二、活动内容回顾

### 2.1 内容清单

| 序号 | 标题 | 类型 | 点赞 | 收藏 | 评论 | 状态 |
|------|------|------|------|------|------|------|

### 2.2 优秀内容

### 2.3 需改进内容

## 三、数据分析

### 3.1 互动趋势
### 3.2 受众分析
### 3.3 转化漏斗

## 四、经验总结

### 成功经验
1. ...
### 失败教训
1. ...

## 五、后续计划

---

*报告由 xiaohongshu-auto-skill 自动生成*
"""
    return report


def build_viral_analysis(data: list[dict]) -> str:
    """生成爆款分析报告"""
    report = """# 🔥 爆款笔记拆解分析报告

---

"""

    for i, note in enumerate(data, 1):
        interaction = note.get("total_interaction", 0)
        report += f"""## 爆款 #{i}：{note.get('title', '无标题')}

| 指标 | 数值 |
|------|------|
| 类型 | {'图文' if note.get('type') == 'normal' else '视频'} |
| 作者 | {note.get('author', '-')} |
| 点赞 | {note.get('likes', 0):,} |
| 收藏 | {note.get('collects', 0):,} |
| 评论 | {note.get('comments', 0):,} |
| 分享 | {note.get('shares', 0):,} |
| 总互动量 | {interaction:,} |

### 标题分析
{note.get('title', '')}

### 内容分析
{note.get('desc', '')[:200]}...

### 标签分析
{', '.join(note.get('tags', []))}

### 爆款因素分析

| 因素 | 分析 |
|------|------|
| 标题钩子 | [待 LLM 分析] |
| 内容价值 | [待 LLM 分析] |
| 情绪触发 | [待 LLM 分析] |
| 互动引导 | [待 LLM 分析] |
| 标签选择 | [待 LLM 分析] |

### 可复用要素
1. [待 LLM 分析]

---

"""

    # 跨爆款共性分析
    report += """## 跨爆款共性规律

### 标题共性
[待 LLM 分析]

### 内容共性
[待 LLM 分析]

### 标签共性
[待 LLM 分析]

## 创作建议
[待 LLM 分析]

---

*报告由 xiaohongshu-auto-skill 自动生成*
"""
    return report


# ─────────────────────────────────────
# 主入口
# ─────────────────────────────────────

def build_report(
    report_type: str,
    data: dict,
    account: str = "",
    campaign: str = "",
) -> str:
    """
    生成运营报告

    Args:
        report_type: 报告类型（daily/weekly/monthly/campaign/viral-analysis）
        data: 数据
        account: 账号
        campaign: 活动名称

    Returns:
        Markdown 格式的报告
    """
    if report_type == "viral-analysis":
        return build_viral_analysis(data)

    analysis = analyze_performance(data)

    builders = {
        "daily": build_daily_report,
        "weekly": build_weekly_report,
        "monthly": build_monthly_report,
        "campaign": build_campaign_report,
    }

    builder = builders.get(report_type)
    if not builder:
        raise ValueError(f"不支持的报告类型: {report_type}，可选: {list(builders.keys())}")

    if report_type == "campaign":
        return builder(campaign, data, analysis)
    return builder(account, data, analysis)


# ─────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运营报告生成工具")
    parser.add_argument("--type", "-t", required=True,
                       choices=["daily", "weekly", "monthly", "campaign", "viral-analysis"],
                       help="报告类型")
    parser.add_argument("--account", default="", help="账号名称/ID")
    parser.add_argument("--campaign", default="", help="活动名称")
    parser.add_argument("--data", "-d", required=True, help="数据文件路径（JSON）")
    parser.add_argument("--output", "-o", required=True, help="输出报告路径（.md）")

    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = build_report(
        report_type=args.type,
        data=data,
        account=args.account,
        campaign=args.campaign,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"✅ 报告已生成: {output_path}")
