"""
Application configuration settings.
"""

import asyncio
from typing import Dict, Any
from .env import get_openai_client

# Default GPT prompt configuration (can be overridden via CONFIG)
DEFAULT_GPT_SYSTEM_PROMPT = (
    "Ты даешь только торговые сигналы. Отвечай одним словом: BUY, SELL или NO_SIGNAL."
)

DEFAULT_GPT_PROMPT_TEMPLATE = (
    "Ты трейдер-аналитик. Дай четкий торговый сигнал для {pair} на основе индикаторов:\n"
    "RSI: {rsi:.1f} ({rsi_state})\n"
    "MACD: {macd:.5f} ({macd_state})\n"
    "Цена: {price:.5f}\n\n"
    "Ответь ТОЛЬКО одним словом: BUY, SELL или NO_SIGNAL"
)

# Default CandlesTutor system prompt
DEFAULT_CANDLESTUTOR_SYSTEM_PROMPT = (
    "Ты специалист по анализу японских свечей (CandlesTutor). "
    "Твоя задача - анализировать свечные паттерны на основе знаний из прикрепленной книги по японским свечам.\n\n"
    "Когда вход представляет собой JSON вида "
    "{\"symbol\": \"...\", \"timeframe\": \"...\", \"last_candles\": [...], "
    "\"indicators\": {...}, \"candidate_signal\": \"...\", \"ta_score\": ...}, "
    "используй знания из прикрепленной книги по японским свечам.\n"
    "- Определи, есть ли четкие свечные паттерны (например, молот, падающая звезда, поглощение, звезда и т.п.).\n"
    "- Оцени, подтверждают ли они направление candidate_signal.\n"
    "- Всегда отвечай СТРОГО в JSON следующего формата без текста вокруг:\n"
    "{\"decision\":\"BUY|SELL|NO_TRADE\",\"pattern\":\"название паттерна или 'нет'\","
    "\"confidence\":0-100,\"comment\":\"краткое объяснение\"}.\n\n"
    "decision: BUY если свечной анализ согласен с candidate_signal, SELL если видит противоположный сценарий, "
    "NO_TRADE если нет четкого паттерна или лучше пропустить.\n"
    "pattern: название опознанного паттерна (молот, повешенный, поглощение, звезда и т.п.) или 'нет'.\n"
    "confidence: уверенность свечного анализа от 0 до 100.\n"
    "comment: короткое человеческое объяснение (например, 'Молот после даунтренда, подтверждение следующей свечой, поддерживает BUY')."
)

# Initialize GPT client
_openai_client, _use_gpt = get_openai_client()

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    "pair": "EUR/USD",  # Keep for backward compatibility
    "symbols": ["EURUSD", "XAUUSD"],  # Supported symbols
    "user_symbols": {},  # Per-user symbol preference {chat_id: "EURUSD"}
    "api_source": "twelvedata",
    "analysis_interval_minutes": 2,
    "min_signal_score": 60,  # Tuned: allow strong setups to pass with relaxed TA filters
    "min_confidence": 65,    # Tuned: maintain quality but permit more trades
    "use_gpt": _use_gpt,
    "gpt_weight": 0.10,      # GPT участвует как фильтр и объяснение
    "ta_weight": 0.90,       # Технический анализ определяет основное решение
    "gpt_weight_min": 0.05,  # Минимальный допустимый вес GPT
    "gpt_weight_max": 0.15,  # Максимальный допустимый вес GPT
    "gpt_model": "gpt-4o-mini",
    "gpt_temperature": 0.1,
    "gpt_max_tokens": 10,
    "gpt_request_timeout": 3.0,
    "gpt_wait_timeout": 2.0,
    "gpt_prompt_template": DEFAULT_GPT_PROMPT_TEMPLATE,
    "gpt_system_prompt": DEFAULT_GPT_SYSTEM_PROMPT,
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
    # Фильтр по времени торговли (все значения в UTC)
    "trading_hours_enabled": True,  # Включить фильтр по времени
    "trading_start_hour": 0,       # Начало торговли в UTC: 0:00 (круглосуточно)
    "trading_end_hour": 23,        # Конец торговли в UTC: 23:59 (круглосуточно)
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
    "max_user_commands_per_minute": 60,  # Allow up to 60 manual requests per minute (1 per second)
    "user_rate_limit_window_seconds": 60,  # Sliding window for rate limiting
    # Error message configuration
    "error_message_max_length": 100,  # Maximum length for error messages (prevents info leakage)
    # Signal expiration tuning
    "atr_low_vol_threshold": 0.05,      # ATR% below this is considered low volatility
    "atr_mid_vol_threshold": 0.10,      # ATR% below this (but above low) is mid volatility
    "atr_high_vol_threshold": 0.20,     # ATR% below this (but above mid) is high volatility
    "atr_extreme_vol_threshold": 0.40,  # ATR% below this (but above high) is extreme volatility
    "atr_ultra_vol_threshold": 0.80,    # ATR% above this treated as ultra volatility
    "expiration_minutes_low_vol": 3,    # Calm markets
    "expiration_minutes_mid_vol": 2,    # Normal volatility
    "expiration_minutes_high_vol": 1,   # Elevated volatility
    "default_expiration_minutes": 2,    # When ATR unavailable
    "max_expiration_minutes": 3,        # Hard ceiling to avoid long exp times
    "expiration_button_seconds": [5, 10, 30, 60, 120, 180],
    "expiration_button_layout": [
        [5, 10, 30],
        [60, 120, 180]
    ],
    "expiration_strategy": "atr",       # 'atr' or 'manual'
    # Cache configuration
    "cache_max_size": 20,               # Maximum entries in API cache (LRU eviction)
    "indicator_cache_max_size": 10,     # Maximum entries in indicator cache
    "indicator_cache_ttl_seconds": 30,  # Time-to-live for indicator cache entries
    # Symbol-specific configurations
    "symbol_configs": {
        "EURUSD": {
            "min_signal_score": 60,
            "min_confidence": 65,
            "atr_multiplier": 1.5,
            "expiration_button_seconds": [60, 120, 180],  # Только минуты для EUR/USD (PocketOption минимум 1 мин)
            "expiration_button_layout": [[60, 120, 180]],  # Одна строка с минутами
        },
        "XAUUSD": {
            "min_signal_score": 65,  # Higher threshold for volatile gold
            "min_confidence": 70,
            "atr_multiplier": 2.0,  # Larger ATR multiplier for gold
            "expiration_button_seconds": [5, 10, 30, 60, 120, 180],  # Все опции для золота
            "expiration_button_layout": [[5, 10, 30], [60, 120, 180]],  # Две строки
        },
    },
    # CandlesTutor configuration
    "candlestutor_enabled": True,  # Включить интеграцию CandlesTutor
    "candlestutor_min_score_gap": 3,  # Минимальный отступ ta_score от порога для вызова GPT
    "candlestutor_min_confidence": 60,  # Минимальный confidence от CandlesTutor для подтверждения
    "candlestutor_cooldown_minutes": 2,  # Cooldown между запросами для одного символа
    "candlestutor_system_prompt": DEFAULT_CANDLESTUTOR_SYSTEM_PROMPT,
    "candlestutor_combine_confidence": True,  # Комбинировать TA confidence + свечной confidence
    "candlestutor_ta_weight": 0.7,  # Вес TA confidence при комбинировании
    "candlestutor_candle_weight": 0.3,  # Вес свечного confidence (должно быть 1.0 в сумме с ta_weight)
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


