"""
AI 内容生成脚本

使用 LLM 批量生成小红书笔记内容，包括选题、标题、正文、标签。
设计为可独立运行，也可作为模块被其他脚本调用。

使用方式：
    # 生成选题
    python content_generator.py --action topics --niche "美妆" --audience "18-25岁女性" --count 10

    # 生成标题
    python content_generator.py --action titles --topic "秋冬护肤指南" --count 5

    # 生成完整笔记
    python content_generator.py --action note --topic "平价好用的护肤品推荐" --style "种草推荐"

    # 批量生成一周内容
    python content_generator.py --action batch --niche "美食探店" --audience "大学生" --days 7

    # 生成标签
    python content_generator.py --action tags --topic "健身减脂" --count 10
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────
# LLM 集成
# ─────────────────────────────────────

def call_llm(prompt: str, system: str = "", temperature: float = 0.8) -> str:
    """
    调用 LLM 生成内容

    本函数是一个适配层，实际使用时可以对接任何 LLM API。
    在 Agent 环境中，LLM 由宿主 Agent 直接提供，
    因此此脚本主要用于定义 prompt 模板和输出格式。

    Args:
        prompt: 用户提示
        system: 系统提示
        temperature: 创造性参数

    Returns:
        LLM 生成的文本
    """
    # 在 Agent 环境中，内容生成由宿主 Agent 完成
    # 此函数仅返回 prompt 供 Agent 使用
    return f"[LLM Prompt]\nSystem: {system}\n\nUser: {prompt}"


# ─────────────────────────────────────
# 选题生成
# ─────────────────────────────────────

def generate_topics(
    niche: str,
    audience: str = "",
    count: int = 10,
    keywords: Optional[list[str]] = None,
    trend_keywords: Optional[list[str]] = None,
) -> dict:
    """
    生成选题方案

    Args:
        niche: 垂直领域（如：美妆、穿搭、美食）
        audience: 目标受众描述
        count: 生成数量
        keywords: 补充关键词
        trend_keywords: 热点关键词

    Returns:
        选题方案
    """
    trend_section = ""
    if trend_keywords:
        trend_section = f"\n\n当前热点关键词：{', '.join(trend_keywords)}，请结合热点选题。"

    keyword_section = ""
    if keywords:
        keyword_section = f"\n\n参考关键词：{', '.join(keywords)}"

    system = """你是一个专业的小红书内容策划师。你需要根据给定的领域和受众，生成高潜力选题。
选题要求：
1. 符合小红书用户兴趣偏好
2. 兼顾时效性和长尾价值
3. 具备明确的差异化角度
4. 标题有吸引力，能激发点击欲望"""

    prompt = f"""请为【{niche}】领域生成 {count} 个小红书笔记选题。

目标受众：{audience or '小红书主流用户（18-35岁女性为主）'}
{keyword_section}{trend_section}

请按以下 JSON 格式输出：
{{
  "topics": [
    {{
      "title": "选题标题（20字以内）",
      "category": "分类（干货教程/种草推荐/测评对比/生活日常/热点话题）",
      "angle": "差异化角度（一句话描述）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "estimated_heat": "预估热度（1-5星）",
      "competition": "竞争度（低/中/高）",
      "reason": "推荐理由"
    }}
  ]
}}"""

    return {
        "action": "generate_topics",
        "system_prompt": system,
        "user_prompt": prompt,
        "niche": niche,
        "audience": audience,
    }


# ─────────────────────────────────────
# 标题生成
# ─────────────────────────────────────

def generate_titles(
    topic: str,
    count: int = 5,
    style: str = "自然种草",
) -> dict:
    """
    生成标题候选

    Args:
        topic: 选题/主题
        count: 生成数量
        style: 风格（自然种草/专业干货/情绪共鸣/悬念好奇/对比测评）

    Returns:
        标题方案
    """
    system = """你是一个小红书爆款标题专家。你需要生成有吸引力的小红书笔记标题。

小红书标题技巧：
- 控制在 20 字以内
- 使用数字增强说服力（"5个"、"3步"）
- 加入情绪词和感官词
- 制造好奇心和期待感
- 适度使用 emoji（1-2个）
- 避免标题党，内容要能兑现标题的承诺

常见标题公式：
1. 数字+痛点+解决方案：如"3步搞定秋冬卡粉"
2. 身份+场景+结果：如"学生党也能学会的平价穿搭"
3. 反常识+揭秘：如"别再这样洗脸了！90%的人都做错"
4. 时间限定+效果：如"7天见效的减脂餐"
5. 对比+建议：如"贵妇vs平价，这些护肤品真的差很多吗"
6. 情绪+共鸣：如"终于找到了！适合黄皮的口红合集"
7. 灵魂拷问+回答：如"为什么你的化妆总是显脏？"
8. 经验总结+教训：如"踩了100个坑后总结的买房经验"
9. 场景+清单：如"办公室必备的提神好物清单"
10. 地域/人群+推荐：如"上海最好吃的brunch合集"
"""

    prompt = f"""请为以下选题生成 {count} 个小红书标题候选：

