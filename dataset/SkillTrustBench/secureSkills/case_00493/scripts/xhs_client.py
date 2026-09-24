"""
小红书 API 客户端 — 数据请求基础库

基于小红书 Web/移动端接口封装，提供统一的 API 调用能力。
支持笔记搜索、用户信息、笔记详情、评论数据等核心接口。

使用方式：
    from xhs_client import XHSClient

    client = XHSClient()
    notes = client.search_notes(keyword="美妆教程", limit=20)
"""

import json
import time
import hashlib
import random
import string
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import quote, urlencode


@dataclass
class XHSConfig:
    """小红书客户端配置"""
    base_url: str = "https://edith.xiaohongshu.com"
    api_url: str = "https://www.xiaohongshu.com"
    # 设备指纹参数
    device_id: str = ""
    platform: str = "web"
    # 请求控制
    request_delay: float = 1.5  # 请求间隔（秒），防频率限制
    max_retries: int = 3
    timeout: int = 30
    # Cookie（登录态）
    cookie: str = ""
    # User-Agent
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


@dataclass
class NoteData:
    """笔记数据模型"""
    note_id: str = ""
    title: str = ""
    desc: str = ""
    type: str = "normal"  # normal | video
    author: str = ""
    author_id: str = ""
    avatar: str = ""
    likes: int = 0
    collects: int = 0
    comments: int = 0
    shares: int = 0
    images: list = field(default_factory=list)
    video_url: str = ""
    tags: list = field(default_factory=list)
    publish_time: str = ""
    ip_location: str = ""
    interaction_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "note_id": self.note_id,
            "title": self.title,
            "desc": self.desc,
            "type": self.type,
            "author": self.author,
            "author_id": self.author_id,
            "likes": self.likes,
            "collects": self.collects,
            "comments": self.comments,
            "shares": self.shares,
            "tags": self.tags,
            "publish_time": self.publish_time,
            "ip_location": self.ip_location,
            "interaction_rate": self.interaction_rate,
        }


@dataclass
class UserProfile:
    """用户资料模型"""
    user_id: str = ""
    nickname: str = ""
    avatar: str = ""
    desc: str = ""
    gender: int = 0
    ip_location: str = ""
    fans: int = 0
    follows: int = 0
    interaction: int = 0
    notes_count: int = 0
    tags: list = field(default_factory=list)


