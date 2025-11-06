"""
Unit tests for additional Telegram handlers
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestMoreHandlers:
    """Test additional Telegram handlers"""
    
    @pytest.mark.asyncio
    async def test_stats_handler(self):
        """Test stats handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribers (required by @require_subscription decorator)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Set up stats
        PocSocSig_Enhanced.STATS["total_signals"] = 10
        PocSocSig_Enhanced.STATS["BUY"] = 6
        PocSocSig_Enhanced.STATS["SELL"] = 4
        PocSocSig_Enhanced.STATS["wins"] = 7
        PocSocSig_Enhanced.STATS["losses"] = 3
        PocSocSig_Enhanced.STATS["AI_signals"] = 5
        
        # Set up metrics
        PocSocSig_Enhanced.METRICS["start_time"] = datetime.now() - timedelta(hours=2)
        PocSocSig_Enhanced.METRICS["api_calls"] = 100
        PocSocSig_Enhanced.METRICS["api_errors"] = 5
        PocSocSig_Enhanced.METRICS["gpt_calls"] = 50
        PocSocSig_Enhanced.METRICS["gpt_success"] = 45
        PocSocSig_Enhanced.METRICS["gpt_errors"] = 5
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.stats_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_stop_handler(self):
        """Test stop handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.stop_handler(mock_message)
            
            # Check user was removed
            assert 12345 not in PocSocSig_Enhanced.SUBSCRIBED_USERS
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_settings_handler(self):
        """Test settings handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribers (required by @require_subscription decorator)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.settings_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_history_handler(self):
        """Test history handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribers (required by @require_subscription decorator)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Add some signals to history
        PocSocSig_Enhanced.SIGNAL_HISTORY = [
            {
                "signal": "BUY",
                "price": 1.0800,
                "score": 65,
                "time": datetime.now(),
                "indicators": {"rsi": 30.5}
            },
            {
                "signal": "SELL",
                "price": 1.0850,
                "score": 35,
                "time": datetime.now(),
                "indicators": {"rsi": 75.5}
            }
        ]
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.history_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_history_handler_empty(self):
        """Test history handler with empty history"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Clear history
        PocSocSig_Enhanced.SIGNAL_HISTORY = []
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.history_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_health_handler(self):
        """Test health check handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribers (required by @require_subscription decorator)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Set up metrics
        PocSocSig_Enhanced.METRICS["api_calls"] = 100
        PocSocSig_Enhanced.METRICS["api_errors"] = 5
        PocSocSig_Enhanced.METRICS["gpt_calls"] = 50
        PocSocSig_Enhanced.METRICS["gpt_errors"] = 2
        PocSocSig_Enhanced.METRICS["signals_generated"] = 10
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.health_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_export_handler(self):
        """Test export statistics handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Set up stats
        PocSocSig_Enhanced.STATS["total_signals"] = 10
        PocSocSig_Enhanced.STATS["BUY"] = 6
        PocSocSig_Enhanced.STATS["SELL"] = 4
        
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_document = AsyncMock()
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.export_handler(mock_message)
            
            # Check document was sent (or error handled)
            assert mock_bot.send_document.called or mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_metrics_handler(self):
        """Test metrics handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribers (required by @require_subscription decorator)
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Set up metrics
        PocSocSig_Enhanced.METRICS["start_time"] = datetime.now() - timedelta(hours=1)
        PocSocSig_Enhanced.METRICS["api_calls"] = 50
        PocSocSig_Enhanced.METRICS["api_errors"] = 2
        PocSocSig_Enhanced.METRICS["avg_response_time"] = 0.5
        
        with patch('PocSocSig_Enhanced.bot'):
            mock_message.answer = AsyncMock()
            
            await PocSocSig_Enhanced.metrics_handler(mock_message)
            
            # Check message was sent
            assert mock_message.answer.called