选题：{topic}
风格偏好：{style}

请按以下 JSON 格式输出：
{{
  "titles": [
    {{
      "text": "标题文本",
      "formula": "使用的标题公式",
      "score": 85,
      "reason": "推荐理由"
    }}
  ]
}}

按 score 降序排列，最推荐的排第一。"""

    return {
        "action": "generate_titles",
        "system_prompt": system,
        "user_prompt": prompt,
        "topic": topic,
    }


# ─────────────────────────────────────
# 正文生成
# ─────────────────────────────────────

def generate_note_content(
    title: str,
    topic: str,
    style: str = "种草推荐",
    keywords: Optional[list[str]] = None,
    word_count: int = 500,
) -> dict:
    """
    生成笔记正文

    Args:
        title: 笔记标题
        topic: 主题描述
        style: 写作风格
        keywords: 关键词
        word_count: 目标字数

    Returns:
        正文生成方案
    """
    style_guide = {
        "种草推荐": "热情分享，真实体验感，用'真的绝了'、'按头安利'等表达",
        "专业干货": "条理清晰，分点论述，专业但不枯燥",
        "测评对比": "客观公正，优缺点分明，数据支撑",
        "生活日常": "轻松自然，有画面感，像朋友聊天",
        "教程攻略": "步骤清晰，操作性强，附注意事项",
        "情绪共鸣": "引发共情，代入感强，结尾有力量",
    }
    guide = style_guide.get(style, style_guide["种草推荐"])

    keyword_hint = ""
    if keywords:
        keyword_hint = f"\n\n请自然融入以下关键词：{', '.join(keywords)}"

    system = f"""你是一个专业的小红书内容创作者，擅长{style}风格的笔记写作。

写作要求：
1. {guide}
2. 第一句话就要抓住注意力（hook）
3. 每段 2-4 句话，段落间空行
4. 适度使用 emoji（不要过多，3-5个）
5. 结尾引导互动（提问/引导收藏/引导关注）
6. 字数控制在 {word_count} 字左右
7. 语气真诚自然，避免生硬的广告感
8. 适当使用小红书常用表达：绝绝子、yyds、真的会谢、破防了、上头等"""

    prompt = f"""请根据以下信息生成一篇小红书笔记正文：

标题：{title}
主题：{topic}
写作风格：{style}
{keyword_hint}

请按以下 JSON 格式输出：
{{
  "content": "正文内容（纯文本，换行用\\n）",
  "hook": "开头第一句话（hook）",
  "cta": "结尾互动引导",
  "keywords_used": ["实际使用的关键词"],
  "word_count": 实际字数,
  "sections": [
    {{
      "type": "hook/核心内容/案例/总结/cta",
      "text": "段落内容"
    }}
  ]
}}"""

    return {
        "action": "generate_note_content",
        "system_prompt": system,
        "user_prompt": prompt,
        "title": title,
    }


# ─────────────────────────────────────
# 标签生成
# ─────────────────────────────────────

def generate_tags(
    topic: str,
    count: int = 10,
    category: str = "",
) -> dict:
    """
    生成标签推荐

    Args:
        topic: 主题
        count: 标签数量
        category: 分类

    Returns:
        标签方案
    """
    system = """你是一个小红书标签优化专家。你需要为笔记推荐最合适的标签组合。

标签策略：
- 大流量标签（2-3个）：领域通用热门标签，获取基础曝光
- 场景标签（2-3个）：使用场景/人群标签，精准触达
- 长尾标签（2-4个）：精准搜索词，提升搜索排名
- 不要超过 10 个标签
- 标签与内容高度相关，不要堆砌热门标签"""

    prompt = f"""请为以下笔记推荐标签：

主题：{topic}
分类：{category or '自动判断'}

请按以下 JSON 格式输出：
{{
  "tags": [
    {{
      "tag": "#标签名",
      "type": "大流量/场景/长尾",
      "search_volume": "预估搜索量（高/中/低）",
      "relevance": "相关性（高/中/低）"
    }}
  ],
  "tag_string": "#标签1 #标签2 #标签3 ..."
}}

