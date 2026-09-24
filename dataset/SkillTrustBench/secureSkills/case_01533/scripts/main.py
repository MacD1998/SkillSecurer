#!/usr/bin/env python3
"""
bp-reporting-templates 主程序入口

流程（更新后）：
1. 解析用户指令（组织名/个人名）
2. 前置选择 BP 周期（period）
3. 前置选择生成类型（月/季/半年/年/组合）
4. 获取 BP 数据（API 主路径；失败可回退文件）
5. 并行生成填写规范并审查输出
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from api_client import BPAPIClient
from filler import fill_template
from input_handler import parse_user_input
from parser import parse_bp_from_file
from reviewer import review_template
from template_manager import TemplateManager
from utils import save_output, setup_logging

TEMPLATE_OPTIONS = ["月报", "季报", "半年报", "年报"]

# 配置（敏感信息走环境变量）
CONFIG = {
    "base_url": "https://sg-al-cwork-web.mediportal.com.cn/open-api",
    "output_dir": "./output",
}


def parse_template_types_arg(raw: Optional[str]) -> List[str]:
    if not raw:
        return []

    text = raw.strip()
    if not text:
        return []

    if text in {"四套", "全部", "all"}:
        return TEMPLATE_OPTIONS.copy()

    parts = [p.strip() for p in text.replace("+", ",").replace("、", ",").split(",")]
    selected: List[str] = []
    for p in parts:
        if not p:
            continue
        if p in TEMPLATE_OPTIONS and p not in selected:
            selected.append(p)
    return selected


def format_template_menu() -> str:
    lines = ["请选择生成类型："]
    for idx, name in enumerate(TEMPLATE_OPTIONS, start=1):
        lines.append(f"  {idx}) {name}")
    lines.append("  5) 四套")
    lines.append("示例输入：1,4 或 5")
    return "\n".join(lines)


def select_template_types_interactive() -> List[str]:
    print(format_template_menu())
    choice = input("请输入选项编号: ").strip()
    if choice == "5":
        return TEMPLATE_OPTIONS.copy()

    selected: List[str] = []
    for token in choice.replace("，", ",").split(","):
        token = token.strip()
        if not token.isdigit():
            continue
        i = int(token)
        if 1 <= i <= 4:
            t = TEMPLATE_OPTIONS[i - 1]
            if t not in selected:
                selected.append(t)
    return selected


def format_period_menu(periods: List[Dict]) -> str:
    lines = ["请选择 BP 周期："]
    for idx, p in enumerate(periods, start=1):
        current_tag = " (当前)" if p.get("is_current") else ""
        lines.append(f"  {idx}) {p.get('name', p['id'])} [{p['id']}]" + current_tag)
    lines.append("可输入编号（如 1）或直接输入 period_id")
    return "\n".join(lines)


def select_period_interactive(periods: List[Dict]) -> str:
    print(format_period_menu(periods))
    choice = input("请输入周期编号或period_id: ").strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(periods):
            return str(periods[idx - 1]["id"])

    for p in periods:
        if choice == str(p.get("id")):
            return str(p["id"])

    raise ValueError("无效周期选择")


def resolve_app_key(cli_app_key: Optional[str]) -> str:
    return (cli_app_key or os.getenv("BP_APP_KEY") or os.getenv("COMPANY_APP_KEY") or "").strip()


def require_selection_error(title: str, menu: str) -> ValueError:
    return ValueError(f"{title}\n{menu}")


def ensure_mapping(bp_data) -> Dict:
    """兼容 parser 返回 dataclass / dict 两种结构。"""
    if isinstance(bp_data, dict):
        return bp_data
    if hasattr(bp_data, "__dict__"):
        return dict(bp_data.__dict__)
    raise TypeError(f"不支持的 bp_data 类型: {type(bp_data)}")


async def generate_single_template(bp_data: dict, template_type: str, template_manager: TemplateManager) -> dict:
    template = template_manager.load_template(template_type)
    filled_content = fill_template(template, bp_data, template_type)
    review_result = review_template(filled_content, bp_data)
    return {"template_type": template_type, "content": filled_content, "review": review_result}


async def generate_templates(
    user_input: str,
    bp_file: Optional[str],
    period_id: Optional[str],
    template_types_override: List[str],
    interactive_select: bool,
    app_key: str,
    org_name_override: Optional[str] = None,
    person_name_override: Optional[str] = None,
) -> List[dict]:
    parsed = parse_user_input(user_input, default_all=False)
    org_name = org_name_override or parsed["org_name"]
    person_name = person_name_override or parsed.get("person_name")

    template_types = template_types_override or parsed.get("template_types", [])
    if not template_types:
        if interactive_select:
            template_types = select_template_types_interactive()
        if not template_types:
            raise require_selection_error("未指定生成类型，需先选择月/季/半年/年", format_template_menu())

    if bp_file:
        print(f"\n📄 从文件读取 BP: {bp_file}")
        bp_data = ensure_mapping(parse_bp_from_file(bp_file))
        org_name = org_name or bp_data.get("org_name")
        person_name = person_name or bp_data.get("person_name")
    else:
        if not app_key:
            raise ValueError("缺少 app_key，请通过 --app-key 或环境变量 BP_APP_KEY/COMPANY_APP_KEY 提供")

        api_client = BPAPIClient(CONFIG["base_url"], app_key)

        if not period_id:
            periods = api_client.list_periods()
            if not periods:
                raise ValueError("未获取到周期列表，请先指定 --period-id（或配置 BP_PERIOD_OPTIONS_JSON）")
            if interactive_select:
                period_id = select_period_interactive(periods)
            else:
                # 非交互模式：若唯一或有当前周期则自动选，否则要求用户选择
                if len(periods) == 1:
                    period_id = str(periods[0]["id"])
                else:
                    current = next((p for p in periods if p.get("is_current")), None)
                    if current:
                        period_id = str(current["id"])
                    else:
                        raise require_selection_error("检测到多个可用周期，请先选择周期", format_period_menu(periods))

        if not org_name:
            org_name = api_client.resolve_org_name(user_input, period_id)
            if org_name:
                print(f"   ℹ️ 自动识别组织: {org_name}")

        if not org_name:
            raise ValueError("未识别组织名，请在输入中包含组织名（如：为产品中心生成季报）或通过 --org-name 指定")

        print(f"\n🔗 从 API 获取 BP... period_id={period_id}")
        bp_data = api_client.fetch_bp_data(org_name, person_name, period_id)

    print("📋 解析结果:")
    print(f"   组织: {org_name or '未识别'}")
    print(f"   个人: {person_name or '未指定'}")
    print(f"   生成: {', '.join(template_types)}")
    print(f"   获取到 {len(bp_data.get('goals', []))} 个目标")

    template_manager = TemplateManager()
    print(f"\n⚙️ 并行生成 {len(template_types)} 套填写规范...")
    tasks = [generate_single_template(bp_data, t_type, template_manager) for t_type in template_types]
    results = await asyncio.gather(*tasks)

    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    file_org_name = org_name or "未识别组织"
    for result in results:
        base_name = f"{file_org_name}_{person_name or '组织'}_{result['template_type']}填写规范"
        if result["review"]["passed"]:
            filename = f"{base_name}.md"
            filepath = output_dir / filename
            save_output(filepath, result["content"])
            print(f"   ✅ {filename}")
        else:
            draft_name = f"{base_name}_DRAFT_审查未通过.md"
            draft_path = output_dir / draft_name
            save_output(draft_path, result["content"])

            review_name = f"{base_name}_REVIEW.json"
            review_path = output_dir / review_name
            save_output(review_path, json.dumps(result["review"], ensure_ascii=False, indent=2))

            print(f"   ⚠️ {result['template_type']} 审查未通过（已输出草稿+审查报告）:")
            print(f"      - 草稿: {draft_name}")
            print(f"      - 审查: {review_name}")
            for issue in result["review"]["issues"][:10]:
                print(f"      - {issue['type']}: {issue['detail']}")
            if len(result["review"]["issues"]) > 10:
                print(f"      - ... 共 {len(result['review']['issues'])} 项")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="BP 填写规范生成器")
    parser.add_argument("input", nargs="?", help="用户输入，如 '为产品中心生成四套'")
    parser.add_argument("--bp-file", help="BP 文件路径（可选，不指定则从 API 获取）")
    parser.add_argument("--output", default="./output", help="输出目录")
    parser.add_argument("--period-id", help="指定 BP 周期 ID")
    parser.add_argument("--template-types", help="模板类型：月报,季报,半年报,年报 或 四套")
    parser.add_argument("--org-name", help="手动指定组织名（覆盖输入解析）")
    parser.add_argument("--person-name", help="手动指定个人名（覆盖输入解析）")
    parser.add_argument("--app-key", help="API appKey（优先级高于环境变量）")
    parser.add_argument("--interactive-select", action="store_true", help="缺失选择时启用命令行交互选择")
    parser.add_argument("--list-template-types", action="store_true", help="仅输出模板类型选项")
    parser.add_argument("--list-periods", action="store_true", help="仅输出周期列表（需 app_key）")

    args = parser.parse_args()
    CONFIG["output_dir"] = args.output

    setup_logging()

    app_key = resolve_app_key(args.app_key)

    if args.list_template_types:
        print(json.dumps({"templateTypes": TEMPLATE_OPTIONS}, ensure_ascii=False, indent=2))
        return

    if args.list_periods:
        if not app_key:
            raise SystemExit("缺少 app_key，请通过 --app-key 或 BP_APP_KEY/COMPANY_APP_KEY 提供")
        api_client = BPAPIClient(CONFIG["base_url"], app_key)
        periods = api_client.list_periods()
        print(json.dumps({"periods": periods}, ensure_ascii=False, indent=2))
        return

    if not args.input:
        raise SystemExit("缺少输入。示例: python main.py '为产品中心生成季报' --period-id <id> --template-types 季报")

    template_types_override = parse_template_types_arg(args.template_types)

    asyncio.run(
        generate_templates(
            user_input=args.input,
            bp_file=args.bp_file,
            period_id=args.period_id,
            template_types_override=template_types_override,
            interactive_select=args.interactive_select,
            app_key=app_key,
            org_name_override=args.org_name,
            person_name_override=args.person_name,
        )
    )


if __name__ == "__main__":
    main()
