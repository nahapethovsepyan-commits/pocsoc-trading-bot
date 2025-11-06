"""
Signal messaging and user communication.
"""

import asyncio
import logging
from typing import Dict, Any, Tuple, Optional
from ..config import CONFIG
from ..models.state import SUBSCRIBED_USERS, STATS, SIGNAL_HISTORY, user_languages, stats_lock, history_lock
from ..database import save_signal_to_db
from ..utils.helpers import safe_divide, format_time
from .utils import get_local_time, clean_markdown


async def send_signal_to_user(
    chat_id: int,
    signal_data: Dict[str, Any],
    safe_reasoning: str,
    bot,
    TEXTS: Dict
) -> Tuple[int, bool]:
    """
    Send signal to a single user (helper for parallel sending).
    
    Args:
        chat_id: Telegram chat ID
        signal_data: Signal data
        safe_reasoning: Cleaned reasoning text
        bot: Telegram bot instance
        TEXTS: Localization dictionary
        
    Returns:
        Tuple of (chat_id, success: bool)
    """
    try:
        user_lang = user_languages.get(chat_id, 'ru')
        t = TEXTS.get(user_lang, TEXTS['ru'])
        
        if signal_data["signal"] == "NO_SIGNAL":
            text = f"❌ {t['signal_why_no']}\n"
            text += f"📊 {t['signal_score'].format(score=signal_data['score'])}\n"
            text += f"🎯 {t['signal_conf'].format(conf=signal_data['confidence'])}\n"
            
            if "indicators" in signal_data and signal_data["indicators"]:
                indicators = signal_data["indicators"]
                text += f"\n📈 {t['indicators']}\n"
                text += f"RSI: {indicators.get('rsi', 'N/A')} | MACD: {indicators.get('macd', 'N/A')}\n"
            
            if safe_reasoning:
                text += f"\n🤖 {safe_reasoning}\n"
        else:
            current_price = signal_data["price"]
            atr = signal_data.get("atr")
            
            # Calculate SL/TP
            if atr and atr > 0:
                if signal_data["signal"] == "BUY":
                    sl = current_price - (atr * CONFIG["atr_sl_multiplier"])
                    tp = current_price + (atr * CONFIG["atr_tp_multiplier"])
                else:
                    sl = current_price + (atr * CONFIG["atr_sl_multiplier"])
                    tp = current_price - (atr * CONFIG["atr_tp_multiplier"])
            else:
                if signal_data["signal"] == "BUY":
                    sl = current_price * (1 - CONFIG["stop_loss_pct"])
                    tp = current_price * (1 + CONFIG["take_profit_pct"])
                else:
                    sl = current_price * (1 + CONFIG["stop_loss_pct"])
                    tp = current_price * (1 - CONFIG["take_profit_pct"])
            
            score = signal_data.get("score", 50)
            confidence = signal_data.get("confidence", 60)
            
            # Expiration based on ATR
            if atr and atr > 0:
                atr_pct = safe_divide(atr, current_price, 0.1) * 100
                if atr_pct < 0.05:
                    expiration_minutes = 5
                elif atr_pct < 0.10:
                    expiration_minutes = 3
                else:
                    expiration_minutes = 1
            else:
                expiration_minutes = 3
            
            # Bet size based on score and confidence
            if score >= 70 and confidence >= 65:
                bet_percent = 5.0
            elif score >= 65 and confidence >= 60:
                bet_percent = 3.5
            elif score >= 55 and confidence >= 60:
                bet_percent = 3.0
            else:
                bet_percent = 2.0
            
            suggested_amount = bet_percent * 10
            
            # Risk level
            if score >= 70 and confidence >= 65:
                risk_level = t['risk_low']
                risk_emoji = "🟢"
            elif score >= 60:
                risk_level = t['risk_medium']
                risk_emoji = "🟡"
            else:
                risk_level = t['risk_high']
                risk_emoji = "🔴"
            
            text = f"🚨 {t['signal_alert']}\n\n"
            text += f"{t['signal_pair']}\n"
            text += f"{t['signal_action'].format(action=signal_data['signal'])}\n"
            text += f"{t['signal_price'].format(price=current_price)}\n"
            text += f"{t['signal_score'].format(score=signal_data['score'])}\n"
            text += f"{t['signal_conf'].format(conf=signal_data['confidence'])}\n"
            
            if "indicators" in signal_data and signal_data["indicators"]:
                indicators = signal_data["indicators"]
                text += f"📈 {t['indicators']}\n"
                text += f"RSI: {indicators.get('rsi', 'N/A')} | MACD: {indicators.get('macd', 'N/A')}\n"
                if indicators.get('bb_position') is not None:
                    text += f"BB Position: {indicators.get('bb_position', 'N/A')}% | ADX: {indicators.get('adx', 'N/A')}\n"
                if indicators.get('stoch_k') is not None:
                    text += f"Stoch: K={indicators.get('stoch_k', 'N/A')}, D={indicators.get('stoch_d', 'N/A')}\n"
                text += "\n"
            
            text += f"🎲 {t['signal_po_rec']}\n"
            text += f"⏱️ {t['signal_exp'].format(exp=expiration_minutes)}\n"
            text += f"💵 {t['signal_bet'].format(bet=bet_percent)}\n"
            text += f"💰 {t['signal_suggested'].format(suggested=suggested_amount)}\n"
            text += f"{risk_emoji} {t['signal_risk'].format(risk=risk_level)}\n\n"
            
            text += f"⚙️ {t['signal_risk_mgmt']}\n"
            text += f"🛑 {t['signal_sl'].format(sl=sl)}\n"
            text += f"🎯 {t['signal_tp'].format(tp=tp)}\n"
            text += f"📊 {t['signal_rr'].format(rr=CONFIG['risk_reward_ratio'])}\n\n"
            
            if safe_reasoning and safe_reasoning != "GPT analysis disabled.":
                text += f"📊 {t['signal_analysis']}\n🤖 GPT: {safe_reasoning}\n"
        
        text += f"\n⏰ {format_time(get_local_time())}"
        
        await bot.send_message(chat_id, text, parse_mode=None)
        logging.info(f"✓ Signal sent to user {chat_id} (lang: {user_lang})")
        return (chat_id, True)
    except Exception as e:
        logging.error(f"Failed to send signal to {chat_id}: {e}")
        return (chat_id, False)


