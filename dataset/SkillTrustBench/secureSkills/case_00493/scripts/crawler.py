"""
小红书数据采集脚本

支持笔记数据采集、竞品分析数据、搜索趋势数据、评论数据等。
依赖 xhs_client.py 的 API 能力。

使用方式：
    # 采集账号笔记
    python crawler.py --action notes --account "用户ID" --limit 50 --output data.csv

    # 竞品分析
    python crawler.py --action competitor --targets "用户1,用户2,用户3" --limit 30

    # 搜索采集
    python crawler.py --action search --keyword "美妆教程" --sort popularity --limit 50

    # 爆款分析
    python crawler.py --action viral --keyword "护肤" --min-interaction 1000

    # 评论采集
    python crawler.py --action comments --note-id "笔记ID" --limit 100

    # 热搜采集
    python crawler.py --action trending --output trending.json
"""

import json
import csv
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import Counter


def _import_client():
    """延迟导入 XHSClient"""
    # 尝试从同目录导入
    sys.path.insert(0, str(Path(__file__).parent))
    from xhs_client import XHSClient
    return XHSClient


# ─────────────────────────────────────
# 数据采集函数
# ─────────────────────────────────────

def crawl_user_notes(
    account: str,
    limit: int = 50,
    output: Optional[str] = None,
    client=None,
) -> list[dict]:
    """
    采集用户笔记数据

    Args:
        account: 用户 ID 或昵称
        limit: 采集数量
        output: 输出文件路径（支持 .json / .csv）
        client: XHSClient 实例

    Returns:
        笔记数据列表
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    print(f"🔍 开始采集用户 [{account}] 的笔记...")

    all_notes = []
    cursor = ""
    batch_size = 30

    while len(all_notes) < limit:
        notes = client.get_user_notes(
            user_id=account,
            limit=min(batch_size, limit - len(all_notes)),
            cursor=cursor,
        )

        if not notes:
            break

        all_notes.extend([n.to_dict() for n in notes])
        print(f"   已采集 {len(all_notes)}/{limit} 条笔记")

        if len(notes) < batch_size:
            break

        # 分页延迟
        time.sleep(2)

    print(f"✅ 采集完成，共 {len(all_notes)} 条笔记")

    if output:
        _save_data(all_notes, output)

    return all_notes


def crawl_competitors(
    targets: list[str],
    limit: int = 30,
    output: Optional[str] = None,
    client=None,
) -> dict:
    """
    采集多个竞品账号数据

    Args:
        targets: 竞品用户 ID 列表
        limit: 每个账号采集笔记数
        output: 输出文件路径
        client: XHSClient 实例

    Returns:
        竞品数据汇总
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    result = {}

    for target in targets:
        print(f"\n📊 采集竞品: {target}")

        # 获取用户资料
        profile = client.get_user_profile(target)
        profile_data = {}
        if profile:
            profile_data = {
                "user_id": profile.user_id,
                "nickname": profile.nickname,
                "fans": profile.fans,
                "follows": profile.follows,
                "notes_count": profile.notes_count,
                "desc": profile.desc,
            }
        result[target] = {"profile": profile_data}

        # 获取笔记
        notes = crawl_user_notes(target, limit=limit, client=client)
        result[target]["notes"] = notes

        # 统计
        if notes:
            avg_likes = sum(n["likes"] for n in notes) / len(notes)
            avg_collects = sum(n["collects"] for n in notes) / len(notes)
            avg_comments = sum(n["comments"] for n in notes) / len(notes)
            top_notes = sorted(notes, key=lambda x: x["interaction_rate"], reverse=True)[:5]

            result[target]["stats"] = {
                "total_notes": len(notes),
                "avg_likes": round(avg_likes, 1),
                "avg_collects": round(avg_collects, 1),
                "avg_comments": round(avg_comments, 1),
                "top_notes": top_notes,
            }

        time.sleep(3)

    if output:
        _save_data(result, output)

    return result


