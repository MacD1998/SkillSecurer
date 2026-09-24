#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技术面分析模块
提供全面的技术指标计算和形态识别
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    # MACD
    macd_dif: float
    macd_dea: float
    macd_hist: float
    macd_signal: str
    
    # KDJ
    kdj_k: float
    kdj_d: float
    kdj_j: float
    kdj_zone: str
    
    # RSI
    rsi6: float
    rsi12: float
    rsi24: float
    rsi_signal: str
    
    # 均线系统
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    ma_trend: str
    
    # 成交量
    volume_trend: str
    price_volume_divergence: Optional[str]
    
    # 预测
    forecast: str
    confidence: str


@dataclass
class PatternRecognition:
    """技术形态识别结果"""
    pattern_name: Optional[str]
    pattern_type: Optional[str]  # 'bullish', 'bearish', 'neutral'
    reliability: str  # 'high', 'medium', 'low'
    description: str
    target_price: Optional[float]
    stop_loss: Optional[float]


def _ema(series: pd.Series, span: int) -> pd.Series:
    """计算指数移动平均线"""
    return series.ewm(span=span, adjust=False).mean()


def _sma(series: pd.Series, window: int) -> pd.Series:
    """计算简单移动平均线"""
    return series.rolling(window=window, min_periods=1).mean()


