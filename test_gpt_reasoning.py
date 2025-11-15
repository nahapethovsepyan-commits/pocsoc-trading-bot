import pytest
from unittest.mock import AsyncMock, patch
from src.signals.generator import generate_signal

@pytest.mark.asyncio
async def test_generate_signal_with_gpt_reasoning():
    """Тест: генерация сигнала с reasoning от GPT"""
    mock_df = AsyncMock()
    mock_df.empty = False
    mock_df.__getitem__.return_value.iloc.__getitem__.return_value = 1.2345  # mock close price

    mock_indicators = {
        "rsi": 55,
        "macd_diff": 0.01,
        "bb_position": 0.5,
        "adx": 20,
        "atr": 0.001,
        "stochastic": 60,
        "volume_score": 0.5,
        "trend_direction": "UP",
        "momentum_score": 0.4,
        "score": 65,
        "confidence": 70
    }

    mock_reasoning = "Based on RSI and MACD, upward movement is expected."

    with patch("src.signals.generator.is_trading_hours", return_value=True),          patch("src.signals.generator.fetch_forex_data", return_value=mock_df),          patch("src.signals.generator.calculate_indicators_parallel", return_value=mock_indicators),          patch("src.signals.generator.get_openai_client") as mock_gpt:

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value.choices = [
            type("Obj", (), {"message": type("Msg", (), {"content": mock_reasoning})})()
        ]
        mock_gpt.return_value = mock_client

        result = await generate_signal("EURUSD")

    assert result["signal"] in ("BUY", "SELL", "NO_SIGNAL")
    assert result["reasoning"] == mock_reasoning
    assert "confidence" in result
    assert "score" in result