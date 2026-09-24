#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一条命令完成：
1. 抓取市场 snapshot
2. 生成固定格式市场日报（纯文本，无图片）
3. 技术面深度分析
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

import fetch_market_and_stock_groups as fetcher
from technical_analysis import generate_technical_summary, get_technical_summary_dict


INDEX_ORDER = [
    ("sh", "上证指数"),
    ("cyb", "创业板指"),
    ("kcb", "科创板指"),
]

# 风格指数顺序
STYLE_INDEX_ORDER = [
    ("sh000016", "上证50", "超大盘"),
    ("sh000300", "沪深300", "大盘"),
    ("sh000905", "中证500", "中盘"),
    ("sh000852", "中证1000", "小盘"),
    ("sz399376", "小盘成长", "成长风格"),
    ("sh000015", "红利指数", "红利策略"),
]


def _to_frame(rows: Iterable[dict]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows))
    if df.empty:
        return df
    for col in ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _calc_macd(close: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif, dea, hist


def _calc_kdj(df: pd.DataFrame, n: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    low_n = df["low"].rolling(window=n, min_periods=1).min()
    high_n = df["high"].rolling(window=n, min_periods=1).max()
    denom = (high_n - low_n).replace(0, pd.NA)
    rsv = ((df["close"] - low_n) / denom * 100).fillna(50)

    k_values: List[float] = []
    d_values: List[float] = []
    k_prev = 50.0
    d_prev = 50.0
    for value in rsv.tolist():
        k_now = (2.0 / 3.0) * k_prev + (1.0 / 3.0) * float(value)
        d_now = (2.0 / 3.0) * d_prev + (1.0 / 3.0) * k_now
        k_values.append(k_now)
        d_values.append(d_now)
        k_prev = k_now
        d_prev = d_now

    k = pd.Series(k_values, index=df.index)
    d = pd.Series(d_values, index=df.index)
    j = 3 * k - 2 * d
    return k, d, j


def _macd_text(dif: float, dea: float, hist: float, hist_prev: float) -> str:
    if dif >= dea and hist > 0 and hist >= hist_prev:
        return "多头排列，强势延续"
    if dif >= dea and hist > 0:
        return "多头格局，动能放缓"
    if dif < dea and hist < 0 and hist <= hist_prev:
        return "空头排列，弱势格局"
    if abs(hist) < max(abs(dif) * 0.15, 0.02):
        return "震荡整理，方向不明"
    return "空头格局，等待修复"


def _kdj_zone(k_value: float, j_value: float) -> str:
    if k_value >= 80 or j_value >= 100:
        return f"超买区域({k_value:.1f})，短线分歧加大"
    if k_value <= 20 or j_value <= 0:
        return f"超卖区域({k_value:.1f})，短线反弹机会"
    return f"中性区域({k_value:.1f})，震荡为主"


def _forecast_text(dif: float, dea: float, hist: float, k_value: float, j_value: float, pct_chg: float) -> str:
    if dif >= dea and hist > 0 and k_value < 80 and pct_chg > 0:
        return "惯性冲高后或回踩"
    if dif < dea and hist < 0 and k_value <= 30:
        return "维持震荡格局"
    if k_value >= 85 or j_value >= 100:
        return "短线冲高后或震荡回落"
    return "维持震荡格局"


def _format_amount_wanyi(amount_qianyuan: Optional[float]) -> str:
    if amount_qianyuan is None or (isinstance(amount_qianyuan, float) and math.isnan(amount_qianyuan)):
        return "暂无数据"
    value = float(amount_qianyuan) * 1000.0 / 1e12
    return f"{value:.2f} 万亿元"


def _index_lines(snapshot: dict) -> List[str]:
    """
    生成指数分析行（简化版，用于目录）
    详细技术面分析使用 _technical_analysis_lines
    """
    lines: List[str] = []
    market_data = snapshot.get("market_data", {})
    lines.append(f"- 成交额：{_format_amount_wanyi(market_data.get('market_turnover_amount_sum'))}")

    kline_map = market_data.get("index_kline", {})
    for key, label in INDEX_ORDER:
        df = _to_frame(kline_map.get(key, []))
        if df.empty or len(df) < 2:
            lines.append(f"- {label}：暂无数据")
            continue

        close = df["close"]
        dif, dea, hist = _calc_macd(close)
        k, d, j = _calc_kdj(df)

        last_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        pct_chg = ((last_close / prev_close) - 1.0) * 100 if prev_close else 0.0

        hist_prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]
        macd_text = _macd_text(float(dif.iloc[-1]), float(dea.iloc[-1]), float(hist.iloc[-1]), float(hist_prev))
        kdj_text = _kdj_zone(float(k.iloc[-1]), float(j.iloc[-1]))
        forecast = _forecast_text(float(dif.iloc[-1]), float(dea.iloc[-1]), float(hist.iloc[-1]), float(k.iloc[-1]), float(j.iloc[-1]), float(pct_chg))

        lines.append(f"- {label}：{last_close:.2f}（{pct_chg:+.2f}%）")
        lines.append(f"  - MACD：{macd_text}；KDJ：{kdj_text}")
        lines.append(f"  - 【2日走势预测】：{forecast}")

    return lines


def _technical_analysis_lines(snapshot: dict) -> List[str]:
    """
    生成详细的技术面分析报告
    使用 technical_analysis 模块进行全面分析
    """
    lines = []
    market_data = snapshot.get("market_data", {})
    kline_map = market_data.get("index_kline", {})
    
    lines.append("【技术面深度分析】")
    lines.append("")
    
    for key, label in INDEX_ORDER:
        df = _to_frame(kline_map.get(key, []))
        if df.empty or len(df) < 30:
            lines.append(f"### {label}")
            lines.append("数据不足，无法完成技术面分析")
            lines.append("")
            continue
        
        # 使用 technical_analysis 模块生成详细分析
        analysis_text = generate_technical_summary(df, label)
        lines.append(analysis_text)
        lines.append("")
    
    return lines


def _style_index_lines(snapshot: dict) -> List[str]:
    """风格指数输出"""
    lines = []
    market_data = snapshot.get("market_data", {})
    style_klines = market_data.get("style_index_kline", {})
    
    lines.append("【风格指数（120日趋势）】")
    
    for key, name, desc in STYLE_INDEX_ORDER:
        idx_data = style_klines.get(key, {})
        rows = idx_data.get("data", [])
        if not rows:
            lines.append(f"- {name}（{desc}）：暂无数据")
            continue
        
        df = _to_frame(rows)
        if df.empty or len(df) < 2:
            lines.append(f"- {name}（{desc}）：暂无数据")
            continue
        
        close = df["close"]
        last_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        pct_chg = ((last_close / prev_close) - 1.0) * 100 if prev_close else 0.0
        
        # 计算20日涨跌幅
        pct_20d = 0
        if len(close) >= 20:
            close_20d_ago = close.iloc[-20]
            pct_20d = ((last_close / close_20d_ago) - 1.0) * 100 if close_20d_ago else 0
        
        lines.append(f"- {name}（{desc}）：{last_close:.2f}（{pct_chg:+.2f}%，20日{pct_20d:+.2f}%）")
    
    return lines


def _pct_distribution_lines(snapshot: dict) -> List[str]:
    """涨跌幅分布输出"""
    lines = []
    stock_universe = snapshot.get("stock_universe", {})
    distribution = stock_universe.get("pct_distribution", [])
    
    if not distribution:
        return lines
    
    lines.append("【涨跌幅分布】")
    for bucket in distribution:
        label = bucket.get("label", "")
        count = bucket.get("count", 0)
        lines.append(f"- {label}：{count}家")
    
    return lines


def _extract_activity(snapshot: dict) -> Tuple[str, str, str]:
    activity = snapshot.get("market_data", {}).get("market_activity_legu", {}) or {}
    emotion = activity.get("activity")
    up_count = activity.get("up_count")
    down_count = activity.get("down_count")
    limit_up = activity.get("limit_up")
    limit_down = activity.get("limit_down")

    # 处理 emotion 可能是带 % 的字符串
    if emotion not in (None, ""):
        emotion_str = str(emotion).replace('%', '')
        try:
            emotion_text = f"{float(emotion_str):.2f}%"
        except (ValueError, TypeError):
            emotion_text = "暂无数据"
    else:
        emotion_text = "暂无数据"
    
    dist_text = (
        f"涨{int(float(up_count))}家 / 跌{int(float(down_count))}家"
        if up_count not in (None, "") and down_count not in (None, "")
        else "暂无数据"
    )
    limit_text = (
        f"{int(float(limit_up))}家，跌停：{int(float(limit_down))}家"
        if limit_up not in (None, "") and limit_down not in (None, "")
        else "暂无数据"
    )
    return emotion_text, dist_text, limit_text


def _pick_directions(df: pd.DataFrame) -> str:
    if df.empty:
        return "样本不足，方向不明显。"

    candidates = []
    if "industry" in df.columns:
        candidates.extend([x for x in df["industry"].fillna("").astype(str).tolist() if x])
    if "market" in df.columns:
        candidates.extend([x for x in df["market"].fillna("").astype(str).tolist() if x])

    common = [name for name, _ in Counter(candidates).most_common(2)]
    if not common:
        return "行业分布分散，主线不清晰。"
    return "、".join(common)


def _format_three_line_summary(df: pd.DataFrame, positive: bool) -> str:
    if df.empty:
        base = "样本不足，暂无显著特征。"
        return f"1. {base}\n2. {base}\n3. {base}"

    df = df.copy()
    if "pct_chg" in df.columns:
        df["pct_chg"] = pd.to_numeric(df["pct_chg"], errors="coerce")
    directions = _pick_directions(df)
    mean_move = df["pct_chg"].mean() if "pct_chg" in df.columns else float("nan")
    median_move = df["pct_chg"].median() if "pct_chg" in df.columns else float("nan")
    top10_mean = df["pct_chg"].head(10).mean() if "pct_chg" in df.columns else float("nan")

    if positive:
        line1 = f"1. 强势方向集中在{directions}，高弹性风格主导当日赚钱效应。"
        line2 = f"2. 涨幅前100平均涨幅{mean_move:.2f}%，前10均值{top10_mean:.2f}%，强势个股向头部集中。"
        line3 = "3. 情绪温度偏暖但扩散有限，若次日量能不放大，持续性更偏结构性轮动。"
    else:
        line1 = f"1. 弱势方向集中在{directions}，高位回撤与弱景气方向承压明显。"
        line2 = f"2. 跌幅前100平均跌幅{mean_move:.2f}%，中位数{median_move:.2f}%，亏损主要集中在尾部杀跌。"
        line3 = "3. 风险偏好回落但未全面失控，恐慌主要体现在局部板块与高波动个股。"
    return "\n".join([line1[:100], line2[:100], line3[:100]])


def _build_report(snapshot: dict) -> str:
    trade_date = snapshot.get("trade_date", "")
    emotion_text, dist_text, limit_text = _extract_activity(snapshot)

    groups = snapshot.get("groups", {})
    gainers = pd.DataFrame(groups.get("top_100_gainers", []))
    losers = pd.DataFrame(groups.get("top_100_losers", []))

    lines = [f"【{trade_date}】大盘数据", "【今日指数】"]
    lines.extend(_index_lines(snapshot))
    lines.extend(
        [
            "【大盘数据】",
            f"• 情绪指数：{emotion_text}",
            f"• 涨跌分布：{dist_text}",
            f"• 涨停：{limit_text}",
        ]
    )
    
    # 添加涨跌幅分布
    lines.extend(_pct_distribution_lines(snapshot))
    
    # 添加风格指数
    lines.append("")
    lines.extend(_style_index_lines(snapshot))
    
    # 添加技术面深度分析
    lines.append("")
    lines.extend(_technical_analysis_lines(snapshot))
    
    # 添加分组特征
    lines.extend([
        "",
        "【分组特征】",
        "- 涨幅前100：",
        _format_three_line_summary(gainers, positive=True),
        "- 跌幅前100：",
        _format_three_line_summary(losers, positive=False),
    ])
    
    return "\n".join(lines)


def generate(
    date_str: Optional[str],
    lookback_days: int,
    min_list_days: int,
    output_dir: str,
    force_date: bool,
) -> Dict[str, Path]:
    import json
    
    snapshot = fetcher.run(
        date_str=date_str,
        lookback_days=lookback_days,
        min_list_days=min_list_days,
        output_dir=output_dir,
        force_date=force_date,
    )
    
    # 添加技术面分析数据到 snapshot
    market_data = snapshot.get("market_data", {})
    kline_map = market_data.get("index_kline", {})
    
    technical_analysis = {}
    for key, label in INDEX_ORDER:
        df = _to_frame(kline_map.get(key, []))
        if not df.empty and len(df) >= 30:
            technical_analysis[key] = get_technical_summary_dict(df, label)
    
    snapshot["technical_analysis"] = technical_analysis
    
    # 保存更新后的 snapshot
    out_dir = Path(output_dir)
    trade_date = snapshot["trade_date"]
    snapshot_path = out_dir / f"snapshot_{trade_date}.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    
    report_path = out_dir / f"market_report_{trade_date}.md"

    report_text = _build_report(snapshot)
    report_path.write_text(report_text, encoding="utf-8")

    return {
        "snapshot": snapshot_path,
        "report": report_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取市场数据、绘图并生成固定格式日报")
    parser.add_argument("--date", type=str, default=None, help="目标日期，格式 YYYY-MM-DD")
    parser.add_argument("--lookback-days", type=int, default=120, help="指数 K 线输出天数")
    parser.add_argument("--min-list-days", type=int, default=60, help="新股过滤阈值")
    parser.add_argument("--output-dir", type=str, default="datas/output_snapshot", help="输出目录")
    parser.add_argument("--force-date", action="store_true", help="强制按指定日期执行，不回退交易日")
    args = parser.parse_args()

    effective_force_date = args.force_date or bool(args.date)
    outputs = generate(
        date_str=args.date,
        lookback_days=args.lookback_days,
        min_list_days=args.min_list_days,
        output_dir=args.output_dir,
        force_date=effective_force_date,
    )

    print(f"snapshot: {outputs['snapshot']}")
    print(f"report: {outputs['report']}")


if __name__ == "__main__":
    main()