class XHSClient:
    """小红书 API 客户端"""

    def __init__(self, config: Optional[XHSConfig] = None):
        self.config = config or XHSConfig()
        self._session = None

    def _get_session(self):
        """获取 HTTP 会话（延迟初始化）"""
        if self._session is None:
            try:
                import requests
            except ImportError:
                raise RuntimeError("请先安装 requests: pip install requests")
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": self.config.user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": self.config.api_url,
                "Referer": f"{self.config.api_url}/",
            })
            if self.config.cookie:
                self._session.headers["Cookie"] = self.config.cookie
        return self._session

    def _generate_xs_sign(self, data: str, xt: str = "") -> str:
        """
        生成 X-s 签名参数（简化版）
        实际项目中需要逆向小红书的签名算法或使用浏览器指纹方案
        """
        timestamp = str(int(time.time() * 1000))
        raw = f"{data}{timestamp}{xt}"
        sign = hashlib.md5(raw.encode()).hexdigest()
        return f"{timestamp},{sign}"

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """统一请求方法，带重试和延迟"""
        session = self._get_session()
        kwargs.setdefault("timeout", self.config.timeout)

        for attempt in range(self.config.max_retries):
            try:
                response = session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    wait = self.config.request_delay * (attempt + 1)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"请求失败（重试 {self.config.max_retries} 次）: {e}")

        return {}

    # ─────────────────────────────────────
    # 搜索接口
    # ─────────────────────────────────────

    def search_notes(
        self,
        keyword: str,
        sort: str = "general",
        limit: int = 20,
        offset: int = 0,
        note_type: str = "",
    ) -> list[NoteData]:
        """
        搜索笔记

        Args:
            keyword: 搜索关键词
            sort: 排序方式 general=综合, popularity=最热, latest=最新
            limit: 每页数量（最大 20）
            offset: 偏移量
            note_type: 笔记类型过滤 normal=图文, video=视频, 空=全部

        Returns:
            NoteData 列表
        """
        params = {
            "keyword": keyword,
            "sort": sort,
            "limit": limit,
            "offset": offset,
            "note_type": note_type,
        }

        # 实际接口地址（需配合签名使用）
        url = f"{self.config.base_url}/api/sns/web/v1/search/notes"
        data = self._request("GET", url, params=params)

        notes = []
        if data.get("success") and data.get("data"):
            for item in data["data"].get("items", []):
                note = self._parse_note(item.get("note_model", {}))
                if note:
                    notes.append(note)

        time.sleep(self.config.request_delay)
        return notes

    def search_users(self, keyword: str, limit: int = 20) -> list[UserProfile]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            limit: 数量

        Returns:
            UserProfile 列表
        """
        params = {"keyword": keyword, "limit": limit}
        url = f"{self.config.base_url}/api/sns/web/v1/search/users"
        data = self._request("GET", url, params=params)

        users = []
        if data.get("success") and data.get("data"):
            for item in data["data"].get("items", []):
                user = self._parse_user(item.get("user", {}))
                if user:
                    users.append(user)

        time.sleep(self.config.request_delay)
        return users

    # ─────────────────────────────────────
    # 笔记接口
    # ─────────────────────────────────────

    def get_note_detail(self, note_id: str) -> Optional[NoteData]:
        """
        获取笔记详情

        Args:
            note_id: 笔记 ID

        Returns:
            NoteData 或 None
        """
        url = f"{self.config.base_url}/api/sns/web/v1/feed"
        params = {"note_id": note_id}
        data = self._request("GET", url, params=params)

        if data.get("success") and data.get("data"):
            items = data["data"].get("items", [])
            if items:
                return self._parse_note(items[0].get("note_model", {}))
        return None

    def get_user_notes(
        self,
        user_id: str,
        limit: int = 30,
        cursor: str = ""
    ) -> list[NoteData]:
        """
        获取用户笔记列表

        Args:
            user_id: 用户 ID
            limit: 数量
            cursor: 分页游标

        Returns:
            NoteData 列表
        """
        params = {
            "user_id": user_id,
            "limit": limit,
            "cursor": cursor,
        }
        url = f"{self.config.base_url}/api/sns/web/v1/user_posted"
        data = self._request("GET", url, params=params)

        notes = []
        if data.get("success") and data.get("data"):
            for item in data["data"].get("notes", []):
                note = self._parse_note(item.get("note_model", {}))
                if note:
                    notes.append(note)

        time.sleep(self.config.request_delay)
        return notes

    # ─────────────────────────────────────
    # 用户接口
    # ─────────────────────────────────────

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        获取用户资料

        Args:
            user_id: 用户 ID

        Returns:
            UserProfile 或 None
        """
        params = {"user_id": user_id}
        url = f"{self.config.base_url}/api/sns/web/v1/user/otherinfo"
        data = self._request("GET", url, params=params)

        if data.get("success") and data.get("data"):
            return self._parse_user(data["data"].get("user", {}))
        return None

    # ─────────────────────────────────────
    # 评论接口
    # ─────────────────────────────────────

    def get_note_comments(
        self,
        note_id: str,
        limit: int = 20,
        cursor: str = ""
    ) -> list[dict]:
        """
        获取笔记评论

        Args:
            note_id: 笔记 ID
            limit: 数量
            cursor: 分页游标

        Returns:
            评论列表
        """
        params = {
            "note_id": note_id,
            "limit": limit,
            "cursor": cursor,
        }
        url = f"{self.config.base_url}/api/sns/web/v2/comment/page"
        data = self._request("GET", url, params=params)

        comments = []
        if data.get("success") and data.get("data"):
            for comment in data["data"].get("comments", []):
                comments.append({
                    "comment_id": comment.get("id", ""),
                    "user_name": comment.get("user_info", {}).get("nickname", ""),
                    "user_id": comment.get("user_info", {}).get("user_id", ""),
                    "content": comment.get("content", ""),
                    "like_count": comment.get("like_count", 0),
                    "sub_comment_count": comment.get("sub_comment_count", 0),
                    "ip_location": comment.get("ip_location", ""),
                    "create_time": comment.get("create_time", ""),
                })

        time.sleep(self.config.request_delay)
        return comments

    def post_comment(self, note_id: str, content: str) -> bool:
        """
        发表评论

        Args:
            note_id: 笔记 ID
            content: 评论内容

        Returns:
            是否成功
        """
        url = f"{self.config.base_url}/api/sns/web/v1/comment/post"
        payload = {"note_id": note_id, "content": content}
        data = self._request("POST", url, json=payload)
        return data.get("success", False)

    # ─────────────────────────────────────
    # 趋势/热搜接口
    # ─────────────────────────────────────

    def get_trending_keywords(self) -> list[dict]:
        """
        获取小红书热搜榜

        Returns:
            热搜关键词列表，每项包含 keyword, hot_level, category
        """
        url = f"{self.config.base_url}/api/sns/web/v1/search/trending"
        data = self._request("GET", url)

        trends = []
        if data.get("success") and data.get("data"):
            for item in data["data"].get("trending_list", []):
                trends.append({
                    "keyword": item.get("keyword", ""),
                    "hot_level": item.get("hot_level", 0),
                    "category": item.get("category", ""),
                })
        return trends

    # ─────────────────────────────────────
    # 数据解析
    # ─────────────────────────────────────

    def _parse_note(self, raw: dict) -> Optional[NoteData]:
        """解析笔记原始数据"""
        if not raw:
            return None
        try:
            interact = raw.get("interact_info", {})
            user = raw.get("user", {})
            likes = int(interact.get("liked_count", "0"))
            collects = int(interact.get("collected_count", "0"))
            comments = int(interact.get("comment_count", "0"))
            shares = int(interact.get("share_count", "0"))
            total = likes + collects + comments + shares

            return NoteData(
                note_id=raw.get("note_id", ""),
                title=raw.get("display_title", ""),
                desc=raw.get("desc", ""),
                type=raw.get("type", "normal"),
                author=user.get("nickname", ""),
                author_id=user.get("user_id", ""),
                avatar=user.get("avatar", ""),
                likes=likes,
                collects=collects,
                comments=comments,
                shares=shares,
                images=[img.get("url_default", "") for img in raw.get("image_list", [])],
                video_url=raw.get("video", {}).get("consumer", {}).get("origin_video_key", ""),
                tags=[t.get("name", "") for t in raw.get("tag_list", [])],
                publish_time=raw.get("time", ""),
                ip_location=raw.get("ip_location", ""),
                interaction_rate=total if total > 0 else 0,
            )
        except Exception:
            return None

    def _parse_user(self, raw: dict) -> Optional[UserProfile]:
        """解析用户原始数据"""
        if not raw:
            return None
        try:
            return UserProfile(
                user_id=raw.get("user_id", ""),
                nickname=raw.get("nickname", ""),
                avatar=raw.get("image", ""),
                desc=raw.get("desc", ""),
                gender=raw.get("gender", 0),
                ip_location=raw.get("ip_location", ""),
                fans=int(raw.get("fans", 0)),
                follows=int(raw.get("follows", 0)),
                interaction=int(raw.get("interaction", 0)),
                notes_count=int(raw.get("notes", 0)),
            )
        except Exception:
            return None