def crawl_search(
    keyword: str,
    sort: str = "popularity",
    limit: int = 50,
    output: Optional[str] = None,
    client=None,
) -> list[dict]:
    """
    通过搜索采集笔记数据

    Args:
        keyword: 搜索关键词
        sort: 排序方式
        limit: 数量
        output: 输出文件路径
        client: XHSClient 实例

    Returns:
        笔记数据列表
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    print(f"🔍 搜索采集: [{keyword}] (排序: {sort})")

    all_notes = []
    offset = 0
    batch_size = 20

    while len(all_notes) < limit:
        notes = client.search_notes(
            keyword=keyword,
            sort=sort,
            limit=min(batch_size, limit - len(all_notes)),
            offset=offset,
        )

        if not notes:
            break

        all_notes.extend([n.to_dict() for n in notes])
        offset += batch_size
        print(f"   已采集 {len(all_notes)}/{limit} 条")

        if len(notes) < batch_size:
            break

        time.sleep(2)

    print(f"✅ 搜索采集完成，共 {len(all_notes)} 条笔记")

    if output:
        _save_data(all_notes, output)

    return all_notes


def crawl_viral_notes(
    keyword: str,
    min_interaction: int = 1000,
    limit: int = 20,
    output: Optional[str] = None,
    client=None,
) -> list[dict]:
    """
    采集爆款笔记（高互动量）

    Args:
        keyword: 搜索关键词
        min_interaction: 最低互动量（点赞+收藏+评论）
        limit: 数量
        output: 输出文件路径
        client: XHSClient 实例

    Returns:
        爆款笔记列表（按互动量降序）
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    # 扩大采集范围以提高爆款命中率
    raw_notes = crawl_search(keyword, sort="popularity", limit=limit * 5, client=client)

    # 过滤爆款
    viral = []
    for note in raw_notes:
        total = note["likes"] + note["collects"] + note["comments"] + note["shares"]
        if total >= min_interaction:
            note["total_interaction"] = total
            viral.append(note)

    # 按互动量降序
    viral.sort(key=lambda x: x["total_interaction"], reverse=True)
    viral = viral[:limit]

    print(f"🔥 筛选到 {len(viral)} 条爆款笔记（互动量 ≥ {min_interaction}）")

    if output:
        _save_data(viral, output)

    return viral


def crawl_comments(
    note_id: str,
    limit: int = 100,
    output: Optional[str] = None,
    client=None,
) -> list[dict]:
    """
    采集笔记评论

    Args:
        note_id: 笔记 ID
        limit: 数量
        output: 输出文件路径
        client: XHSClient 实例

    Returns:
        评论列表
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    print(f"💬 采集笔记 [{note_id}] 的评论...")

    all_comments = []
    cursor = ""
    batch_size = 20

    while len(all_comments) < limit:
        comments = client.get_note_comments(
            note_id=note_id,
            limit=min(batch_size, limit - len(all_comments)),
            cursor=cursor,
        )

        if not comments:
            break

        all_comments.extend(comments)
        print(f"   已采集 {len(all_comments)}/{limit} 条评论")

        if len(comments) < batch_size:
            break

        time.sleep(1.5)

    print(f"✅ 评论采集完成，共 {len(all_comments)} 条")

    if output:
        _save_data(all_comments, output)

    return all_comments


def crawl_trending(output: Optional[str] = None, client=None) -> list[dict]:
    """
    采集小红书热搜榜

    Args:
        output: 输出文件路径
        client: XHSClient 实例

    Returns:
        热搜关键词列表
    """
    if client is None:
        XHSClient = _import_client()
        client = XHSClient()

    print("📈 采集热搜榜...")
    trends = client.get_trending_keywords()
    print(f"✅ 获取到 {len(trends)} 条热搜")

    if output:
        _save_data(trends, output)

    return trends


# ─────────────────────────────────────
# 数据分析函数
# ─────────────────────────────────────

def analyze_notes(notes: list[dict]) -> dict:
    """
    分析笔记数据，提取关键指标和规律

    Args:
        notes: 笔记数据列表

    Returns:
        分析结果
    """
    if not notes:
        return {"error": "无数据"}

    total = len(notes)

    # 基础统计
    avg_likes = sum(n.get("likes", 0) for n in notes) / total
    avg_collects = sum(n.get("collects", 0) for n in notes) / total
    avg_comments = sum(n.get("comments", 0) for n in notes) / total
    avg_shares = sum(n.get("shares", 0) for n in notes) / total

    # 类型分布
    type_counter = Counter(n.get("type", "unknown") for n in notes)

    # 爆款分析（Top 10%）
    sorted_notes = sorted(notes, key=lambda x: x.get("interaction_rate", 0), reverse=True)
    top_count = max(1, total // 10)
    top_notes = sorted_notes[:top_count]
    avg_top_interaction = sum(n.get("interaction_rate", 0) for n in top_notes) / len(top_notes)

    # 标签频率
    all_tags = []
    for n in notes:
        all_tags.extend(n.get("tags", []))
    tag_counter = Counter(all_tags)
    top_tags = tag_counter.most_common(20)

    # 标题长度分布
    title_lengths = [len(n.get("title", "")) for n in notes]
    avg_title_len = sum(title_lengths) / len(title_lengths) if title_lengths else 0

    return {
        "total_notes": total,
        "avg_metrics": {
            "likes": round(avg_likes, 1),
            "collects": round(avg_collects, 1),
            "comments": round(avg_comments, 1),
            "shares": round(avg_shares, 1),
        },
        "type_distribution": dict(type_counter),
        "top_notes": [n.to_dict() if hasattr(n, "to_dict") else n for n in top_notes],
        "avg_top_interaction": round(avg_top_interaction, 1),
        "top_tags": top_tags,
        "avg_title_length": round(avg_title_len, 1),
        "title_length_range": [min(title_lengths), max(title_lengths)] if title_lengths else [0, 0],
    }


# ─────────────────────────────────────
# 数据保存
# ─────────────────────────────────────

def _save_data(data, output_path: str):
    """保存数据到文件"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ext = path.suffix.lower()

    if ext == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 数据已保存: {path}")

    elif ext == ".csv":
        if isinstance(data, list) and data:
            _save_csv(data, path)
        else:
            print("⚠️  CSV 格式仅支持列表数据")
    else:
        # 默认 JSON
        json_path = path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 数据已保存: {json_path}")


