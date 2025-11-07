"""
Application configuration settings.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from .env import get_openai_client

# Initialize GPT client
_openai_client, _use_gpt = get_openai_client()

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    "pair": "EUR/USD",
    "api_source": "twelvedata",
    "analysis_interval_minutes": 2,
    "min_signal_score": 60,  # Tuned: allow strong setups to pass with relaxed TA filters
    "min_confidence": 65,    # Tuned: maintain quality but permit more trades
    "use_gpt": _use_gpt,
    "gpt_weight": 0.35,      # Уменьшен вес GPT
    "ta_weight": 0.65,       # Увеличен вес технического анализа
    "lookback_window": 60,
    "max_signals_per_hour": 12,  # Увеличен лимит сигналов
    "max_sell_score": 40,       # Base SELL threshold (can tighten via adaptive thresholds)
    "risk_reward_ratio": 1.8,
    "cache_duration_seconds": 90,
    # Magic numbers вынесены в конфиг
    "stop_loss_pct": 0.002,      # 0.2% от цены для Stop Loss (fallback)
    "take_profit_pct": 0.002,   # 0.2% от цены для Take Profit (fallback)
    "atr_sl_multiplier": 2.0,    # Множитель ATR для Stop Loss (2x ATR)
    "atr_tp_multiplier": 2.5,    # Множитель ATR для Take Profit (2.5x ATR для R:R 1.8)
    "history_max_size": 100,     # Максимальный размер истории сигналов
    "history_display_limit": 10,  # Количество сигналов для отображения в /history
    "backtest_min_signals": 10,   # Минимум сигналов для backtesting
    "default_price": 1.0800,     # Fallback цена если API недоступен
    # Фильтр по времени торговли
    "trading_hours_enabled": True,  # Включить фильтр по времени
    "trading_start_hour": 0,       # Начало торговли (UTC): 0:00 (круглосуточно)
    "trading_end_hour": 23,        # Конец торговли (UTC): 23:59 (круглосуточно)
    # Система алертов
    "alert_api_error_rate": 10.0,  # Порог ошибок API для алерта (%)
    "alert_gpt_error_rate": 20.0,  # Порог ошибок GPT для алерта (%)
    "alert_no_signals_hours": 2,   # Часы без сигналов для алерта
    # Магические числа вынесены в конфиг
    "exponential_backoff_base": 2,  # База для exponential backoff (2^attempt)
    # Часовой пояс для отображения времени (смещение от UTC в часах)
    "timezone_offset": 4,  # UTC+4 (например, Армения, Грузия, Дубай)
    # Пороговые значения индикаторов (вынесены из кода для легкой настройки)
    "rsi_oversold": 40,
    "rsi_overbought": 60,
    "rsi_strong_oversold": 30,
    "rsi_strong_overbought": 70,
    "bb_oversold": 30,
    "bb_overbought": 70,
    "bb_strong_oversold": 20,
    "bb_strong_overbought": 80,
    "adx_trend_threshold": 25,
    "stoch_oversold": 30,
    "stoch_overbought": 70,
    "stoch_strong_oversold": 20,
    "stoch_strong_overbought": 80,
    # FIXED: New thresholds for binary options (stronger requirements)
    "rsi_very_oversold": 35,      # Was 40 - stronger requirement
    "rsi_very_overbought": 65,    # Was 60 - stronger requirement
    "macd_strong_threshold": 0.0002,  # Was 0.0001 - stronger requirement
    "min_confirmations": 4,       # Minimum indicator confirmations required
    "require_momentum": True,      # Require price momentum alignment
    "require_trend_alignment": True,  # Require trend alignment for strong trends
    "momentum_penalty_score": 7,   # Score penalty when momentum opposes signal
    "momentum_penalty_confidence": 5,  # Confidence penalty when momentum opposes signal
    # Per-user rate limiting
    "max_user_commands_per_minute": 10,  # Maximum commands per user per minute
    # Error message configuration
    "error_message_max_length": 100,  # Maximum length for error messages (prevents info leakage)
}

# Lock for thread-safe config updates
config_lock = asyncio.Lock()


def get_config(key: str, default: Any = None) -> Any:
    """
    Get configuration value by key.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    return CONFIG.get(key, default)


async def update_config(key: str, value: Any, user_id: int = None) -> bool:
    """
    Update configuration value (thread-safe).
    
    Args:
        key: Configuration key
        value: New value
        user_id: Optional user ID for audit logging
        
    Returns:
        bool: True if update successful
    """
    async with config_lock:
        if key in CONFIG:
            old_value = CONFIG[key]
            CONFIG[key] = value
            # Audit logging if user_id provided
            if user_id is not None:
                try:
                    from ..utils.audit import log_config_change
                    await log_config_change(user_id, key, old_value, value)
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to log config change to audit: {e}")
            return True
        return False


