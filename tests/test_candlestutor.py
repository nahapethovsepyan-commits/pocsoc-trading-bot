"""
Unit tests for CandlesTutor integration.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
from src.signals.candles_tutor import (
    call_candlestutor,
    format_candles_for_tutor,
    check_candlestutor_rate_limit,
    check_symbol_cooldown,
    MAX_CANDLESTUTOR_CALLS_PER_MINUTE,
    MAX_CANDLESTUTOR_CALLS_PER_HOUR,
    _candlestutor_call_times,
    _candlestutor_cooldown,
    DEFAULT_CANDLESTUTOR_SYSTEM_PROMPT,
)


BASE_CONFIG = {
    "candlestutor_enabled": True,
    "candlestutor_cooldown_minutes": 0,
    "gpt_model": "gpt-4o-mini",
    "gpt_temperature": 0.1,
    "gpt_request_timeout": 5.0,
    "candlestutor_system_prompt": DEFAULT_CANDLESTUTOR_SYSTEM_PROMPT,
    "use_gpt": True,
    "candlestutor_min_confidence": 60,
}


@pytest.mark.asyncio
async def test_format_candles_for_tutor():
    """Тест форматирования свечей для CandlesTutor."""
    df = pd.DataFrame({
        "time": ["2024-01-01 10:00", "2024-01-01 10:01", "2024-01-01 10:02"],
        "open": [1.08, 1.081, 1.082],
        "high": [1.085, 1.086, 1.087],
        "low": [1.079, 1.080, 1.081],
        "close": [1.084, 1.085, 1.086],
    })
    
    candles = format_candles_for_tutor(df, num_candles=2)
    
    assert len(candles) == 2
    assert candles[0]["open"] == 1.081
    assert candles[1]["close"] == 1.086
    assert "time" in candles[0]
    assert "high" in candles[0]
    assert "low" in candles[0]


@pytest.mark.asyncio
async def test_format_candles_empty():
    """Тест форматирования пустого DataFrame."""
    df = pd.DataFrame()
    candles = format_candles_for_tutor(df)
    assert candles == []


@pytest.mark.asyncio
async def test_call_candlestutor_success():
    """Тест успешного вызова CandlesTutor."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "decision": "BUY",
        "pattern": "Молот",
        "confidence": 75,
        "comment": "Молот после даунтренда, подтверждает BUY"
    })
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(mock_client, True)):
        with patch("src.signals.candles_tutor.CONFIG", BASE_CONFIG):
            with patch("src.signals.candles_tutor.check_candlestutor_rate_limit", new_callable=AsyncMock, return_value=True):
                with patch("src.signals.candles_tutor.check_symbol_cooldown", new_callable=AsyncMock, return_value=True):
                    result = await call_candlestutor(
                        symbol="EURUSD",
                        timeframe="1min",
                        candles=[{"time": "2024-01-01", "open": 1.08, "high": 1.09, "low": 1.07, "close": 1.085}],
                        indicators={"rsi": 55, "macd": 0.001, "bb_position": 50, "adx": 25, "stoch_k": 60, "stoch_d": 55},
                        candidate_signal="BUY",
                        ta_score=65,
                        ta_confidence=70
                    )
    
    assert result is not None
    assert result["decision"] == "BUY"
    assert result["pattern"] == "Молот"
    assert result["confidence"] == 75
    assert result["comment"] == "Молот после даунтренда, подтверждает BUY"


@pytest.mark.asyncio
async def test_call_candlestutor_disabled():
    """Тест когда CandlesTutor отключен."""
    with patch("src.signals.candles_tutor.CONFIG", {
        "candlestutor_enabled": False,
    }):
        result = await call_candlestutor(
            symbol="EURUSD",
            timeframe="1min",
            candles=[],
            indicators={},
            candidate_signal="BUY",
            ta_score=65,
            ta_confidence=70
        )
    
    assert result is None


@pytest.mark.asyncio
async def test_call_candlestutor_invalid_json():
    """Тест обработки невалидного JSON ответа."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Это не JSON текст"
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(mock_client, True)):
        with patch("src.signals.candles_tutor.CONFIG", BASE_CONFIG):
            with patch("src.signals.candles_tutor.check_candlestutor_rate_limit", new_callable=AsyncMock, return_value=True):
                with patch("src.signals.candles_tutor.check_symbol_cooldown", new_callable=AsyncMock, return_value=True):
                    result = await call_candlestutor(
                        symbol="EURUSD",
                        timeframe="1min",
                        candles=[],
                        indicators={},
                        candidate_signal="BUY",
                        ta_score=65,
                        ta_confidence=70
                    )
    
    # При невалидном JSON должна быть ошибка и None
    assert result is None


@pytest.mark.asyncio
async def test_call_candlestutor_timeout():
    """Тест обработки timeout."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()
    
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(mock_client, True)):
        with patch("src.signals.candles_tutor.CONFIG", BASE_CONFIG):
            with patch("src.signals.candles_tutor.check_candlestutor_rate_limit", new_callable=AsyncMock, return_value=True):
                with patch("src.signals.candles_tutor.check_symbol_cooldown", new_callable=AsyncMock, return_value=True):
                    result = await call_candlestutor(
                        symbol="EURUSD",
                        timeframe="1min",
                        candles=[],
                        indicators={},
                        candidate_signal="BUY",
                        ta_score=65,
                        ta_confidence=70
                    )
    
    assert result is None


