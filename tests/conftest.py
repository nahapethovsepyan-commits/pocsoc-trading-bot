"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к основному модулю
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    """Mock CONFIG dictionary"""
    return {
        "pair": "EUR/USD",
        "api_source": "twelvedata",
        "analysis_interval_minutes": 2,
        "min_signal_score": 55,
        "min_confidence": 60,
        "use_gpt": False,  # По умолчанию отключаем GPT для тестов
        "gpt_weight": 0.10,
        "ta_weight": 0.90,
        "gpt_weight_min": 0.05,
        "gpt_weight_max": 0.15,
        "lookback_window": 60,
        "max_signals_per_hour": 12,
        "risk_reward_ratio": 1.8,
        "cache_duration_seconds": 90,
        "stop_loss_pct": 0.002,
        "take_profit_pct": 0.002,
        "atr_sl_multiplier": 2.0,
        "atr_tp_multiplier": 2.5,
        "history_max_size": 100,
        "default_price": 1.0800,
        "trading_hours_enabled": False,  # Отключаем для большинства тестов
        "trading_start_hour": 0,
        "trading_end_hour": 23,
        "alert_api_error_rate": 10.0,
        "alert_gpt_error_rate": 20.0,
        "alert_no_signals_hours": 2,
        "exponential_backoff_base": 2,
        "timezone_offset": 4,
    }

@pytest.fixture
def sample_forex_dataframe():
    """Create a sample DataFrame with forex data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=60, freq='1min')
    # Создаем реалистичные данные EUR/USD
    base_price = 1.0800
    prices = []
    for i in range(60):
        # Добавляем небольшую волатильность
        change = np.random.normal(0, 0.0001)
        price = base_price + change
        prices.append(price)
        base_price = price
    
    df = pd.DataFrame({
        'time': dates,
        'open': prices,
        'high': [p * 1.0002 for p in prices],
        'low': [p * 0.9998 for p in prices],
        'close': prices,
        'volume': [1000] * 60
    })
    return df

@pytest.fixture
def mock_gpt_client():
    """Mock GPT client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "BUY"
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client

@pytest.fixture
def mock_http_session():
    """Mock HTTP session"""
    session = AsyncMock()
    session.get = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    conn.close = AsyncMock()
    return conn

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state before each test"""
    # Импортируем здесь, чтобы избежать проблем с импортом
    import PocSocSig_Enhanced
    from src.models import state as state_module
    from src.signals import utils as signal_utils_module
    PocSocSig_Enhanced.STATS = {
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
    state_module.STATS = PocSocSig_Enhanced.STATS
    state_module.API_CACHE = PocSocSig_Enhanced.API_CACHE
    signal_utils_module.STATS = PocSocSig_Enhanced.STATS
    PocSocSig_Enhanced.SIGNAL_HISTORY = []
    PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
    state_module.SUBSCRIBED_USERS.clear()
    PocSocSig_Enhanced.user_languages.clear()
    state_module.user_languages.clear()
    PocSocSig_Enhanced.API_CACHE.clear()
    yield
    # Cleanup after test
    PocSocSig_Enhanced.STATS = {
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
    state_module.STATS = PocSocSig_Enhanced.STATS
    state_module.API_CACHE = PocSocSig_Enhanced.API_CACHE
    signal_utils_module.STATS = PocSocSig_Enhanced.STATS
    PocSocSig_Enhanced.SIGNAL_HISTORY = []
    PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
    state_module.SUBSCRIBED_USERS.clear()
    PocSocSig_Enhanced.user_languages.clear()
    state_module.user_languages.clear()
    PocSocSig_Enhanced.API_CACHE.clear()


@pytest.fixture(autouse=True)
def stub_aiosqlite_connect():
    """Prevent real aiosqlite connections during tests to avoid thread warnings."""
    from src.database import repository as repository_module

    class DummyCursor:
        async def fetchall(self):
            return []

        async def close(self):
            return None

    class DummyConnection:
        def __init__(self):
            self.row_factory = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, *args, **kwargs):
            return DummyCursor()

        async def commit(self):
            return None

    def _connect_stub(*args, **kwargs):
        return DummyConnection()

    connect_mock = MagicMock(side_effect=_connect_stub)

    with patch.object(repository_module.aiosqlite, "connect", connect_mock), \
         patch("PocSocSig_Enhanced.aiosqlite.connect", connect_mock):
        yield

