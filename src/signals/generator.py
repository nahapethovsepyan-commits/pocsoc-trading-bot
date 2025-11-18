"""
Signal generation logic with GPT integration.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ..config import CONFIG, get_openai_client
from ..config.settings import (
    DEFAULT_GPT_PROMPT_TEMPLATE,
    DEFAULT_GPT_SYSTEM_PROMPT,
)
from ..utils.symbols import normalize_symbol, symbol_to_pair, get_symbol_config
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
from .candles_tutor import call_candlestutor, format_candles_for_tutor


async def generate_signal(symbol: str = "EURUSD") -> Dict[str, Any]:
    """
    Генерация торгового сигнала с поддержкой символов.
    
    Args:
        symbol: Торговый символ (EURUSD, XAUUSD). По умолчанию "EURUSD".
    
    Returns:
        Словарь с данными сигнала
    """
    try:
        # Normalize symbol
        normalized_symbol = normalize_symbol(symbol)
        pair = symbol_to_pair(normalized_symbol)
        default_price = get_symbol_config(normalized_symbol, "default_price")
        
        # Get symbol-specific configuration
        symbol_config = CONFIG.get("symbol_configs", {}).get(normalized_symbol, {})
        
        # Check trading hours
        if not is_trading_hours():
            current_hour = datetime.now(timezone.utc).hour
            logging.debug(f"Outside trading hours (current: {current_hour}:00 UTC), skipping analysis")
            return {
                "signal": "NO_SIGNAL",
                "price": default_price,
                "score": 50,
                "confidence": 0,
                "reasoning": f"Outside trading hours ({CONFIG['trading_start_hour']}:00-{CONFIG['trading_end_hour']}:00 UTC)",
                "time": datetime.now(),
                "entry": default_price,
                "indicators": {},
                "symbol": normalized_symbol
            }
        
        # Get market data (use normalized symbol)
        df = await fetch_forex_data(normalized_symbol)
        if df is None or df.empty:
            raise ValueError("No market data received")

        try:
            current_price = float(df["close"].iloc[-1])
        except (ValueError, IndexError) as e:
            logging.warning(f"Price extraction error: {e}")
            current_price = default_price

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
                rsi_state = "перепродан" if rsi < CONFIG.get("rsi_strong_oversold", 30) else (
                    "перекуплен" if rsi > CONFIG.get("rsi_strong_overbought", 70) else "нейтральный"
                )
                macd_state = "положительный" if macd_diff > 0 else "отрицательный"

                # Symbol-specific GPT prompt
                if normalized_symbol == "XAUUSD":
                    prompt_template = (
                        "Ты трейдер-аналитик. Анализируй пару XAU/USD (золото). "
                        "Учитывай корреляцию с DXY (обратная), новости по ФРС, инфляции, геополитике. "
                        "Уровни: 2700, 2750, 2800. Волатильность выше, чем у EUR/USD.\n"
                        "RSI: {rsi:.1f} ({rsi_state})\n"
                        "MACD: {macd:.5f} ({macd_state})\n"
                        "Цена: {price:.5f}\n\n"
                        "Ответь ТОЛЬКО одним словом: BUY, SELL или NO_SIGNAL"
                    )
                else:
                    prompt_template = CONFIG.get("gpt_prompt_template", DEFAULT_GPT_PROMPT_TEMPLATE)
                
                prompt_context = {
                    "pair": pair,
                    "rsi": rsi,
                    "rsi_state": rsi_state,
                    "macd": macd_diff,
                    "macd_state": macd_state,
                    "price": current_price,
                }
                try:
                    prompt = prompt_template.format(**prompt_context)
                except Exception as fmt_error:
                    logging.warning(f"GPT prompt formatting error: {fmt_error}")
                    prompt = DEFAULT_GPT_PROMPT_TEMPLATE.format(**prompt_context)

                gpt_model = CONFIG.get("gpt_model", "gpt-4o-mini")
                gpt_temperature = CONFIG.get("gpt_temperature", 0.1)
                gpt_max_tokens = CONFIG.get("gpt_max_tokens", 10)
                gpt_request_timeout = CONFIG.get("gpt_request_timeout", 3.0)
                gpt_system_prompt = CONFIG.get("gpt_system_prompt", DEFAULT_GPT_SYSTEM_PROMPT)
                try:
                    async with metrics_lock:
                        METRICS["gpt_calls"] += 1
                    
                    resp = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=gpt_model,
                            messages=[
                                {"role": "system", "content": gpt_system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=gpt_max_tokens,
                            temperature=gpt_temperature,
                        ),
                        timeout=gpt_request_timeout
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
                    logging.warning(f"GPT request timeout ({gpt_request_timeout}s)")
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
            gpt_wait_timeout = CONFIG.get("gpt_wait_timeout", 2.0)
            try:
                gpt_score, reasoning = await asyncio.wait_for(gpt_task, timeout=gpt_wait_timeout)
            except asyncio.TimeoutError:
                logging.info(f"GPT still processing after {gpt_wait_timeout:.1f}s, using TA-only score")
                reasoning = f"GPT slow response (> {gpt_wait_timeout:.1f}s), using TA only"

        # Final scoring with safety bounds (TA must dominate decision-making)
        gpt_min = CONFIG.get("gpt_weight_min", 0.05)
        gpt_max = CONFIG.get("gpt_weight_max", 0.15)
        configured_gpt_weight = CONFIG.get("gpt_weight", gpt_min)
        gpt_weight = max(gpt_min, min(gpt_max, configured_gpt_weight))
        ta_weight = 1.0 - gpt_weight
        final_score = float(gpt_weight * gpt_score + ta_weight * ta_score)

        # Calculate confidence BEFORE signal decision (for filtering)
        # Determine preliminary direction for confidence calculation
        preliminary_signal = "NO_SIGNAL"
        if final_score > 50:
            preliminary_signal = "BUY"
        elif final_score < 50:
            preliminary_signal = "SELL"
        
        confidence = calculate_confidence(rsi, macd_diff, bb_position, adx, stoch_k, preliminary_signal)
        
        # Use symbol-specific thresholds
        base_min_buy = symbol_config.get("min_signal_score", CONFIG.get("min_signal_score", 60))
        base_max_sell = CONFIG.get("max_sell_score", 40)
        
        # FIXED: Higher thresholds for binary options (was 55/45, now 65/35)
        thresholds = get_adaptive_thresholds(atr, current_price)
        min_buy = max(base_min_buy, thresholds["min_buy_score"])
        max_sell = min(base_max_sell, thresholds["max_sell_score"])
        
        # ЭТАП 1: Определение кандидата на сигнал для CandlesTutor
        candidate_signal = "NO_SIGNAL"
        if ta_score >= min_buy:
            candidate_signal = "BUY"
        elif ta_score <= max_sell:
            candidate_signal = "SELL"
        
        # ЭТАП 2: Условный вызов CandlesTutor (только если есть кандидат)
        candlestutor_result = None
        candlestutor_enabled = CONFIG.get("candlestutor_enabled", True)
        
        if (candlestutor_enabled and 
            candidate_signal != "NO_SIGNAL" and
            confidence >= CONFIG.get("min_confidence", 65)):
            
            # Проверяем минимальный отступ от порога
            min_score_gap = CONFIG.get("candlestutor_min_score_gap", 3)
            should_call = False
            
            if candidate_signal == "BUY" and ta_score >= (min_buy + min_score_gap):
                should_call = True
            elif candidate_signal == "SELL" and ta_score <= (max_sell - min_score_gap):
                should_call = True
            
            if should_call:
                # Форматируем свечи
                candles_list = format_candles_for_tutor(df, num_candles=15)
                
                # Формируем индикаторы для отправки
                indicators_dict = {
                    "rsi": rsi,
                    "macd": macd_diff,
                    "bb_position": bb_position,
                    "adx": adx,
                    "stoch_k": stoch_k,
                    "stoch_d": stoch_d,
                }
                
                # Вызываем CandlesTutor
                candlestutor_result = await call_candlestutor(
                    symbol=normalized_symbol,
                    timeframe="1min",
                    candles=candles_list,
                    indicators=indicators_dict,
                    candidate_signal=candidate_signal,
                    ta_score=ta_score,
                    ta_confidence=confidence
                )
                
                if candlestutor_result:
                    logging.info(
                        f"CandlesTutor: decision={candlestutor_result.get('decision')}, "
                        f"pattern={candlestutor_result.get('pattern')}, "
                        f"confidence={candlestutor_result.get('confidence')}"
                    )
                else:
                    logging.debug("CandlesTutor не ответил (лимит/ошибка), используем только TA")
        
        # ЭТАП 3: Комбинирование TA и CandlesTutor решений
        final_decision = candidate_signal
        combined_confidence = confidence
        
        if candlestutor_result:
            ct_decision = candlestutor_result.get("decision", "NO_TRADE")
            ct_confidence = candlestutor_result.get("confidence", 0)
            ct_pattern = candlestutor_result.get("pattern", "нет")
            
            # Правило комбинирования
            candlestutor_min_conf = CONFIG.get("candlestutor_min_confidence", 60)
            combine_conf = CONFIG.get("candlestutor_combine_confidence", True)
            
            if combine_conf:
                # Взвешенное комбинирование confidence
                ta_weight = CONFIG.get("candlestutor_ta_weight", 0.7)
                candle_weight = CONFIG.get("candlestutor_candle_weight", 0.3)
                # Нормализуем веса на случай если сумма != 1.0
                total_weight = ta_weight + candle_weight
                if total_weight > 0:
                    ta_weight = ta_weight / total_weight
                    candle_weight = candle_weight / total_weight
                combined_confidence = (confidence * ta_weight) + (ct_confidence * candle_weight)
            
            # Логика принятия решения
            if ct_decision == "NO_TRADE" or ct_confidence < candlestutor_min_conf:
                # GPT блокирует или не уверен - пропускаем сигнал
                final_decision = "NO_SIGNAL"
                logging.warning(
                    f"⚠️ CandlesTutor блокирует сигнал: decision={ct_decision}, "
                    f"confidence={ct_confidence} < {candlestutor_min_conf}"
                )
            elif ct_decision != candidate_signal:
                # GPT против направления - пропускаем (контрверсивный кейс)
                final_decision = "NO_SIGNAL"
                logging.warning(
                    f"⚠️ CandlesTutor против направления: TA={candidate_signal}, "
                    f"CandlesTutor={ct_decision}, пропускаем"
                )
            else:
                # GPT подтверждает - используем комбинированный confidence
                final_decision = candidate_signal
                confidence = combined_confidence if combine_conf else min(confidence, ct_confidence)
                logging.info(
                    f"✅ CandlesTutor подтверждает {candidate_signal}: pattern={ct_pattern}, "
                    f"combined_confidence={combined_confidence:.1f}"
                )
        else:
            # CandlesTutor не ответил - используем только TA
            logging.debug("CandlesTutor не вызван или вернул None, используем только TA")
        
        # Generate signal: используем решение CandlesTutor если оно есть, иначе старую логику
        signal = final_decision
        
        # Если CandlesTutor не был вызван или вернул None, используем старую логику с momentum фильтрами
        if not candlestutor_result:
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

            # FIXED: Use final_score with momentum and confidence filters (только если CandlesTutor не вызван)
            min_confidence = symbol_config.get("min_confidence", CONFIG.get("min_confidence", 70))
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
                    signal = "NO_SIGNAL"
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
                    adjusted_score += momentum_penalty_score
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
                    signal = "NO_SIGNAL"
                    decision_reasons.append(
                        f"Rejected SELL: adjusted score {adjusted_score:.1f} / confidence {adjusted_confidence:.1f}"
                    )
            else:
                signal = "NO_SIGNAL"
                logging.debug(
                    "⏭️  NO_SIGNAL: final_score=%.1f in middle range (%.1f < score < %.1f)",
                    final_score, max_sell, min_buy
                )
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
        else:
            # CandlesTutor был вызван, используем его решение
            logging.info(
                "Trend: %s | Momentum: %s (%.4f%%) | TA score: %.1f | GPT score: %.1f | CandlesTutor: %s",
                trend_direction,
                momentum["direction"],
                price_change,
                ta_score,
                gpt_score,
                signal,
            )
            logging.info(
                "Final decision from CandlesTutor: %s | Combined confidence: %.1f",
                signal,
                combined_confidence,
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
            "price_change": round(price_change, 4),
            "symbol": normalized_symbol,
            "candlestutor": candlestutor_result if candlestutor_result else None,
            "combined_confidence": round(combined_confidence, 1) if candlestutor_result else round(confidence, 1),
        }

    except Exception as e:
        logging.error(f"Signal generation error for {symbol}: {e}")
        try:
            normalized_symbol = normalize_symbol(symbol)
            default_price = get_symbol_config(normalized_symbol, "default_price")
        except Exception:
            normalized_symbol = "EURUSD"
            default_price = CONFIG["default_price"]
        return {
            "signal": "NO_SIGNAL",
            "price": default_price,
            "score": 50,
            "confidence": 0,
            "reasoning": f"Error: {str(e)[:100]}",
            "time": datetime.now(),
            "entry": default_price,
            "indicators": {},
            "symbol": normalized_symbol
        }


async def main_analysis(symbol: str = "EURUSD", bot=None, TEXTS=None):
    """
    Основная функция автоматического анализа рынка и генерации сигналов.
    
    Args:
        symbol: Торговый символ (EURUSD, XAUUSD). По умолчанию "EURUSD".
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
            current_hour = datetime.now(timezone.utc).hour
            logging.debug(f"Outside trading hours (current: {current_hour}:00 UTC), skipping analysis")
            return
            
        if not await check_rate_limit():
            logging.debug(f"Rate limit reached ({CONFIG['max_signals_per_hour']} signals/hour), skipping analysis")
            return
            
        signal_data = await generate_signal(symbol)
        
        if signal_data["signal"] != "NO_SIGNAL":
            if bot is not None and TEXTS is not None:
                await send_signal_message(signal_data, lang='ru', bot=bot, TEXTS=TEXTS)
            async with stats_lock:
                STATS["signals_per_hour"] += 1
                STATS["last_signal_time"] = datetime.now()
            logging.info(f"📤 Signal '{signal_data['signal']}' for {symbol} sent to {len(SUBSCRIBED_USERS)} users")
        else:
            logging.debug(
                "⏭️  NO_SIGNAL generated for %s (score=%.1f, confidence=%.1f) - not sending automatically",
                symbol,
                signal_data.get('score', 0),
                signal_data.get('confidence', 0)
            )
            
    except Exception as e:
        logging.error(f"Main analysis error for {symbol}: {e}")


