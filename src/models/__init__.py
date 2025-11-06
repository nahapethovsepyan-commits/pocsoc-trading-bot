"""
Application state and global variables.
"""

from .state import (
    SUBSCRIBED_USERS,
    STATS,
    SIGNAL_HISTORY,
    user_languages,
    stats_lock,
    history_lock,
    http_session,
    API_CACHE,
    CACHE_MAX_SIZE,
    cache_lock,
    LAST_ATR_VALUE,
    last_atr_lock,
    INDICATOR_CACHE,
    indicator_cache_lock,
    METRICS,
    metrics_lock,
    ALERT_HISTORY,
    ALERT_COOLDOWN_HOURS,
    alert_lock,
)

__all__ = [
    'SUBSCRIBED_USERS',
    'STATS',
    'SIGNAL_HISTORY',
    'user_languages',
    'stats_lock',
    'history_lock',
    'http_session',
    'API_CACHE',
    'CACHE_MAX_SIZE',
    'cache_lock',
    'LAST_ATR_VALUE',
    'last_atr_lock',
    'INDICATOR_CACHE',
    'indicator_cache_lock',
    'METRICS',
    'metrics_lock',
    'ALERT_HISTORY',
    'ALERT_COOLDOWN_HOURS',
    'alert_lock',
]


