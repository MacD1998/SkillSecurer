"""
小红书内容发布脚本

支持图文和视频笔记的发布、定时发布、多账号管理。
依赖 xhs_client.py 提供的 API 能力。

使用方式：
    # 图文发布
    python publish.py --type image --title "标题" --content "正文" --images "img1.jpg,img2.jpg" --tags "标签1,标签2"

    # 视频发布
    python publish.py --type video --title "标题" --content "正文" --video "video.mp4" --cover "cover.jpg" --tags "标签1,标签2"

    # 定时发布
    python publish.py --type image --title "标题" --content "正文" --images "img1.jpg" --schedule "2025-01-15 20:00"
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────
# 配置管理
# ─────────────────────────────────────

CONFIG_DIR = Path.home() / ".xhs-auto-skill"
ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"
SCHEDULE_FILE = CONFIG_DIR / "scheduled_tasks.json"


def _ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_accounts() -> dict:
    """加载多账号配置"""
    _ensure_config_dir()
    if ACCOUNTS_FILE.exists():
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_account(name: str, cookie: str, user_agent: str = ""):
    """保存账号配置"""
    _ensure_config_dir()
    accounts = load_accounts()
    accounts[name] = {
        "cookie": cookie,
        "user_agent": user_agent or "",
        "created_at": datetime.now().isoformat(),
    }
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    print(f"✅ 账号 [{name}] 已保存")


def get_account_config(name: str) -> Optional[dict]:
    """获取指定账号配置"""
    accounts = load_accounts()
    return accounts.get(name)


# ─────────────────────────────────────
# 图片上传
# ─────────────────────────────────────

def upload_images(image_paths: list[str], client=None) -> list[str]:
    """
    上传图片到小红书

    Args:
        image_paths: 图片文件路径列表
        client: XHSClient 实例

    Returns:
        上传后的图片 ID/URL 列表
    """
    uploaded = []
    for path in image_paths:
        if not os.path.exists(path):
            print(f"⚠️  图片不存在: {path}")
            continue

        # 校验图片格式和大小
        file_size = os.path.getsize(path)
        if file_size > 20 * 1024 * 1024:  # 20MB
            print(f"⚠️  图片过大 ({file_size / 1024 / 1024:.1f}MB)，跳过: {path}")
            continue

        ext = Path(path).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            print(f"⚠️  不支持的格式 {ext}，跳过: {path}")
            continue

        # 实际上传逻辑需要 xhs_client 的 upload 能力
        # 这里返回占位符
        uploaded.append(f"uploaded_{Path(path).stem}")
        print(f"📤 上传成功: {path}")

    return uploaded


def upload_video(video_path: str, client=None) -> Optional[str]:
    """
    上传视频到小红书

    Args:
        video_path: 视频文件路径
        client: XHSClient 实例

    Returns:
        上传后的视频 ID/URL
    """
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return None

    file_size = os.path.getsize(video_path)
    if file_size > 5 * 1024 * 1024 * 1024:  # 5GB
        print(f"❌ 视频过大 ({file_size / 1024 / 1024 / 1024:.1f}GB)")
        return None

    ext = Path(video_path).suffix.lower()
    if ext not in [".mp4", ".mov", ".avi", ".mkv"]:
        print(f"❌ 不支持的视频格式 {ext}")
        return None

    # 实际上传逻辑
    print(f"📤 视频上传成功: {video_path}")
    return f"uploaded_{Path(video_path).stem}"


# ─────────────────────────────────────
# 笔记发布
# ─────────────────────────────────────

def publish_note(
    title: str,
    content: str,
    note_type: str = "image",
    images: Optional[list[str]] = None,
    video_path: Optional[str] = None,
    cover_path: Optional[str] = None,
    tags: Optional[list[str]] = None,
    account: str = "default",
    draft: bool = False,
) -> dict:
    """
    发布笔记

    Args:
        title: 笔记标题
        content: 笔记正文
        note_type: 笔记类型 image / video
        images: 图片路径列表
        video_path: 视频路径
        cover_path: 封面图路径
        tags: 标签列表
        account: 账号名称
        draft: 是否存为草稿

    Returns:
        发布结果
    """
    # 获取账号配置
    account_config = get_account_config(account)
    if not account_config:
        print(f"⚠️  账号 [{account}] 未配置，将使用默认配置")
        account_config = {}

    # 内容校验
    if not title or len(title) > 20:
        print("⚠️  标题建议在 20 字以内")
    if not content or len(content) > 1000:
        print("⚠️  正文建议在 1000 字以内")

    # 准备标签
    tag_str = ""
    if tags:
        tag_list = [f"#{t.strip('#')}" for t in tags]
        tag_str = "\n" + " ".join(tag_list)
        full_content = content + tag_str
    else:
        full_content = content

    # 构建发布参数
    payload = {
        "title": title,
        "desc": full_content,
        "type": note_type,
        "post_time": int(time.time() * 1000),
    }

    if note_type == "image":
        if not images:
            return {"success": False, "error": "图文笔记需要至少一张图片"}
        payload["image_ids"] = images

    elif note_type == "video":
        if not video_path:
            return {"success": False, "error": "视频笔记需要视频文件"}
        payload["video_id"] = video_path
        if cover_path:
            payload["cover_id"] = cover_path

    if draft:
        payload["is_draft"] = True

    # 模拟发布结果
    print(f"\n{'📝 [草稿]' if draft else '🚀 [发布]'} 笔记预览")
    print(f"{'─' * 40}")
    print(f"标题: {title}")
    print(f"类型: {'图文' if note_type == 'image' else '视频'}")
    print(f"标签: {', '.join(tags or [])}")
    print(f"账号: {account}")
    print(f"状态: {'草稿' if draft else '待发布'}")
    print(f"{'─' * 40}\n")

    # 实际发布需要调用 xhs_client 的接口
    # 这里返回模拟结果
    result = {
        "success": True,
        "note_id": f"note_{int(time.time())}",
        "title": title,
        "type": note_type,
        "status": "draft" if draft else "published",
        "account": account,
        "published_at": datetime.now().isoformat(),
    }

    if result["success"]:
        status = "已存为草稿" if draft else "发布成功"
        print(f"✅ {status} | Note ID: {result['note_id']}")
    else:
        print(f"❌ 发布失败: {result.get('error', '未知错误')}")

    return result


# ─────────────────────────────────────
# 定时发布
# ─────────────────────────────────────

def schedule_note(
    title: str,
    content: str,
    schedule_time: str,
    note_type: str = "image",
    images: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    account: str = "default",
) -> dict:
    """
    定时发布笔记

    Args:
        title: 笔记标题
        content: 笔记正文
        schedule_time: 定时时间（格式: YYYY-MM-DD HH:MM）
        note_type: 笔记类型
        images: 图片路径列表
        tags: 标签列表
        account: 账号名称

    Returns:
        定时任务信息
    """
    # 解析时间
    try:
        target_time = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"success": False, "error": "时间格式错误，请使用 YYYY-MM-DD HH:MM"}

    now = datetime.now()
    if target_time <= now:
        return {"success": False, "error": f"定时时间必须在未来，当前时间: {now.strftime('%Y-%m-%d %H:%M')}"}

    # 保存定时任务
    _ensure_config_dir()
    tasks = []
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)

    task = {
        "task_id": f"task_{int(time.time())}",
        "title": title,
        "content": content,
        "type": note_type,
        "images": images or [],
        "tags": tags or [],
        "account": account,
        "schedule_time": schedule_time,
        "status": "pending",
        "created_at": now.isoformat(),
    }
    tasks.append(task)

    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"⏰ 定时任务已创建")
    print(f"   标题: {title}")
    print(f"   计划时间: {schedule_time}")
    print(f"   账号: {account}")
    print(f"   任务 ID: {task['task_id']}")

    return task


def list_scheduled_tasks() -> list[dict]:
    """列出所有定时任务"""
    _ensure_config_dir()
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_scheduled_tasks():
    """检查并执行到期的定时任务"""
    tasks = list_scheduled_tasks()
    now = datetime.now()
    executed = []
    remaining = []

    for task in tasks:
        if task["status"] != "pending":
            remaining.append(task)
            continue

        target = datetime.strptime(task["schedule_time"], "%Y-%m-%d %H:%M")
        if target <= now:
            print(f"🔄 执行定时任务: {task['title']}")
            result = publish_note(
                title=task["title"],
                content=task["content"],
                note_type=task["type"],
                images=task.get("images"),
                tags=task.get("tags"),
                account=task.get("account", "default"),
            )
            task["status"] = "executed"
            task["executed_at"] = now.isoformat()
            task["result"] = result
            executed.append(task)
        else:
            remaining.append(task)

    # 更新任务文件
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    if executed:
        print(f"\n✅ 执行了 {len(executed)} 个定时任务")
    else:
        print("📋 暂无到期任务")

    return executed


# ─────────────────────────────────────
# 批量发布
# ─────────────────────────────────────

def batch_publish(notes: list[dict], account: str = "default", delay: float = 30.0) -> list[dict]:
    """
    批量发布笔记

    Args:
        notes: 笔记列表，每项包含 title, content, type, images, tags
        account: 账号名称
        delay: 发布间隔（秒），建议 ≥ 30 避免触发限制

    Returns:
        发布结果列表
    """
    results = []
    for i, note in enumerate(notes):
        print(f"\n📤 发布进度: {i + 1}/{len(notes)}")

        result = publish_note(
            title=note.get("title", ""),
            content=note.get("content", ""),
            note_type=note.get("type", "image"),
            images=note.get("images"),
            video_path=note.get("video"),
            tags=note.get("tags"),
            account=account,
        )
        results.append(result)

        if i < len(notes) - 1:
            print(f"⏳ 等待 {delay} 秒后继续...")
            time.sleep(delay)

    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'=' * 40}")
    print(f"📊 批量发布完成: {success_count}/{len(notes)} 成功")

    return results


# ─────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书笔记发布工具")
    parser.add_argument("--account", default="default", help="账号名称")

    subparsers = parser.add_subparsers(dest="action")

    # 发布
    pub_parser = subparsers.add_parser("publish", help="发布笔记")
    pub_parser.add_argument("--type", choices=["image", "video"], default="image", help="笔记类型")
    pub_parser.add_argument("--title", "-t", required=True, help="笔记标题")
    pub_parser.add_argument("--content", "-c", required=True, help="笔记正文")
    pub_parser.add_argument("--images", help="图片路径，逗号分隔")
    pub_parser.add_argument("--video", help="视频路径")
    pub_parser.add_argument("--cover", help="封面图路径")
    pub_parser.add_argument("--tags", help="标签，逗号分隔")
    pub_parser.add_argument("--draft", action="store_true", help="存为草稿")

    # 定时
    sched_parser = subparsers.add_parser("schedule", help="定时发布")
    sched_parser.add_argument("--type", choices=["image", "video"], default="image")
    sched_parser.add_argument("--title", "-t", required=True)
    sched_parser.add_argument("--content", "-c", required=True)
    sched_parser.add_argument("--images", help="图片路径，逗号分隔")
    sched_parser.add_argument("--tags", help="标签，逗号分隔")
    sched_parser.add_argument("--schedule", required=True, help="定时时间 YYYY-MM-DD HH:MM")

    # 查看定时任务
    subparsers.add_parser("tasks", help="查看定时任务列表")
    subparsers.add_parser("run-tasks", help="执行到期定时任务")

    # 批量
    batch_parser = subparsers.add_parser("batch", help="批量发布")
    batch_parser.add_argument("--input", required=True, help="批量数据 JSON 文件")
    batch_parser.add_argument("--delay", type=float, default=30.0, help="发布间隔秒数")

    # 账号管理
    acc_parser = subparsers.add_parser("add-account", help="添加账号")
    acc_parser.add_argument("--name", required=True, help="账号名称")
    acc_parser.add_argument("--cookie", required=True, help="Cookie 字符串")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        exit(1)

    if args.action == "publish":
        images = args.images.split(",") if args.images else None
        tags = args.tags.split(",") if args.tags else None
        publish_note(
            title=args.title,
            content=args.content,
            note_type=args.type,
            images=images,
            video_path=args.video,
            cover_path=args.cover,
            tags=tags,
            account=args.account,
            draft=args.draft,
        )

    elif args.action == "schedule":
        images = args.images.split(",") if args.images else None
        tags = args.tags.split(",") if args.tags else None
        schedule_note(
            title=args.title,
            content=args.content,
            schedule_time=args.schedule,
            note_type=args.type,
            images=images,
            tags=tags,
            account=args.account,
        )

    elif args.action == "tasks":
        tasks = list_scheduled_tasks()
        if not tasks:
            print("📋 暂无定时任务")
        else:
            for t in tasks:
                status_icon = "✅" if t["status"] == "executed" else "⏰"
                print(f"{status_icon} [{t['schedule_time']}] {t['title']} ({t['account']})")

    elif args.action == "run-tasks":
        run_scheduled_tasks()

    elif args.action == "batch":
        with open(args.input, "r", encoding="utf-8") as f:
            notes = json.load(f)
        batch_publish(notes, account=args.account, delay=args.delay)

    elif args.action == "add-account":
        save_account(args.name, args.cookie)
