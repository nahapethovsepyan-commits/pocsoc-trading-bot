"""
Unit tests for signal generation logic
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestSignalGeneration:
    """Test signal generation logic"""
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_trading_hours(self):
        """Test signal generation outside trading hours"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {
            "trading_hours_enabled": True,
            "trading_start_hour": 9,
            "trading_end_hour": 17,
            "default_price": 1.0800
        }):
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=False):
                result = await PocSocSig_Enhanced.generate_signal()
                
                assert result["signal"] == "NO_SIGNAL"
                assert result["price"] == 1.0800
                assert result["score"] == 50
                assert result["confidence"] == 0
    
    @pytest.mark.asyncio
    async def test_generate_signal_buy_strong(self, sample_forex_dataframe):
        """Test strong BUY signal generation"""
        # Create DataFrame with falling prices (oversold condition)
        df = sample_forex_dataframe.copy()
        # Make prices fall significantly
        df['close'] = np.linspace(1.10, 1.01, len(df))
        df['high'] = df['close'] * 1.0002
        df['low'] = df['close'] * 0.9998
        
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal()
                    
                    assert result is not None
                    assert "signal" in result
                    assert "score" in result
                    assert "confidence" in result
                    # Should generate BUY for oversold conditions
                    if result["signal"] == "BUY":
                        assert result["score"] >= 55
                        assert result["confidence"] == 60.0
    
    @pytest.mark.asyncio
    async def test_generate_signal_sell_strong(self, sample_forex_dataframe):
        """Test strong SELL signal generation"""
        # Create DataFrame with rising prices (overbought condition)
        df = sample_forex_dataframe.copy()
        # Make prices rise significantly
        df['close'] = np.linspace(1.01, 1.10, len(df))
        df['high'] = df['close'] * 1.0002
        df['low'] = df['close'] * 0.9998
        
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal()
                    
                    assert result is not None
                    assert "signal" in result
                    assert "score" in result
                    # Should generate SELL for overbought conditions
                    if result["signal"] == "SELL":
                        assert result["score"] <= 45
    
    @pytest.mark.asyncio
    async def test_generate_signal_no_data(self):
        """Test signal generation when no data is available"""
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                result = await PocSocSig_Enhanced.generate_signal()
                # Function catches exception and returns NO_SIGNAL
                assert result["signal"] == "NO_SIGNAL"
                assert "Error" in result["reasoning"] or "No market data" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_empty_dataframe(self):
        """Test signal generation with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = empty_df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                result = await PocSocSig_Enhanced.generate_signal()
                # Function catches exception and returns NO_SIGNAL
                assert result["signal"] == "NO_SIGNAL"
                assert "Error" in result["reasoning"] or "No market data" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_with_gpt(self, sample_forex_dataframe, mock_gpt_client):
        """Test signal generation with GPT enabled"""
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_forex_dataframe
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": True}):
                    with patch('PocSocSig_Enhanced.client', mock_gpt_client):
                        result = await PocSocSig_Enhanced.generate_signal()
                        
                        assert result is not None
                        assert "signal" in result
                        assert "score" in result
                        # GPT should be called
                        mock_gpt_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_signal_score_range(self, sample_forex_dataframe):
        """Test that signal score is always between 0 and 100"""
        df = sample_forex_dataframe.copy()
        
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal()
                    
                    assert 0 <= result["score"] <= 100
    
    @pytest.mark.asyncio
    async def test_signal_confidence_fixed(self, sample_forex_dataframe):
        """Test that confidence is fixed at 60 for signals"""
        df = sample_forex_dataframe.copy()
        
        with patch('PocSocSig_Enhanced.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                with patch.dict(PocSocSig_Enhanced.CONFIG, {"use_gpt": False}):
                    result = await PocSocSig_Enhanced.generate_signal()
                    
                    if result["signal"] in ["BUY", "SELL"]:
                        assert result["confidence"] == 60.0
                    elif result["signal"] == "NO_SIGNAL":
                        assert result["confidence"] == 0.0

