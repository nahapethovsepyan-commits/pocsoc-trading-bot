"""
Technical indicator calculator with parallel execution.
"""

import asyncio
import logging
import pandas as pd
import ta
from datetime import datetime
from typing import Dict, Any, Optional
from ..config import CONFIG
from ..utils.helpers import safe_divide
from ..models.state import INDICATOR_CACHE, indicator_cache_lock


def calculate_ta_score(rsi: float, macd_diff: float, bb_position: float, 
                       adx: float = 20.0, stoch_k: float = 50.0, stoch_d: float = 50.0,
                       price_change: float = 0.0, trend_direction: str = "RANGING") -> float:
    """
    Calculate technical analysis score (0-100) for binary options.
    FIXED: Requires trend alignment, momentum, and multiple confirmations.
    
    Args:
        rsi: RSI indicator value
        macd_diff: MACD difference value
        bb_position: Bollinger Bands position (0-100%)
        adx: ADX trend strength
        stoch_k: Stochastic K value
        stoch_d: Stochastic D value
        price_change: Price change percentage
        trend_direction: Trend direction (UPTREND/DOWNTREND/RANGING)
        
    Returns:
        TA score (0-100), where >50 is bullish, <50 is bearish
    """
    ta_score = 50  # Start neutral
    
    # CRITICAL FIX #1: Check trend direction first
    # For binary options, we MUST trade WITH the trend in strong trends
    if trend_direction == "DOWNTREND" and adx > CONFIG.get("adx_trend_threshold", 25):
        # Strong downtrend - bias score bearish but don’t immediately discard setups
        ta_score = 45  # start with bearish lean
        if rsi < 55:
            ta_score -= 3
        if macd_diff < -CONFIG.get("macd_strong_threshold", 0.0002) / 2:
            ta_score -= 5
        if price_change < 0:
            ta_score -= 4
        if stoch_k > stoch_d:
            ta_score -= 2
        if bb_position > 60:
            ta_score -= 2
        return max(0, min(100, ta_score))
    
    if trend_direction == "UPTREND" and adx > CONFIG.get("adx_trend_threshold", 25):
        # Strong uptrend - bias score bullish but keep flexibility
        ta_score = 55  # start with bullish lean
        if rsi > 45:
            ta_score += 3
        if macd_diff > CONFIG.get("macd_strong_threshold", 0.0002) / 2:
            ta_score += 5
        if price_change > 0:
            ta_score += 4
        if stoch_k < stoch_d:
            ta_score += 2
        if bb_position < 40:
            ta_score += 2
        return max(0, min(100, ta_score))
    
    # For ranging/weak trend - need STRONG confirmations (4+ indicators)
    # FIXED: Use stronger thresholds for binary options (from CONFIG)
    rsi_very_oversold = CONFIG.get("rsi_oversold", 40)
    rsi_very_overbought = CONFIG.get("rsi_overbought", 60)
    macd_strong_threshold = CONFIG.get("macd_strong_threshold", 0.0001)
    
    buy_confirmations = 0
    sell_confirmations = 0
    
    # BUY signals require multiple strong confirmations
    if rsi < rsi_very_oversold:  # Very oversold (not just 40)
        buy_confirmations += 1
    if macd_diff > macd_strong_threshold:  # Strong positive MACD
        buy_confirmations += 1
    if bb_position < 25:  # Very oversold on BB (not just 30)
        buy_confirmations += 1
    if stoch_k < 25 and stoch_k < stoch_d:  # Strong oversold
        buy_confirmations += 1
    if price_change > 0:  # Price moving up (momentum confirmation)
        buy_confirmations += 1
    if adx > 25:  # Strong trend
        buy_confirmations += 1
    
    # SELL signals require multiple strong confirmations
    if rsi > rsi_very_overbought:  # Very overbought (not just 60)
        sell_confirmations += 1
    if macd_diff < -macd_strong_threshold:  # Strong negative MACD
        sell_confirmations += 1
    if bb_position > 75:  # Very overbought on BB (not just 70)
        sell_confirmations += 1
    if stoch_k > 75 and stoch_k > stoch_d:  # Strong overbought
        sell_confirmations += 1
    if price_change < 0:  # Price moving down (momentum confirmation)
        sell_confirmations += 1
    if adx > 25:  # Strong trend
        sell_confirmations += 1
    
    # Score based on confirmations (allow strong bias at >=3)
    # Momentum alignment adds bonus rather than invalidating signal outright
    if buy_confirmations >= 3:
        ta_score = 65  # Strong BUY bias
        if price_change <= 0:
            ta_score -= 7  # Slight penalty when momentum lags
    elif buy_confirmations == 2:
        ta_score = 58  # Moderate BUY bias
        if price_change <= 0:
            ta_score -= 5
    elif sell_confirmations >= 3:
        ta_score = 35  # Strong SELL bias
        if price_change >= 0:
            ta_score += 7
    elif sell_confirmations == 2:
        ta_score = 42  # Moderate SELL bias
        if price_change >= 0:
            ta_score += 5
    else:
        ta_score = 50  # Not enough confirmations

    # SECONDARY: Stochastic Oscillator (20% weight)
    if stoch_k < CONFIG["stoch_strong_oversold"] and stoch_k < stoch_d:
        ta_score += 8
    elif stoch_k < CONFIG["stoch_oversold"]:
        ta_score += 4
    elif stoch_k > CONFIG["stoch_strong_overbought"] and stoch_k > stoch_d:
        ta_score -= 8
    elif stoch_k > CONFIG["stoch_overbought"]:
        ta_score -= 4

    # TREND STRENGTH: ADX (20% weight)
    if adx > CONFIG["adx_trend_threshold"]:
        if ta_score > 50:
            ta_score += 5
        elif ta_score < 50:
            ta_score -= 5

    # VOLATILITY: Bollinger Bands (20% weight)
    if bb_position < CONFIG["bb_strong_oversold"]:
        ta_score += 7
    elif bb_position < CONFIG["bb_oversold"]:
        ta_score += 3
    elif bb_position > CONFIG["bb_strong_overbought"]:
        ta_score -= 7
    elif bb_position > CONFIG["bb_overbought"]:
        ta_score -= 3

    return max(0, min(100, ta_score))


