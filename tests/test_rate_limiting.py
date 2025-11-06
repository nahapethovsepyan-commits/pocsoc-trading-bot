"""
Unit tests for rate limiting functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestRateLimiting:
    """Test rate limiting for signals"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self):
        """Test that rate limit check passes when under limit"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            PocSocSig_Enhanced.STATS["signals_per_hour"] = 5
            PocSocSig_Enhanced.STATS["hour_start"] = datetime.now()
            
            result = await PocSocSig_Enhanced.check_rate_limit()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test that rate limit check fails when exceeded"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            PocSocSig_Enhanced.STATS["signals_per_hour"] = 12
            PocSocSig_Enhanced.STATS["hour_start"] = datetime.now()
            
            result = await PocSocSig_Enhanced.check_rate_limit()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_hour(self):
        """Test that rate limit resets after an hour"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            # Set hour_start to 2 hours ago
            PocSocSig_Enhanced.STATS["signals_per_hour"] = 15  # Over limit
            PocSocSig_Enhanced.STATS["hour_start"] = datetime.now() - timedelta(hours=2)
            
            result = await PocSocSig_Enhanced.check_rate_limit()
            assert result is True  # Should reset and allow
            assert PocSocSig_Enhanced.STATS["signals_per_hour"] == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_hour(self):
        """Test that rate limit doesn't reset within an hour"""
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            PocSocSig_Enhanced.STATS["signals_per_hour"] = 10
            PocSocSig_Enhanced.STATS["hour_start"] = datetime.now() - timedelta(minutes=30)
            
            result = await PocSocSig_Enhanced.check_rate_limit()
            assert result is True
            assert PocSocSig_Enhanced.STATS["signals_per_hour"] == 10  # Should not reset