def _save_csv(data: list[dict], path: Path):
    """保存列表数据到 CSV"""
    # 展开嵌套字典
    flat_data = []
    for item in data:
        flat = {}
        for k, v in item.items():
            if isinstance(v, (list, dict)):
                flat[k] = json.dumps(v, ensure_ascii=False)
            else:
                flat[k] = v
        flat_data.append(flat)

    if flat_data:
        keys = flat_data[0].keys()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flat_data)
        print(f"💾 数据已保存: {path}")


# ─────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书数据采集工具")
    subparsers = parser.add_subparsers(dest="action")

    # 采集用户笔记
    notes_parser = subparsers.add_parser("notes", help="采集用户笔记")
    notes_parser.add_argument("--account", required=True, help="用户 ID")
    notes_parser.add_argument("--limit", type=int, default=50)
    notes_parser.add_argument("--output", "-o", help="输出文件路径")

    # 竞品分析
    comp_parser = subparsers.add_parser("competitor", help="竞品数据采集")
    comp_parser.add_argument("--targets", required=True, help="竞品用户 ID，逗号分隔")
    comp_parser.add_argument("--limit", type=int, default=30)
    comp_parser.add_argument("--output", "-o", help="输出文件路径")

    # 搜索采集
    search_parser = subparsers.add_parser("search", help="搜索采集笔记")
    search_parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    search_parser.add_argument("--sort", default="popularity", choices=["general", "popularity", "latest"])
    search_parser.add_argument("--limit", type=int, default=50)
    search_parser.add_argument("--output", "-o", help="输出文件路径")

    # 爆款采集
    viral_parser = subparsers.add_parser("viral", help="爆款笔记采集")
    viral_parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    viral_parser.add_argument("--min-interaction", type=int, default=1000, help="最低互动量")
    viral_parser.add_argument("--limit", type=int, default=20)
    viral_parser.add_argument("--output", "-o", help="输出文件路径")

    # 评论采集
    comment_parser = subparsers.add_parser("comments", help="采集笔记评论")
    comment_parser.add_argument("--note-id", required=True, help="笔记 ID")
    comment_parser.add_argument("--limit", type=int, default=100)
    comment_parser.add_argument("--output", "-o", help="输出文件路径")

    # 热搜
    trend_parser = subparsers.add_parser("trending", help="采集热搜榜")
    trend_parser.add_argument("--output", "-o", help="输出文件路径")

    # 分析
    analyze_parser = subparsers.add_parser("analyze", help="分析采集数据")
    analyze_parser.add_argument("--input", required=True, help="输入数据文件（JSON）")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        exit(1)

    if args.action == "notes":
        crawl_user_notes(args.account, limit=args.limit, output=args.output)

    elif args.action == "competitor":
        targets = [t.strip() for t in args.targets.split(",")]
        crawl_competitors(targets, limit=args.limit, output=args.output)

    elif args.action == "search":
        crawl_search(args.keyword, sort=args.sort, limit=args.limit, output=args.output)

    elif args.action == "viral":
        crawl_viral_notes(
            args.keyword,
            min_interaction=args.min_interaction,
            limit=args.limit,
            output=args.output,
        )

    elif args.action == "comments":
        crawl_comments(args.note_id, limit=args.limit, output=args.output)

    elif args.action == "trending":
        crawl_trending(output=args.output)

    elif args.action == "analyze":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = analyze_notes(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