def detect_trend_direction(macd_diff: float, rsi: float, adx: float, 
                          price_change: float = 0.0) -> Dict[str, Any]:
    """
    Detect market trend direction for binary options trading.
    
    Args:
        macd_diff: MACD difference value
        rsi: RSI indicator value
        adx: ADX trend strength
        price_change: Price change percentage (optional)
        
    Returns:
        Dictionary with trend direction and strength
    """
    trend_strength = 0
    trend_direction = "RANGING"
    
    # Strong trend requires ADX > 25
    if adx > CONFIG["adx_trend_threshold"]:
        # Uptrend: Positive MACD + RSI not oversold + price rising
        if macd_diff > 0.0001 and rsi > 40 and (price_change > 0 or price_change == 0):
            trend_direction = "UPTREND"
            if macd_diff > 0.0003 and rsi > 50:
                trend_strength = 80  # Very strong uptrend
            elif macd_diff > 0.0002:
                trend_strength = 65  # Strong uptrend
            else:
                trend_strength = 55  # Moderate uptrend
        
        # Downtrend: Negative MACD + RSI not overbought + price falling
        elif macd_diff < -0.0001 and rsi < 60 and (price_change < 0 or price_change == 0):
            trend_direction = "DOWNTREND"
            if macd_diff < -0.0003 and rsi < 50:
                trend_strength = 20  # Very strong downtrend
            elif macd_diff < -0.0002:
                trend_strength = 35  # Strong downtrend
            else:
                trend_strength = 45  # Moderate downtrend
    
    return {
        "direction": trend_direction,
        "strength": trend_strength,
        "adx": adx
    }


def calculate_price_momentum(df: pd.DataFrame, periods: int = 3) -> Dict[str, float]:
    """
    Calculate price momentum for binary options entry timing.
    
    Args:
        df: Market data with 'close' column
        periods: Number of periods to look back
        
    Returns:
        Dictionary with momentum direction and percentage change
    """
    try:
        if len(df) < periods + 1:
            return {"change_pct": 0.0, "direction": "NEUTRAL", "strength": 0.0}
        
        current_price = float(df["close"].iloc[-1])
        past_price = float(df["close"].iloc[-periods-1])
        
        change_pct = ((current_price - past_price) / past_price) * 100
        
        if change_pct > 0.01:  # > 0.01% rise
            direction = "UP"
            strength = min(100, abs(change_pct) * 100)  # Scale to 0-100
        elif change_pct < -0.01:  # > 0.01% fall
            direction = "DOWN"
            strength = min(100, abs(change_pct) * 100)
        else:
            direction = "NEUTRAL"
            strength = 0.0
        
        return {
            "change_pct": change_pct,
            "direction": direction,
            "strength": strength
        }
    except Exception as e:
        logging.warning(f"Price momentum calculation error: {e}")
        return {"change_pct": 0.0, "direction": "NEUTRAL", "strength": 0.0}