# ─────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书 API 客户端 CLI")
    subparsers = parser.add_subparsers(dest="command")

    # 搜索笔记
    search_parser = subparsers.add_parser("search", help="搜索笔记")
    search_parser.add_argument("--keyword", "-k", required=True, help="搜索关键词")
    search_parser.add_argument("--sort", default="general", choices=["general", "popularity", "latest"])
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--output", "-o", help="输出文件路径（JSON）")

    # 笔记详情
    detail_parser = subparsers.add_parser("detail", help="获取笔记详情")
    detail_parser.add_argument("--note-id", required=True, help="笔记 ID")
    detail_parser.add_argument("--output", "-o", help="输出文件路径")

    # 用户资料
    user_parser = subparsers.add_parser("user", help="获取用户资料")
    user_parser.add_argument("--user-id", required=True, help="用户 ID")
    user_parser.add_argument("--output", "-o", help="输出文件路径")

    # 用户笔记
    notes_parser = subparsers.add_parser("notes", help="获取用户笔记列表")
    notes_parser.add_argument("--user-id", required=True, help="用户 ID")
    notes_parser.add_argument("--limit", type=int, default=30)
    notes_parser.add_argument("--output", "-o", help="输出文件路径（JSON）")

    # 热搜
    trend_parser = subparsers.add_parser("trending", help="获取热搜榜")
    trend_parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    client = XHSClient()

    if args.command == "search":
        notes = client.search_notes(args.keyword, sort=args.sort, limit=args.limit)
        result = [n.to_dict() for n in notes]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

    elif args.command == "detail":
        note = client.get_note_detail(args.note_id)
        if note:
            print(json.dumps(note.to_dict(), ensure_ascii=False, indent=2))
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(note.to_dict(), f, ensure_ascii=False, indent=2)
        else:
            print(f"未找到笔记: {args.note_id}")

    elif args.command == "user":
        user = client.get_user_profile(args.user_id)
        if user:
            print(json.dumps({
                "user_id": user.user_id,
                "nickname": user.nickname,
                "desc": user.desc,
                "fans": user.fans,
                "follows": user.follows,
                "notes_count": user.notes_count,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"未找到用户: {args.user_id}")

    elif args.command == "notes":
        notes = client.get_user_notes(args.user_id, limit=args.limit)
        result = [n.to_dict() for n in notes]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

    elif args.command == "trending":
        trends = client.get_trending_keywords()
        print(json.dumps(trends, ensure_ascii=False, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(trends, f, ensure_ascii=False, indent=2)
