"""
Advanced tests for check_system_health
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestHealthCheckAdvanced:
    """Advanced tests for system health checks"""
    
    @pytest.mark.asyncio
    async def test_check_system_health_api_errors_high(self):
        """Test health check with high API error rate"""
        # Set high error rate
        PocSocSig_Enhanced.METRICS["api_calls"] = 50
        PocSocSig_Enhanced.METRICS["api_errors"] = 10  # 20% error rate (> 10% threshold)
        
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.ALERT_HISTORY.clear()
        
        with patch('src.monitoring.health.send_alert', new_callable=AsyncMock) as mock_alert:
            await PocSocSig_Enhanced.check_system_health()
            
            # Should send alert
            assert mock_alert.called
    
    @pytest.mark.asyncio
    async def test_check_system_health_gpt_errors_high(self):
        """Test health check with high GPT error rate"""
        # Set high GPT error rate
        PocSocSig_Enhanced.METRICS["gpt_calls"] = 50
        PocSocSig_Enhanced.METRICS["gpt_errors"] = 15  # 30% error rate (> 20% threshold)
        
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.ALERT_HISTORY.clear()
        
        with patch('src.monitoring.health.send_alert', new_callable=AsyncMock) as mock_alert:
            await PocSocSig_Enhanced.check_system_health()
            
            # Should send alert
            assert mock_alert.called
    
    @pytest.mark.asyncio
    async def test_check_system_health_no_signals_long_time(self):
        """Test health check with no signals for long time"""
        # Set last signal time to 3 hours ago
        PocSocSig_Enhanced.STATS["last_signal_time"] = datetime.now() - timedelta(hours=3)
        
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.ALERT_HISTORY.clear()
        
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"alert_no_signals_hours": 2}):
            with patch('src.monitoring.health.send_alert', new_callable=AsyncMock) as mock_alert:
                await PocSocSig_Enhanced.check_system_health()
                
                # Should send alert
                assert mock_alert.called
    
    @pytest.mark.asyncio
    async def test_check_system_health_alert_cooldown(self):
        """Test health check respects alert cooldown"""
        # Set high error rate
        PocSocSig_Enhanced.METRICS["api_calls"] = 50
        PocSocSig_Enhanced.METRICS["api_errors"] = 10
        
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        # Set recent alert (within cooldown)
        PocSocSig_Enhanced.ALERT_HISTORY["api_error"] = datetime.now() - timedelta(minutes=30)
        
        with patch('src.monitoring.health.send_alert', new_callable=AsyncMock) as mock_alert:
            await PocSocSig_Enhanced.check_system_health()
            
            # Should NOT send alert (cooldown active)
            assert not mock_alert.called
    
    @pytest.mark.asyncio
    async def test_check_system_health_no_users(self):
        """Test health check when no users subscribed"""
        # Clear users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        
        # Set high error rate
        PocSocSig_Enhanced.METRICS["api_calls"] = 50
        PocSocSig_Enhanced.METRICS["api_errors"] = 10
        
        with patch('src.monitoring.health.send_alert', new_callable=AsyncMock) as mock_alert:
            await PocSocSig_Enhanced.check_system_health()
            
            # Should not send alert (no users)
            assert not mock_alert.called