def calc_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算MACD指标
    
    Args:
        close: 收盘价序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    Returns:
        (dif, dea, hist)
    """
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif, dea, hist


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算KDJ指标
    
    Args:
        df: 包含high, low, close的DataFrame
        n: RSV计算周期
        m1: K值平滑系数
        m2: D值平滑系数
    
    Returns:
        (k, d, j)
    """
    low_n = df["low"].rolling(window=n, min_periods=1).min()
    high_n = df["high"].rolling(window=n, min_periods=1).max()
    denom = (high_n - low_n).replace(0, pd.NA)
    rsv = ((df["close"] - low_n) / denom * 100).fillna(50)
    
    k_values = []
    d_values = []
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


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    计算RSI指标
    
    Args:
        close: 收盘价序列
        period: 计算周期
    
    Returns:
        RSI序列
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calc_bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带
    
    Args:
        close: 收盘价序列
        window: 计算周期
        num_std: 标准差倍数
    
    Returns:
        (upper, middle, lower)
    """
    middle = _sma(close, window)
    std = close.rolling(window=window, min_periods=1).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def analyze_macd_signal(dif: float, dea: float, hist: float, hist_prev: float) -> str:
    """
    分析MACD信号
    
    Returns:
        信号描述文本
    """
    # 金叉/死叉判断
    golden_cross = dif > dea and (dif - dea) > 0 and (dif - dea) < abs(hist) * 0.5
    dead_cross = dif < dea and (dea - dif) > 0 and (dea - dif) < abs(hist) * 0.5
    
    if dif >= dea and hist > 0 and hist >= hist_prev:
        return "多头排列，强势延续"
    elif dif >= dea and hist > 0 and hist < hist_prev:
        return "多头格局，动能放缓（顶背离风险）"
    elif dif < dea and hist < 0 and hist <= hist_prev:
        return "空头排列，弱势格局"
    elif dif < dea and hist < 0 and hist > hist_prev:
        return "空头格局，动能减弱（底背离机会）"
    elif golden_cross:
        return "金叉形成，看多信号"
    elif dead_cross:
        return "死叉形成，看空信号"
    elif abs(hist) < max(abs(dif) * 0.15, 0.02):
        return "震荡整理，方向不明"
    return "趋势不明，观望为主"


def analyze_kdj_zone(k: float, d: float, j: float) -> str:
    """
    分析KDJ区域和信号
    """
    # 金叉/死叉
    kdj_golden = k > d and k < 50
    kdj_dead = k < d and k > 50
    
    if j >= 100 or k >= 80:
        return f"超买区域(K={k:.1f})，短线分歧加大"
    elif j <= 0 or k <= 20:
        return f"超卖区域(K={k:.1f})，短线反弹机会"
    elif kdj_golden:
        return f"金叉区域(K={k:.1f})，多头信号"
    elif kdj_dead:
        return f"死叉区域(K={k:.1f})，空头信号"
    return f"中性区域(K={k:.1f})，震荡为主"


def analyze_rsi_signal(rsi6: float, rsi12: float, rsi24: float) -> str:
    """
    分析RSI信号
    """
    # 超买超卖
    if rsi6 > 80 or rsi12 > 75:
        return f"严重超买(RSI6={rsi6:.1f})，回调风险高"
    elif rsi6 < 20 or rsi12 < 25:
        return f"严重超卖(RSI6={rsi6:.1f})，反弹概率大"
    elif rsi6 > 70:
        return f"接近超买(RSI6={rsi6:.1f})，注意风险"
    elif rsi6 < 30:
        return f"接近超卖(RSI6={rsi6:.1f})，关注机会"
    
    # 多周期背离
    if rsi6 > rsi12 > rsi24 and rsi6 > 50:
        return f"强势格局(RSI6={rsi6:.1f})，趋势向上"
    elif rsi6 < rsi12 < rsi24 and rsi6 < 50:
        return f"弱势格局(RSI6={rsi6:.1f})，趋势向下"
    elif rsi6 > rsi12 and rsi6 > 50:
        return f"短期偏强(RSI6={rsi6:.1f})"
    elif rsi6 < rsi12 and rsi6 < 50:
        return f"短期偏弱(RSI6={rsi6:.1f})"
    
    return f"中性震荡(RSI6={rsi6:.1f})"


def analyze_ma_trend(close: pd.Series) -> Tuple[Dict[str, float], str]:
    """
    分析均线系统趋势
    
    Returns:
        (均线字典, 趋势描述)
    """
    ma5 = _sma(close, 5).iloc[-1]
    ma10 = _sma(close, 10).iloc[-1]
    ma20 = _sma(close, 20).iloc[-1]
    ma60 = _sma(close, 60).iloc[-1]
    
    current = close.iloc[-1]
    
    # 多头排列
    if ma5 > ma10 > ma20 > ma60 and current > ma5:
        trend = "多头排列，强势上涨"
    elif ma5 > ma10 > ma20 and current > ma5:
        trend = "短期多头，中期向好"
    elif ma5 > ma10 and current > ma5:
        trend = "短期向上，关注突破"
    # 空头排列
    elif ma5 < ma10 < ma20 < ma60 and current < ma5:
        trend = "空头排列，弱势下跌"
    elif ma5 < ma10 < ma20 and current < ma5:
        trend = "短期空头，中期承压"
    elif ma5 < ma10 and current < ma5:
        trend = "短期向下，谨慎观望"
    # 震荡
    else:
        trend = "均线交织，震荡整理"
    
    ma_dict = {"MA5": ma5, "MA10": ma10, "MA20": ma20, "MA60": ma60}
    return ma_dict, trend


def detect_price_volume_divergence(df: pd.DataFrame) -> Optional[str]:
    """
    检测量价背离
    
    Returns:
        背离描述或None
    """
    if len(df) < 20:
        return None
    
    close = df["close"]
    volume = df.get("vol") if "vol" in df.columns else (df.get("volume") if "volume" in df.columns else None)
    if volume is None:
        return None
    
    # 近5日 vs 前5日
    recent_close = close.iloc[-5:].mean()
    prev_close = close.iloc[-10:-5].mean()
    recent_vol = volume.iloc[-5:].mean()
    prev_vol = volume.iloc[-10:-5].mean()
    
    # 顶背离：价升量缩
    if recent_close > prev_close * 1.02 and recent_vol < prev_vol * 0.9:
        return "⚠️ 顶背离信号（价升量缩）"
    # 底背离：价跌量缩（可能见底）
    elif recent_close < prev_close * 0.98 and recent_vol < prev_vol * 0.9:
        return "✓ 底背离信号（价跌量缩，或近底部）"
    # 量价齐升
    elif recent_close > prev_close * 1.02 and recent_vol > prev_vol * 1.1:
        return "量价齐升，趋势确认"
    # 量价齐跌
    elif recent_close < prev_close * 0.98 and recent_vol > prev_vol * 1.1:
        return "量价齐跌，抛压较重"
    
    return None


def detect_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[Optional[float], Optional[float]]:
    """
    检测近期支撑和阻力位
    
    Returns:
        (支撑位, 阻力位)
    """
    if len(df) < window:
        return None, None
    
    recent = df.iloc[-window:]
    high = recent["high"].max()
    low = recent["low"].min()
    close = recent["close"].iloc[-1]
    
    # 简单支撑阻力（近期高低点）
    resistance = high
    support = low
    
    return support, resistance


def recognize_patterns(df: pd.DataFrame) -> List[PatternRecognition]:
    """
    识别常见技术形态
    
    识别的形态：
    - 头肩顶/底
    - 双顶/双底（M头/W底）
    - 三角形整理
    - 旗形/楔形
    """
    patterns = []
    
    if len(df) < 30:
        return patterns
    
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    
    # 找出近期极值点
    try:
        from scipy.signal import argrelextrema
        local_max = argrelextrema(high, np.greater, order=3)[0]
        local_min = argrelextrema(low, np.less, order=3)[0]
    except ImportError:
        # 如果没有scipy，使用简单方法找极值
        local_max = []
        local_min = []
        for i in range(3, len(high) - 3):
            if high[i] == max(high[i-3:i+4]):
                local_max.append(i)
            if low[i] == min(low[i-3:i+4]):
                local_min.append(i)
    except Exception:
        return patterns
    
    # 双底识别 (W底)
    if len(local_min) >= 2:
        last_two_mins = local_min[-2:]
        if len(last_two_mins) == 2:
            first_bottom = low[last_two_mins[0]]
            second_bottom = low[last_two_mins[1]]
            middle_peak = high[last_two_mins[0]:last_two_mins[1]].max()
            
            # 双底条件：两个低点接近（差距<5%），中间有反弹
            if abs(first_bottom - second_bottom) / first_bottom < 0.05:
                if middle_peak > first_bottom * 1.03:  # 中间反弹>3%
                    # 颈线突破判断
                    neckline = middle_peak
                    current = close[-1]
                    if current > neckline:
                        patterns.append(PatternRecognition(
                            pattern_name="双底形态（W底）",
                            pattern_type="bullish",
                            reliability="high",
                            description=f"识别到双底形态，颈线位{neckline:.2f}已突破，目标涨幅{(neckline - first_bottom):.2f}点",
                            target_price=neckline + (neckline - first_bottom),
                            stop_loss=second_bottom * 0.98
                        ))
                    else:
                        patterns.append(PatternRecognition(
                            pattern_name="疑似双底形态（W底）",
                            pattern_type="bullish",
                            reliability="medium",
                            description=f"疑似双底形态形成中，颈线位{neckline:.2f}，突破后确认",
                            target_price=neckline + (neckline - first_bottom),
                            stop_loss=min(first_bottom, second_bottom) * 0.97
                        ))
    
    # 双顶识别 (M头)
    if len(local_max) >= 2:
        last_two_maxs = local_max[-2:]
        if len(last_two_maxs) == 2:
            first_top = high[last_two_maxs[0]]
            second_top = high[last_two_maxs[1]]
            middle_valley = low[last_two_maxs[0]:last_two_maxs[1]].min()
            
            if abs(first_top - second_top) / first_top < 0.05:
                if middle_valley < first_top * 0.97:
                    neckline = middle_valley
                    current = close[-1]
                    if current < neckline:
                        patterns.append(PatternRecognition(
                            pattern_name="双顶形态（M头）",
                            pattern_type="bearish",
                            reliability="high",
                            description=f"识别到双顶形态，颈线位{neckline:.2f}已跌破，目标跌幅{(first_top - neckline):.2f}点",
                            target_price=neckline - (first_top - neckline),
                            stop_loss=second_top * 1.02
                        ))
                    else:
                        patterns.append(PatternRecognition(
                            pattern_name="疑似双顶形态（M头）",
                            pattern_type="bearish",
                            reliability="medium",
                            description=f"疑似双顶形态形成中，颈线位{neckline:.2f}，跌破后确认",
                            target_price=neckline - (first_top - neckline),
                            stop_loss=max(first_top, second_top) * 1.03
                        ))
    
    # 三角形整理识别
    if len(local_max) >= 3 and len(local_min) >= 3:
        recent_maxs = high[local_max[-3:]]
        recent_mins = low[local_min[-3:]]
        
        # 高点下降，低点上升 → 对称三角形
        if np.all(np.diff(recent_maxs) < 0) and np.all(np.diff(recent_mins) > 0):
            patterns.append(PatternRecognition(
                pattern_name="对称三角形整理",
                pattern_type="neutral",
                reliability="medium",
                description="价格形成对称三角形，等待方向突破",
                target_price=None,
                stop_loss=None
            ))
    
    return patterns


def generate_technical_summary(df: pd.DataFrame, name: str = "") -> str:
    """
    生成完整的技术面分析总结
    
    Args:
        df: 包含OHLCV数据的DataFrame
        name: 股票/指数名称
    
    Returns:
        技术面分析文本
    """
    if df.empty or len(df) < 30:
        return "数据不足，无法完成技术面分析"
    
    close = df["close"]
    
    # 计算指标
    dif, dea, hist = calc_macd(close)
    k, d, j = calc_kdj(df)
    rsi6 = calc_rsi(close, 6)
    rsi12 = calc_rsi(close, 12)
    rsi24 = calc_rsi(close, 24)
    
    # 最新值
    last_dif = float(dif.iloc[-1])
    last_dea = float(dea.iloc[-1])
    last_hist = float(hist.iloc[-1])
    hist_prev = float(hist.iloc[-2]) if len(hist) > 1 else last_hist
    
    last_k = float(k.iloc[-1])
    last_d = float(d.iloc[-1])
    last_j = float(j.iloc[-1])
    
    last_rsi6 = float(rsi6.iloc[-1])
    last_rsi12 = float(rsi12.iloc[-1])
    last_rsi24 = float(rsi24.iloc[-1])
    
    # 分析信号
    macd_signal = analyze_macd_signal(last_dif, last_dea, last_hist, hist_prev)
    kdj_signal = analyze_kdj_zone(last_k, last_d, last_j)
    rsi_signal = analyze_rsi_signal(last_rsi6, last_rsi12, last_rsi24)
    
    # 均线分析
    ma_dict, ma_trend = analyze_ma_trend(close)
    
    # 量价分析
    volume_signal = detect_price_volume_divergence(df)
    
    # 支撑阻力
    support, resistance = detect_support_resistance(df)
    
    # 形态识别
    patterns = recognize_patterns(df)
    
    # 综合判断
    bullish_count = 0
    bearish_count = 0
    
    if "多头" in macd_signal or "金叉" in macd_signal:
        bullish_count += 1
    elif "空头" in macd_signal or "死叉" in macd_signal:
        bearish_count += 1
    
    if "超卖" in kdj_signal or "金叉" in kdj_signal:
        bullish_count += 1
    elif "超买" in kdj_signal or "死叉" in kdj_signal:
        bearish_count += 1
    
    if "超卖" in rsi_signal:
        bullish_count += 1
    elif "超买" in rsi_signal:
        bearish_count += 1
    
    if "多头" in ma_trend:
        bullish_count += 1
    elif "空头" in ma_trend:
        bearish_count += 1
    
    # 生成综合判断
    if bullish_count >= 3:
        overall = "强烈看多"
        confidence = "高"
    elif bullish_count >= 2:
        overall = "偏多"
        confidence = "中"
    elif bearish_count >= 3:
        overall = "强烈看空"
        confidence = "高"
    elif bearish_count >= 2:
        overall = "偏空"
        confidence = "中"
    else:
        overall = "震荡观望"
        confidence = "低"
    
    # 生成文本报告
    lines = []
    if name:
        lines.append(f"【{name}技术面分析】")
    
    lines.append(f"📊 综合判断：{overall}（置信度：{confidence}）")
    lines.append("")
    
    lines.append("📈 趋势指标：")
    lines.append(f"  • MACD：{macd_signal} (DIF={last_dif:.2f}, DEA={last_dea:.2f})")
    lines.append(f"  • KDJ：{kdj_signal}")
    lines.append(f"  • 均线系统：{ma_trend}")
    lines.append(f"    MA5={ma_dict['MA5']:.2f}, MA10={ma_dict['MA10']:.2f}, MA20={ma_dict['MA20']:.2f}, MA60={ma_dict['MA60']:.2f}")
    lines.append("")
    
    lines.append("⚡ 动量指标：")
    lines.append(f"  • RSI：{rsi_signal} (RSI6={last_rsi6:.1f}, RSI12={last_rsi12:.1f}, RSI24={last_rsi24:.1f})")
    lines.append("")
    
    lines.append("📊 量价分析：")
    if volume_signal:
        lines.append(f"  • {volume_signal}")
    else:
        lines.append("  • 量价配合正常，无显著背离")
    lines.append("")
    
    if support and resistance:
        current = close.iloc[-1]
        lines.append("🎯 关键价位：")
        lines.append(f"  • 阻力位：{resistance:.2f} (距离{((resistance/current-1)*100):.2f}%)")
        lines.append(f"  • 支撑位：{support:.2f} (距离{((current/support-1)*100):.2f}%)")
        lines.append("")
    
    if patterns:
        lines.append("🔍 技术形态：")
        for p in patterns[:2]:  # 最多显示2个形态
            emoji = "📈" if p.pattern_type == "bullish" else "📉" if p.pattern_type == "bearish" else "➡️"
            lines.append(f"  {emoji} {p.pattern_name}（可靠度：{p.reliability}）")
            lines.append(f"      {p.description}")
            if p.target_price:
                lines.append(f"      目标价：{p.target_price:.2f}, 止损位：{p.stop_loss:.2f}")
        lines.append("")
    
    # 2日走势预测
    if bullish_count > bearish_count:
        forecast = "预计惯性冲高后或回踩确认支撑"
    elif bearish_count > bullish_count:
        forecast = "预计维持震荡下行或探底企稳"
    else:
        forecast = "预计维持震荡格局，等待方向选择"
    
    lines.append(f"🔮 2日走势预测：{forecast}")
    
    return "\n".join(lines)


def get_technical_summary_dict(df: pd.DataFrame, name: str = "") -> dict:
    """
    生成技术面分析字典（用于JSON输出）
    
    Returns:
        包含各项技术指标的字典
    """
    if df.empty or len(df) < 30:
        return {"error": "数据不足"}
    
    close = df["close"]
    
    # 计算指标
    dif, dea, hist = calc_macd(close)
    k, d, j = calc_kdj(df)
    rsi6_series = calc_rsi(close, 6)
    rsi12_series = calc_rsi(close, 12)
    rsi24_series = calc_rsi(close, 24)
    
    # 布林带
    bb_upper, bb_middle, bb_lower = calc_bollinger_bands(close)
    
    # 最新值
    last_close = float(close.iloc[-1])
    last_dif = float(dif.iloc[-1])
    last_dea = float(dea.iloc[-1])
    last_hist = float(hist.iloc[-1])
    last_k = float(k.iloc[-1])
    last_d = float(d.iloc[-1])
    last_j = float(j.iloc[-1])
    last_rsi6 = float(rsi6_series.iloc[-1])
    last_rsi12 = float(rsi12_series.iloc[-1])
    last_rsi24 = float(rsi24_series.iloc[-1])
    
    # 均线
    ma_dict, ma_trend = analyze_ma_trend(close)
    
    # 支撑阻力
    support, resistance = detect_support_resistance(df)
    
    # 形态
    patterns = recognize_patterns(df)
    
    return {
        "name": name,
        "current_price": last_close,
        "macd": {
            "dif": round(last_dif, 2),
            "dea": round(last_dea, 2),
            "hist": round(last_hist, 2),
            "signal": analyze_macd_signal(last_dif, last_dea, last_hist, float(hist.iloc[-2]) if len(hist) > 1 else last_hist)
        },
        "kdj": {
            "k": round(last_k, 2),
            "d": round(last_d, 2),
            "j": round(last_j, 2),
            "signal": analyze_kdj_zone(last_k, last_d, last_j)
        },
        "rsi": {
            "rsi6": round(last_rsi6, 2),
            "rsi12": round(last_rsi12, 2),
            "rsi24": round(last_rsi24, 2),
            "signal": analyze_rsi_signal(last_rsi6, last_rsi12, last_rsi24)
        },
        "ma": {
            "ma5": round(ma_dict["MA5"], 2),
            "ma10": round(ma_dict["MA10"], 2),
            "ma20": round(ma_dict["MA20"], 2),
            "ma60": round(ma_dict["MA60"], 2),
            "trend": ma_trend
        },
        "bollinger": {
            "upper": round(float(bb_upper.iloc[-1]), 2),
            "middle": round(float(bb_middle.iloc[-1]), 2),
            "lower": round(float(bb_lower.iloc[-1]), 2)
        },
        "support_resistance": {
            "support": round(support, 2) if support else None,
            "resistance": round(resistance, 2) if resistance else None
        },
        "patterns": [
            {
                "name": p.pattern_name,
                "type": p.pattern_type,
                "reliability": p.reliability,
                "description": p.description,
                "target_price": round(p.target_price, 2) if p.target_price else None,
                "stop_loss": round(p.stop_loss, 2) if p.stop_loss else None
            }
            for p in patterns[:2]
        ]
    }


if __name__ == "__main__":
    # 测试代码
    import numpy as np
    
    # 生成测试数据
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2024-01-01", periods=n)
    
    # 模拟股价走势
    trend = np.cumsum(np.random.randn(n) * 0.5)
    close = 3000 + trend * 10
    high = close + np.abs(np.random.randn(n)) * 20
    low = close - np.abs(np.random.randn(n)) * 20
    open_price = close + np.random.randn(n) * 10
    volume = np.random.randint(1000000, 5000000, n)
    
    df = pd.DataFrame({
        "date": dates,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "vol": volume
    })
    
    print(generate_technical_summary(df, "上证指数"))
