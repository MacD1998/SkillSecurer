"""
API 客户端模块

封装玄关开发者平台 BP 相关 API 调用
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class BPGoal:
    """BP 目标数据结构"""
    id: str
    code: str
    name: str
    type: str  # "personal" | "org"
    measure_standard: Optional[str] = None
    number_anchors: List[str] = None
    key_results: List[Dict] = None
    status: Optional[str] = None


class BPAPIClient:
    """BP API 客户端"""
    
    def __init__(self, base_url: str, app_key: str):
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.headers = {"appKey": app_key}
    
    def _call_api(self, path: str, params: dict = None) -> dict:
        """调用 API"""
        url = f"{self.base_url}{path}"
        response = requests.get(url, params=params, headers=self.headers, timeout=20)

        if response.status_code == 401:
            raise PermissionError(f"API 权限不足: {path}")

        data = response.json()
        if data.get("resultCode") != 1:
            raise Exception(f"API 错误: {data.get('resultMsg')}")

        return data.get("data")
    
    def _normalize_periods(self, raw: Any) -> List[Dict[str, Any]]:
        """将不同返回结构归一化为 period 列表"""
        if raw is None:
            return []

        candidates: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            candidates = [x for x in raw if isinstance(x, dict)]
        elif isinstance(raw, dict):
            for key in ("list", "records", "items", "data", "periods"):
                if isinstance(raw.get(key), list):
                    candidates = [x for x in raw[key] if isinstance(x, dict)]
                    if candidates:
                        break

        normalized: List[Dict[str, Any]] = []
        for item in candidates:
            pid = str(
                item.get("id")
                or item.get("periodId")
                or item.get("value")
                or ""
            ).strip()
            name = str(
                item.get("name")
                or item.get("periodName")
                or item.get("label")
                or item.get("title")
                or ""
            ).strip()
            if not pid:
                continue
            normalized.append(
                {
                    "id": pid,
                    "name": name or pid,
                    "is_current": bool(
                        item.get("isCurrent")
                        or item.get("is_current")
                        or item.get("current")
                        or item.get("default")
                        or item.get("selected")
                        or item.get("status") == 1
                    ),
                }
            )
        return normalized

    def list_periods(self) -> List[Dict[str, Any]]:
        """列出可选 BP 周期（用于前置选择）"""
        api_candidates = [
            ("/bp/period/getAllPeriod", {}),
            ("/bp/period/list", {}),
            ("/bp/period/getList", {}),
            ("/bp/task/v2/getPeriodList", {}),
            ("/bp/task/v2/period/list", {}),
        ]

        for path, params in api_candidates:
            try:
                raw = self._call_api(path, params)
                periods = self._normalize_periods(raw)
                if periods:
                    return periods
            except Exception:
                continue

        # API 未取到时，支持从环境变量兜底
        # 例：BP_PERIOD_OPTIONS_JSON='[{"id":"1994...","name":"2026年度计划BP","is_current":true}]'
        raw_env = os.getenv("BP_PERIOD_OPTIONS_JSON", "").strip()
        if raw_env:
            try:
                periods = self._normalize_periods(json.loads(raw_env))
                if periods:
                    return periods
            except Exception:
                pass

        return []

    def search_groups_by_name(self, period_id: str, keyword: str) -> List[Dict[str, Any]]:
        """按名称模糊搜索组织分组"""
        if not period_id or not keyword:
            return []
        data = self._call_api("/bp/group/searchByName", {"periodId": period_id, "name": keyword})
        return [x for x in (data or []) if isinstance(x, dict)]

    def resolve_org_name(self, user_input: str, period_id: str) -> Optional[str]:
        """从自然语言输入中自动解析组织名（基于 searchByName）。"""
        import re

        if not user_input or not period_id:
            return None

        candidates: List[str] = []
        patterns = [
            r"为\s*([^，。；;\n]+?)\s*(?:生成|做|出|写)",
            r"给\s*([^，。；;\n]+?)\s*(?:生成|做|出|写)",
            r"把\s*([^，。；;\n]+?)\s*(?:生成|做|出|写)",
        ]
        for pattern in patterns:
            m = re.search(pattern, user_input)
            if not m:
                continue
            raw = m.group(1).strip()
            for token in re.split(r"[、,，\s]+", raw):
                token = token.strip()
                if token:
                    candidates.append(token)

        # 补充：提取常见组织后缀
        suffix_hits = re.findall(r"([\u4e00-\u9fffA-Za-z0-9]{1,20}(?:集团|中心|部门|事业部|公司|部))", user_input)
        candidates.extend([x.strip() for x in suffix_hits if x.strip()])

        # 去重并按长度降序优先
        seen = set()
        uniq_candidates: List[str] = []
        for c in sorted(candidates, key=len, reverse=True):
            if c not in seen:
                seen.add(c)
                uniq_candidates.append(c)

        for keyword in uniq_candidates:
            try:
                groups = self.search_groups_by_name(period_id, keyword)
            except Exception:
                continue
            if not groups:
                continue

            # 优先精确匹配，其次取首个候选
            exact = next((g for g in groups if str(g.get("name", "")).strip() == keyword), None)
            chosen = exact or groups[0]
            name = str(chosen.get("name", "")).strip()
            if name:
                return name

        return None

    def get_org_tree(self, period_id: str) -> List[Dict]:
        """API 4.2: 获取组织架构树"""
        return self._call_api("/bp/group/getTree", {"periodId": period_id})
    
    def get_bp_tree(self, group_id: str) -> List[Dict]:
        """API 4.4: 获取 BP 树（简化）"""
        return self._call_api("/bp/task/v2/getSimpleTree", {"groupId": group_id})
    
    def get_goal_detail(self, goal_id: str) -> Dict:
        """API 4.5: 获取目标详情"""
        return self._call_api("/bp/task/v2/getGoalAndKeyResult", {"id": goal_id})
    
    def find_group_id(self, org_tree: List[Dict], org_name: str) -> Optional[str]:
        """在组织树中查找 groupId"""
        for node in org_tree:
            if org_name in node.get("name", ""):
                return node.get("id")
            if node.get("children"):
                result = self.find_group_id(node["children"], org_name)
                if result:
                    return result
        return None

    def _iter_goal_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """递归展开任务树，提取“目标”节点。"""
        goals: List[Dict] = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            if node.get("type") == "目标":
                goals.append(node)
            children = node.get("children") or []
            if children:
                goals.extend(self._iter_goal_nodes(children))
        return goals

    @staticmethod
    def _pick_measure_standard(detail: Dict[str, Any]) -> str:
        """优先取目标衡量标准，缺失时回退到关键成果字段。"""
        if not isinstance(detail, dict):
            return ""
        measure_standard = str(detail.get("measureStandard") or "").strip()
        if measure_standard:
            return measure_standard

        key_results = detail.get("keyResults") or []
        for kr in key_results:
            if not isinstance(kr, dict):
                continue
            for key in ("measureStandard", "name", "targetValue"):
                val = str(kr.get(key) or "").strip()
                if val:
                    return val
        return ""

    def fetch_bp_data(
        self,
        org_name: str,
        person_name: Optional[str] = None,
        period_id: str = None
    ) -> Dict:
        """
        获取完整 BP 数据
        
        返回：
        {
            "org_name": str,
            "person_name": Optional[str],
            "period": str,
            "goals": List[BPGoal]
        }
        """
        if not period_id:
            raise ValueError("period_id 不能为空，请先选择 BP 周期")

        # 1. 获取组织架构
        org_tree = self.get_org_tree(period_id)
        
        # 2. 查找组织 ID
        group_id = self.find_group_id(org_tree, org_name)
        if not group_id:
            raise ValueError(f"未找到组织: {org_name}")
        
        # 3. 获取 BP 树
        bp_tree = self.get_bp_tree(group_id)
        
        # 4. 获取每个目标的详情
        goals = []
        goal_nodes = self._iter_goal_nodes(bp_tree)
        for goal_node in goal_nodes:
            detail = self.get_goal_detail(goal_node["id"])
            measure_standard = self._pick_measure_standard(detail)

            goal = BPGoal(
                id=goal_node["id"],
                code=goal_node.get("levelNumber", ""),
                name=goal_node.get("name", ""),
                type="personal" if goal_node.get("levelNumber", "").startswith("P") else "org",
                measure_standard=measure_standard,
                number_anchors=extract_number_anchors(measure_standard),
                key_results=detail.get("keyResults", []),
                status=goal_node.get("status"),
            )
            goals.append(goal)
        
        return {
            "org_name": org_name,
            "person_name": person_name,
            "period": period_id,
            "goals": goals,
        }


def extract_number_anchors(text: str) -> List[str]:
    """从文本中提取数字锚点"""
    import re
    
    if not text:
        return []
    
    # 匹配模式：≥90%, ≤5%, 100%, 3月31日 等
    patterns = [
        r"[≥<>≤]\s*\d+\.?\d*%?",  # 百分比
        r"\d+月\d+日",              # 日期
        r"\d+个",                   # 数量
    ]
    
    anchors = []
    for pattern in patterns:
        anchors.extend(re.findall(pattern, text))
    
    return anchors


# 使用示例
if __name__ == "__main__":
    app_key = os.getenv("BP_APP_KEY") or os.getenv("COMPANY_APP_KEY")
    if not app_key:
        raise SystemExit("请先设置 BP_APP_KEY 或 COMPANY_APP_KEY")

    client = BPAPIClient(
        base_url="https://sg-al-cwork-web.mediportal.com.cn/open-api",
        app_key=app_key,
    )

    periods = client.list_periods()
    print(f"可用周期: {len(periods)}")
    if periods:
        print(f"示例周期: {periods[0]['id']} {periods[0]['name']}")
