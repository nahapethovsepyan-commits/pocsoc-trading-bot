"""
Unit tests for trading hours functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestTradingHours:
    """Test trading hours checking"""
    
    @pytest.mark.asyncio
    async def test_trading_hours_disabled(self):
        """Test that trading hours check returns True when disabled"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"trading_hours_enabled": False}):
            result = PocSocSig_Enhanced.is_trading_hours()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_trading_hours_normal_range(self):
        """Test trading hours with normal range (e.g., 0-23)"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {
            "trading_hours_enabled": True,
            "trading_start_hour": 0,
            "trading_end_hour": 23
        }):
            # Mock current time to 12:00
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_now = datetime(2025, 1, 1, 12, 0, 0)
                mock_dt.utcnow.return_value = mock_now
                result = PocSocSig_Enhanced.is_trading_hours()
                assert result is True
    
    @pytest.mark.asyncio
    async def test_trading_hours_outside_range(self):
        """Test trading hours outside normal range"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {
            "trading_hours_enabled": True,
            "trading_start_hour": 9,
            "trading_end_hour": 17
        }):
            # Mock current time to 8:00 (outside range)
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_now = datetime(2025, 1, 1, 8, 0, 0)
                mock_dt.utcnow.return_value = mock_now
                result = PocSocSig_Enhanced.is_trading_hours()
                assert result is False
    
    @pytest.mark.asyncio
    async def test_trading_hours_wrapping_range(self):
        """Test trading hours with wrapping range (e.g., 22-2)"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {
            "trading_hours_enabled": True,
            "trading_start_hour": 22,
            "trading_end_hour": 2
        }):
            # Test at 23:00 (should be True)
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_now = datetime(2025, 1, 1, 23, 0, 0)
                mock_dt.utcnow.return_value = mock_now
                result = PocSocSig_Enhanced.is_trading_hours()
                assert result is True
            
            # Test at 1:00 (should be True)
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_now = datetime(2025, 1, 1, 1, 0, 0)
                mock_dt.utcnow.return_value = mock_now
                result = PocSocSig_Enhanced.is_trading_hours()
                assert result is True
            
            # Test at 10:00 (should be False)
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_now = datetime(2025, 1, 1, 10, 0, 0)
                mock_dt.utcnow.return_value = mock_now
                result = PocSocSig_Enhanced.is_trading_hours()
                assert result is False


class TestLocalTime:
    """Test local time conversion"""
    
    @pytest.mark.asyncio
    async def test_get_local_time(self):
        """Test getting local time with timezone offset"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"timezone_offset": 4}):
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_utc = datetime(2025, 1, 1, 12, 0, 0)
                mock_dt.utcnow.return_value = mock_utc
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
                
                local_time = PocSocSig_Enhanced.get_local_time()
                
                # Should be UTC + 4 hours
                expected = mock_utc + timedelta(hours=4)
                assert local_time.hour == expected.hour
    
    @pytest.mark.asyncio
    async def test_get_local_time_zero_offset(self):
        """Test getting local time with zero offset"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"timezone_offset": 0}):
            with patch('PocSocSig_Enhanced.datetime') as mock_dt:
                mock_utc = datetime(2025, 1, 1, 12, 0, 0)
                mock_dt.utcnow.return_value = mock_utc
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
                
                local_time = PocSocSig_Enhanced.get_local_time()
                
                # Should be same as UTC
                assert local_time.hour == mock_utc.hour

