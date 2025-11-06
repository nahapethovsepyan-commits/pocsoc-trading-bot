"""
Unit tests for send_signal_message function
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced


class TestSendSignalMessage:
    """Test send_signal_message function"""
    
    @pytest.mark.asyncio
    async def test_send_signal_message_buy(self):
        """Test sending BUY signal message"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        
        # Create signal data
        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 65,
            "confidence": 60,
            "reasoning": "Test BUY signal",
            "time": datetime.now(),
            "entry": 1.0800,
            "indicators": {
                "rsi": 30.5,
                "macd": 0.0001,
                "bb_position": 10.0,
                "atr": 0.0003,
                "adx": 25.0,
                "stoch_k": 20.0,
                "stoch_d": 18.0
            },
            "atr": 0.0003
        }
        
        # Mock bot
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_signal_message(signal_data, lang='ru')
            
            # Check message was sent
            assert mock_bot.send_message.called
            call_args = mock_bot.send_message.call_args
            # chat_id is the first positional argument
            assert call_args[0][0] == test_user_id
    
    @pytest.mark.asyncio
    async def test_send_signal_message_sell(self):
        """Test sending SELL signal message"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        
        # Create signal data
        signal_data = {
            "signal": "SELL",
            "price": 1.0850,
            "score": 35,
            "confidence": 60,
            "reasoning": "Test SELL signal",
            "time": datetime.now(),
            "entry": 1.0850,
            "indicators": {
                "rsi": 75.5,
                "macd": -0.0001,
                "bb_position": 90.0,
                "atr": 0.0004,
                "adx": 30.0,
                "stoch_k": 80.0,
                "stoch_d": 82.0
            },
            "atr": 0.0004
        }
        
        # Mock bot
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_signal_message(signal_data, lang='ru')
            
            # Check message was sent
            assert mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_no_users(self):
        """Test sending signal when no users subscribed"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        
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
        
        # Mock bot
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_signal_message(signal_data)
            
            # Should not send message if no users
            assert not mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_no_signal(self):
        """Test sending NO_SIGNAL message"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        
        signal_data = {
            "signal": "NO_SIGNAL",
            "price": 1.0800,
            "score": 50,
            "confidence": 0,
            "reasoning": "No clear signal",
            "time": datetime.now(),
            "indicators": {},
            "atr": None
        }
        
        # Mock bot
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_signal_message(signal_data)
            
            # Check message was sent
            assert mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_dynamic_recommendations(self):
        """Test dynamic PocketOption recommendations based on score and ATR"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        
        # Test strong signal (high score, high confidence)
        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 75,  # High score
            "confidence": 70,  # High confidence
            "reasoning": "Strong signal",
            "time": datetime.now(),
            "indicators": {},
            "atr": 0.0005  # Medium volatility
        }
        
        # Mock bot
        with patch('PocSocSig_Enhanced.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await PocSocSig_Enhanced.send_signal_message(signal_data)
            
            # Check message was sent
            assert mock_bot.send_message.called
            # Check that message contains recommendations
            message_text = mock_bot.send_message.call_args[0][1]
            assert "POCKETOPTION" in message_text or "Рекомендации" in message_text

