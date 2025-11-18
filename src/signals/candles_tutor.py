"""
CandlesTutor integration: свечной анализ через OpenAI с книгой по японским свечам.
"""

import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from ..config import CONFIG, get_openai_client
from ..models.state import METRICS, metrics_lock

# Cooldown для GPT-запросов по инструменту (чтобы не спамить)
_candlestutor_cooldown: Dict[str, datetime] = {}  # symbol -> last_request_time
_cooldown_lock = asyncio.Lock()

# Лимиты на частоту вызовов
MAX_CANDLESTUTOR_CALLS_PER_MINUTE = 5
MAX_CANDLESTUTOR_CALLS_PER_HOUR = 30
_candlestutor_call_times: List[datetime] = []
_calls_lock = asyncio.Lock()


async def check_candlestutor_rate_limit() -> bool:
    """
    Проверка лимитов на вызовы CandlesTutor.
    
    Returns:
        True если можно вызывать, False если лимит превышен
    """
    async with _calls_lock:
        now = datetime.now()
        # Удаляем старые записи (старше часа)
        _candlestutor_call_times[:] = [
            ts for ts in _candlestutor_call_times
            if (now - ts).total_seconds() < 3600
        ]
        
        # Проверяем лимит в час
        if len(_candlestutor_call_times) >= MAX_CANDLESTUTOR_CALLS_PER_HOUR:
            logging.debug(
                f"CandlesTutor hourly limit reached "
                f"({len(_candlestutor_call_times)}/{MAX_CANDLESTUTOR_CALLS_PER_HOUR})"
            )
            return False
        
        # Проверяем лимит в минуту
        recent_calls = [
            ts for ts in _candlestutor_call_times
            if (now - ts).total_seconds() < 60
        ]
        if len(recent_calls) >= MAX_CANDLESTUTOR_CALLS_PER_MINUTE:
            logging.debug(
                f"CandlesTutor per-minute limit reached "
                f"({len(recent_calls)}/{MAX_CANDLESTUTOR_CALLS_PER_MINUTE})"
            )
            return False
        
        return True


async def check_symbol_cooldown(symbol: str, cooldown_minutes: int = 2) -> bool:
    """
    Проверка cooldown для конкретного символа.
    
    Args:
        symbol: Торговый символ
        cooldown_minutes: Минуты между запросами для одного символа
        
    Returns:
        True если можно вызывать, False если в cooldown
    """
    async with _cooldown_lock:
        normalized_symbol = symbol.upper()
        last_call = _candlestutor_cooldown.get(normalized_symbol)
        
        if last_call is None:
            return True
        
        elapsed = (datetime.now() - last_call).total_seconds()
        cooldown_seconds = cooldown_minutes * 60
        if elapsed < cooldown_seconds:
            logging.debug(
                f"CandlesTutor cooldown active for {normalized_symbol} "
                f"({elapsed:.1f}s < {cooldown_seconds}s)"
            )
            return False
        
        return True


def format_candles_for_tutor(df, num_candles: int = 15) -> List[Dict[str, Any]]:
    """
    Форматирует последние свечи для отправки в CandlesTutor.
    
    Args:
        df: DataFrame с колонками ['time', 'open', 'high', 'low', 'close']
        num_candles: Количество последних свечей
        
    Returns:
        Список словарей с OHLC данными
    """
    if df is None or df.empty:
        return []
    
    last_candles = df.tail(num_candles)
    candles_list = []
    
    for _, row in last_candles.iterrows():
        candles_list.append({
            "time": str(row.get("time", "")),
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "close": float(row.get("close", 0)),
        })
    
    return candles_list


