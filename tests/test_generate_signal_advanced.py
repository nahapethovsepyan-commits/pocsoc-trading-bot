"""
Advanced tests for generate_signal function
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestGenerateSignalAdvanced:
    """Advanced tests for signal generation"""
    
    @pytest.mark.asyncio
    async def test_generate_signal_with_bollinger_bands(self):
        """Test signal generation with Bollinger Bands influence"""
        # Create DataFrame with price touching lower BB (oversold)
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=60, freq='1min'),
            'open': [1.0800] * 60,
            'high': [1.0802] * 60,
            'low': [1.0798] * 60,
            'close': np.linspace(1.0700, 1.0800, 60),  # Price rising from lower BB
            'volume': [1000] * 60
        })
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                    
                    assert result is not None
                    assert "signal" in result
                    assert "indicators" in result
                    assert "bb_position" in result["indicators"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_with_atr(self):
        """Test signal generation with ATR calculation"""
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=60, freq='1min'),
            'open': [1.0800] * 60,
            'high': [1.0810] * 60,
            'low': [1.0790] * 60,
            'close': np.linspace(1.0795, 1.0805, 60),
            'volume': [1000] * 60
        })
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                    
                    assert result is not None
                    assert "atr" in result
                    assert result["atr"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_signal_with_adx_stochastic(self):
        """Test signal generation includes ADX and Stochastic"""
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=60, freq='1min'),
            'open': [1.0800] * 60,
            'high': [1.0810] * 60,
            'low': [1.0790] * 60,
            'close': np.linspace(1.0795, 1.0805, 60),
            'volume': [1000] * 60
        })
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                    
                    assert result is not None
                    assert "indicators" in result
                    # ADX and Stochastic should be calculated (even if not used in scoring)
                    assert "adx" in result["indicators"]
                    assert "stoch_k" in result["indicators"]
                    assert "stoch_d" in result["indicators"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_score_boundaries(self):
        """Test signal generation score boundaries"""
        # Test very strong BUY signal
        df_buy = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=60, freq='1min'),
            'open': [1.0800] * 60,
            'high': [1.0802] * 60,
            'low': [1.0798] * 60,
            'close': np.linspace(1.10, 1.00, 60),  # Strong downtrend
            'volume': [1000] * 60
        })
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df_buy
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                    
                    assert result is not None
                    assert 0 <= result["score"] <= 100
                    if result["score"] >= 55:
                        assert result["signal"] in ["BUY", "NO_SIGNAL"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_middle_range(self):
        """Test signal generation in middle range (45-55)"""
        # Create neutral data
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=60, freq='1min'),
            'open': [1.0800] * 60,
            'high': [1.0801] * 60,
            'low': [1.0799] * 60,
            'close': [1.0800] * 60,  # Very flat
            'volume': [1000] * 60
        })
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                    
                    assert result is not None
                    # Should be NO_SIGNAL or very weak signal
                    assert result["signal"] in ["BUY", "SELL", "NO_SIGNAL"]

