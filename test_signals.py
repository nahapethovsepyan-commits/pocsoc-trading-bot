import pytest
from src.signals.generator import generate_signal

@pytest.mark.asyncio
async def test_generate_signal_eurusd():
    """Проверка, что generate_signal возвращает корректный результат"""
    result = await generate_signal("EURUSD")
    assert isinstance(result, dict)
    assert "signal" in result
    assert "symbol" in result
    assert result["symbol"] == "EURUSD"