async def call_candlestutor(
    symbol: str,
    timeframe: str,
    candles: List[Dict[str, Any]],
    indicators: Dict[str, float],
    candidate_signal: str,  # "BUY" или "SELL"
    ta_score: float,
    ta_confidence: float
) -> Optional[Dict[str, Any]]:
    """
    Вызов CandlesTutor агента через OpenAI API.
    
    Args:
        symbol: Торговый символ (EURUSD, XAUUSD)
        timeframe: Таймфрейм (например, "1min")
        candles: Список последних свечей (OHLC)
        indicators: Словарь с индикаторами (rsi, macd, bb_position, adx, stoch_k, stoch_d)
        candidate_signal: Направление от TA ("BUY" или "SELL")
        ta_score: TA score (0-100)
        ta_confidence: TA confidence (0-100)
        
    Returns:
        Словарь с ответом:
        {
            "decision": "BUY" | "SELL" | "NO_TRADE",
            "pattern": "название паттерна" | "нет",
            "confidence": 0-100,
            "comment": "объяснение"
        }
        или None при ошибке/лимите
    """
    # Проверка включен ли CandlesTutor
    if not CONFIG.get("candlestutor_enabled", True):
        logging.debug("CandlesTutor disabled in config")
        return None
    
    # Проверка лимитов (внутри функции, чтобы генератор не думал об этом)
    if not await check_candlestutor_rate_limit():
        logging.warning("CandlesTutor rate limit exceeded, skipping")
        async with metrics_lock:
            METRICS["candlestutor_errors"] = METRICS.get("candlestutor_errors", 0) + 1
        return None
    
    normalized_symbol = symbol.upper()
    cooldown_minutes = CONFIG.get("candlestutor_cooldown_minutes", 2)
    if not await check_symbol_cooldown(normalized_symbol, cooldown_minutes):
        logging.debug(f"CandlesTutor cooldown active for {normalized_symbol}")
        return None
    
    client, use_gpt = get_openai_client()
    if not CONFIG.get("use_gpt") or not use_gpt or client is None:
        logging.debug("GPT/CandlesTutor disabled (no OpenAI client)")
        return None
    
    # Увеличиваем счетчик вызовов (даже если потом будет ошибка)
    async with metrics_lock:
        METRICS["candlestutor_calls"] = METRICS.get("candlestutor_calls", 0) + 1
    
    # Формируем JSON для отправки
    input_data = {
        "symbol": normalized_symbol,
        "timeframe": timeframe,
        "last_candles": candles,
        "indicators": {
            "rsi": indicators.get("rsi", 0),
            "macd": indicators.get("macd", 0),
            "bb_position": indicators.get("bb_position", 50),
            "adx": indicators.get("adx", 0),
            "stoch_k": indicators.get("stoch_k", 50),
            "stoch_d": indicators.get("stoch_d", 50),
        },
        "candidate_signal": candidate_signal,
        "ta_score": round(ta_score, 1),
        "ta_confidence": round(ta_confidence, 1),
    }
    
    # Системный промпт для CandlesTutor (из CONFIG)
    system_prompt = CONFIG.get(
        "candlestutor_system_prompt",
        DEFAULT_CANDLESTUTOR_SYSTEM_PROMPT
    )
    
    # Пользовательский промпт с JSON
    user_prompt = (
        f"Проанализируй следующие данные рынка и определи свечные паттерны:\n\n"
        f"{json.dumps(input_data, indent=2, ensure_ascii=False)}\n\n"
        f"Используй знания из прикрепленной книги по японским свечам. "
        f"Определи, есть ли четкие свечные паттерны (молот, падающая звезда, поглощение и т.п.). "
        f"Оцени, подтверждают ли они направление candidate_signal ({candidate_signal}). "
        f"Ответь СТРОГО в JSON формате без текста вокруг."
    )
    
    try:
        # Обновляем cooldown
        async with _cooldown_lock:
            _candlestutor_cooldown[normalized_symbol] = datetime.now()
        
        async with _calls_lock:
            _candlestutor_call_times.append(datetime.now())
        
        gpt_model = CONFIG.get("gpt_model", "gpt-4o-mini")
        gpt_temperature = CONFIG.get("gpt_temperature", 0.1)
        gpt_request_timeout = CONFIG.get("gpt_request_timeout", 5.0)  # Увеличено для CandlesTutor
        
        # Вызов OpenAI с принудительным JSON
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        logging.info(
            f"CandlesTutor call: symbol={normalized_symbol}, "
            f"candidate={candidate_signal}, ta_score={ta_score:.1f}, "
            f"ta_conf={ta_confidence:.1f}"
        )
        
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=gpt_model,
                messages=messages,
                max_tokens=200,  # Больше токенов для JSON ответа
                temperature=gpt_temperature,
                response_format={"type": "json_object"},  # Принудительный JSON
            ),
            timeout=gpt_request_timeout
        )
        
        if not resp.choices or len(resp.choices) == 0:
            raise ValueError("Empty response from GPT")
        
        response_text = resp.choices[0].message.content.strip()
        
        # Парсим JSON ответ
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logging.error(f"CandlesTutor returned invalid JSON: {response_text[:200]}")
            # Попытка извлечь JSON из текста
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {e}")
        
        # Валидация структуры ответа
        required_fields = ["decision", "pattern", "confidence", "comment"]
        for field in required_fields:
            if field not in result:
                logging.warning(
                    f"CandlesTutor response missing field '{field}', using defaults"
                )
                if field == "decision":
                    result[field] = "NO_TRADE"
                elif field == "pattern":
                    result[field] = "нет"
                elif field == "confidence":
                    result[field] = 0
                else:
                    result[field] = ""
        
        # Нормализация decision
        decision = result.get("decision", "NO_TRADE").upper()
        if decision not in ("BUY", "SELL", "NO_TRADE"):
            logging.warning(f"Invalid decision '{decision}', defaulting to NO_TRADE")
            decision = "NO_TRADE"
        
        result["decision"] = decision
        result["confidence"] = max(0, min(100, int(result.get("confidence", 0))))
        
        # Нормализация pattern (если пусто/None -> "нет")
        pattern = result.get("pattern", "")
        if not pattern or pattern.strip() == "":
            result["pattern"] = "нет"
        else:
            result["pattern"] = pattern.strip()
        
        async with metrics_lock:
            METRICS["gpt_success"] += 1
            METRICS["candlestutor_success"] = METRICS.get("candlestutor_success", 0) + 1
        
        logging.info(
            f"CandlesTutor response: decision={decision}, "
            f"pattern={result.get('pattern')}, confidence={result.get('confidence')}"
        )
        
        return result
        
    except asyncio.TimeoutError:
        async with metrics_lock:
            METRICS["gpt_errors"] += 1
            METRICS["candlestutor_errors"] = METRICS.get("candlestutor_errors", 0) + 1
        logging.error(f"CandlesTutor request timeout ({gpt_request_timeout}s)")
        return None
        
    except Exception as e:
        async with metrics_lock:
            METRICS["gpt_errors"] += 1
            METRICS["candlestutor_errors"] = METRICS.get("candlestutor_errors", 0) + 1
        error_msg = str(e)[:100] if e else "Unknown error"
        error_type = type(e).__name__
        logging.error(f"CandlesTutor API error [{error_type}]: {error_msg}")
        return None


# Системный промпт по умолчанию для CandlesTutor
# (используется если не задан в CONFIG)
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