推荐 {count} 个标签，按相关性降序排列。"""

    return {
        "action": "generate_tags",
        "system_prompt": system,
        "user_prompt": prompt,
        "topic": topic,
    }


# ─────────────────────────────────────
# 完整笔记生成
# ─────────────────────────────────────

def generate_full_note(
    topic: str,
    style: str = "种草推荐",
    audience: str = "",
    keywords: Optional[list[str]] = None,
) -> dict:
    """
    生成完整笔记（标题 + 正文 + 标签）

    Args:
        topic: 主题
        style: 写作风格
        audience: 目标受众
        keywords: 补充关键词

    Returns:
        完整笔记生成方案
    """
    audience_hint = f"\n目标受众：{audience}" if audience else ""
    keyword_hint = ""
    if keywords:
        keyword_hint = f"\n参考关键词：{', '.join(keywords)}"

    system = """你是一个顶级的小红书内容创作者。你需要为一篇笔记生成完整的标题、正文和标签。

质量标准：
- 标题：20字以内，有吸引力，包含核心关键词
- 正文：500-800字，结构清晰，有 hook，有 cta
- 标签：5-10 个，混合大流量词和长尾词
- 整体风格统一、真实、有价值"""

    prompt = f"""请为一篇小红书笔记生成完整内容：

主题：{topic}
写作风格：{style}
{audience_hint}{keyword_hint}

请按以下 JSON 格式输出：
{{
  "title": "笔记标题",
  "content": "正文内容",
  "tags": ["#标签1", "#标签2", "#标签3"],
  "hook": "开头第一句话",
  "cta": "结尾互动引导",
  "cover_suggestion": "封面设计建议（描述）",
  "publish_time_suggestion": "建议发布时间段",
  "seo_keywords": ["SEO 优化关键词"]
}}"""

    return {
        "action": "generate_full_note",
        "system_prompt": system,
        "user_prompt": prompt,
        "topic": topic,
    }


# ─────────────────────────────────────
# 批量生成
# ─────────────────────────────────────

def generate_batch(
    niche: str,
    audience: str = "",
    days: int = 7,
    style: str = "混合",
) -> dict:
    """
    批量生成多天内容

    Args:
        niche: 垂直领域
        audience: 目标受众
        days: 天数
        style: 写作风格

    Returns:
        批量内容方案
    """
    styles = ["种草推荐", "专业干货", "测评对比", "生活日常", "教程攻略"]
    if style == "混合":
        selected_styles = styles
    else:
        selected_styles = [style]

    system = """你是一个专业的小红书内容策划师。你需要为一个账号规划并生成多天的内容。

内容矩阵要求：
1. 每天发布 1-2 篇笔记
2. 内容类型多样化（干货、种草、日常、互动各占合理比例）
3. 内容之间有逻辑关联，形成系列感
4. 热点和常青内容搭配"""

    prompt = f"""请为【{niche}】领域规划 {days} 天的小红书内容。

目标受众：{audience or '小红书主流用户'}
风格偏好：{style}

请按以下 JSON 格式输出：
{{
  "plan": [
    {{
      "day": 1,
      "date": "日期建议",
      "publish_time": "建议发布时间",
      "notes": [
        {{
          "title": "标题",
          "content": "正文",
          "tags": ["#标签1", "#标签2"],
          "type": "图文/视频",
          "style": "写作风格",
          "cover_suggestion": "封面建议"
        }}
      ]
    }}
  ]
}}

请确保内容质量和多样性，每篇笔记都应该是高质量的原创内容。"""

    return {
        "action": "generate_batch",
        "system_prompt": system,
        "user_prompt": prompt,
        "niche": niche,
        "days": days,
    }


# ─────────────────────────────────────
# 内容优化
# ─────────────────────────────────────

def optimize_content(
    title: str,
    content: str,
    tags: Optional[list[str]] = None,
    optimize_for: str = "engagement",
) -> dict:
    """
    优化已有笔记内容

    Args:
        title: 原标题
        content: 原正文
        tags: 原标签
        optimize_for: 优化目标（engagement=互动率, search=搜索排名, conversion=转化率）

    Returns:
        优化建议
    """
    opt_guide = {
        "engagement": "提升互动率：强化情绪共鸣、增加互动引导、优化标题吸引力",
        "search": "提升搜索排名：优化关键词布局、增加长尾词、优化标签组合",
        "conversion": "提升转化率：强化产品卖点、增加信任背书、优化 CTA",
    }

    system = f"""你是一个小红书内容优化专家。你需要分析已有笔记并提出优化建议。

优化目标：{opt_guide.get(optimize_for, opt_guide['engagement'])}

分析维度：
1. 标题是否足够吸引
2. 正文结构是否清晰
3. hook 是否有效
4. CTA 是否有力
5. 标签是否优化
6. 整体质量评估"""

    tags_str = ", ".join(tags) if tags else "无"
    prompt = f"""请分析并优化以下小红书笔记：

【原标题】{title}

