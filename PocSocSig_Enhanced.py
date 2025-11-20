"""
Enhanced EUR/USD Trading Signal Bot with GPT Analysis
=====================================================
Features:
- Multiple forex API sources (Twelve Data, Alpha Vantage)
- GPT-4o-mini AI analysis (replaces LSTM)
- Advanced technical indicators (BB, ADX, Stochastic, ATR, RSI, MACD)
- Hybrid scoring system: GPT (10%) + Technical Analysis (90%)
- PocketOption binary options recommendations
- Risk management (Stop Loss, Take Profit)
- Performance tracking

Optimized for binary options trading on PocketOption.
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import warnings
import signal
import sys
from datetime import datetime, timedelta, timezone
from collections import deque
import re
import io
import csv
import aiosqlite as _aiosqlite

# Telegram imports
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram.exceptions import TelegramConflictError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Module imports - Phase 2 refactoring
from src.config import CONFIG, get_bot_token, get_api_keys, get_openai_client as _get_openai_client
from src.models.state import (
    SUBSCRIBED_USERS, STATS, SIGNAL_HISTORY, user_languages,
    user_expiration_preferences,
    stats_lock, history_lock, config_lock, USER_RATE_LIMITS, user_rate_lock,
    CACHE_MAX_SIZE, ALERT_HISTORY, API_CACHE
)
from src.database import (
    init_database, save_signal_to_db, load_recent_signals_from_db,
    save_stats_to_db, backup_database, DB_PATH,
    add_subscriber_to_db, remove_subscriber_from_db,
    load_subscribers_into_state
)
from src.api import fetch_forex_data
from src.signals import generate_signal, main_analysis
from src.signals import messaging as messaging_module
from src.monitoring import (
    check_system_health as monitor_check_system_health,
    send_alert as monitor_send_alert
)
from src.telegram import TEXTS, get_main_keyboard, language_keyboard, get_expiration_keyboard, get_symbol_keyboard
from src.telegram.decorators import require_subscription, with_error_handling, get_user_locale
from src.utils.http_session import close_http_session, get_http_session, http_session
from src.utils.helpers import sanitize_user_input, validate_config_input
from src.utils.audit import log_config_change, log_security_event, log_admin_action
from src.signals import utils as signal_utils_module
from src.signals.utils import (
    check_user_rate_limit,
    cleanup_user_rate_limits,
    clean_markdown,
)
from typing import Tuple, Optional, Any, Union, Set

# Backwards compatibility for tests expecting these symbols at module scope
from src.models.state import METRICS  # re-export shared metrics dictionary
get_openai_client = _get_openai_client  # re-export GPT client getter for tests

# Фильтруем warnings
warnings.filterwarnings("ignore")

# Re-export modules expected by tests
aiosqlite = _aiosqlite


def is_trading_hours():
    """Backwards-compatible wrapper that honors patched datetime in tests."""
    signal_utils_module.datetime = datetime
    return signal_utils_module.is_trading_hours()


def get_local_time():
    """Backwards-compatible wrapper that honors patched datetime/timedelta in tests."""
    signal_utils_module.datetime = datetime
    signal_utils_module.timedelta = timedelta
    return signal_utils_module.get_local_time()


async def send_signal_message(
    signal_data,
    lang: str = 'ru',
    bot=None,
    TEXTS=None
):
    """Wrapper that defaults to global bot/TEXTS for older tests."""
    active_bot = bot or globals().get("bot")
    texts = TEXTS if TEXTS is not None else globals().get("TEXTS")
    if active_bot is None or texts is None:
        raise ValueError("bot and TEXTS must be provided to send_signal_message")
    return await messaging_module.send_signal_message(
        signal_data,
        lang=lang,
        bot=active_bot,
        TEXTS=texts
    )


async def send_signal_to_user(
    chat_id,
    signal_data,
    safe_reasoning,
    bot=None,
    TEXTS=None
):
    """Wrapper to maintain original signature for tests."""
    active_bot = bot or globals().get("bot")
    texts = TEXTS if TEXTS is not None else globals().get("TEXTS")
    if active_bot is None or texts is None:
        raise ValueError("bot and TEXTS must be provided to send_signal_to_user")
    return await messaging_module.send_signal_to_user(
        chat_id,
        signal_data,
        safe_reasoning,
        active_bot,
        texts
    )


async def send_alert(message_text: str, bot=None):
    """Wrapper that defaults to global bot for compatibility."""
    active_bot = bot or globals().get("bot")
    if active_bot is None:
        raise ValueError("bot must be available to send alerts")
    return await monitor_send_alert(message_text, active_bot)


async def check_system_health(bot=None):
    """Wrapper that defaults to global bot for compatibility."""
    active_bot = bot or globals().get("bot")
    if active_bot is None:
        raise ValueError("bot must be available to run health checks")
    return await monitor_check_system_health(active_bot)


# ==================== BOT INITIALIZATION ====================

# Get bot token and initialize bot
BOT_TOKEN = get_bot_token()
TWELVE_DATA_KEY, ALPHA_VANTAGE_KEY = get_api_keys()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# ==================== LOGGING SETUP ====================

from logging.handlers import RotatingFileHandler
import os  # Required for os.getenv() and os.makedirs()

# Admin configuration
ADMIN_USER_IDS: Set[int] = set()
_admin_env = os.getenv("ADMIN_USER_IDS", "").strip()
if _admin_env:
    try:
        ADMIN_USER_IDS = {
            int(user_id.strip())
            for user_id in _admin_env.split(",")
            if user_id.strip()
        }
        logging.info(f"✓ Loaded {len(ADMIN_USER_IDS)} admin chat IDs for rate reset command")
    except ValueError:
        logging.warning("⚠️  ADMIN_USER_IDS contains invalid values. Falling back to no admin restriction.")
        ADMIN_USER_IDS = set()


def is_admin(user_id: int) -> bool:
    """Check if user is an administrator."""
    return user_id in ADMIN_USER_IDS


# Настройка логирования с ротацией файлов
handlers = [logging.StreamHandler()]

# Добавляем файловое логирование с ротацией (только локально, не на Render)
if os.getenv('RENDER') is None:
    try:
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler(
            'logs/enhanced_bot.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        handlers.append(file_handler)
        logging.info("✓ File logging enabled with rotation (logs/enhanced_bot.log)")
    except Exception as e:
        logging.warning(f"⚠️  Could not setup file logging: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Проверка API ключей (после настройки логирования)
if not TWELVE_DATA_KEY and not ALPHA_VANTAGE_KEY:
    logging.warning("⚠️ No forex API keys found - please set TWELVE_DATA_API_KEY or ALPHA_VANTAGE_KEY in .env")

# Import helper functions from modules
from src.utils.helpers import safe_divide, is_successful_status, format_time, sanitize_user_input
from src.signals.utils import check_rate_limit

# ==================== COMMAND HANDLERS ====================

@dp.message(Command("start"))
async def start_handler(message):
    """
    Обработчик команды /start - подписка пользователя на сигналы.
    
    Добавляет пользователя в список подписанных (SUBSCRIBED_USERS) и отправляет
    приветственное сообщение с инструкциями по использованию бота.
    
    Args:
        message (aiogram.types.Message): Сообщение от пользователя с командой /start.
        
    Note:
        - Добавляет chat_id в SUBSCRIBED_USERS
        - Отправляет приветственное сообщение с выбором языка
        - Показывает клавиатуру с основными кнопками
        - Устанавливает язык по умолчанию 'ru'
        
    Example:
        >>> # Вызывается автоматически при команде /start
        >>> # Пользователь отправляет /start в Telegram
    """
    chat_id = message.chat.id
    
    # Добавляем пользователя в список подписчиков
    SUBSCRIBED_USERS.add(chat_id)
    default_lang = user_languages.get(chat_id, 'ru')
    user_languages[chat_id] = default_lang
    CONFIG["user_symbols"][chat_id] = "EURUSD"  # Default symbol
    logging.info(f"User {chat_id} subscribed to signals")

    try:
        await add_subscriber_to_db(
            chat_id,
            default_lang,
            user_expiration_preferences.get(chat_id)
        )
    except Exception as e:
        logging.error(f"Failed to persist subscriber {chat_id}: {e}")
    
    await message.answer(TEXTS['ru']['choose_language'], reply_markup=language_keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def language_handler(callback):
    """
    Обработчик выбора языка пользователем.
    
    Устанавливает язык интерфейса для пользователя и отправляет подтверждение.
    
    Args:
        callback (aiogram.types.CallbackQuery): Callback от inline кнопки выбора языка.
            Ожидается формат callback.data = "lang_<код_языка>" (например, "lang_ru").
            
    Note:
        - Сохраняет выбранный язык в user_languages[chat_id]
        - Отправляет подтверждение выбора языка
        - Показывает главную клавиатуру на выбранном языке
        - Поддерживаемые языки: 'ru', 'en'
        
    Example:
        >>> # Вызывается при нажатии на inline кнопку выбора языка
        >>> # Callback data: "lang_ru" или "lang_en"
    """
    lang = callback.data.split("_")[1]
    user_languages[callback.message.chat.id] = lang
    t = TEXTS[lang]

    try:
        await add_subscriber_to_db(
            callback.message.chat.id,
            lang,
            user_expiration_preferences.get(callback.message.chat.id)
        )
    except Exception as e:
        logging.error(f"Failed to update subscriber {callback.message.chat.id} language: {e}")
    
    await callback.message.answer(t['welcome'], reply_markup=get_main_keyboard(lang), parse_mode=None)
    await callback.answer()
    

@dp.message(Command("metrics"))
@require_subscription
@with_error_handling
async def metrics_handler(message):
    """Display performance metrics and API statistics.
    
    Shows API calls, response times, cache hit rates, GPT usage, and health status.
    """
    lang, t = get_user_locale(message)
    async with metrics_lock:
        uptime = (datetime.now() - METRICS["start_time"]).total_seconds()
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        # Calculate success rates
        total_api = METRICS["api_calls"] + METRICS["api_errors"]
        api_success_rate = safe_divide(METRICS["api_calls"], total_api, 0.0) * 100
        
        # Calculate GPT success rate
        total_gpt = METRICS["gpt_calls"]
        gpt_success_rate = safe_divide(METRICS["gpt_success"], total_gpt, 0.0) * 100
        
        # Calculate cache efficiency
        total_cache = METRICS["api_cache_hits"] + METRICS["api_cache_misses"]
        cache_hit_rate = safe_divide(METRICS["api_cache_hits"], total_cache, 0.0) * 100
        
        text = "📊 **Metrics / Метрики**\n\n"
        text += f"⏱️ Uptime: {hours}h {minutes}m\n"
        text += f"📡 API Calls: {METRICS['api_calls']}\n"
        text += f"❌ API Errors: {METRICS['api_errors']}\n"
        text += f"✅ API Success Rate: {api_success_rate:.1f}%\n"
        text += f"⚡ Avg Response Time: {METRICS['avg_response_time']:.2f}s\n\n"
        text += f"💾 Cache Hits: {METRICS['api_cache_hits']}\n"
        text += f"💾 Cache Misses: {METRICS['api_cache_misses']}\n"
        text += f"📈 Cache Hit Rate: {cache_hit_rate:.1f}%\n\n"
        text += f"🤖 GPT Calls: {METRICS['gpt_calls']}\n"
        text += f"✅ GPT Success: {METRICS['gpt_success']}\n"
        text += f"❌ GPT Errors: {METRICS['gpt_errors']}\n"
        text += f"📊 GPT Success Rate: {gpt_success_rate:.1f}%\n\n"
        text += f"📈 Signals Generated: {METRICS['signals_generated']}\n"
        text += f"👥 Subscribed Users: {len(SUBSCRIBED_USERS)}\n"
    
    await message.answer(text, parse_mode=None)

@dp.message(Command("stop"))
async def stop_handler(message):
    """Stop command handler - отписка пользователя"""
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, 'ru')
    t = TEXTS[lang]
    
    if chat_id in SUBSCRIBED_USERS:
        SUBSCRIBED_USERS.remove(chat_id)
        try:
            await remove_subscriber_from_db(chat_id)
        except Exception as e:
            logging.error(f"Failed to remove subscriber {chat_id} from database: {e}")
        user_expiration_preferences.pop(chat_id, None)
        CONFIG["user_symbols"].pop(chat_id, None)
        await message.answer(t['unsubscribed'])
        logging.info(f"User {chat_id} unsubscribed from signals")
    else:
        await message.answer(t['not_subscribed'])

async def _run_manual_signal(chat_id: int, lang: str, t: dict) -> None:
    """
    Trigger manual signal generation after user chooses expiration.
    """
    from src.utils.symbols import normalize_symbol
    
    # Get and normalize symbol to ensure consistency
    raw_symbol = CONFIG["user_symbols"].get(chat_id, "EURUSD")
    logging.info(f"Generating signal for user {chat_id}: raw_symbol={raw_symbol}, stored symbols={CONFIG['user_symbols'].get(chat_id)}")
    try:
        symbol = normalize_symbol(raw_symbol)
        logging.info(f"Normalized symbol for user {chat_id}: {symbol}")
    except ValueError:
        # Fallback to EURUSD if symbol is invalid
        symbol = "EURUSD"
        CONFIG["user_symbols"][chat_id] = symbol
        logging.warning(f"Invalid symbol '{raw_symbol}' for user {chat_id}, defaulting to EURUSD")
    
    analyzing_msg = None
    try:
        if not await check_rate_limit():
            await bot.send_message(chat_id, t['rate_limit'])
            return
        
        # Формируем сообщение с правильным символом
        from src.utils.symbols import symbol_to_pair
        try:
            pair = symbol_to_pair(symbol)
        except ValueError:
            pair = symbol
        analyzing_msg = await bot.send_message(chat_id, t['analyzing'].format(symbol=pair))
        
        signal_data = await asyncio.wait_for(generate_signal(symbol), timeout=30.0)
        if "symbol" not in signal_data:
            raise ValueError("Signal data does not include 'symbol'")
        if signal_data["signal"] == "NO_SIGNAL":
            no_signal_text = f"❌ {t['signal_why_no']}\n"
            no_signal_text += f"📊 {t['signal_score'].format(score=signal_data['score'])}\n"
            no_signal_text += f"🎯 {t['signal_conf'].format(conf=signal_data['confidence'])}\n"

            if signal_data.get("indicators"):
                indicators = signal_data["indicators"]
                if indicators:
                    no_signal_text += f"\n📈 {t['indicators']}\n"
                    no_signal_text += f"RSI: {indicators.get('rsi', 'N/A')} | MACD: {indicators.get('macd', 'N/A')}\n"

            if signal_data.get("reasoning"):
                safe_reasoning = clean_markdown(signal_data["reasoning"])
                if safe_reasoning:
                    no_signal_text += f"\n🤖 {safe_reasoning}\n"

            no_signal_text += f"\n⏰ {format_time(get_local_time())}"
            await bot.send_message(chat_id, no_signal_text)
        else:
            await send_signal_message(signal_data, lang, bot=bot, TEXTS=TEXTS)
            async with stats_lock:
                STATS["signals_per_hour"] += 1
                STATS["last_signal_time"] = datetime.now()
    except asyncio.TimeoutError:
        await bot.send_message(chat_id, t['timeout'])
    except Exception as e:
        logging.error(f"Error in _run_manual_signal for user {chat_id}: {e}", exc_info=True)
        await bot.send_message(chat_id, t['error'].format(error=str(e)[:100]))
    finally:
        if analyzing_msg:
            try:
                await analyzing_msg.delete()
            except Exception:
                pass


@dp.message(F.text.in_({"📊 СИГНАЛ", "📊 SIGNAL"}))
@require_subscription
async def manual_signal_handler(message):
    """Manual signal request that now requires choosing expiration."""
    lang, t = get_user_locale(message)
    keyboard = get_expiration_keyboard(lang)
    await message.answer(t['select_expiration'], reply_markup=keyboard)


@dp.callback_query(F.data.startswith("exp_select:"))
@require_subscription
async def expiration_select_handler(callback):
    """Handle expiration selection from inline buttons."""
    chat_id = callback.message.chat.id
    lang, t = get_user_locale(callback)

    try:
        _, raw_value = callback.data.split(":")
        selected_seconds = int(raw_value)
    except (ValueError, IndexError):
        await callback.answer(t['expiration_not_supported'], show_alert=True)
        return

    allowed_options = {
        max(1, int(value)) for value in CONFIG.get("expiration_button_seconds", [5, 10, 30, 60, 120, 180])
    }
    if selected_seconds not in allowed_options:
        await callback.answer(t['expiration_not_supported'], show_alert=True)
        return

    user_expiration_preferences[chat_id] = selected_seconds

    try:
        await add_subscriber_to_db(
            chat_id,
            user_languages.get(chat_id, lang),
            selected_seconds
        )
    except Exception as e:
        logging.error(f"Failed to persist expiration for {chat_id}: {e}")

    if selected_seconds >= 60:
        exp_label = t['expiration_button_minutes'].format(value=selected_seconds // 60)
    else:
        exp_label = t['expiration_button_seconds'].format(value=selected_seconds)
    confirmation = t['expiration_saved'].format(exp=exp_label)
    await callback.answer(confirmation, show_alert=False)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Wrap _run_manual_signal in try-except to handle errors and provide user feedback
    try:
        await _run_manual_signal(chat_id, lang, t)
    except Exception as e:
        logging.error(f"Error in expiration_select_handler after selecting expiration: {e}", exc_info=True)
        # Send error message to user
        try:
            await bot.send_message(chat_id, t['error'].format(error=str(e)[:100]))
        except Exception as send_error:
            logging.error(f"Failed to send error message to user {chat_id}: {send_error}")
            # Fallback: try to answer callback with error
            try:
                await callback.answer(t.get('error', '❌ Error occurred').format(error=str(e)[:50]), show_alert=True)
            except Exception:
                pass

@dp.message(Command("symbol"))
@require_subscription
@with_error_handling
async def symbol_handler(message):
    """Handler for /symbol command: show inline keyboard for symbol selection."""
    lang, t = get_user_locale(message)
    keyboard = get_symbol_keyboard(lang)
    await message.answer(t['select_symbol'], reply_markup=keyboard)

@dp.message(F.text.in_({"📈 Активы", "📈 Symbols"}))
@require_subscription
@with_error_handling
async def assets_handler(message):
    """Handler for assets/symbols button - shows symbol selection."""
    await symbol_handler(message)

@dp.callback_query(F.data.startswith("symbol_"))
@require_subscription
async def symbol_select_handler(callback):
    """Handle symbol selection from inline buttons."""
    from src.utils.symbols import normalize_symbol, symbol_to_pair
    
    chat_id = callback.message.chat.id
    lang, t = get_user_locale(callback.message)
    
    try:
        raw_symbol = callback.data.split("_")[1]
        # Normalize symbol before saving (EURUSD, XAUUSD)
        symbol = normalize_symbol(raw_symbol)
    except (IndexError, ValueError) as e:
        logging.error(f"Invalid symbol in callback: {callback.data}, error: {e}")
        await callback.answer(t['invalid_symbol'], show_alert=True)
        return
    
    # Validate symbol (use normalized)
    if symbol not in CONFIG.get("symbols", ["EURUSD", "XAUUSD"]):
        await callback.answer(t['invalid_symbol'], show_alert=True)
        return
    
    # Save user's symbol preference (normalized)
    CONFIG["user_symbols"][chat_id] = symbol
    logging.info(f"User {chat_id} selected symbol: {symbol} (normalized from {raw_symbol})")
    
    # Send confirmation with pair format for display (EUR/USD, XAU/USD)
    try:
        pair = symbol_to_pair(symbol)
        confirmation = f"✅ {t['switched_to']} {pair}"
    except ValueError:
        confirmation = f"✅ {t['switched_to']} {symbol}"
    await callback.answer(confirmation, show_alert=False)
    
    # Remove inline keyboard
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    # Automatically show expiration menu after symbol selection
    keyboard = get_expiration_keyboard(lang)
    pair = symbol_to_pair(symbol)
    await callback.message.answer(
        f"{t['current_symbol'].format(symbol=pair)}\n\n{t['select_expiration']}", 
        reply_markup=keyboard
    )

@dp.message(F.text.in_({"📈 СТАТИСТИКА", "📈 STATISTICS"}))
@require_subscription
@with_error_handling
async def stats_handler(message):
    """Statistics handler"""
    lang, t = get_user_locale(message)
    
    # Thread-safe чтение статистики - минимизируем время блокировки
    async with stats_lock:
        # Быстрое копирование нужных значений
        total = STATS.get('total_signals', 0)
        wins = STATS.get('wins', 0)
        losses = STATS.get('losses', 0)
        buy_count = STATS.get('BUY', 0)
        sell_count = STATS.get('SELL', 0)
        ai_signals = STATS.get('AI_signals', 0)
    
    # Вычисления БЕЗ БЛОКИРОВКИ (после чтения данных)
    win_rate = safe_divide(wins, total, 0.0) * 100
    
    api_source = "Unknown"
    if TWELVE_DATA_KEY:
        api_source = "Twelve Data ✓"
    elif ALPHA_VANTAGE_KEY:
        api_source = "Alpha Vantage ✓"
    else:
        api_source = "No API configured"
    
    text = t['stats_title']
    text += t['stats_total'].format(total=total)
    text += t['stats_call'].format(call=buy_count)
    text += t['stats_put'].format(put=sell_count)
    text += t['stats_ai'].format(ai=ai_signals)
    text += t['stats_wins'].format(wins=wins)
    text += t['stats_losses'].format(losses=losses)
    text += t['stats_winrate'].format(winrate=win_rate)
    text += t['stats_api'].format(api=api_source)
    text += t['stats_interval'].format(interval=CONFIG['analysis_interval_minutes'])
    
    await message.answer(text, parse_mode=None)

@dp.message(F.text.in_({"⚙️ НАСТРОЙКИ", "⚙️ SETTINGS"}))
@require_subscription
@with_error_handling
async def settings_handler(message):
    """Settings handler"""
    lang, t = get_user_locale(message)
    
    text = t['settings_title']
    text += t['settings_min_score'].format(score=CONFIG['min_signal_score'])
    text += t['settings_min_conf'].format(conf=CONFIG['min_confidence'])
    text += t['settings_ai_weight'].format(weight=int(CONFIG.get('gpt_weight', 0.1)*100))
    text += t['settings_rr'].format(rr=CONFIG['risk_reward_ratio'])
    text += t['settings_lookback'].format(lookback=CONFIG['lookback_window'])
    text += t['settings_max_signals'].format(max=CONFIG['max_signals_per_hour'])
    text += f"\n⏰ Trading Hours: {CONFIG['trading_start_hour']}:00-{CONFIG['trading_end_hour']}:00 UTC\n"
    text += f"📊 Trading Hours Filter: {'✅ Enabled' if CONFIG['trading_hours_enabled'] else '❌ Disabled'}\n"
    text += f"📈 Symbols: {', '.join(CONFIG['symbols'])}\n"
    text += "\n💡 To change settings, use:\n"
    text += "/config min_score=55\n"
    text += "/config min_confidence=45\n"
    text += "/config trading_hours=2-22\n"
    text += "/config trading_hours=off\n"
    text += "/config gpt_weight=0.10\n"
    text += "/config gpt_model=gpt-4o\n"
    text += "/config gpt_wait=2.0\n"
    
    await message.answer(text, parse_mode=None)

# Allowed configuration parameters (whitelist for security)
ALLOWED_CONFIG_PARAMS = {
    'min_score',
    'min_confidence',
    'trading_hours',
    'max_signals',
    'gpt_weight',
    'gpt_model',
    'gpt_wait',
    'gpt_timeout',
    'gpt_temperature',
}


def validate_config_value(param: str, value: str) -> Tuple[bool, Optional[Union[int, str, Tuple[int, int]]], Optional[str]]:
    """
    Validate config parameter value.
    
    Args:
        param: Parameter name
        value: Parameter value as string
        
    Returns:
        Tuple of (is_valid, parsed_value, error_message)
        - is_valid: True if validation passed
        - parsed_value: Parsed value (int for numeric params, str "off" or Tuple[int, int] for trading_hours, or None)
        - error_message: Error message if validation failed, None otherwise
    """
    gpt_min = CONFIG.get("gpt_weight_min", 0.05)
    gpt_max = CONFIG.get("gpt_weight_max", 0.15)

    validators = {
        'min_score': (
            lambda v: 0 <= int(v) <= 100,
            int,
            '0-100'
        ),
        'min_confidence': (
            lambda v: 0 <= int(v) <= 100,
            int,
            '0-100'
        ),
        'max_signals': (
            lambda v: int(v) > 0,
            int,
            'positive integer'
        ),
        'gpt_weight': (
            lambda v: gpt_min <= v <= gpt_max,
            float,
            f'{gpt_min:.2f}-{gpt_max:.2f}'
        ),
        'gpt_temperature': (
            lambda v: 0.0 <= float(v) <= 2.0,
            float,
            '0.0-2.0'
        ),
        'gpt_timeout': (
            lambda v: 0.1 <= float(v) <= 30.0,
            float,
            '0.1-30.0 seconds'
        ),
        'gpt_wait': (
            lambda v: 0.1 <= float(v) <= 30.0,
            float,
            '0.1-30.0 seconds'
        ),
        'gpt_model': (
            lambda v: True,
            None,
            'alphanumeric/dash/underscore/dot (3-64 chars)'
        ),
        'trading_hours': (
            lambda v: True,  # Special handling below
            None,
            'start-end (e.g., 2-22) or "off"'
        ),
    }
    
    if param not in validators:
        return False, None, f"Unknown parameter: {param}"
    
    # Special handling for trading_hours
    if param == "trading_hours":
        if value.lower() == "off":
            return True, "off", None
        try:
            parts = value.split("-")
            if len(parts) != 2:
                return False, None, "Format must be: start-end (e.g., 2-22)"
            start, end = int(parts[0]), int(parts[1])
            if not (0 <= start <= 23 and 0 <= end <= 23):
                return False, None, f"Hours must be between 0 and 23, got: {start}-{end}"
            return True, (start, end), None
        except (ValueError, IndexError):
            return False, None, "Invalid format. Use: start-end (e.g., 2-22) or 'off'"
    
    if param == "gpt_model":
        cleaned = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,64}", cleaned):
            return False, None, "Model name must be 3-64 characters (letters, digits, dot, dash, underscore)"
        return True, cleaned, None

    # Standard validation for other parameters
    validator, parser, allowed_range = validators[param]
    try:
        parsed = parser(value)
        if validator(parsed):
            return True, parsed, None
        else:
            return False, None, f"Value must be {allowed_range}, got: {parsed}"
    except ValueError:
        return False, None, f"Invalid {parser.__name__} value: {value}"


@dp.message(Command("config"))
@require_subscription
@with_error_handling
async def config_handler(message):
    """Настройки через Telegram команды (с валидацией, audit logging и rate limiting)"""
    lang, t = get_user_locale(message)
    user_id = message.chat.id
    
    # 🛡️ ADMIN CHECK - Must be first
    if not is_admin(user_id):
        await message.answer("⚠️ Access denied. Configuration changes are restricted to administrators.")
        await log_security_event(
            user_id=user_id,
            event_type='unauthorized_config_attempt',
            description=f'User {user_id} attempted to access /config without admin privileges',
            severity='medium'
        )
        return
    
    # Check per-user rate limit
    if not await check_user_rate_limit(user_id):
        await log_security_event(
            user_id=user_id,
            event_type='rate_limit_exceeded',
            description=f'User {user_id} exceeded rate limit for config commands',
            severity='medium'
        )
        await message.answer("⏳ Too many requests. Please wait a minute before trying again.")
        return
    
    # Парсим команду /config param=value
    command_text = message.text
    
    # Enhanced input validation
    if not validate_config_input(command_text):
        await log_security_event(
            user_id=user_id,
            event_type='invalid_input',
            description=f'Invalid config command format from user {user_id}',
            severity='low'
        )
        await message.answer("❌ Invalid command format. Only alphanumeric characters, underscores, equals, dashes, and spaces are allowed.")
        return
    
    sanitized_text = sanitize_user_input(command_text, max_length=200)
    if not sanitized_text:
        await message.answer("❌ Invalid command format")
        return
    command_text = sanitized_text
        
    if "=" not in command_text:
        await message.answer(
            "📝 Usage:\n"
            "/config min_score=55\n"
            "/config min_confidence=45\n"
            "/config trading_hours=2-22\n"
            "/config trading_hours=off\n"
            "/config max_signals=15\n"
        )
        return
    
    param, value = command_text.split("=", 1)
    param = param.split()[-1].strip()  # Берем последнее слово после /config
    value = value.strip()
    
    # Parameter whitelist check
    if param not in ALLOWED_CONFIG_PARAMS:
        await log_security_event(
            user_id=user_id,
            event_type='invalid_parameter',
            description=f'User {user_id} attempted to use unknown parameter: {param}',
            severity='low'
        )
        await message.answer(f"❌ Unknown parameter: {param}\n\nAvailable: {', '.join(sorted(ALLOWED_CONFIG_PARAMS))}")
        return
    
    # Validate parameter value using helper function
    is_valid, parsed_value, error_msg = validate_config_value(param, value)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Обновляем CONFIG с валидацией и lock
    updated = False
    old_value = None
    
    # Используем глобальный lock для безопасного изменения CONFIG
    async with config_lock:
        if param == "min_score":
            old_value = CONFIG["min_signal_score"]
            CONFIG["min_signal_score"] = parsed_value
            updated = True
                
        elif param == "min_confidence":
            old_value = CONFIG["min_confidence"]
            CONFIG["min_confidence"] = parsed_value
            updated = True
                
        elif param == "trading_hours":
            if isinstance(parsed_value, str) and parsed_value == "off":
                old_value = f"{CONFIG['trading_start_hour']}-{CONFIG['trading_end_hour']} (enabled)"
                CONFIG["trading_hours_enabled"] = False
                updated = True
            elif isinstance(parsed_value, tuple) and len(parsed_value) == 2:
                start, end = parsed_value
                old_value = f"{CONFIG['trading_start_hour']}-{CONFIG['trading_end_hour']}"
                CONFIG["trading_start_hour"] = start
                CONFIG["trading_end_hour"] = end
                CONFIG["trading_hours_enabled"] = True
                updated = True
            else:
                await message.answer(f"❌ Invalid trading_hours value type: {type(parsed_value)}")
                return
                    
        elif param == "max_signals":
            old_value = CONFIG["max_signals_per_hour"]
            CONFIG["max_signals_per_hour"] = parsed_value
            updated = True
        
        elif param == "gpt_weight":
            old_value = CONFIG.get("gpt_weight", CONFIG.get("gpt_weight_min", 0.05))
            new_weight = max(0.0, min(1.0, float(parsed_value)))
            CONFIG["gpt_weight"] = new_weight
            CONFIG["ta_weight"] = max(0.0, min(1.0, 1.0 - new_weight))
            parsed_value = new_weight  # normalized float for logging
            updated = True
        
        elif param == "gpt_model":
            old_value = CONFIG.get("gpt_model", "gpt-4o-mini")
            CONFIG["gpt_model"] = parsed_value
            updated = True
        
        elif param == "gpt_timeout":
            old_value = CONFIG.get("gpt_request_timeout", 3.0)
            CONFIG["gpt_request_timeout"] = parsed_value
            updated = True
        
        elif param == "gpt_wait":
            old_value = CONFIG.get("gpt_wait_timeout", 2.0)
            CONFIG["gpt_wait_timeout"] = parsed_value
            updated = True
        
        elif param == "gpt_temperature":
            old_value = CONFIG.get("gpt_temperature", 0.1)
            CONFIG["gpt_temperature"] = parsed_value
            updated = True
    
    if updated:
        # Audit logging for config changes
        await log_config_change(user_id, param, old_value, parsed_value)
        await message.answer(f"✅ Updated: {param} = {old_value} → {parsed_value}")
    else:
        await message.answer(f"❌ Failed to update parameter: {param}")


@dp.message(Command("reset_rate"))
@require_subscription
@with_error_handling
async def reset_rate_handler(message):
    """Manually clear per-user rate limit cache."""
    user_id = message.chat.id

    if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
        await message.answer("❌ Only authorized admins can reset rate limits. Set ADMIN_USER_IDS in .env.")
        return

    async with user_rate_lock:
        cleared_users = len(USER_RATE_LIMITS)
        USER_RATE_LIMITS.clear()

    await cleanup_user_rate_limits()
    await log_admin_action(user_id, "reset_rate_limits", {"cleared_users": cleared_users})

    await message.answer(f"✅ Rate limits cleared for {cleared_users} users.")

@dp.message(Command("backtest"))
@require_subscription
@with_error_handling
async def backtest_handler(message):
    """Простая система backtesting"""
    lang, t = get_user_locale(message)
    
    # Загружаем исторические сигналы из БД
    signals = await load_recent_signals_from_db(100)  # Последние 100 сигналов
    
    if len(signals) < CONFIG["backtest_min_signals"]:
        await message.answer(f"⚠️ Not enough signals for backtesting (need at least {CONFIG['backtest_min_signals']})")
        return
    
    # Простой backtesting: считаем win rate
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    sell_signals = [s for s in signals if s['signal'] == 'SELL']
    
    # Для упрощения считаем, что сигнал успешен если confidence > 60
    successful_buys = sum(1 for s in buy_signals if s.get('confidence', 0) > 60)
    successful_sells = sum(1 for s in sell_signals if s.get('confidence', 0) > 60)
    
    total_signals = len(buy_signals) + len(sell_signals)
    successful_total = successful_buys + successful_sells
    
    win_rate = (successful_total / total_signals * 100) if total_signals > 0 else 0
    
    # Средняя confidence
    avg_confidence = sum(s.get('confidence', 0) for s in signals) / len(signals) if signals else 0
    
    text = "📊 **Backtesting Results**\n\n"
    text += f"📈 Total Signals: {total_signals}\n"
    text += f"✅ BUY Signals: {len(buy_signals)} (High confidence: {successful_buys})\n"
    text += f"✅ SELL Signals: {len(sell_signals)} (High confidence: {successful_sells})\n\n"
    text += f"🎯 Estimated Win Rate: {win_rate:.1f}%\n"
    text += f"📊 Average Confidence: {avg_confidence:.1f}%\n\n"
    text += f"⏰ Period: {signals[-1]['time'].strftime('%Y-%m-%d') if isinstance(signals[-1]['time'], datetime) else 'N/A'} to {signals[0]['time'].strftime('%Y-%m-%d') if isinstance(signals[0]['time'], datetime) else 'N/A'}\n"
    
    await message.answer(text, parse_mode=None)

@dp.message(F.text.in_({"📜 ИСТОРИЯ", "📜 HISTORY"}))
@require_subscription
@with_error_handling
async def history_handler(message):
    """Signal history handler"""
    lang, t = get_user_locale(message)
    
    async with history_lock:
        if not SIGNAL_HISTORY:
            await message.answer(t['no_history'])
            return
        # Копия для безопасности (создаем внутри lock)
        history_copy = list(SIGNAL_HISTORY)[-CONFIG["history_display_limit"]:]
    
    text = t['history_title']
    
    for sig in history_copy:
        time_str = format_time(sig['time'], '%H:%M')
        symbol = sig.get('symbol', 'EURUSD')
        text += f"{symbol} {sig['signal']} @ {sig['entry']:.5f} ({time_str})\n"
    
    await message.answer(text, parse_mode=None)

@dp.message(Command("export"))
@require_subscription
@with_error_handling
async def export_handler(message):
    """Export statistics to CSV/JSON"""
    lang, t = get_user_locale(message)
    
    # Загружаем данные из БД
    signals = await load_recent_signals_from_db(CONFIG["history_max_size"])
    
    if not signals:
        await message.answer("No data to export")
        return
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(['timestamp', 'symbol', 'signal', 'price', 'score', 'confidence', 'rsi', 'macd', 'bb_position', 'adx', 'atr'])
    
    # Данные
    for sig in signals:
        indicators = sig.get('indicators', {})
        writer.writerow([
            sig['time'].isoformat() if isinstance(sig['time'], datetime) else str(sig['time']),
            sig.get('symbol', 'EURUSD'),  # Add symbol
            sig['signal'],
            sig['price'],
            sig['score'],
            sig['confidence'],
            indicators.get('rsi', ''),
            indicators.get('macd', ''),
            indicators.get('bb_position', ''),
            indicators.get('adx', ''),
            sig.get('atr', ''),  # Добавляем ATR в экспорт
        ])
    
    csv_data = output.getvalue()
    output.close()
    
    # Отправляем как файл
    try:
        file = BufferedInputFile(csv_data.encode('utf-8'), filename=f"signals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        await message.answer_document(file, caption=f"📊 Exported {len(signals)} signals")
    except Exception as file_error:
        # Fallback: отправляем как текст если BufferedInputFile не работает
        logging.warning(f"Could not send file, sending as text: {file_error}")
        await message.answer(f"📊 Exported {len(signals)} signals\n\nCSV data:\n```csv\n{csv_data[:2000]}\n```", parse_mode=None)

@dp.message(Command("health"))
@require_subscription
@with_error_handling
async def health_handler(message):
    """Health check handler"""
    lang, t = get_user_locale(message)
    
    async with metrics_lock:
        metrics_snapshot = {
            "start_time": METRICS.get("start_time"),
            "api_calls": METRICS.get("api_calls", 0),
            "api_errors": METRICS.get("api_errors", 0),
            "gpt_calls": METRICS.get("gpt_calls", 0),
            "gpt_errors": METRICS.get("gpt_errors", 0),
            "signals_generated": METRICS.get("signals_generated", 0),
        }
    
    async with stats_lock:
        last_signal_time = STATS.get("last_signal_time")
        subscribed_count = len(SUBSCRIBED_USERS)
    
    now = datetime.now()
    uptime_seconds = (
        (now - metrics_snapshot["start_time"]).total_seconds()
        if metrics_snapshot["start_time"]
        else 0
    )
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
            
    total_api = metrics_snapshot["api_calls"] + metrics_snapshot["api_errors"]
    api_error_rate = (
        safe_divide(metrics_snapshot["api_errors"], total_api, 0.0) * 100
        if total_api
        else 0.0
    )
    gpt_error_rate = (
        safe_divide(metrics_snapshot["gpt_errors"], metrics_snapshot["gpt_calls"], 0.0) * 100
        if metrics_snapshot["gpt_calls"]
        else 0.0
    )
    
    health_status = "✅ Healthy"
    issues = []
    if api_error_rate > CONFIG["alert_api_error_rate"]:
        health_status = "⚠️ Degraded"
        issues.append(f"High API error rate: {api_error_rate:.1f}%")
    if gpt_error_rate > CONFIG["alert_gpt_error_rate"]:
        health_status = "⚠️ Degraded"
        issues.append(f"High GPT error rate: {gpt_error_rate:.1f}%")
    
    db_status = "✅ Connected"
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("SELECT 1")
    except Exception as db_error:
        db_status = "❌ Error"
        health_status = "❌ Unhealthy"
        issues.append(f"Database connection failed: {str(db_error)[:80]}")
        logging.error(f"Database health check failed: {db_error}")
    
    if last_signal_time:
        hours_since = (now - last_signal_time).total_seconds() / 3600
        last_signal_text = f"{last_signal_time.strftime('%Y-%m-%d %H:%M:%S')} ({hours_since:.1f}h ago)"
    else:
        last_signal_text = "N/A"
    
    text = f"🏥 **Health Check**\n\n"
    text += f"Status: {health_status}\n"
    text += f"⏱️ Uptime: {hours}h {minutes}m\n"
    text += f"👥 Subscribers: {subscribed_count}\n"
    text += f"📡 API Calls: {metrics_snapshot['api_calls']} (errors: {metrics_snapshot['api_errors']} / {api_error_rate:.1f}%)\n"
    text += f"🤖 GPT Calls: {metrics_snapshot['gpt_calls']} (errors: {metrics_snapshot['gpt_errors']} / {gpt_error_rate:.1f}%)\n"
    text += f"🕒 Last Signal: {last_signal_text}\n"
    text += f"📈 Signals Generated (session): {metrics_snapshot['signals_generated']}\n"
    text += f"💾 Database: {db_status}\n"
    
    if issues:
        text += f"\n⚠️ Issues:\n"
        for issue in issues:
            text += f"• {issue}\n"
    else:
        text += f"\n✅ All systems operational"
    
    await message.answer(text, parse_mode=None)

# ==================== GRACEFUL SHUTDOWN ====================

def setup_signal_handlers():
    """Настройка обработчиков сигналов для graceful shutdown"""
    def signal_handler(sig, frame):
        logging.info("=" * 50)
        logging.info("🛑 Received shutdown signal, shutting down gracefully...")
        logging.info("=" * 50)
        # Останавливаем scheduler
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logging.info("✓ Scheduler stopped")
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Main entry point"""
    # Настройка graceful shutdown
    setup_signal_handlers()
    
    logging.info("=" * 50)
    logging.info("🚀 Enhanced EUR/USD Signal Bot Starting")
    logging.info("=" * 50)
    
    # Инициализация базы данных
    await init_database()
    
    # Загружаем историю из БД при старте
    global SIGNAL_HISTORY
    loaded_signals = await load_recent_signals_from_db(CONFIG["history_max_size"])
    if loaded_signals:
        async with history_lock:
            SIGNAL_HISTORY = deque(loaded_signals, maxlen=CONFIG["history_max_size"])
    
    logging.info(f"Config: Min Score={CONFIG['min_signal_score']}, Confidence={CONFIG['min_confidence']}%")
    logging.info(f"Analysis Interval: {CONFIG['analysis_interval_minutes']} minutes")

    # Настройка scheduler и запуск первой аналитики
    async def main_analysis_with_deps():
        for symbol in CONFIG["symbols"]:
            await main_analysis(symbol=symbol, bot=bot, TEXTS=TEXTS)

    async def check_health_with_deps():
        await check_system_health(bot=bot)

    if not scheduler.running:
        scheduler.add_job(
            main_analysis_with_deps,
            "interval",
            minutes=CONFIG['analysis_interval_minutes'],
            id='main_analysis'
        )
        scheduler.add_job(
            check_health_with_deps,
            "interval",
            minutes=30,
            id='health_check'
        )
        scheduler.add_job(
            backup_database,
            "interval",
            hours=6,
            id='db_backup'
        )
        scheduler.add_job(
            cleanup_user_rate_limits,
            "interval",
            minutes=10,
            id='rate_limit_cleanup'
        )
        scheduler.start()
        logging.info("✓ Scheduler started")

    # Run first analysis immediately
    await main_analysis_with_deps()
    
    # АГРЕССИВНОЕ удаление webhook перед стартом polling
    # Пытаемся несколько раз, так как может быть конфликт с другим экземпляром
    max_webhook_attempts = 5
    webhook_deleted = False
    
    for attempt in range(max_webhook_attempts):
        try:
            logging.info(f"Checking for existing webhook (attempt {attempt + 1}/{max_webhook_attempts})...")
            webhook_info = await bot.get_webhook_info()
            
            if webhook_info.url:
                logging.info(f"⚠️  Found existing webhook: {webhook_info.url}")
                logging.info("Deleting webhook to enable polling...")
                await bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(2)  # Увеличена задержка для обработки Telegram
                
                # Проверяем, что webhook действительно удален
                webhook_info_check = await bot.get_webhook_info()
                if not webhook_info_check.url:
                    logging.info("✓ Webhook deleted successfully")
                    webhook_deleted = True
                    break
                else:
                    logging.warning(f"⚠️  Webhook still exists after deletion attempt {attempt + 1}")
                    await asyncio.sleep(3)  # Ждем дольше перед следующей попыткой
            else:
                logging.info("✓ No webhook found, polling can start")
                webhook_deleted = True
                break
        except Exception as e:
            logging.warning(f"⚠️  Error checking/deleting webhook (attempt {attempt + 1}): {e}")
            if attempt < max_webhook_attempts - 1:
                await asyncio.sleep(3)  # Ждем перед следующей попыткой
            else:
                logging.error("❌ Failed to delete webhook after all attempts")
    
    # Увеличена задержка перед стартом, чтобы старый экземпляр успел завершиться
    logging.info("Waiting 5 seconds before starting polling to ensure old instance is fully stopped...")
    await asyncio.sleep(5)
    
    try:
        # Start bot (aiogram автоматически обрабатывает SIGTERM/SIGINT)
        logging.info("Starting polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        
    except TelegramConflictError as e:
        logging.error(f"❌ Telegram Conflict Error: {e}")
        logging.error("This usually means another bot instance is running.")
        logging.error("Please ensure:")
        logging.error("  1. No other instance is running locally")
        logging.error("  2. Only one Render service is active")
        logging.error("  3. Wait a few minutes and try again")
        
        # АГРЕССИВНАЯ попытка разрешить конфликт
        max_retry_attempts = 3
        for retry_attempt in range(max_retry_attempts):
            try:
                logging.info(f"Attempting to resolve conflict (retry {retry_attempt + 1}/{max_retry_attempts})...")
                
                # Удаляем webhook несколько раз
                for i in range(3):
                    await bot.delete_webhook(drop_pending_updates=True)
                    await asyncio.sleep(2)
                
                # Ждем дольше перед повторной попыткой
                wait_time = (retry_attempt + 1) * 5
                logging.info(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
                
                logging.info("Retrying polling...")
                await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
                logging.info("✓ Successfully started polling after conflict resolution")
                return  # Успешно начали polling
                
            except TelegramConflictError as retry_error:
                if retry_attempt < max_retry_attempts - 1:
                    logging.warning(f"Retry {retry_attempt + 1} failed: {retry_error}, trying again...")
                else:
                    logging.error(f"All retry attempts failed. Last error: {retry_error}")
                    logging.error("❌ Cannot resolve conflict. Please manually stop all bot instances.")
                    raise
            except Exception as retry_error:
                logging.error(f"Retry failed with unexpected error: {retry_error}")
                raise
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        # Cleanup при остановке
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logging.info("✓ Scheduler stopped")
        
        # Сохраняем статистику в БД перед завершением
        await save_stats_to_db()
        
        # Закрываем HTTP session
        await close_http_session()
        
        logging.info("✓ Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutdown complete")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)