@pytest.mark.asyncio
async def test_call_candlestutor_missing_fields():
    """Тест обработки ответа с отсутствующими полями."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "decision": "BUY",
        # pattern отсутствует
        "confidence": 75,
        # comment отсутствует
    })
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(mock_client, True)):
        with patch("src.signals.candles_tutor.CONFIG", BASE_CONFIG):
            with patch("src.signals.candles_tutor.check_candlestutor_rate_limit", new_callable=AsyncMock, return_value=True):
                with patch("src.signals.candles_tutor.check_symbol_cooldown", new_callable=AsyncMock, return_value=True):
                    result = await call_candlestutor(
                        symbol="EURUSD",
                        timeframe="1min",
                        candles=[],
                        indicators={},
                        candidate_signal="BUY",
                        ta_score=65,
                        ta_confidence=70
                    )
    
    assert result is not None
    assert result["decision"] == "BUY"
    assert result["pattern"] == "нет"  # Должно быть по умолчанию
    assert result["confidence"] == 75
    assert result["comment"] == ""  # Должно быть по умолчанию


@pytest.mark.asyncio
async def test_call_candlestutor_normalize_decision():
    """Тест нормализации decision."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "decision": "buy",  # lowercase
        "pattern": "Молот",
        "confidence": 75,
        "comment": "Test"
    })
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(mock_client, True)):
        with patch("src.signals.candles_tutor.CONFIG", BASE_CONFIG):
            with patch("src.signals.candles_tutor.check_candlestutor_rate_limit", new_callable=AsyncMock, return_value=True):
                with patch("src.signals.candles_tutor.check_symbol_cooldown", new_callable=AsyncMock, return_value=True):
                    result = await call_candlestutor(
                        symbol="EURUSD",
                        timeframe="1min",
                        candles=[],
                        indicators={},
                        candidate_signal="BUY",
                        ta_score=65,
                        ta_confidence=70
                    )
    
    assert result is not None
    assert result["decision"] == "BUY"  # Должно быть uppercase


@pytest.mark.asyncio
async def test_check_candlestutor_rate_limit():
    """Тест проверки rate limit."""
    # Очищаем историю вызовов
    _candlestutor_call_times.clear()
    
    # Первые вызовы должны проходить
    for _ in range(MAX_CANDLESTUTOR_CALLS_PER_MINUTE):
        result = await check_candlestutor_rate_limit()
        assert result is True
        _candlestutor_call_times.append(datetime.now())
    
    # После превышения лимита в минуту должен вернуть False
    result = await check_candlestutor_rate_limit()
    assert result is False
    
    # Очищаем после теста
    _candlestutor_call_times.clear()


@pytest.mark.asyncio
async def test_check_symbol_cooldown():
    """Тест проверки cooldown по символу."""
    symbol = "EURUSD"
    cooldown_minutes = 2
    
    # Очищаем cooldown
    _candlestutor_cooldown.clear()
    
    # Первый вызов должен пройти
    result = await check_symbol_cooldown(symbol, cooldown_minutes)
    assert result is True
    
    # Устанавливаем cooldown вручную
    _candlestutor_cooldown[symbol.upper()] = datetime.now()
    
    # Второй вызов сразу после должен быть заблокирован
    result = await check_symbol_cooldown(symbol, cooldown_minutes)
    assert result is False
    
    # Очищаем после теста
    _candlestutor_cooldown.clear()


@pytest.mark.asyncio
async def test_call_candlestutor_no_openai_client():
    """Тест когда OpenAI client недоступен."""
    with patch("src.signals.candles_tutor.get_openai_client", return_value=(None, False)):
        with patch("src.signals.candles_tutor.CONFIG", {
            "candlestutor_enabled": True,
            "use_gpt": False,
        }):
            result = await call_candlestutor(
                symbol="EURUSD",
                timeframe="1min",
                candles=[],
                indicators={},
                candidate_signal="BUY",
                ta_score=65,
                ta_confidence=70
            )
    
    assert result is None