def get_adaptive_cache_duration(atr: float, current_price: float) -> int:
    """
    Calculate adaptive cache duration based on market volatility.
    
    Args:
        atr: Average True Range
        current_price: Current price
        
    Returns:
        Cache duration in seconds
    """
    try:
        volatility_pct = safe_divide(atr, current_price, 0.1) * 100
        
        if volatility_pct > 0.15:
            return 30
        elif volatility_pct < 0.05:
            return 180
        else:
            return 90
    except Exception:
        return 90


def get_adaptive_thresholds(atr: float, current_price: float) -> Dict[str, Any]:
    """
    Adjust signal thresholds based on market volatility.
    
    Args:
        atr: Average True Range value
        current_price: Current market price
        
    Returns:
        Adjusted thresholds for signal generation
    """
    try:
        volatility_pct = safe_divide(atr, current_price, 0.1) * 100
        
        if volatility_pct > 0.15:
            return {"min_buy_score": 60, "max_sell_score": 40, "label": "HIGH VOLATILITY"}
        elif volatility_pct < 0.05:
            return {"min_buy_score": 52, "max_sell_score": 48, "label": "LOW VOLATILITY"}
        else:
            return {"min_buy_score": 55, "max_sell_score": 45, "label": "NORMAL VOLATILITY"}
    except Exception as e:
        logging.warning(f"Adaptive threshold error: {e}")
        return {"min_buy_score": 55, "max_sell_score": 45, "label": "DEFAULT"}


def analyze_volume(df: pd.DataFrame) -> float:
    """
    Analyze volume to confirm signal strength.
    
    Args:
        df: Market data with 'volume' column
        
    Returns:
        Volume bonus points (0-10) to add to TA score
    """
    try:
        if 'volume' not in df.columns or df['volume'].empty:
            return 0.0
        
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].rolling(20).mean().iloc[-1]
        
        if pd.isna(current_vol) or pd.isna(avg_vol) or avg_vol == 0:
            return 0.0
        
        volume_ratio = safe_divide(current_vol, avg_vol, 1.0)
        
        if volume_ratio > 2.0:
            return 10.0
        elif volume_ratio > 1.5:
            return 7.0
        elif volume_ratio > 1.2:
            return 4.0
        elif volume_ratio > 1.0:
            return 2.0
        else:
            return 0.0
            
    except Exception as e:
        logging.warning(f"Volume analysis error: {e}")
        return 0.0


def calculate_confidence(rsi: float, macd_diff: float, bb_position: float, 
                        adx: float, stoch_k: float, signal_direction: str) -> float:
    """
    Calculate dynamic confidence based on indicator convergence.
    
    Args:
        rsi: RSI value
        macd_diff: MACD diff value
        bb_position: Bollinger Bands position (0-100)
        adx: ADX trend strength
        stoch_k: Stochastic K value
        signal_direction: "BUY" or "SELL"
        
    Returns:
        Confidence level (40-95%)
    """
    confirmations = 0
    max_confirmations = 5
    
    if signal_direction == "BUY":
        if rsi < CONFIG["rsi_oversold"]:
            confirmations += 1
        if macd_diff > 0:
            confirmations += 1
        if bb_position < CONFIG["bb_oversold"]:
            confirmations += 1
        if stoch_k < CONFIG["stoch_oversold"]:
            confirmations += 1
        if adx > CONFIG["adx_trend_threshold"]:
            confirmations += 1
    elif signal_direction == "SELL":
        if rsi > CONFIG["rsi_overbought"]:
            confirmations += 1
        if macd_diff < 0:
            confirmations += 1
        if bb_position > CONFIG["bb_overbought"]:
            confirmations += 1
        if stoch_k > CONFIG["stoch_overbought"]:
            confirmations += 1
        if adx > CONFIG["adx_trend_threshold"]:
            confirmations += 1
    else:
        return 0.0
    
    confidence = 40.0 + (confirmations / max_confirmations) * 55.0
    return round(confidence, 1)


def get_df_hash(df: pd.DataFrame) -> Optional[int]:
    """Generate a hash for dataframe to check if data changed."""
    try:
        subset = df[['close', 'high', 'low', 'open']].tail(10)
        return hash(tuple(subset.values.flatten().tolist()))
    except Exception:
        return None


