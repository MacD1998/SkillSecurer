#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立脚本：获取大盘数据 + 全市场股票分组。

功能：
1) 大盘数据
   - 三大指数（上证/创业板/科创板）120天 K 线（Tushare index_daily）
   - 大盘成交额（使用 index_daily.amount；按三大指数当日 amount 求和作为口径）
   - 大盘指标（AKShare stock_market_activity_legu）

2) 全市场股票指标
   - 当日 tushare daily_basic + daily + stock_basic（补全名称）
   - 过滤：去除 ST、退市、北交所、新股
   - 分组：
       top_100_gainers: 涨幅前100
       top_100_losers:  跌幅前100

输出：
- {output_dir}/snapshot_{trade_date}.json
- {output_dir}/top_100_gainers_{trade_date}.csv
- {output_dir}/top_100_losers_{trade_date}.csv
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import akshare as ak
import pandas as pd
import tushare as ts


INDEX_CODES = {
    "sh": "000001.SH",      # 上证指数
    "sz": "399001.SZ",      # 深证成指
    "cyb": "399006.SZ",     # 创业板指
    "kcb": "000688.SH",     # 科创50
}

# 风格指数配置 (代码, 名称, 描述)
STYLE_INDEX_CODES = {
    "sh000016": ("000016.SH", "上证50", "超大盘"),
    "sh000300": ("000300.SH", "沪深300", "大盘"),
    "sh000905": ("000905.SH", "中证500", "中盘"),
    "sh000852": ("000852.SH", "中证1000", "小盘"),
    "sz399376": ("399376.SZ", "小盘成长", "成长风格"),
    "sh000015": ("000015.SH", "红利指数", "红利策略"),
}
TURNOVER_SUM_KEYS = {"sh", "sz"}  # 汇总口径：仅上证 + 深证

INDEX_NAMES = {
    "sh": "上证指数",
    "sz": "深证成指",
    "cyb": "创业板指",
    "kcb": "科创50",
}


def _get_tushare_token() -> str:
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token

    raise RuntimeError("未找到 TUSHARE_TOKEN，请设置环境变量")


def _parse_date(date_str: Optional[str]) -> dt.date:
    if not date_str:
        return dt.date.today()
    return dt.datetime.strptime(date_str, "%Y-%m-%d").date()