async def send_signal_message(
    signal_data: Dict[str, Any],
    lang: str = 'ru',
    bot=None,
    TEXTS: Optional[Dict] = None
) -> None:
    """
    Отправка сигнала всем подписанным пользователям на их языках.
    
    Args:
        signal_data: Словарь с данными сигнала
        lang: Язык по умолчанию
        bot: Telegram bot instance (required)
        TEXTS: Localization dictionary (required)
    """
    if bot is None or TEXTS is None:
        logging.error("send_signal_message: bot and TEXTS must be provided")
        return
        
    try:
        safe_reasoning = clean_markdown(signal_data["reasoning"]) if signal_data["reasoning"] else ""
        
        if not SUBSCRIBED_USERS:
            logging.warning("No subscribed users to send signal to")
            return
        
        users_snapshot = list(SUBSCRIBED_USERS.copy())
        send_tasks = [
            send_signal_to_user(chat_id, signal_data, safe_reasoning, bot, TEXTS)
            for chat_id in users_snapshot
        ]
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        failed_sends = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Unexpected error during parallel send: {result}")
            elif isinstance(result, tuple):
                chat_id, success = result
                if not success:
                    failed_sends.append(chat_id)
        
        if failed_sends:
            SUBSCRIBED_USERS.difference_update(failed_sends)
            logging.info(f"Removed {len(failed_sends)} users from subscribers (send failed)")
        
        if signal_data["signal"] != "NO_SIGNAL":
            async with stats_lock:
                STATS["total_signals"] += 1
                signal_type = signal_data["signal"]
                if signal_type in STATS:
                    STATS[signal_type] += 1
                if "GPT" in signal_data.get("reasoning", ""):
                    STATS["AI_signals"] += 1
            
            async with history_lock:
                SIGNAL_HISTORY.append(signal_data)
            
            asyncio.create_task(save_signal_to_db(signal_data))
                
    except Exception as e:
        logging.error(f"Error sending signal message: {e}")
