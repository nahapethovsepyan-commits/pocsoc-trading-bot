"""
Application state management (global variables, locks, caches).
"""

import asyncio
from datetime import datetime
from collections import deque, OrderedDict
from typing import Set, Dict, Any, Optional, List

# Global State
SUBSCRIBED_USERS: Set[int] = set()  # Множество подписанных пользователей (chat_id)

STATS: Dict[str, Any] = {
    "BUY": 0, 
    "SELL": 0, 
    "AI_signals": 0,
    "total_signals": 0,
    "wins": 0,
    "losses": 0,
    "last_signal_time": None,
    "signals_per_hour": 0,
    "hour_start": datetime.now()
}

SIGNAL_HISTORY: deque = deque(maxlen=100)  # Will be updated from CONFIG
user_languages: Dict[int, str] = {}
user_expiration_preferences: Dict[int, int] = {}  # chat_id -> expiration seconds override

# Locks для thread-safe доступа к глобальному состоянию
stats_lock = asyncio.Lock()
history_lock = asyncio.Lock()
config_lock = asyncio.Lock()
user_rate_lock = asyncio.Lock()

# Глобальный HTTP session для переиспользования
http_session: Optional[Any] = None

# Кеш для API ответов (LRU с ограничением размера)
API_CACHE: OrderedDict = OrderedDict()
# CACHE_MAX_SIZE is now loaded from CONFIG in repository.py
CACHE_MAX_SIZE = 10  # Default fallback value
cache_lock = asyncio.Lock()

# Кеш для последнего ATR (для адаптивного кеширования)
LAST_ATR_VALUE: Optional[float] = None
last_atr_lock = asyncio.Lock()

# Кеш для индикаторов (для избежания повторных вычислений)
INDICATOR_CACHE: OrderedDict = OrderedDict()
# INDICATOR_CACHE_MAX_SIZE is now loaded from CONFIG
INDICATOR_CACHE_MAX_SIZE = 5  # Default fallback value
indicator_cache_lock = asyncio.Lock()

# Метрики для мониторинга
METRICS: Dict[str, Any] = {
    "api_calls": 0,
    "api_errors": 0,
    "api_cache_hits": 0,
    "api_cache_misses": 0,
    "signals_generated": 0,
    "gpt_calls": 0,
    "gpt_errors": 0,
    "gpt_success": 0,
    "avg_response_time": 0.0,
    "total_response_time": 0.0,
    "response_count": 0,
    "start_time": datetime.now(),
}
metrics_lock = asyncio.Lock()

# Отслеживание отправленных алертов для дедупликации
ALERT_HISTORY: Dict[str, Optional[datetime]] = {
    "api_error": None,
    "gpt_error": None,
    "no_signals": None,
}
ALERT_COOLDOWN_HOURS = 1
alert_lock = asyncio.Lock()

# Per-user rate limiting: track command timestamps per user
USER_RATE_LIMITS: Dict[int, List[datetime]] = {}  # user_id -> list of command timestamps