【原正文】
{content}

【原标签】{tags_str}

【优化目标】{optimize_for}

请按以下 JSON 格式输出：
{{
  "analysis": {{
    "title_score": 70,
    "content_score": 75,
    "tags_score": 65,
    "overall_score": 70,
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"]
  }},
  "optimized": {{
    "title": "优化后的标题",
    "content": "优化后的正文",
    "tags": ["#优化标签1", "#优化标签2"]
  }},
  "suggestions": [
    {{
      "aspect": "优化方面",
      "before": "优化前",
      "after": "优化后",
      "reason": "原因"
    }}
  ]
}}"""

    return {
        "action": "optimize_content",
        "system_prompt": system,
        "user_prompt": prompt,
    }


# ─────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 内容生成工具")
    subparsers = parser.add_subparsers(dest="action")

    # 选题
    topic_parser = subparsers.add_parser("topics", help="生成选题")
    topic_parser.add_argument("--niche", "-n", required=True, help="垂直领域")
    topic_parser.add_argument("--audience", default="", help="目标受众")
    topic_parser.add_argument("--count", type=int, default=10)
    topic_parser.add_argument("--output", "-o", help="输出文件")

    # 标题
    title_parser = subparsers.add_parser("titles", help="生成标题")
    title_parser.add_argument("--topic", "-t", required=True, help="选题")
    title_parser.add_argument("--count", type=int, default=5)
    title_parser.add_argument("--style", default="自然种草")
    title_parser.add_argument("--output", "-o", help="输出文件")

    # 正文
    content_parser = subparsers.add_parser("content", help="生成正文")
    content_parser.add_argument("--title", required=True, help="笔记标题")
    content_parser.add_argument("--topic", required=True, help="主题")
    content_parser.add_argument("--style", default="种草推荐")
    content_parser.add_argument("--keywords", help="关键词，逗号分隔")
    content_parser.add_argument("--output", "-o", help="输出文件")

    # 完整笔记
    note_parser = subparsers.add_parser("note", help="生成完整笔记")
    note_parser.add_argument("--topic", "-t", required=True, help="主题")
    note_parser.add_argument("--style", default="种草推荐")
    note_parser.add_argument("--audience", default="")
    note_parser.add_argument("--keywords", help="关键词，逗号分隔")
    note_parser.add_argument("--output", "-o", help="输出文件")

    # 标签
    tag_parser = subparsers.add_parser("tags", help="生成标签")
    tag_parser.add_argument("--topic", "-t", required=True, help="主题")
    tag_parser.add_argument("--count", type=int, default=10)
    tag_parser.add_argument("--output", "-o", help="输出文件")

    # 批量
    batch_parser = subparsers.add_parser("batch", help="批量生成内容")
    batch_parser.add_argument("--niche", "-n", required=True, help="垂直领域")
    batch_parser.add_argument("--audience", default="", help="目标受众")
    batch_parser.add_argument("--days", type=int, default=7)
    batch_parser.add_argument("--style", default="混合")
    batch_parser.add_argument("--output", "-o", help="输出文件")

    # 优化
    opt_parser = subparsers.add_parser("optimize", help="优化已有内容")
    opt_parser.add_argument("--title", required=True, help="原标题")
    opt_parser.add_argument("--content", required=True, help="原正文")
    opt_parser.add_argument("--tags", help="原标签，逗号分隔")
    opt_parser.add_argument("--for", dest="optimize_for", default="engagement",
                           choices=["engagement", "search", "conversion"])
    opt_parser.add_argument("--output", "-o", help="输出文件")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        exit(1)

    result = None

    if args.action == "topics":
        result = generate_topics(args.niche, audience=args.audience, count=args.count)

    elif args.action == "titles":
        result = generate_titles(args.topic, count=args.count, style=args.style)

    elif args.action == "content":
        kws = args.keywords.split(",") if args.keywords else None
        result = generate_note_content(
            args.title, args.topic, style=args.style, keywords=kws
        )

    elif args.action == "note":
        kws = args.keywords.split(",") if args.keywords else None
        result = generate_full_note(args.topic, style=args.style, audience=args.audience, keywords=kws)

    elif args.action == "tags":
        result = generate_tags(args.topic, count=args.count)

    elif args.action == "batch":
        result = generate_batch(args.niche, audience=args.audience, days=args.days, style=args.style)

    elif args.action == "optimize":
        tags_list = args.tags.split(",") if args.tags else None
        result = optimize_content(args.title, args.content, tags=tags_list, optimize_for=args.optimize_for)

    if result:
        output = json.dumps(result, ensure_ascii=False, indent=2)
        print(output)

        if hasattr(args, "output") and args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\n💾 已保存: {args.output}")
