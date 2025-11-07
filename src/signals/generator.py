"""
Signal generation logic with GPT integration.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from ..config import CONFIG, get_openai_client
from ..api import fetch_forex_data
from ..indicators import (
    calculate_indicators_parallel,
    calculate_ta_score,
    get_adaptive_thresholds,
    analyze_volume,
    calculate_confidence,
    detect_trend_direction,
    calculate_price_momentum,
)
from ..models.state import METRICS, metrics_lock
from .utils import is_trading_hours


async def generate_signal() -> Dict[str, Any]:
    """
    Генерация торгового сигнала EUR/USD.
    
    Returns:
        Словарь с данными сигнала
    """
    try:
        # Check trading hours
        if not is_trading_hours():
            current_hour = datetime.utcnow().hour
            logging.debug(f"Outside trading hours (current: {current_hour}:00 UTC), skipping analysis")
            return {
                "signal": "NO_SIGNAL",
                "price": CONFIG["default_price"],
                "score": 50,
                "confidence": 0,
                "reasoning": f"Outside trading hours ({CONFIG['trading_start_hour']}:00-{CONFIG['trading_end_hour']}:00 UTC)",
                "time": datetime.now(),
                "entry": CONFIG["default_price"],
                "indicators": {}
            }
        
        # Get market data
        df = await fetch_forex_data(CONFIG["pair"])
        if df is None or df.empty:
            raise ValueError("No market data received")

        try:
            current_price = float(df["close"].iloc[-1])
        except (ValueError, IndexError) as e:
            logging.warning(f"Price extraction error: {e}")
            current_price = CONFIG["default_price"]

        # Calculate indicators in parallel
        indicators = await calculate_indicators_parallel(df, current_price)
        rsi = indicators["rsi"]
        macd_diff = indicators["macd_diff"]
        bb_position = indicators["bb_position"]
        atr = indicators["atr"]
        adx = indicators["adx"]
        stoch_k = indicators["stoch_k"]
        stoch_d = indicators["stoch_d"]

        # FIXED: Calculate price momentum for entry timing
        momentum = calculate_price_momentum(df, periods=3)
        price_change = momentum["change_pct"]

        # FIXED: Detect trend direction BEFORE signal generation
        trend_info = detect_trend_direction(macd_diff, rsi, adx, price_change)
        trend_direction = trend_info["direction"]

        # Start GPT analysis in background (if enabled)
        gpt_task = None
        client, use_gpt = get_openai_client()
        if CONFIG["use_gpt"] and use_gpt and client is not None:
            async def get_gpt_analysis():
                """Get GPT analysis in background"""
                prompt = (
                    f"Ты трейдер-аналитик. Дай четкий торговый сигнал для EUR/USD на основе индикаторов:\n"
                    f"RSI: {rsi:.1f} ({'перепродан' if rsi < 30 else 'перекуплен' if rsi > 70 else 'нейтральный'})\n"
                    f"MACD: {macd_diff:.5f} ({'положительный' if macd_diff > 0 else 'отрицательный'})\n"
                    f"Цена: {current_price:.5f}\n\n"
                    f"Ответь ТОЛЬКО одним словом: BUY, SELL или NO_SIGNAL"
                )
                try:
                    async with metrics_lock:
                        METRICS["gpt_calls"] += 1
                    
                    resp = await asyncio.wait_for(
                        client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Ты даешь только торговые сигналы. Отвечай одним словом: BUY, SELL или NO_SIGNAL."},
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=10,
                            temperature=0.1,
                        ),
                        timeout=3.0
                    )
                    
                    if not resp.choices or len(resp.choices) == 0:
                        raise ValueError("Empty response from GPT")
                    
                    gpt_reply = resp.choices[0].message.content.strip().upper()
                    
                    if not gpt_reply:
                        raise ValueError("Empty content from GPT")
                    
                    if "BUY" in gpt_reply:
                        score = 70
                    elif "SELL" in gpt_reply:
                        score = 30
                    else:
                        score = 50
                    
                    async with metrics_lock:
                        METRICS["gpt_success"] += 1
                    
                    return (score, gpt_reply)
                        
                except asyncio.TimeoutError:
                    async with metrics_lock:
                        METRICS["gpt_errors"] += 1
                    logging.warning("GPT request timeout (3s)")
                    return (50, "GPT timeout")
                except Exception as e:
                    async with metrics_lock:
                        METRICS["gpt_errors"] += 1
                    error_msg = str(e)[:100] if e else "Unknown error"
                    error_type = type(e).__name__
                    logging.error(f"GPT API error [{error_type}]: {error_msg}")
                    return (50, f"GPT error: {error_type}")
            
            gpt_task = asyncio.create_task(get_gpt_analysis())

        # FIXED: Calculate TA score with trend and momentum
        ta_score = calculate_ta_score(
            rsi, macd_diff, bb_position, adx, stoch_k, stoch_d,
            price_change=price_change,
            trend_direction=trend_direction
        )
        
        # Volume confirmation
        volume_bonus = analyze_volume(df)
        ta_score += volume_bonus
        ta_score = max(0, min(100, ta_score))
        
        if volume_bonus > 0:
            logging.info(f"Volume bonus applied: +{volume_bonus:.1f} points (ta_score now: {ta_score:.1f})")

        # Wait for GPT result
        gpt_score = 50
        reasoning = "GPT analysis disabled."
        
        if gpt_task is not None:
            try:
                gpt_score, reasoning = await asyncio.wait_for(gpt_task, timeout=0.5)
            except asyncio.TimeoutError:
                logging.info("GPT still processing, using TA-only score")
                reasoning = "GPT slow response, using TA only"

        # Final scoring
        final_score = float(CONFIG["gpt_weight"] * gpt_score + CONFIG["ta_weight"] * ta_score)

        # Calculate confidence BEFORE signal decision (for filtering)
        # Determine preliminary direction for confidence calculation
        preliminary_signal = "NO_SIGNAL"
        if final_score > 50:
            preliminary_signal = "BUY"
        elif final_score < 50:
            preliminary_signal = "SELL"
        
        confidence = calculate_confidence(rsi, macd_diff, bb_position, adx, stoch_k, preliminary_signal)
        
        # Generate signal with adaptive thresholds
        signal = "NO_SIGNAL"
        
        # FIXED: Higher thresholds for binary options (was 55/45, now 65/35)
        thresholds = get_adaptive_thresholds(atr, current_price)
        base_min_buy = CONFIG.get("min_signal_score", 60)
        base_max_sell = CONFIG.get("max_sell_score", 40)
        min_buy = max(base_min_buy, thresholds["min_buy_score"])
        max_sell = min(base_max_sell, thresholds["max_sell_score"])
        
        logging.info(
            "Trend: %s | Momentum: %s (%.4f%%) | TA score: %.1f | GPT score: %.1f",
            trend_direction,
            momentum["direction"],
            price_change,
            ta_score,
            gpt_score,
        )
        logging.info(
            "Adaptive thresholds (%s volatility): BUY>=%s, SELL<=%s | Final score: %.1f | Confidence: %.1f",
            thresholds["label"],
            min_buy,
            max_sell,
            final_score,
            confidence,
        )

        # FIXED: Use final_score with momentum and confidence filters
        min_confidence = CONFIG.get("min_confidence", 70)  # Default 70% for binary options
        momentum_penalty_score = CONFIG.get("momentum_penalty_score", 7)
        momentum_penalty_confidence = CONFIG.get("momentum_penalty_confidence", 5)
        decision_reasons = []
        adjusted_score = final_score
        adjusted_confidence = confidence
        
        if final_score >= min_buy:
            if momentum["direction"] not in ("UP", "NEUTRAL"):
                logging.info(
                    "⚠️ BUY momentum mismatch (%s) - applying penalties score:%s conf:%s",
                    momentum["direction"],
                    momentum_penalty_score,
                    momentum_penalty_confidence,
                )
                adjusted_score -= momentum_penalty_score
                adjusted_confidence -= momentum_penalty_confidence
                decision_reasons.append(
                    f"BUY penalty applied due to momentum {momentum['direction']}"
                )
            if adjusted_confidence >= min_confidence and adjusted_score >= min_buy:
                signal = "BUY"
                logging.info(
                    "✅ BUY signal: adjusted_score=%.1f >= %s, adjusted_confidence=%.1f, momentum=%s",
                    adjusted_score,
                    min_buy,
                    adjusted_confidence,
                    momentum["direction"],
                )
                decision_reasons.append("BUY: passed thresholds")
            else:
                decision_reasons.append(
                    f"Rejected BUY: adjusted score {adjusted_score:.1f} / confidence {adjusted_confidence:.1f}"
                )
        elif final_score <= max_sell:
            adjusted_score = final_score
            adjusted_confidence = confidence
            if momentum["direction"] not in ("DOWN", "NEUTRAL"):
                logging.info(
                    "⚠️ SELL momentum mismatch (%s) - applying penalties score:%s conf:%s",
                    momentum["direction"],
                    momentum_penalty_score,
                    momentum_penalty_confidence,
                )
                adjusted_score += momentum_penalty_score  # score is bearish, so add penalty to move toward 50
                adjusted_confidence -= momentum_penalty_confidence
                decision_reasons.append(
                    f"SELL penalty applied due to momentum {momentum['direction']}"
                )
            if adjusted_confidence >= min_confidence and adjusted_score <= max_sell:
                signal = "SELL"
                logging.info(
                    "✅ SELL signal: adjusted_score=%.1f <= %s, adjusted_confidence=%.1f, momentum=%s",
                    adjusted_score,
                    max_sell,
                    adjusted_confidence,
                    momentum["direction"],
                )
                decision_reasons.append("SELL: passed thresholds")
            else:
                decision_reasons.append(
                    f"Rejected SELL: adjusted score {adjusted_score:.1f} / confidence {adjusted_confidence:.1f}"
                )
        # If in middle range, stay NO_SIGNAL (don't force a signal)
        else:
            logging.debug(f"⏭️  NO_SIGNAL: final_score={final_score:.1f} in middle range ({max_sell} < score < {min_buy})")
            decision_reasons.append(
                f"Score {final_score:.1f} between thresholds ({max_sell} < score < {min_buy})"
            )
        logging.info(
            "Decision summary -> signal: %s | score: %.1f | confidence: %.1f | momentum: %s | reasons: %s",
            signal,
            final_score,
            confidence,
            momentum["direction"],
            "; ".join(decision_reasons) or "n/a",
        )
        
        # Update metrics
        async with metrics_lock:
            METRICS["signals_generated"] += 1
        
        return {
            "signal": signal,
            "price": current_price,
            "score": round(final_score, 1),
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
            "time": datetime.now(),
            "entry": current_price,
            "indicators": {
                "rsi": round(rsi, 1),
                "macd": round(macd_diff, 5),
                "bb_position": round(bb_position, 1),
                "atr": round(atr, 5),
                "adx": round(adx, 1),
                "stoch_k": round(stoch_k, 1),
                "stoch_d": round(stoch_d, 1),
            },
            "atr": atr,
            "trend": trend_direction,
            "momentum": momentum["direction"],
            "price_change": round(price_change, 4)
        }

    except Exception as e:
        logging.error(f"Signal generation error: {e}")
        return {
            "signal": "NO_SIGNAL",
            "price": CONFIG["default_price"],
            "score": 50,
            "confidence": 0,
            "reasoning": f"Error: {str(e)[:100]}",
            "time": datetime.now(),
            "entry": CONFIG["default_price"],
            "indicators": {}
        }


async def main_analysis(bot=None, TEXTS=None):
    """
    Основная функция автоматического анализа рынка и генерации сигналов.
    
    Args:
        bot: Telegram bot instance (required for sending signals)
        TEXTS: Localization dictionary (required for sending signals)
    """
    from .utils import is_trading_hours, check_rate_limit
    from .messaging import send_signal_message
    from ..models.state import SUBSCRIBED_USERS, STATS, stats_lock
    
    try:
        if not SUBSCRIBED_USERS:
            logging.debug("No subscribed users, skipping analysis")
            return
        
        if not is_trading_hours():
            current_hour = datetime.utcnow().hour
            logging.debug(f"Outside trading hours (current: {current_hour}:00 UTC), skipping analysis")
            return
            
        if not await check_rate_limit():
            logging.debug(f"Rate limit reached ({CONFIG['max_signals_per_hour']} signals/hour), skipping analysis")
            return
            
        signal_data = await generate_signal()
        
        if signal_data["signal"] != "NO_SIGNAL":
            if bot is not None and TEXTS is not None:
                await send_signal_message(signal_data, lang='ru', bot=bot, TEXTS=TEXTS)
            async with stats_lock:
                STATS["signals_per_hour"] += 1
                STATS["last_signal_time"] = datetime.now()
            logging.info(f"📤 Signal '{signal_data['signal']}' sent to {len(SUBSCRIBED_USERS)} users")
        else:
            logging.debug(f"⏭️  NO_SIGNAL generated (score={signal_data.get('score', 0):.1f}, confidence={signal_data.get('confidence', 0):.1f}) - not sending automatically")
            
    except Exception as e:
        logging.error(f"Main analysis error: {e}")


