#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据 snapshot JSON 绘制三指数 120 日 K 线图。

输出文件默认命名为:
- index_kline_{trade_date}.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


PLOT_INDEXES = [
    ("sh", "上证指数"),
    ("cyb", "创业板指"),
    ("kcb", "科创板指"),
]

FONT_CANDIDATES = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
]


def _load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_kline(rows: Iterable[dict]) -> List[dict]:
    out = []
    for row in rows:
        trade_date = row.get("trade_date")
        open_price = row.get("open")
        high_price = row.get("high")
        low_price = row.get("low")
        close_price = row.get("close")
        if None in (trade_date, open_price, high_price, low_price, close_price):
            continue
        out.append(
            {
                "trade_date": mdates.datestr2num(str(trade_date)),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
            }
        )
    return out


def _draw_candles(ax, rows: List[dict], title: str) -> None:
    if not rows:
        ax.text(0.5, 0.5, "无数据", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        ax.axis("off")
        return

    width = 0.6
    up_color = "#d84a4a"
    down_color = "#2a9d5b"

    for row in rows:
        color = up_color if row["close"] >= row["open"] else down_color
        ax.vlines(row["trade_date"], row["low"], row["high"], color=color, linewidth=1.0, alpha=0.9)

        body_bottom = min(row["open"], row["close"])
        body_height = abs(row["close"] - row["open"])
        if body_height == 0:
            body_height = max(row["close"] * 0.0005, 0.01)

        rect = Rectangle(
            (row["trade_date"] - width / 2.0, body_bottom),
            width,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.8,
        )
        ax.add_patch(rect)

    closes = [row["close"] for row in rows]
    last_close = closes[-1]
    prev_close = closes[-2] if len(closes) > 1 else closes[-1]
    pct_chg = ((last_close / prev_close) - 1.0) * 100 if prev_close else 0.0

    ax.set_title(f"{title}  {last_close:.2f} ({pct_chg:+.2f}%)", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.18)
    ax.set_xlim(rows[0]["trade_date"] - 2, rows[-1]["trade_date"] + 2)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.tick_params(axis="x", labelrotation=0, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)


def render(snapshot_path: Path, output_path: Path) -> Path:
    data = _load_snapshot(snapshot_path)
    trade_date = data.get("trade_date", "")
    kline_map: Dict[str, List[dict]] = data.get("market_data", {}).get("index_kline", {})

    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.2), constrained_layout=True)
    fig.suptitle(f"今日指数日K线  {trade_date}", fontsize=16, fontweight="bold")

    for ax, (key, label) in zip(axes, PLOT_INDEXES):
        rows = _coerce_kline(kline_map.get(key, []))
        _draw_candles(ax, rows, label)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 snapshot JSON 绘制今日指数日K线图")
    parser.add_argument("--snapshot", required=True, help="snapshot JSON 文件路径")
    parser.add_argument("--output", default=None, help="输出 PNG 路径")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        raise FileNotFoundError(f"snapshot 不存在: {snapshot_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        trade_date = _load_snapshot(snapshot_path).get("trade_date", "unknown")
        output_path = snapshot_path.parent / f"index_kline_{trade_date}.png"

    saved = render(snapshot_path, output_path)
    print(str(saved))


if __name__ == "__main__":
    main()
