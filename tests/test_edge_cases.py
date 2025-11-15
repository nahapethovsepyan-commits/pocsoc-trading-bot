"""
Unit tests for edge cases and error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_send_alert_no_users(self):
        """Test send_alert when no users subscribed"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        
        # Should not raise error, just return
        await PocSocSig_Enhanced.send_alert("Test alert")
        # Should complete without error
    
    @pytest.mark.asyncio
    async def test_generate_signal_empty_dataframe(self):
        """Test generate_signal with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = empty_df
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                
                # Should return NO_SIGNAL with error
                assert result["signal"] == "NO_SIGNAL"
                assert "Error" in result["reasoning"] or "No market data" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_generate_signal_none_data(self):
        """Test generate_signal when fetch returns None"""
        with patch('src.signals.generator.fetch_forex_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with patch('PocSocSig_Enhanced.is_trading_hours', return_value=True):
                result = await PocSocSig_Enhanced.generate_signal("EURUSD")
                
                # Should return NO_SIGNAL with error
                assert result["signal"] == "NO_SIGNAL"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_edge_cases(self):
        """Test rate limit edge cases"""
        # Test with exactly max signals
        PocSocSig_Enhanced.STATS["signals_per_hour"] = 12
        PocSocSig_Enhanced.STATS["hour_start"] = datetime.now()
        
        with patch.dict(PocSocSig_Enhanced.CONFIG, {"max_signals_per_hour": 12}):
            result = await PocSocSig_Enhanced.check_rate_limit()
            assert result is False  # Should be at limit
    
    @pytest.mark.asyncio
    async def test_send_signal_message_failed_sends(self):
        """Test send_signal_message when some sends fail"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        
        # Add test users
        user1 = 11111
        user2 = 22222
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user1)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(user2)
        PocSocSig_Enhanced.user_languages[user1] = 'ru'
        PocSocSig_Enhanced.user_languages[user2] = 'ru'
        
        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 65,
            "confidence": 60,
            "reasoning": "Test",
            "time": datetime.now(),
            "indicators": {},
            "atr": 0.0003
        }
        
        # Mock bot to fail for one user
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            call_count = 0
            async def mock_send(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Failed to send")
                return MagicMock()
            
            mock_bot.send_message = AsyncMock(side_effect=mock_send)
            
            await PocSocSig_Enhanced.send_signal_message(signal_data)
            
            # Failed user should be removed
            assert user1 not in PocSocSig_Enhanced.SUBSCRIBED_USERS or user2 not in PocSocSig_Enhanced.SUBSCRIBED_USERS
    
    @pytest.mark.asyncio
    async def test_load_recent_signals_from_db_empty(self):
        """Test loading signals from empty database"""
        with patch('src.database.repository.aiosqlite.connect') as mock_connect:
            mock_db = AsyncMock()
            mock_cursor = AsyncMock()
            mock_cursor.fetchall = AsyncMock(return_value=[])
            mock_cursor.close = AsyncMock(return_value=None)
            mock_db.execute.return_value = mock_cursor
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)
            
            signals = await PocSocSig_Enhanced.load_recent_signals_from_db(limit=10)
            
            assert isinstance(signals, list)
            assert len(signals) == 0
    
    @pytest.mark.asyncio
    async def test_save_signal_to_db_invalid_data(self):
        """Test save_signal_to_db with invalid data"""
        invalid_signal = {
            "signal": "BUY",
            # Missing required fields
        }
        
        with patch('src.database.repository.aiosqlite.connect') as mock_connect:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(side_effect=Exception("Invalid data"))
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Should not raise, just log error
            await PocSocSig_Enhanced.save_signal_to_db(invalid_signal)
            # Should complete without raising
    
    @pytest.mark.asyncio
    async def test_main_analysis_no_subscribers(self):
        """Test main_analysis when no subscribers"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        
        # Should return early without error
        await PocSocSig_Enhanced.main_analysis("EURUSD")
        # Should complete without error
    
    @pytest.mark.asyncio
    async def test_main_analysis_outside_trading_hours(self):
        """Test main_analysis outside trading hours"""
        # Add user
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        with patch('PocSocSig_Enhanced.is_trading_hours', return_value=False):
            # Should return early without error
            await PocSocSig_Enhanced.main_analysis()
            # Should complete without error
    
    @pytest.mark.asyncio
    async def test_check_system_health_no_errors(self):
        """Test check_system_health when no errors"""
        # Set metrics with no errors
        PocSocSig_Enhanced.METRICS["api_calls"] = 100
        PocSocSig_Enhanced.METRICS["api_errors"] = 0
        PocSocSig_Enhanced.METRICS["gpt_calls"] = 50
        PocSocSig_Enhanced.METRICS["gpt_errors"] = 0
        PocSocSig_Enhanced.STATS["last_signal_time"] = datetime.now()
        
        # Should complete without sending alerts
        await PocSocSig_Enhanced.check_system_health()
        # Should complete without error