def _format_trade_date(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def _to_iso_date(date_yyyymmdd: str) -> str:
    return dt.datetime.strptime(date_yyyymmdd, "%Y%m%d").strftime("%Y-%m-%d")


def _json_default(obj):
    if isinstance(obj, (dt.date, dt.datetime, pd.Timestamp)):
        return obj.isoformat()
    if isinstance(obj, (pd.Int64Dtype,)):
        return int(obj)
    return str(obj)


def _ensure_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _get_prev_open_trade_date(pro, on_or_before: dt.date) -> str:
    end = _format_trade_date(on_or_before)
    start = _format_trade_date(on_or_before - dt.timedelta(days=30))
    cal = pro.trade_cal(exchange="", start_date=start, end_date=end)
    if cal is None or cal.empty:
        raise RuntimeError("trade_cal 返回为空，无法确定交易日")
    cal = cal.copy()
    cal = cal[cal["is_open"] == 1]
    if cal.empty:
        raise RuntimeError("指定日期前无交易日")
    return str(cal.iloc[-1]["cal_date"])


def _get_index_kline_120d(pro, trade_date: str) -> Tuple[Dict[str, List[dict]], List[dict]]:
    end = dt.datetime.strptime(trade_date, "%Y%m%d").date()
    start = end - dt.timedelta(days=220)
    start_str = start.strftime("%Y%m%d")

    kline_map: Dict[str, List[dict]] = {}
    turnover_rows = []

    for key, ts_code in INDEX_CODES.items():
        df = pro.index_daily(
            ts_code=ts_code,
            start_date=start_str,
            end_date=trade_date,
            fields="ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
        )
        if df is None or df.empty:
            kline_map[key] = []
            turnover_rows.append({"index": key, "name": INDEX_NAMES[key], "ts_code": ts_code, "amount": None})
            continue

        df = df.sort_values("trade_date").tail(120).copy()
        df = _ensure_numeric(df, ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"])
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        kline_map[key] = df.to_dict(orient="records")

        last_row = df.iloc[-1] if not df.empty else None
        turnover_rows.append(
            {
                "index": key,
                "name": INDEX_NAMES[key],
                "ts_code": ts_code,
                "amount": None if last_row is None or pd.isna(last_row.get("amount")) else float(last_row["amount"]),
            }
        )

    return kline_map, turnover_rows


def _get_market_activity_legu() -> Dict[str, Optional[float]]:
    # 直接标准化为 key-value；若接口字段变化会做兜底
    out = {
        "up_count": None,
        "down_count": None,
        "limit_up": None,
        "limit_down": None,
        "activity": None,
        "raw": [],
    }

    try:
        df = ak.stock_market_activity_legu()
        if df is None or df.empty:
            return out

        out["raw"] = df.to_dict(orient="records")
        if {"item", "value"}.issubset(df.columns):
            view = df[["item", "value"]].copy()
            view["item"] = view["item"].astype(str)
            item_map = dict(zip(view["item"], view["value"]))

            def _find(keys: List[str]):
                for k, v in item_map.items():
                    if any(x in k for x in keys):
                        return v
                return None

            out["up_count"] = _find(["上涨"])
            out["down_count"] = _find(["下跌"])
            out["limit_up"] = _find(["涨停"])
            out["limit_down"] = _find(["跌停"])
            out["activity"] = _find(["活跃度", "情绪"])
            return out

        # 列名不匹配时只返回 raw
        return out
    except Exception:
        return out


def _get_style_index_klines(pro, trade_date: str, lookback_days: int = 120) -> Dict[str, List[dict]]:
    """获取风格指数 K 线数据"""
    end = dt.datetime.strptime(trade_date, "%Y%m%d").date()
    start = end - dt.timedelta(days=lookback_days * 2)
    start_str = start.strftime("%Y%m%d")
    
    kline_map = {}
    for key, (ts_code, name, desc) in STYLE_INDEX_CODES.items():
        try:
            df = pro.index_daily(
                ts_code=ts_code,
                start_date=start_str,
                end_date=trade_date,
                fields="ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
            )
            if df is None or df.empty:
                kline_map[key] = {"name": name, "desc": desc, "data": []}
                continue
            
            df = df.sort_values("trade_date").tail(lookback_days).copy()
            df = _ensure_numeric(df, ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"])
            df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            kline_map[key] = {
                "name": name,
                "desc": desc,
                "data": df.to_dict(orient="records"),
            }
        except Exception:
            kline_map[key] = {"name": name, "desc": desc, "data": []}
    
    return kline_map


def _build_pct_distribution(df: pd.DataFrame) -> List[dict]:
    """
    构建涨跌幅分布统计
    区间: >20%, 10%~20%, 5%~10%, 3%~5%, 0%~3%, -3%~0%, -5%~-3%, -10%~-5%, <-10%
    """
    if df is None or df.empty or "pct_chg" not in df.columns:
        return []
    
    df = df.copy()
    df["pct_chg"] = pd.to_numeric(df["pct_chg"], errors="coerce")
    df = df.dropna(subset=["pct_chg"])
    
    buckets = [
        (">20%", 20, float('inf'), 20),
        ("10%~20%", 10, 20, 10),
        ("5%~10%", 5, 10, 5),
        ("3%~5%", 3, 5, 3),
        ("0%~3%", 0, 3, 0),
        ("-3%~0%", -3, 0, -3),
        ("-5%~-3%", -5, -3, -5),
        ("-10%~-5%", -10, -5, -10),
        ("<-10%", float('-inf'), -10, -20),
    ]
    
    distribution = []
    for label, low, high, bucket_start in buckets:
        if low == float('-inf'):
            count = len(df[df["pct_chg"] < high])
        elif high == float('inf'):
            count = len(df[df["pct_chg"] >= low])
        else:
            count = len(df[(df["pct_chg"] >= low) & (df["pct_chg"] < high)])
        distribution.append({
            "label": label,
            "count": count,
            "bucket_start": bucket_start,
        })
    
    return distribution


def _build_base_stock_df(
    pro,
    trade_date: str,
    min_list_days: int,
) -> pd.DataFrame:
    # 当日 daily_basic（估值+市值）
    daily_basic = pro.daily_basic(
        trade_date=trade_date,
        fields="ts_code,trade_date,close,total_mv,circ_mv,turnover_rate,turnover_rate_f,volume_ratio,pe,pb,ps,dv_ratio",
    )
    if daily_basic is None or daily_basic.empty:
        raise RuntimeError(f"daily_basic 空数据: {trade_date}")

    # 当日 daily（涨跌幅、成交额）
    daily = pro.daily(
        trade_date=trade_date,
        fields="ts_code,trade_date,open,high,low,close,pct_chg,vol,amount",
    )
    if daily is None or daily.empty:
        raise RuntimeError(f"daily 空数据: {trade_date}")

    # 股票基础信息（名称、上市日）
    stock_basic = pro.stock_basic(
        exchange="",
        list_status="L",
        fields="ts_code,symbol,name,area,industry,market,list_date",
    )
    if stock_basic is None or stock_basic.empty:
        raise RuntimeError("stock_basic 空数据")

    df = daily_basic.merge(daily, on=["ts_code", "trade_date"], how="left", suffixes=("_basic", ""))
    df = df.merge(stock_basic, on="ts_code", how="left")

    df = _ensure_numeric(
        df,
        [
            "close_basic",
            "close",
            "pct_chg",
            "vol",
            "amount",
            "total_mv",
            "circ_mv",
            "turnover_rate",
            "turnover_rate_f",
            "volume_ratio",
            "pe",
            "pb",
            "ps",
            "dv_ratio",
        ],
    )

    # 统一 close 列（优先 daily）
    if "close" in df.columns and "close_basic" in df.columns:
        df["close"] = df["close"].fillna(df["close_basic"])
    elif "close_basic" in df.columns and "close" not in df.columns:
        df["close"] = df["close_basic"]

    # 过滤：ST、退市、北交所、新股
    df["name"] = df["name"].fillna("").astype(str)
    df["market"] = df["market"].fillna("").astype(str)
    df["list_date"] = pd.to_datetime(df["list_date"], format="%Y%m%d", errors="coerce")
    target_dt = dt.datetime.strptime(trade_date, "%Y%m%d")
    list_days = (target_dt - df["list_date"]).dt.days

    is_st = df["name"].str.upper().str.contains("ST", na=False)
    is_delist = df["name"].str.contains("退", na=False)
    is_bj = df["ts_code"].astype(str).str.endswith(".BJ") | df["market"].str.contains("北交", na=False)
    is_new = list_days < int(min_list_days)

    filtered = df[~is_st & ~is_delist & ~is_bj & ~is_new].copy()
    filtered = filtered.dropna(subset=["ts_code", "name", "pct_chg", "amount", "total_mv"])
    return filtered


def _build_groups(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """构建股票分组：涨幅前100、跌幅前100"""
    view = df.copy()
    view = _ensure_numeric(view, ["pct_chg", "amount", "total_mv"])

    # 单位转换（Tushare: amount=千元, total_mv=万元）
    view["amount_yuan"] = view["amount"] * 1000.0
    view["total_mv_yuan"] = view["total_mv"] * 10000.0
    view["amount_yi"] = view["amount_yuan"] / 1e8
    view["total_mv_yi"] = view["total_mv_yuan"] / 1e8

    keep_cols = [
        "ts_code",
        "symbol",
        "name",
        "trade_date",
        "close",
        "pct_chg",
        "amount",
        "amount_yuan",
        "amount_yi",
        "total_mv",
        "total_mv_yuan",
        "total_mv_yi",
        "circ_mv",
        "turnover_rate",
        "turnover_rate_f",
        "volume_ratio",
        "pe",
        "pb",
        "ps",
        "dv_ratio",
        "market",
        "industry",
        "list_date",
    ]
    keep_cols = [c for c in keep_cols if c in view.columns]
    view = view[keep_cols].copy()

    top_100_gainers = view.sort_values("pct_chg", ascending=False).head(100).reset_index(drop=True)
    top_100_losers = view.sort_values("pct_chg", ascending=True).head(100).reset_index(drop=True)

    return {
        "top_100_gainers": top_100_gainers,
        "top_100_losers": top_100_losers,
    }


def _df_to_records(df: pd.DataFrame) -> List[dict]:
    if df is None or df.empty:
        return []
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d")
    return out.to_dict(orient="records")


def _save_outputs(
    out_dir: Path,
    trade_date: str,
    result: dict,
    groups: Dict[str, pd.DataFrame],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    iso_date = _to_iso_date(trade_date)

    json_path = out_dir / f"snapshot_{iso_date}.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")

    for key, df in groups.items():
        csv_path = out_dir / f"{key}_{iso_date}.csv"
        if df is None:
            continue
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")


def run(
    date_str: Optional[str],
    lookback_days: int,
    min_list_days: int,
    output_dir: str,
    force_date: bool = False,
) -> dict:
    token = _get_tushare_token()
    ts.set_token(token)
    pro = ts.pro_api(token)

    input_date = _parse_date(date_str)
    trade_date = _format_trade_date(input_date) if force_date else _get_prev_open_trade_date(pro, input_date)
    iso_trade_date = _to_iso_date(trade_date)

    # 1. 大盘数据
    index_klines, index_turnover_rows = _get_index_kline_120d(pro, trade_date)
    index_turnover_df = pd.DataFrame(index_turnover_rows)
    if not index_turnover_df.empty and {"index", "amount"}.issubset(index_turnover_df.columns):
        turnover_sum_df = index_turnover_df[index_turnover_df["index"].isin(TURNOVER_SUM_KEYS)]
    else:
        turnover_sum_df = index_turnover_df
    market_turnover_amount = pd.to_numeric(turnover_sum_df["amount"], errors="coerce").sum(min_count=1)
    market_turnover_amount = None if pd.isna(market_turnover_amount) else float(market_turnover_amount)

    market_activity = _get_market_activity_legu()

    # 2. 风格指数数据
    style_index_klines = _get_style_index_klines(pro, trade_date, lookback_days)

    # 3. 全市场股票指标 + 分组
    base_df = _build_base_stock_df(pro, trade_date, min_list_days=min_list_days)
    groups = _build_groups(base_df)

    # 4. 涨跌幅分布
    pct_distribution = _build_pct_distribution(base_df)

    # 限制 index kline 输出长度（允许参数覆盖）
    limit_n = max(1, int(lookback_days))
    index_klines = {k: v[-limit_n:] if v else [] for k, v in index_klines.items()}

    result = {
        "trade_date": iso_trade_date,
        "input_date": input_date.strftime("%Y-%m-%d"),
        "force_date": bool(force_date),
        "lookback_days": limit_n,
        "market_data": {
            "index_kline": index_klines,
            "index_turnover_today": _df_to_records(index_turnover_df),
            "market_turnover_amount_sum": market_turnover_amount,
            "market_turnover_unit": "index_daily.amount(千元), 上证+深证求和",
            "market_turnover_sum_scope": ["000001.SH", "399001.SZ"],
            "market_activity_legu": market_activity,
            "style_index_kline": style_index_klines,
        },
        "stock_universe": {
            "total_after_filters": int(len(base_df)),
            "filters": {
                "remove_st": True,
                "remove_delist_name_contains_退": True,
                "remove_bj": True,
                "remove_new_stock_min_list_days": int(min_list_days),
            },
            "daily_basic_plus_daily_fields": _df_to_records(base_df.head(0)),
            "pct_distribution": pct_distribution,
        },
        "groups": {
            "top_100_gainers": _df_to_records(groups["top_100_gainers"]),
            "top_100_losers": _df_to_records(groups["top_100_losers"]),
        },
    }

    _save_outputs(Path(output_dir), trade_date, result, groups)
    return result


def main():
    parser = argparse.ArgumentParser(description="获取大盘与全市场分组数据（独立脚本）")
    parser.add_argument("--date", type=str, default=None, help="目标日期，格式 YYYY-MM-DD，默认今天（自动回退到最近交易日）")
    parser.add_argument("--lookback-days", type=int, default=120, help="指数K线输出天数，默认120")
    parser.add_argument("--min-list-days", type=int, default=60, help="新股过滤阈值：上市天数小于该值视为新股，默认60")
    parser.add_argument("--output-dir", type=str, default="datas/output_snapshot", help="输出目录")
    parser.add_argument("--force-date", action="store_true", help="强制使用 --date 指定日期抓取，不做交易日回退")
    args = parser.parse_args()

    result = run(
        date_str=args.date,
        lookback_days=args.lookback_days,
        min_list_days=args.min_list_days,
        output_dir=args.output_dir,
        force_date=args.force_date,
    )

    print("完成")
    print(f"交易日: {result['trade_date']}")
    print(f"全市场样本数(过滤后): {result['stock_universe']['total_after_filters']}")
    print(f"top_100_gainers: {len(result['groups']['top_100_gainers'])}")
    print(f"top_100_losers: {len(result['groups']['top_100_losers'])}")


if __name__ == "__main__":
    main()
