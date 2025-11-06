"""
System health monitoring and alerting.
"""

import logging
from datetime import datetime
from typing import Optional
from ..config import CONFIG
from ..models.state import (
    SUBSCRIBED_USERS,
    STATS,
    METRICS,
    ALERT_HISTORY,
    ALERT_COOLDOWN_HOURS,
    stats_lock,
    metrics_lock,
    alert_lock,
)
from ..utils.helpers import safe_divide


async def send_alert(message_text: str, bot) -> None:
    """
    Отправка алерта всем подписанным пользователям.
    
    Args:
        message_text: Текст алерта для отправки
        bot: Telegram bot instance
    """
    if not SUBSCRIBED_USERS:
        return
    
    alert_text = f"🚨 **ALERT** 🚨\n\n{message_text}"
    
    failed_sends = []
    for chat_id in SUBSCRIBED_USERS.copy():
        try:
            await bot.send_message(chat_id, alert_text, parse_mode=None)
            logging.warning(f"Alert sent to user {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send alert to {chat_id}: {e}")
            failed_sends.append(chat_id)
    
    if failed_sends:
        SUBSCRIBED_USERS.difference_update(failed_sends)


async def check_system_health(bot) -> None:
    """
    Проверка здоровья системы и отправка алертов при проблемах (с дедупликацией).
    
    Args:
        bot: Telegram bot instance (required for sending alerts)
    
    Проверяет:
    - Процент ошибок API (порог: CONFIG["alert_api_error_rate"], по умолчанию 10%)
    - Процент ошибок GPT (порог: CONFIG["alert_gpt_error_rate"], по умолчанию 20%)
    - Отсутствие сигналов в течение длительного времени (порог: CONFIG["alert_no_signals_hours"])
    """
    try:
        now = datetime.now()
        
        async with metrics_lock:
            # Проверка API ошибок
            total_api = METRICS["api_calls"] + METRICS["api_errors"]
            if total_api > 0:
                api_error_rate = safe_divide(METRICS["api_errors"], total_api, 0.0) * 100
                if api_error_rate >= CONFIG["alert_api_error_rate"]:
                    async with alert_lock:
                        last_alert = ALERT_HISTORY.get("api_error")
                        if last_alert is None or (now - last_alert).total_seconds() > (ALERT_COOLDOWN_HOURS * 3600):
                            await send_alert(
                                f"⚠️ High API error rate: {api_error_rate:.1f}%\n"
                                f"API calls: {METRICS['api_calls']}, Errors: {METRICS['api_errors']}",
                                bot
                            )
                            ALERT_HISTORY["api_error"] = now
            
            # Проверка GPT ошибок
            if METRICS["gpt_calls"] > 0:
                gpt_error_rate = safe_divide(METRICS["gpt_errors"], METRICS["gpt_calls"], 0.0) * 100
                if gpt_error_rate > CONFIG["alert_gpt_error_rate"]:
                    async with alert_lock:
                        last_alert = ALERT_HISTORY.get("gpt_error")
                        if last_alert is None or (now - last_alert).total_seconds() > (ALERT_COOLDOWN_HOURS * 3600):
                            await send_alert(
                                f"⚠️ High GPT error rate: {gpt_error_rate:.1f}%\n"
                                f"GPT calls: {METRICS['gpt_calls']}, Errors: {METRICS['gpt_errors']}",
                                bot
                            )
                            ALERT_HISTORY["gpt_error"] = now
        
        # Проверка отсутствия сигналов
        async with stats_lock:
            last_signal_time = STATS.get("last_signal_time")
        
        if last_signal_time:
            hours_without_signals = (now - last_signal_time).total_seconds() / 3600
            if hours_without_signals >= CONFIG["alert_no_signals_hours"]:
                async with alert_lock:
                    last_alert = ALERT_HISTORY.get("no_signals")
                    if last_alert is None or (now - last_alert).total_seconds() > (ALERT_COOLDOWN_HOURS * 3600):
                        await send_alert(
                            f"⚠️ No signals generated for {hours_without_signals:.1f} hours\n"
                            f"Last signal: {last_signal_time.strftime('%Y-%m-%d %H:%M:%S')}",
                            bot
                        )
                        ALERT_HISTORY["no_signals"] = now
    except Exception as e:
        logging.error(f"Error in health check: {e}")

