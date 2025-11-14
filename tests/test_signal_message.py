"""
Unit tests for send_signal_message function
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import PocSocSig_Enhanced
from src.models.state import SUBSCRIBED_USERS as STATE_SUBSCRIBERS, user_languages as STATE_LANGUAGES


class TestSendSignalMessage:
    """Test send_signal_message function"""
    
    @pytest.mark.asyncio
    async def test_send_signal_message_buy(self):
        """Test sending BUY signal message"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        STATE_SUBSCRIBERS.add(test_user_id)
        STATE_LANGUAGES[test_user_id] = 'ru'
        
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
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            lang='ru',
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )
        
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
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        STATE_SUBSCRIBERS.add(test_user_id)
        STATE_LANGUAGES[test_user_id] = 'ru'
        
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
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            lang='ru',
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )
        
        # Check message was sent
        assert mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_no_users(self):
        """Test sending signal when no users subscribed"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        STATE_SUBSCRIBERS.clear()
        
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
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )
        
        # Should not send message if no users
        assert not mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_no_signal(self):
        """Test sending NO_SIGNAL message"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        STATE_SUBSCRIBERS.add(test_user_id)
        STATE_LANGUAGES[test_user_id] = 'ru'
        
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
        
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )
        
        # NO_SIGNAL should not trigger outbound messages
        assert not mock_bot.send_message.called
    
    @pytest.mark.asyncio
    async def test_send_signal_message_dynamic_recommendations(self):
        """Test dynamic PocketOption recommendations based on score and ATR"""
        # Clear subscribed users
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()
        
        # Add test user
        test_user_id = 12345
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'ru'
        STATE_SUBSCRIBERS.add(test_user_id)
        STATE_LANGUAGES[test_user_id] = 'ru'
        
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
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        
        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )
        
        # Check message was sent
        assert mock_bot.send_message.called
        # Check that message contains recommendations
        message_text = mock_bot.send_message.call_args[0][1]
        assert "POCKETOPTION" in message_text or "Рекомендации" in message_text

    @pytest.mark.asyncio
    async def test_send_signal_message_extreme_vol_uses_seconds(self):
        """High volatility should produce sub-minute expiration text"""
        PocSocSig_Enhanced.SUBSCRIBED_USERS.clear()
        PocSocSig_Enhanced.user_languages.clear()
        STATE_SUBSCRIBERS.clear()
        STATE_LANGUAGES.clear()

        test_user_id = 98765
        PocSocSig_Enhanced.SUBSCRIBED_USERS.add(test_user_id)
        PocSocSig_Enhanced.user_languages[test_user_id] = 'en'
        STATE_SUBSCRIBERS.add(test_user_id)
        STATE_LANGUAGES[test_user_id] = 'en'

        signal_data = {
            "signal": "BUY",
            "price": 1.0800,
            "score": 80,
            "confidence": 75,
            "reasoning": "Extreme volatility test",
            "time": datetime.now(),
            "indicators": {},
            "atr": 0.005  # ~0.46% ATR -> should map to 10 seconds
        }

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        await PocSocSig_Enhanced.send_signal_message(
            signal_data,
            bot=mock_bot,
            TEXTS=PocSocSig_Enhanced.TEXTS
        )

        assert mock_bot.send_message.called
        message_text = mock_bot.send_message.call_args[0][1]
        assert "Expiration: 10 seconds" in message_text

