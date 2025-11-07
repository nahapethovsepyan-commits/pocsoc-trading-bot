"""
Signal generation utilities.
"""

import re
import logging
from datetime import datetime, timedelta
from ..config import CONFIG
from ..models.state import STATS, stats_lock, USER_RATE_LIMITS, user_rate_lock

def get_local_time():
    """
    Получить локальное время с учетом часового пояса из CONFIG.
    
    Returns:
        Локальное время с учетом часового пояса.
    """
    utc_now = datetime.utcnow()
    offset = timedelta(hours=CONFIG.get("timezone_offset", 0))
    local_time = utc_now + offset
    return local_time


def is_trading_hours():
    """
    Проверка, рабочее ли время для торговли.
    
    Returns:
        True если торговля разрешена, False если вне торговых часов.
    """
    if not CONFIG["trading_hours_enabled"]:
        return True
    
    now = datetime.utcnow()
    hour = now.hour
    
    start_hour = CONFIG["trading_start_hour"]
    end_hour = CONFIG["trading_end_hour"]
    
    if start_hour < end_hour:
        return start_hour <= hour < end_hour
    else:
        return hour >= start_hour or hour < end_hour


async def check_rate_limit():
    """
    Проверка, не превышен ли лимит сигналов в час.
    
    Returns:
        True если лимит не превышен, False если превышен.
    """
    now = datetime.now()
    
    async with stats_lock:
        hour_start = STATS.get("hour_start", now)
        
        if (now - hour_start).total_seconds() > 3600:
            STATS["hour_start"] = now
            STATS["signals_per_hour"] = 0
        
        if STATS["signals_per_hour"] >= CONFIG["max_signals_per_hour"]:
            return False
        
        return True


async def check_user_rate_limit(user_id: int, max_per_minute: int = None, window_seconds: int = None) -> bool:
    """
    Check if user has exceeded rate limit for commands.
    
    Args:
        user_id: Telegram user ID
        max_per_minute: Maximum commands per minute (defaults to CONFIG value)
        
    Returns:
        True if user is within rate limit, False if exceeded
    """
    if max_per_minute is None:
        max_per_minute = CONFIG.get("max_user_commands_per_minute", 60)
    if window_seconds is None:
        window_seconds = CONFIG.get("user_rate_limit_window_seconds", 60)
    
    async with user_rate_lock:
        now = datetime.now()
        
        if user_id not in USER_RATE_LIMITS:
            USER_RATE_LIMITS[user_id] = []
        
        # Remove entries outside sliding window
        USER_RATE_LIMITS[user_id] = [
            ts for ts in USER_RATE_LIMITS[user_id] 
            if (now - ts).total_seconds() < window_seconds
        ]
        
        if len(USER_RATE_LIMITS[user_id]) >= max_per_minute:
            return False
        
        USER_RATE_LIMITS[user_id].append(now)
        return True


async def cleanup_user_rate_limits() -> None:
    """
    Remove entries for users inactive > 1 hour to prevent memory leak.
    This should be called periodically (e.g., every 10 minutes).
    """
    async with user_rate_lock:
        now = datetime.now()
        inactive_users = []
        
        for uid, timestamps in USER_RATE_LIMITS.items():
            if not timestamps:
                # Empty list - can be removed
                inactive_users.append(uid)
            else:
                # Check if most recent timestamp is > 1 hour old
                most_recent = max(timestamps)
                if (now - most_recent).total_seconds() > 3600:
                    inactive_users.append(uid)
        
        # Remove inactive users
        for uid in inactive_users:
            del USER_RATE_LIMITS[uid]
        
        if inactive_users:
            logging.debug(f"Cleaned up {len(inactive_users)} inactive user rate limit entries")


def clean_markdown(text):
    """
    Очистка текста от проблемных символов для Markdown.
    
    Args:
        text: Текст для очистки
        
    Returns:
        Очищенный текст
    """
    if not text:
        return text
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


