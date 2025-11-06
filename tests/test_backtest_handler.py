"""
Unit tests for backtest_handler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestBacktestHandler:
    """Test backtest handler"""
    
    @pytest.mark.asyncio
    async def test_backtest_handler(self):
        """Test backtest handler"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.answer = AsyncMock()
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Add some signals to database
        with patch('PocSocSig_Enhanced.load_recent_signals_from_db', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [
                {
                    "signal": "BUY",
                    "price": 1.0800,
                    "score": 65,
                    "confidence": 60,
                    "time": datetime.now(),
                    "atr": 0.0003
                },
                {
                    "signal": "SELL",
                    "price": 1.0850,
                    "score": 35,
                    "confidence": 60,
                    "time": datetime.now(),
                    "atr": 0.0004
                }
            ]
            
            with patch('PocSocSig_Enhanced.bot'):
                await PocSocSig_Enhanced.backtest_handler(mock_message)
                
                # Check message was sent
                assert mock_message.answer.called
    
    @pytest.mark.asyncio
    async def test_backtest_handler_no_signals(self):
        """Test backtest handler with no signals"""
        # Mock message
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.answer = AsyncMock()
        PocSocSig_Enhanced.user_languages[12345] = 'ru'
        
        # Add user to subscribed
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(12345)
        
        # Mock empty database
        with patch('PocSocSig_Enhanced.load_recent_signals_from_db', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = []
            
            with patch('PocSocSig_Enhanced.bot'):
                await PocSocSig_Enhanced.backtest_handler(mock_message)
                
                # Check message was sent
                assert mock_message.answer.called