async def calculate_indicators_parallel(df: pd.DataFrame, current_price: float) -> Dict[str, float]:
    """
    Calculate all technical indicators in parallel for maximum speed.
    
    Args:
        df: Market data with OHLCV columns
        current_price: Current price for BB position calculation
        
    Returns:
        Dictionary with all calculated indicators
    """
    # Check cache first
    df_hash = get_df_hash(df)
    if df_hash is not None:
        async with indicator_cache_lock:
            if df_hash in INDICATOR_CACHE:
                cached_time, cached_indicators = INDICATOR_CACHE[df_hash]
                age = (datetime.now() - cached_time).total_seconds()
                if age < 30:
                    logging.debug(f"✓ Using cached indicators (age: {age:.1f}s)")
                    return cached_indicators
    
    loop = asyncio.get_running_loop()
    
    def calc_rsi():
        try:
            rsi = float(ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1])
            return rsi if not pd.isna(rsi) else 50.0
        except Exception as e:
            logging.warning(f"RSI calculation error: {e}")
            return 50.0
    
    def calc_macd():
        try:
            macd_diff = float(ta.trend.MACD(df["close"]).macd_diff().iloc[-1])
            return macd_diff if not pd.isna(macd_diff) else 0.0
        except Exception as e:
            logging.warning(f"MACD calculation error: {e}")
            return 0.0
    
    def calc_bb():
        try:
            bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
            bb_upper = float(bb.bollinger_hband().iloc[-1])
            bb_lower = float(bb.bollinger_lband().iloc[-1])
            bb_range = bb_upper - bb_lower
            if bb_range > 0:
                bb_position = safe_divide((current_price - bb_lower), bb_range, 0.5) * 100
            else:
                bb_position = 50.0
            return bb_position if not pd.isna(bb_position) else 50.0
        except Exception as e:
            logging.warning(f"Bollinger Bands calculation error: {e}")
            return 50.0
    
    def calc_atr():
        try:
            atr = float(ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range().iloc[-1])
            if pd.isna(atr) or atr <= 0:
                return current_price * 0.001
            return atr
        except Exception as e:
            logging.warning(f"ATR calculation error: {e}")
            return current_price * 0.001
    
    def calc_adx():
        try:
            adx = float(ta.trend.ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1])
            return adx if not pd.isna(adx) else 20.0
        except Exception as e:
            logging.warning(f"ADX calculation error: {e}")
            return 20.0
    
    def calc_stoch():
        try:
            stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
            stoch_k = float(stoch.stoch().iloc[-1])
            stoch_d = float(stoch.stoch_signal().iloc[-1])
            k = stoch_k if not pd.isna(stoch_k) else 50.0
            d = stoch_d if not pd.isna(stoch_d) else 50.0
            return (k, d)
        except Exception as e:
            logging.warning(f"Stochastic calculation error: {e}")
            return (50.0, 50.0)
    
    # Run all calculations in parallel
    results = await asyncio.gather(
        loop.run_in_executor(None, calc_rsi),
        loop.run_in_executor(None, calc_macd),
        loop.run_in_executor(None, calc_bb),
        loop.run_in_executor(None, calc_atr),
        loop.run_in_executor(None, calc_adx),
        loop.run_in_executor(None, calc_stoch),
        return_exceptions=True
    )
    
    # Parse results with error handling
    rsi = results[0] if not isinstance(results[0], Exception) else 50.0
    macd_diff = results[1] if not isinstance(results[1], Exception) else 0.0
    bb_position = results[2] if not isinstance(results[2], Exception) else 50.0
    atr = results[3] if not isinstance(results[3], Exception) else current_price * 0.001
    adx = results[4] if not isinstance(results[4], Exception) else 20.0
    stoch_k, stoch_d = results[5] if not isinstance(results[5], Exception) else (50.0, 50.0)
    
    indicators = {
        "rsi": rsi,
        "macd_diff": macd_diff,
        "bb_position": bb_position,
        "atr": atr,
        "adx": adx,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d
    }
    
    # Cache the results
    if df_hash is not None:
        async with indicator_cache_lock:
            if len(INDICATOR_CACHE) >= 5:
                INDICATOR_CACHE.popitem(last=False)
            INDICATOR_CACHE[df_hash] = (datetime.now(), indicators)
            INDICATOR_CACHE.move_to_end(df_hash)
            logging.debug(f"Cached indicators (hash: {df_hash})")
    
    return indicators


